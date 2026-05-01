from __future__ import annotations

import base64
import json
import math
import re
from datetime import datetime
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import Settings


class VisionAnalysisError(RuntimeError):
    """Raised when a local image payload cannot be analyzed safely."""


class VisionService:
    max_upload_bytes = 12 * 1024 * 1024

    def __init__(
        self,
        settings: Settings,
        *,
        request_executor: Callable[[dict[str, Any]], Mapping[str, Any]] | None = None,
        now_provider: Callable[[], datetime] | None = None,
    ) -> None:
        self.settings = settings
        self._request_executor = request_executor
        self._now_provider = now_provider or (lambda: datetime.now().astimezone())

    def status(self) -> dict[str, Any]:
        model = (self.settings.vision_model or "").strip()
        ready = bool(self.settings.llm_api_key and model)
        return {
            "ready": ready,
            "provider": "openai_compatible" if ready else "local_only",
            "mode": "multimodal" if ready else "metadata_only",
            "model": model or None,
            "max_upload_bytes": self.max_upload_bytes,
        }

    def analyze_data_url(
        self,
        data_url: str,
        *,
        filename: str = "",
        prompt: str = "",
    ) -> dict[str, Any]:
        media_type, image_bytes = decode_image_data_url(data_url)
        return self.analyze_image_bytes(
            image_bytes,
            media_type=media_type,
            filename=filename,
            prompt=prompt,
        )

    def analyze_image_bytes(
        self,
        image_bytes: bytes,
        *,
        media_type: str = "",
        filename: str = "",
        prompt: str = "",
    ) -> dict[str, Any]:
        if not image_bytes:
            raise VisionAnalysisError("No image data was provided.")
        if len(image_bytes) > self.max_upload_bytes:
            raise VisionAnalysisError("The image is too large for local analysis.")

        image = probe_image_metadata(image_bytes, filename=filename, media_type=media_type)
        warnings: list[str] = []
        summary = build_local_summary(image, prompt=prompt)
        model = self.status()

        if model["ready"]:
            try:
                summary = self._analyze_with_model(
                    image_bytes=image_bytes,
                    media_type=image["media_type"],
                    image=image,
                    prompt=prompt,
                )
            except Exception as exc:
                warnings.append(f"Multimodal analysis fallback: {format_exception(exc)}")

        return {
            "captured_at": self._now_provider().isoformat(),
            "image": image,
            "summary": summary,
            "model": model,
            "warnings": warnings,
        }

    def _analyze_with_model(
        self,
        *,
        image_bytes: bytes,
        media_type: str,
        image: Mapping[str, Any],
        prompt: str,
    ) -> dict[str, Any]:
        payload = self._build_request_payload(
            data_url=encode_image_data_url(image_bytes, media_type=media_type),
            image=image,
            prompt=prompt,
        )
        response_payload = (
            self._request_executor(payload)
            if self._request_executor is not None
            else self._send_request(payload)
        )
        content = self._extract_content(response_payload)
        parsed = self._extract_json_object(content)
        summary = coerce_summary_payload(parsed)
        summary["provider"] = "openai_compatible"
        summary["mode"] = "multimodal"
        summary["model"] = self.settings.vision_model or None
        return summary

    def _build_request_payload(
        self,
        *,
        data_url: str,
        image: Mapping[str, Any],
        prompt: str,
    ) -> dict[str, Any]:
        focus_prompt = prompt.strip() or "Describe the screenshot clearly, highlight important UI elements, and call out any errors or next actions."
        metadata_line = (
            f"Format: {image.get('format', 'unknown')}, "
            f"size: {image.get('width') or '?'} x {image.get('height') or '?'} pixels, "
            f"orientation: {image.get('orientation') or 'unknown'}."
        )
        instruction = (
            "Analyze the user-provided image for a local-first desktop assistant.\n"
            "Return exactly one JSON object with keys: overview (string), key_points (array of short strings), "
            "visible_text (array of short strings), suggested_actions (array of short strings), "
            "contains_sensitive_content (boolean or null).\n"
            "Only describe what is visually present. If something is unclear, say so briefly.\n"
            f"User focus: {focus_prompt}\n"
            f"Image metadata: {metadata_line}"
        )
        return {
            "model": self.settings.vision_model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": "You analyze screenshots and images and return strict JSON only.",
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": instruction},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ],
        }

    def _send_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = Request(
            url=f"{self.settings.llm_base_url.rstrip('/')}/chat/completions",
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.settings.llm_api_key}",
            },
            data=json.dumps(payload).encode("utf-8"),
        )
        try:
            with urlopen(request, timeout=self.settings.llm_timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {body or exc.reason}") from exc
        except URLError as exc:
            raise RuntimeError(str(exc.reason)) from exc

    def _extract_content(self, response_payload: Mapping[str, Any]) -> str:
        choices = response_payload.get("choices")
        if isinstance(choices, list) and choices:
            message = choices[0].get("message", {})
            content = message.get("content", "")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                parts: list[str] = []
                for item in content:
                    if not isinstance(item, Mapping):
                        continue
                    text = item.get("text")
                    if text:
                        parts.append(str(text))
                if parts:
                    return "\n".join(parts)
        raise ValueError("Vision response did not contain assistant content.")

    def _extract_json_object(self, content: str) -> dict[str, Any]:
        stripped = content.strip()
        if not stripped:
            raise ValueError("Vision response was empty.")
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            fenced_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", stripped, flags=re.DOTALL)
            if fenced_match is not None:
                return json.loads(fenced_match.group(1))
            start = stripped.find("{")
            end = stripped.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(stripped[start : end + 1])
            raise


def decode_image_data_url(data_url: str) -> tuple[str, bytes]:
    text = str(data_url or "").strip()
    if not text.startswith("data:"):
        raise VisionAnalysisError("Expected an image data URL.")
    header, separator, payload = text.partition(",")
    if separator != "," or ";base64" not in header.lower():
        raise VisionAnalysisError("Only base64 image data URLs are supported.")
    media_type = header[5:].split(";")[0].strip().lower() or "application/octet-stream"
    if not media_type.startswith("image/"):
        raise VisionAnalysisError("Only image uploads are supported.")
    try:
        return media_type, base64.b64decode(payload, validate=True)
    except Exception as exc:  # pragma: no cover - defensive path
        raise VisionAnalysisError("The image payload could not be decoded.") from exc


def encode_image_data_url(image_bytes: bytes, *, media_type: str) -> str:
    return f"data:{media_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"


def probe_image_metadata(image_bytes: bytes, *, filename: str = "", media_type: str = "") -> dict[str, Any]:
    file_name = sanitize_filename(filename, default="capture")
    detected = detect_image_type(image_bytes, media_type=media_type, filename=file_name)
    width, height = detected["width"], detected["height"]
    orientation = "unknown"
    aspect_ratio = None
    megapixels = None
    if width and height:
        if width > height:
            orientation = "landscape"
        elif height > width:
            orientation = "portrait"
        else:
            orientation = "square"
        aspect_ratio = format_aspect_ratio(width, height)
        megapixels = round((width * height) / 1_000_000, 2)
    return {
        "filename": file_name,
        "media_type": detected["media_type"],
        "format": detected["format"],
        "bytes": len(image_bytes),
        "size_label": format_byte_size(len(image_bytes)),
        "width": width,
        "height": height,
        "orientation": orientation,
        "aspect_ratio": aspect_ratio,
        "megapixels": megapixels,
    }


def detect_image_type(image_bytes: bytes, *, media_type: str = "", filename: str = "") -> dict[str, Any]:
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n") and len(image_bytes) >= 24:
        return {
            "format": "png",
            "media_type": media_type or "image/png",
            "width": int.from_bytes(image_bytes[16:20], "big"),
            "height": int.from_bytes(image_bytes[20:24], "big"),
        }
    if image_bytes.startswith((b"GIF87a", b"GIF89a")) and len(image_bytes) >= 10:
        return {
            "format": "gif",
            "media_type": media_type or "image/gif",
            "width": int.from_bytes(image_bytes[6:8], "little"),
            "height": int.from_bytes(image_bytes[8:10], "little"),
        }
    if image_bytes.startswith(b"BM") and len(image_bytes) >= 26:
        return {
            "format": "bmp",
            "media_type": media_type or "image/bmp",
            "width": int.from_bytes(image_bytes[18:22], "little", signed=True),
            "height": abs(int.from_bytes(image_bytes[22:26], "little", signed=True)),
        }
    if image_bytes.startswith(b"\xff\xd8\xff"):
        width, height = parse_jpeg_dimensions(image_bytes)
        return {
            "format": "jpeg",
            "media_type": media_type or "image/jpeg",
            "width": width,
            "height": height,
        }
    if image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP":
        width, height = parse_webp_dimensions(image_bytes)
        return {
            "format": "webp",
            "media_type": media_type or "image/webp",
            "width": width,
            "height": height,
        }
    fallback_media_type = media_type or guess_media_type_from_filename(filename) or "application/octet-stream"
    return {
        "format": media_type_to_format(fallback_media_type),
        "media_type": fallback_media_type,
        "width": None,
        "height": None,
    }


def parse_jpeg_dimensions(image_bytes: bytes) -> tuple[int | None, int | None]:
    index = 2
    while index < len(image_bytes):
        if image_bytes[index] != 0xFF:
            index += 1
            continue
        while index < len(image_bytes) and image_bytes[index] == 0xFF:
            index += 1
        if index >= len(image_bytes):
            break
        marker = image_bytes[index]
        index += 1
        if marker in {0xD8, 0xD9}:
            continue
        if marker == 0xDA:
            break
        if index + 2 > len(image_bytes):
            break
        segment_length = int.from_bytes(image_bytes[index : index + 2], "big")
        if segment_length < 2 or index + segment_length > len(image_bytes):
            break
        if marker in {
            0xC0,
            0xC1,
            0xC2,
            0xC3,
            0xC5,
            0xC6,
            0xC7,
            0xC9,
            0xCA,
            0xCB,
            0xCD,
            0xCE,
            0xCF,
        } and index + 7 < len(image_bytes):
            height = int.from_bytes(image_bytes[index + 3 : index + 5], "big")
            width = int.from_bytes(image_bytes[index + 5 : index + 7], "big")
            return width, height
        index += segment_length
    return None, None


def parse_webp_dimensions(image_bytes: bytes) -> tuple[int | None, int | None]:
    if len(image_bytes) < 30:
        return None, None
    chunk_type = image_bytes[12:16]
    if chunk_type == b"VP8X" and len(image_bytes) >= 30:
        width = 1 + int.from_bytes(image_bytes[24:27], "little")
        height = 1 + int.from_bytes(image_bytes[27:30], "little")
        return width, height
    if chunk_type == b"VP8 " and len(image_bytes) >= 30:
        width = int.from_bytes(image_bytes[26:28], "little") & 0x3FFF
        height = int.from_bytes(image_bytes[28:30], "little") & 0x3FFF
        return width, height
    if chunk_type == b"VP8L" and len(image_bytes) >= 25:
        bits = int.from_bytes(image_bytes[21:25], "little")
        width = (bits & 0x3FFF) + 1
        height = ((bits >> 14) & 0x3FFF) + 1
        return width, height
    return None, None


def build_local_summary(image: Mapping[str, Any], *, prompt: str = "") -> dict[str, Any]:
    format_label = str(image.get("format") or "image").upper()
    width = image.get("width")
    height = image.get("height")
    orientation = str(image.get("orientation") or "unknown")
    size_label = str(image.get("size_label") or "")
    overview = f"Captured a {format_label} image"
    if width and height:
        overview = f"{overview} sized {width} x {height} pixels"
    if size_label:
        overview = f"{overview} ({size_label})"
    overview = (
        f"{overview}. No multimodal vision model is configured, so this local analysis is limited to image metadata."
    )
    key_points = [
        f"Orientation: {orientation}.",
        f"File size: {size_label}.",
    ]
    if width and height:
        key_points.insert(0, f"Resolution: {width} x {height} pixels.")
    if image.get("aspect_ratio"):
        key_points.append(f"Aspect ratio: {image['aspect_ratio']}.")
    if prompt.strip():
        key_points.append(f"Requested focus: {prompt.strip()}.")
    return {
        "provider": "local",
        "mode": "metadata_only",
        "overview": overview,
        "key_points": key_points[:5],
        "visible_text": [],
        "suggested_actions": [
            "Add a focused prompt if you want the model to concentrate on a dialog, chart, or error state.",
            "Configure ZIVRA_VISION_MODEL with an OpenAI-compatible multimodal model for scene-level summaries.",
        ],
        "contains_sensitive_content": None,
    }


def coerce_summary_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    def coerce_list(name: str, limit: int) -> list[str]:
        raw = payload.get(name)
        if isinstance(raw, list):
            values = [str(item).strip() for item in raw if str(item).strip()]
            return values[:limit]
        return []

    sensitive = payload.get("contains_sensitive_content")
    if sensitive not in {True, False, None}:
        sensitive = None
    overview = str(payload.get("overview", "")).strip() or "The image was analyzed, but no overview was returned."
    return {
        "overview": overview,
        "key_points": coerce_list("key_points", 5),
        "visible_text": coerce_list("visible_text", 8),
        "suggested_actions": coerce_list("suggested_actions", 4),
        "contains_sensitive_content": sensitive,
    }


def sanitize_filename(filename: str, *, default: str) -> str:
    cleaned = re.sub(r"[^\w.\- ]+", "", str(filename or "").strip())
    return cleaned[:120] or default


def media_type_to_format(media_type: str) -> str:
    if "/" in media_type:
        return media_type.split("/", 1)[1].lower()
    return "unknown"


def guess_media_type_from_filename(filename: str) -> str | None:
    lowered = filename.lower()
    if lowered.endswith(".png"):
        return "image/png"
    if lowered.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if lowered.endswith(".gif"):
        return "image/gif"
    if lowered.endswith(".bmp"):
        return "image/bmp"
    if lowered.endswith(".webp"):
        return "image/webp"
    return None


def format_byte_size(size_in_bytes: int) -> str:
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    if size_in_bytes < 1024 * 1024:
        return f"{round(size_in_bytes / 1024, 1)} KB"
    return f"{round(size_in_bytes / (1024 * 1024), 2)} MB"


def format_aspect_ratio(width: int, height: int) -> str:
    divisor = math.gcd(width, height) or 1
    return f"{width // divisor}:{height // divisor}"


def format_exception(exc: Exception) -> str:
    message = str(exc).strip()
    return message or exc.__class__.__name__

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from typing import Any, Callable
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from app.services.prompt_injection import PromptInjectionDefense


class WebPageUnavailableError(RuntimeError):
    """Raised when a webpage cannot be fetched or parsed safely."""


@dataclass(slots=True)
class FetchedPage:
    url: str
    content_type: str
    text: str
    title: str = ""
    headings: list[str] | None = None


class _ReadableHtmlParser(HTMLParser):
    BLOCK_TAGS = {
        "address",
        "article",
        "aside",
        "blockquote",
        "br",
        "dd",
        "div",
        "dt",
        "fieldset",
        "figcaption",
        "figure",
        "footer",
        "form",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "hr",
        "li",
        "main",
        "nav",
        "ol",
        "p",
        "pre",
        "section",
        "table",
        "td",
        "th",
        "tr",
        "ul",
    }
    SKIP_TAGS = {"script", "style", "noscript", "template", "svg"}
    HEADING_TAGS = {"h1", "h2", "h3"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._title_depth = 0
        self._current_heading: str | None = None
        self._text_parts: list[str] = []
        self._title_parts: list[str] = []
        self._heading_parts: list[str] = []
        self._headings: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # noqa: ANN001
        lowered = tag.lower()
        if lowered in self.SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if lowered == "title":
            self._title_depth += 1
            return
        if lowered in self.HEADING_TAGS:
            self._current_heading = lowered
            self._heading_parts = []
        if lowered in self.BLOCK_TAGS:
            self._text_parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered in self.SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._skip_depth:
            return
        if lowered == "title":
            self._title_depth = max(0, self._title_depth - 1)
            return
        if lowered in self.HEADING_TAGS and self._current_heading == lowered:
            heading = self._collapse("".join(self._heading_parts))
            if heading:
                self._headings.append(heading)
            self._current_heading = None
            self._heading_parts = []
        if lowered in self.BLOCK_TAGS:
            self._text_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        cleaned = unescape(data or "")
        if self._title_depth:
            self._title_parts.append(cleaned)
            return
        if self._current_heading is not None:
            self._heading_parts.append(cleaned)
        self._text_parts.append(cleaned)

    def as_payload(self) -> tuple[str, str, list[str]]:
        title = self._collapse("".join(self._title_parts))
        content = self._collapse("".join(self._text_parts), preserve_lines=True)
        headings = [heading for heading in (self._collapse(item) for item in self._headings) if heading]
        return title, content, headings

    def _collapse(self, value: str, *, preserve_lines: bool = False) -> str:
        if not preserve_lines:
            return re.sub(r"\s+", " ", value).strip()
        normalized = value.replace("\r", "")
        normalized = re.sub(r"[ \t\f\v]+", " ", normalized)
        normalized = re.sub(r"\n\s*\n\s*\n+", "\n\n", normalized)
        return normalized.strip()


class WebPageService:
    USER_AGENT = "Zivra/0.1 (+https://local.zivra)"

    def __init__(
        self,
        *,
        fetcher: Callable[[str], FetchedPage] | None = None,
        prompt_injection_defense: PromptInjectionDefense | None = None,
        timeout_seconds: float = 12.0,
        max_bytes: int = 400_000,
        max_content_chars: int = 12_000,
    ) -> None:
        self._fetcher = fetcher or self._default_fetch
        self.prompt_injection_defense = prompt_injection_defense or PromptInjectionDefense()
        self.timeout_seconds = timeout_seconds
        self.max_bytes = max_bytes
        self.max_content_chars = max_content_chars

    def read_page(self, url: str) -> dict[str, Any]:
        normalized_url = self._normalize_url(url)
        fetched = self._fetcher(normalized_url)
        content_signal = self.prompt_injection_defense.sanitize_text(fetched.text)
        heading_signal = self.prompt_injection_defense.filter_items(fetched.headings or [])
        security = self.prompt_injection_defense.merge_metadata(content_signal, heading_signal)
        content = self._truncate_content(content_signal["sanitized_text"])
        if not content and security.get("prompt_injection_detected"):
            content = "Suspicious instruction-like content was removed from this untrusted source."
        headings = list(heading_signal.get("items", []))[:6]
        title = fetched.title or self._title_from_url(fetched.url)
        word_count = len(re.findall(r"\b\w+\b", content))
        return {
            "url": fetched.url,
            "title": title,
            "content": content,
            "preview": self._extract_preview(content),
            "headings": headings,
            "source_kind": self._classify_content_type(fetched.content_type),
            "content_type": fetched.content_type,
            "word_count": word_count,
            "character_count": len(content),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "security": security,
        }

    def summarize_page(self, url: str) -> dict[str, Any]:
        page = self.read_page(url)
        summary = self._build_summary(page)
        return {"page": page, "summary": summary}

    def audit_payload(self, page: dict[str, Any]) -> dict[str, Any]:
        return {
            "url": page["url"],
            "title": page["title"],
            "source_kind": page.get("source_kind", "web"),
            "content_type": page.get("content_type", ""),
            "word_count": page.get("word_count", 0),
            "character_count": page.get("character_count", 0),
            "fetched_at": page.get("fetched_at", ""),
            "security": self.prompt_injection_defense.to_metadata(page.get("security", {})),
        }

    def summary_audit_payload(self, summary: dict[str, Any]) -> dict[str, Any]:
        return {
            "key_point_count": len(summary.get("key_points", [])),
            "heading_count": len(summary.get("headings", [])),
            "estimated_read_time_minutes": summary.get("estimated_read_time_minutes", 0),
            "security": self.prompt_injection_defense.to_metadata(summary.get("security", {})),
        }

    def _default_fetch(self, url: str) -> FetchedPage:
        request = Request(
            url,
            headers={
                "User-Agent": self.USER_AGENT,
                "Accept": "text/html,text/plain;q=0.9,*/*;q=0.1",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read(self.max_bytes + 1)
                final_url = response.geturl()
                content_type_header = response.headers.get("Content-Type", "text/html")
        except Exception as exc:  # pragma: no cover - network failure normalization
            raise WebPageUnavailableError(str(exc)) from exc

        if len(raw) > self.max_bytes:
            raw = raw[: self.max_bytes]

        content_type = content_type_header.split(";", 1)[0].strip().lower() or "text/html"
        if content_type not in {"text/html", "text/plain", "application/xhtml+xml"}:
            raise WebPageUnavailableError(f"Unsupported content type: {content_type}")

        charset_match = re.search(r"charset=([A-Za-z0-9._-]+)", content_type_header, flags=re.IGNORECASE)
        charset = charset_match.group(1) if charset_match else "utf-8"
        decoded = raw.decode(charset, errors="ignore")

        if content_type in {"text/plain"}:
            content = self._normalize_plain_text(decoded)
            return FetchedPage(
                url=final_url,
                content_type=content_type,
                title=self._title_from_url(final_url),
                text=content,
                headings=[],
            )

        parser = _ReadableHtmlParser()
        parser.feed(decoded)
        title, content, headings = parser.as_payload()
        if not content:
            raise WebPageUnavailableError("No readable page content was found.")
        return FetchedPage(
            url=final_url,
            content_type=content_type,
            title=title,
            text=content,
            headings=headings,
        )

    def _normalize_url(self, url: str) -> str:
        normalized = str(url or "").strip()
        if not normalized:
            raise WebPageUnavailableError("A webpage URL is required.")
        if "://" not in normalized:
            normalized = f"https://{normalized}"
        parsed = urlparse(normalized)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise WebPageUnavailableError("Only http and https webpage URLs are supported.")
        return normalized

    def _classify_content_type(self, content_type: str) -> str:
        if content_type == "text/plain":
            return "text"
        return "html"

    def _normalize_plain_text(self, text: str) -> str:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        normalized = re.sub(r"\n\s*\n\s*\n+", "\n\n", normalized)
        return normalized.strip()

    def _truncate_content(self, text: str) -> str:
        normalized = self._normalize_plain_text(text)
        if len(normalized) <= self.max_content_chars:
            return normalized
        return f"{normalized[: self.max_content_chars].rstrip()}..."

    def _extract_preview(self, text: str) -> str:
        sentences = self._collect_sentences(text)
        for sentence in sentences:
            if len(sentence) >= 40:
                return sentence[:220]
        return text[:220]

    def _collect_sentences(self, text: str) -> list[str]:
        normalized = re.sub(r"\s+", " ", text).strip()
        if not normalized:
            return []
        return [segment.strip() for segment in re.split(r"(?<=[.!?])\s+", normalized) if segment.strip()]

    def _build_summary(self, page: dict[str, Any]) -> dict[str, Any]:
        content = str(page.get("content", ""))
        sentences = self._collect_sentences(content)
        overview = next((sentence[:260] for sentence in sentences if len(sentence) >= 50), page.get("preview", ""))
        headings = list(page.get("headings", []))[:5]
        key_points: list[str] = []
        for heading in headings[:3]:
            key_points.append(heading)
        for sentence in sentences:
            if len(key_points) >= 4:
                break
            if sentence not in key_points:
                key_points.append(sentence[:180])
        return {
            "overview": overview or "No summary available.",
            "key_points": key_points[:4],
            "headings": headings,
            "estimated_read_time_minutes": max(1, round(int(page.get("word_count", 0)) / 200)) if page.get("word_count") else 1,
            "security": self.prompt_injection_defense.to_metadata(page.get("security", {})),
        }

    def _title_from_url(self, url: str) -> str:
        parsed = urlparse(url)
        host = parsed.netloc or "webpage"
        path = parsed.path.rstrip("/").split("/")[-1]
        return path or host

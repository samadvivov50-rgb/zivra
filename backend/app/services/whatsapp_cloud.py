from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request

from app.core.config import Settings


class WhatsAppCloudError(RuntimeError):
    def __init__(self, message: str, *, status_code: int = 0, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.details = details or {}


def _mask_identifier(value: str) -> str:
    cleaned = str(value or "").strip()
    if not cleaned:
        return ""
    if len(cleaned) <= 6:
        return "*" * len(cleaned)
    return f"{cleaned[:3]}...{cleaned[-3:]}"


class WhatsAppCloudClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def is_configured(self) -> bool:
        return bool(self.settings.whatsapp_phone_number_id.strip() and self.settings.whatsapp_access_token.strip())

    def status(self) -> dict[str, Any]:
        return {
            "channel": "whatsapp",
            "cloud_configured": self.is_configured(),
            "api_version": self.settings.whatsapp_api_version.strip() or "v23.0",
            "phone_number_id_masked": _mask_identifier(self.settings.whatsapp_phone_number_id),
            "verify_token_configured": bool(self.settings.whatsapp_verify_token.strip()),
            "signature_validation": bool(self.settings.whatsapp_app_secret.strip()),
            "webhook_path": "/messages/whatsapp/webhook",
        }

    def send_text_message(self, *, to_number: str, body: str) -> dict[str, Any]:
        if not self.is_configured():
            raise WhatsAppCloudError(
                "WhatsApp Cloud API is not configured yet. Add a phone number ID and access token first."
            )

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": str(to_number or "").strip(),
            "type": "text",
            "text": {
                "preview_url": False,
                "body": str(body or "").strip(),
            },
        }
        endpoint = (
            f"https://graph.facebook.com/{self.settings.whatsapp_api_version.strip() or 'v23.0'}/"
            f"{self.settings.whatsapp_phone_number_id.strip()}/messages"
        )
        headers = {
            "Authorization": f"Bearer {self.settings.whatsapp_access_token.strip()}",
            "Content-Type": "application/json",
        }
        response = self._request_json("POST", endpoint, payload, headers=headers)
        message_id = ""
        messages = response.get("messages")
        if isinstance(messages, list) and messages:
            message_id = str(messages[0].get("id") or "")
        return {
            "message_id": message_id,
            "response": response,
        }

    def verify_webhook(self, *, mode: str, verify_token: str, challenge: str) -> str:
        if mode != "subscribe":
            raise WhatsAppCloudError("WhatsApp webhook verification mode was invalid.", status_code=403)
        expected = self.settings.whatsapp_verify_token.strip()
        if not expected:
            raise WhatsAppCloudError(
                "WhatsApp webhook verification is not configured yet. Add a verify token in Settings first.",
                status_code=503,
            )
        if verify_token != expected:
            raise WhatsAppCloudError("WhatsApp webhook verification token did not match.", status_code=403)
        return challenge

    def validate_signature(self, body: bytes, signature_header: str | None) -> bool:
        app_secret = self.settings.whatsapp_app_secret.strip()
        if not app_secret:
            return True
        if not signature_header:
            return False
        expected = "sha256=" + hmac.new(app_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature_header.strip())

    def parse_webhook_events(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        for entry in payload.get("entry") or []:
            if not isinstance(entry, dict):
                continue
            for change in entry.get("changes") or []:
                if not isinstance(change, dict):
                    continue
                value = change.get("value") or {}
                if not isinstance(value, dict):
                    continue
                contacts = value.get("contacts") or []
                contacts_by_id = {
                    str(contact.get("wa_id") or ""): str((contact.get("profile") or {}).get("name") or "").strip()
                    for contact in contacts
                    if isinstance(contact, dict)
                }
                metadata = value.get("metadata") or {}
                phone_number_id = str(metadata.get("phone_number_id") or "").strip()
                display_phone_number = str(metadata.get("display_phone_number") or "").strip()

                for message in value.get("messages") or []:
                    if not isinstance(message, dict):
                        continue
                    sender_digits = "".join(ch for ch in str(message.get("from") or "") if ch.isdigit())
                    timestamp = self._normalize_timestamp(message.get("timestamp"))
                    message_type = str(message.get("type") or "unknown").strip() or "unknown"
                    events.append(
                        {
                            "event_type": "message",
                            "provider": "cloud_api",
                            "provider_message_id": str(message.get("id") or "").strip(),
                            "direction": "inbound",
                            "status": "received",
                            "phone_digits": sender_digits,
                            "to_number": f"+{sender_digits}" if sender_digits else str(message.get("from") or "").strip(),
                            "contact_name": contacts_by_id.get(sender_digits, ""),
                            "body": self._extract_message_body(message),
                            "message_type": message_type,
                            "remote_timestamp": timestamp,
                            "source": "whatsapp_cloud",
                            "metadata": {
                                "phone_number_id": phone_number_id,
                                "display_phone_number": display_phone_number,
                                "context_id": str((message.get("context") or {}).get("id") or "").strip(),
                            },
                        }
                    )

                for status in value.get("statuses") or []:
                    if not isinstance(status, dict):
                        continue
                    recipient_digits = "".join(ch for ch in str(status.get("recipient_id") or "") if ch.isdigit())
                    errors = status.get("errors") or []
                    error_text = ""
                    if isinstance(errors, list) and errors:
                        first = errors[0] if isinstance(errors[0], dict) else {}
                        error_text = str(first.get("title") or first.get("message") or "").strip()
                    events.append(
                        {
                            "event_type": "status",
                            "provider": "cloud_api",
                            "provider_message_id": str(status.get("id") or "").strip(),
                            "status": str(status.get("status") or "").strip() or "unknown",
                            "phone_digits": recipient_digits,
                            "to_number": f"+{recipient_digits}" if recipient_digits else str(status.get("recipient_id") or "").strip(),
                            "error": error_text,
                            "remote_timestamp": self._normalize_timestamp(status.get("timestamp")),
                            "metadata": {
                                "conversation_id": str((status.get("conversation") or {}).get("id") or "").strip(),
                                "pricing_category": str((status.get("pricing") or {}).get("category") or "").strip(),
                                "phone_number_id": phone_number_id,
                                "display_phone_number": display_phone_number,
                            },
                        }
                    )
        return events

    def _request_json(
        self,
        method: str,
        url: str,
        payload: dict[str, Any],
        *,
        headers: dict[str, str],
    ) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib_request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib_request.urlopen(request, timeout=20) as response:
                raw = response.read().decode("utf-8")
                parsed = json.loads(raw or "{}")
                if isinstance(parsed, dict):
                    return parsed
                raise WhatsAppCloudError("WhatsApp Cloud API returned an unexpected response payload.")
        except urllib_error.HTTPError as exc:
            response_body = exc.read().decode("utf-8", errors="replace")
            details = self._safe_json(response_body)
            error_payload = details.get("error") if isinstance(details, dict) else {}
            if not isinstance(error_payload, dict):
                error_payload = {}
            message = str(error_payload.get("message") or response_body or exc.reason or "WhatsApp Cloud API request failed.")
            raise WhatsAppCloudError(message, status_code=exc.code, details=details if isinstance(details, dict) else {}) from exc
        except urllib_error.URLError as exc:
            raise WhatsAppCloudError(f"WhatsApp Cloud API network error: {exc.reason}") from exc

    def _extract_message_body(self, message: dict[str, Any]) -> str:
        message_type = str(message.get("type") or "").strip()
        if message_type == "text":
            return str((message.get("text") or {}).get("body") or "").strip()
        if message_type == "button":
            return str((message.get("button") or {}).get("text") or "").strip()
        if message_type == "interactive":
            interactive = message.get("interactive") or {}
            button_reply = interactive.get("button_reply") or {}
            list_reply = interactive.get("list_reply") or {}
            return str(button_reply.get("title") or list_reply.get("title") or "").strip()
        if message_type == "image":
            return str((message.get("image") or {}).get("caption") or "").strip()
        if message_type == "video":
            return str((message.get("video") or {}).get("caption") or "").strip()
        if message_type == "document":
            document = message.get("document") or {}
            return str(document.get("caption") or document.get("filename") or "").strip()
        if message_type == "audio":
            return "[audio]"
        if message_type == "sticker":
            return "[sticker]"
        return f"[{message_type or 'message'}]"

    def _normalize_timestamp(self, value: Any) -> str:
        raw = str(value or "").strip()
        if not raw:
            return ""
        try:
            if raw.isdigit():
                return datetime.fromtimestamp(int(raw), timezone.utc).isoformat()
            return datetime.fromisoformat(raw).astimezone(timezone.utc).isoformat()
        except (ValueError, OSError):
            return ""

    def _safe_json(self, raw: str) -> dict[str, Any]:
        try:
            payload = json.loads(raw or "{}")
            return payload if isinstance(payload, dict) else {}
        except json.JSONDecodeError:
            return {}

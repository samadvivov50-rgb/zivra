from __future__ import annotations

import json
import re
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import quote_plus

from app.core.config import Settings
from app.services.browser_launch import BrowserLauncher, normalize_browser_launch_result
from app.services.whatsapp_cloud import WhatsAppCloudClient, WhatsAppCloudError


class MessagingService:
    def __init__(
        self,
        db_path: Path,
        *,
        settings: Settings | None = None,
        opener: Callable[[str], Any] | None = None,
        cloud_client: WhatsAppCloudClient | None = None,
    ) -> None:
        self.db_path = db_path
        self.settings = settings
        self.browser_launcher = BrowserLauncher() if opener is None else None
        self.opener = opener or self.browser_launcher.open
        self.cloud_client = cloud_client or (WhatsAppCloudClient(settings) if settings is not None else None)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel TEXT NOT NULL DEFAULT 'whatsapp',
                    direction TEXT NOT NULL DEFAULT 'outbound',
                    to_number TEXT NOT NULL,
                    phone_digits TEXT NOT NULL,
                    contact_name TEXT NOT NULL DEFAULT '',
                    body TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'draft',
                    source TEXT NOT NULL DEFAULT 'assistant',
                    provider TEXT NOT NULL DEFAULT 'browser_handoff',
                    provider_message_id TEXT,
                    message_type TEXT NOT NULL DEFAULT 'text',
                    remote_timestamp TEXT,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    handed_off_at TEXT
                )
                """
            )
            self._ensure_column(connection, "direction", "TEXT NOT NULL DEFAULT 'outbound'")
            self._ensure_column(connection, "contact_name", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(connection, "provider", "TEXT NOT NULL DEFAULT 'browser_handoff'")
            self._ensure_column(connection, "provider_message_id", "TEXT")
            self._ensure_column(connection, "message_type", "TEXT NOT NULL DEFAULT 'text'")
            self._ensure_column(connection, "remote_timestamp", "TEXT")
            self._ensure_column(connection, "metadata_json", "TEXT NOT NULL DEFAULT '{}'")
            connection.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_messages_provider_message_id
                ON messages(provider_message_id)
                WHERE provider_message_id IS NOT NULL AND provider_message_id != ''
                """
            )
            connection.commit()

    def _ensure_column(self, connection: sqlite3.Connection, column_name: str, definition: str) -> None:
        columns = {
            str(row["name"])
            for row in connection.execute("PRAGMA table_info(messages)").fetchall()
        }
        if column_name in columns:
            return
        connection.execute(f"ALTER TABLE messages ADD COLUMN {column_name} {definition}")

    def delivery_status(self) -> dict[str, Any]:
        cloud_status = self.cloud_client.status() if self.cloud_client is not None else {
            "cloud_configured": False,
            "api_version": "v23.0",
            "phone_number_id_masked": "",
            "verify_token_configured": False,
            "signature_validation": False,
            "webhook_path": "/messages/whatsapp/webhook",
        }
        if cloud_status["cloud_configured"]:
            return {
                "channel": "whatsapp",
                "ready": True,
                "delivery_mode": "cloud_api",
                "status_label": "Cloud API",
                "final_send_in_app": False,
                "cloud_configured": True,
                "api_version": cloud_status["api_version"],
                "phone_number_id_masked": cloud_status["phone_number_id_masked"],
                "verify_token_configured": bool(cloud_status["verify_token_configured"]),
                "signature_validation": bool(cloud_status["signature_validation"]),
                "webhook_path": cloud_status["webhook_path"],
                "browser": "",
                "mode": "cloud_api",
                "isolated_available": False,
                "conversation_ready": bool(cloud_status["verify_token_configured"]),
            }

        capabilities = self.browser_launcher.capabilities() if self.browser_launcher is not None else {}
        isolated_available = bool(capabilities.get("isolated_available"))
        return {
            "channel": "whatsapp",
            "ready": True,
            "delivery_mode": "isolated_browser_handoff" if isolated_available else "browser_handoff",
            "status_label": capabilities.get("status_label", "Browser handoff"),
            "final_send_in_app": True,
            "cloud_configured": False,
            "api_version": cloud_status["api_version"],
            "phone_number_id_masked": cloud_status["phone_number_id_masked"],
            "verify_token_configured": bool(cloud_status["verify_token_configured"]),
            "signature_validation": bool(cloud_status["signature_validation"]),
            "webhook_path": cloud_status["webhook_path"],
            "isolated_available": isolated_available,
            "browser": capabilities.get("browser", ""),
            "mode": capabilities.get("mode", "default_browser"),
            "conversation_ready": False,
        }

    def summary(self) -> dict[str, int]:
        summary = {
            "draft": 0,
            "opened": 0,
            "sent": 0,
            "delivered": 0,
            "read": 0,
            "failed": 0,
            "received": 0,
        }
        with closing(self._connect()) as connection:
            status_rows = connection.execute("SELECT status, COUNT(*) AS total FROM messages GROUP BY status").fetchall()
            direction_rows = connection.execute(
                "SELECT direction, COUNT(*) AS total FROM messages GROUP BY direction"
            ).fetchall()

        for row in status_rows:
            status = str(row["status"] or "")
            if status in summary:
                summary[status] = int(row["total"] or 0)
        for row in direction_rows:
            if str(row["direction"] or "") == "inbound":
                summary["received"] = int(row["total"] or 0)
        return summary

    def list_messages(
        self,
        *,
        limit: int = 12,
        status: str | None = None,
        direction: str | None = None,
    ) -> list[dict[str, Any]]:
        query = """
            SELECT
                id,
                channel,
                direction,
                to_number,
                phone_digits,
                contact_name,
                body,
                status,
                source,
                provider,
                provider_message_id,
                message_type,
                remote_timestamp,
                metadata_json,
                error,
                created_at,
                updated_at,
                handed_off_at
            FROM messages
            WHERE channel = 'whatsapp'
        """
        parameters: list[Any] = []
        if status:
            query += " AND status = ?"
            parameters.append(status)
        if direction:
            query += " AND direction = ?"
            parameters.append(direction)
        query += " ORDER BY COALESCE(remote_timestamp, handed_off_at, updated_at, created_at) DESC, id DESC LIMIT ?"
        parameters.append(limit)

        with closing(self._connect()) as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [self._serialize_row(row) for row in rows]

    def get_message(self, message_id: int) -> dict[str, Any] | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    channel,
                    direction,
                    to_number,
                    phone_digits,
                    contact_name,
                    body,
                    status,
                    source,
                    provider,
                    provider_message_id,
                    message_type,
                    remote_timestamp,
                    metadata_json,
                    error,
                    created_at,
                    updated_at,
                    handed_off_at
                FROM messages
                WHERE id = ?
                """,
                (message_id,),
            ).fetchone()

        if row is None:
            return None
        return self._serialize_row(row)

    def create_whatsapp_draft(
        self,
        *,
        to_number: str,
        body: str,
        source: str = "assistant",
    ) -> dict[str, Any]:
        cleaned_to, phone_digits = self._normalize_phone_number(to_number)
        cleaned_body = str(body or "").strip()
        cleaned_source = source.strip() or "assistant"
        now = self._now()
        provider = "cloud_api" if self._cloud_ready() else "browser_handoff"

        with closing(self._connect()) as connection:
            cursor = connection.execute(
                """
                INSERT INTO messages (
                    channel,
                    direction,
                    to_number,
                    phone_digits,
                    contact_name,
                    body,
                    status,
                    source,
                    provider,
                    message_type,
                    metadata_json,
                    created_at,
                    updated_at
                )
                VALUES ('whatsapp', 'outbound', ?, ?, '', ?, 'draft', ?, ?, 'text', '{}', ?, ?)
                """,
                (cleaned_to, phone_digits, cleaned_body, cleaned_source, provider, now, now),
            )
            connection.commit()
            message_id = int(cursor.lastrowid)

        message = self.get_message(message_id)
        if message is None:
            raise RuntimeError("WhatsApp draft creation completed but could not be reloaded.")
        return message

    def send_whatsapp_draft(self, message_id: int) -> dict[str, Any] | None:
        message = self.get_message(message_id)
        if message is None:
            return None

        if self._cloud_ready():
            return self._send_via_cloud_api(message_id, message)
        return self._send_via_browser_handoff(message_id, message)

    def format_dispatch_message(self, message: dict[str, Any]) -> str:
        if message["status"] == "failed":
            provider = str(message.get("provider") or "")
            if provider == "cloud_api":
                return f"WhatsApp Cloud API send failed: {message['error'] or 'Unknown Cloud API error.'}"
            return f"WhatsApp handoff failed: {message['error'] or 'Unknown browser error.'}"

        provider = str(message.get("provider") or "")
        if provider == "cloud_api" and message["status"] in {"sent", "delivered", "read"}:
            return f"Sent a WhatsApp message to {message['to']} through Meta Cloud API."

        launch = message.get("launch", {})
        if launch.get("isolated_used"):
            return (
                f"Opened an isolated WhatsApp compose window for {message['to']} in "
                f"{launch.get('browser', 'a private browser window')}. Final send still happens in WhatsApp."
            )
        if launch.get("used_fallback"):
            return (
                f"Opened a WhatsApp compose window for {message['to']} in the default browser because isolated launch "
                "was unavailable. Final send still happens in WhatsApp."
            )
        return f"Opened a WhatsApp compose window for {message['to']}. Final send still happens in WhatsApp."

    def audit_payload(self, message: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "id": message["id"],
            "channel": message["channel"],
            "direction": message["direction"],
            "to": message["to"],
            "status": message["status"],
            "source": message["source"],
            "provider": message["provider"],
            "provider_message_id": message["provider_message_id"],
            "message_type": message["message_type"],
            "contact_name": message["contact_name"],
            "error": message["error"],
            "created_at": message["created_at"],
            "updated_at": message["updated_at"],
            "handed_off_at": message["handed_off_at"],
            "remote_timestamp": message["remote_timestamp"],
            "body_length": message["body_length"],
            "has_body": bool(message["body_length"]),
        }
        if message.get("launch"):
            launch = message["launch"]
            payload["launch"] = {
                "isolated_used": bool(launch.get("isolated_used")),
                "used_fallback": bool(launch.get("used_fallback")),
                "browser": str(launch.get("browser", "") or ""),
                "mode": str(launch.get("mode", "default_browser") or "default_browser"),
            }
        return payload

    def verify_whatsapp_webhook(self, *, mode: str, verify_token: str, challenge: str) -> str:
        if self.cloud_client is None:
            raise ValueError("WhatsApp Cloud API is not configured in this runtime.")
        try:
            return self.cloud_client.verify_webhook(mode=mode, verify_token=verify_token, challenge=challenge)
        except WhatsAppCloudError as exc:
            raise ValueError(str(exc)) from exc

    def receive_whatsapp_webhook(self, raw_body: bytes, *, signature_header: str | None = None) -> dict[str, Any]:
        if self.cloud_client is None:
            raise ValueError("WhatsApp Cloud API is not configured in this runtime.")
        if not self.cloud_client.validate_signature(raw_body, signature_header):
            raise ValueError("WhatsApp webhook signature validation failed.")

        try:
            payload = json.loads(raw_body.decode("utf-8") or "{}")
        except json.JSONDecodeError as exc:
            raise ValueError("WhatsApp webhook payload was not valid JSON.") from exc
        if not isinstance(payload, dict):
            raise ValueError("WhatsApp webhook payload must be a JSON object.")

        events = self.cloud_client.parse_webhook_events(payload)
        received = 0
        updated = 0
        for event in events:
            if event["event_type"] == "message":
                if self._store_inbound_event(event):
                    received += 1
                continue
            if event["event_type"] == "status" and self._apply_status_event(event):
                updated += 1

        return {
            "processed_events": len(events),
            "received_messages": received,
            "updated_messages": updated,
        }

    def build_whatsapp_url(self, phone_digits: str, body: str) -> str:
        encoded_body = quote_plus(str(body or ""))
        if encoded_body:
            return f"https://wa.me/{phone_digits}?text={encoded_body}"
        return f"https://wa.me/{phone_digits}"

    def _send_via_cloud_api(self, message_id: int, message: dict[str, Any]) -> dict[str, Any]:
        if self.cloud_client is None:
            raise RuntimeError("WhatsApp Cloud API client was not initialized.")
        try:
            result = self.cloud_client.send_text_message(
                to_number=str(message["phone_digits"]),
                body=str(message["body"]),
            )
        except WhatsAppCloudError as exc:
            self._update_message(
                message_id,
                status="failed",
                error=str(exc),
                provider="cloud_api",
            )
            failed_message = self.get_message(message_id)
            if failed_message is None:
                raise RuntimeError("WhatsApp Cloud API send failed and the draft could not be reloaded.") from exc
            return failed_message

        self._update_message(
            message_id,
            status="sent",
            error=None,
            provider="cloud_api",
            provider_message_id=str(result.get("message_id") or ""),
            metadata={
                "cloud_response": result.get("response", {}),
            },
        )
        sent_message = self.get_message(message_id)
        if sent_message is None:
            raise RuntimeError("WhatsApp Cloud API send completed but the message could not be reloaded.")
        return sent_message

    def _send_via_browser_handoff(self, message_id: int, message: dict[str, Any]) -> dict[str, Any]:
        compose_url = self.build_whatsapp_url(str(message["phone_digits"]), str(message["body"]))
        try:
            launch = normalize_browser_launch_result(self.opener(compose_url), compose_url)
        except Exception as exc:
            self._update_message(message_id, status="failed", error=str(exc), provider="browser_handoff")
            failed_message = self.get_message(message_id)
            if failed_message is None:
                raise RuntimeError("WhatsApp handoff failed and the draft could not be reloaded.") from exc
            return failed_message

        if not launch["success"]:
            self._update_message(
                message_id,
                status="failed",
                error=launch["error"] or "The browser did not report a successful launch.",
                provider="browser_handoff",
            )
            failed_message = self.get_message(message_id)
            if failed_message is None:
                raise RuntimeError("WhatsApp handoff failed and the draft could not be reloaded.")
            return failed_message

        handed_off_at = self._now()
        self._update_message(
            message_id,
            status="opened",
            error=None,
            handed_off_at=handed_off_at,
            provider="browser_handoff",
            metadata={
                "launch": self._public_launch_payload(launch),
            },
        )
        handed_off_message = self.get_message(message_id)
        if handed_off_message is None:
            return None
        handed_off_message["launch"] = self._public_launch_payload(launch)
        return handed_off_message

    def _update_message(
        self,
        message_id: int,
        *,
        status: str,
        error: str | None = None,
        handed_off_at: str | None = None,
        provider: str | None = None,
        provider_message_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        with closing(self._connect()) as connection:
            existing = connection.execute(
                "SELECT metadata_json, provider_message_id, provider FROM messages WHERE id = ?",
                (message_id,),
            ).fetchone()
            existing_metadata = self._load_metadata(existing["metadata_json"] if existing else "{}")
            if metadata:
                existing_metadata.update(metadata)
            next_provider_message_id = (
                provider_message_id
                if provider_message_id is not None
                else str(existing["provider_message_id"] or "") if existing is not None else ""
            )
            next_provider = provider if provider is not None else str(existing["provider"] or "") if existing else ""
            connection.execute(
                """
                UPDATE messages
                SET status = ?,
                    error = ?,
                    updated_at = ?,
                    handed_off_at = COALESCE(?, handed_off_at),
                    provider = ?,
                    provider_message_id = ?,
                    metadata_json = ?
                WHERE id = ?
                """,
                (
                    status,
                    error,
                    self._now(),
                    handed_off_at,
                    next_provider,
                    next_provider_message_id or None,
                    json.dumps(existing_metadata, sort_keys=True),
                    message_id,
                ),
            )
            connection.commit()

    def _store_inbound_event(self, event: dict[str, Any]) -> bool:
        provider_message_id = str(event.get("provider_message_id") or "").strip()
        now = self._now()
        with closing(self._connect()) as connection:
            existing = None
            if provider_message_id:
                existing = connection.execute(
                    "SELECT id FROM messages WHERE provider_message_id = ?",
                    (provider_message_id,),
                ).fetchone()
            if existing is not None:
                return False
            connection.execute(
                """
                INSERT INTO messages (
                    channel,
                    direction,
                    to_number,
                    phone_digits,
                    contact_name,
                    body,
                    status,
                    source,
                    provider,
                    provider_message_id,
                    message_type,
                    remote_timestamp,
                    metadata_json,
                    created_at,
                    updated_at
                )
                VALUES ('whatsapp', 'inbound', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(event.get("to_number") or "").strip(),
                    str(event.get("phone_digits") or "").strip(),
                    str(event.get("contact_name") or "").strip(),
                    str(event.get("body") or "").strip(),
                    str(event.get("status") or "received").strip(),
                    str(event.get("source") or "whatsapp_cloud").strip(),
                    str(event.get("provider") or "cloud_api").strip(),
                    provider_message_id or None,
                    str(event.get("message_type") or "text").strip(),
                    str(event.get("remote_timestamp") or "").strip() or None,
                    json.dumps(event.get("metadata") or {}, sort_keys=True),
                    str(event.get("remote_timestamp") or "").strip() or now,
                    now,
                ),
            )
            connection.commit()
        return True

    def _apply_status_event(self, event: dict[str, Any]) -> bool:
        provider_message_id = str(event.get("provider_message_id") or "").strip()
        if not provider_message_id:
            return False
        with closing(self._connect()) as connection:
            existing = connection.execute(
                "SELECT id, metadata_json FROM messages WHERE provider_message_id = ?",
                (provider_message_id,),
            ).fetchone()
            if existing is None:
                return False
            metadata = self._load_metadata(existing["metadata_json"])
            metadata.update(event.get("metadata") or {})
            connection.execute(
                """
                UPDATE messages
                SET status = ?,
                    error = ?,
                    remote_timestamp = COALESCE(?, remote_timestamp),
                    metadata_json = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    str(event.get("status") or "unknown").strip() or "unknown",
                    str(event.get("error") or "").strip() or None,
                    str(event.get("remote_timestamp") or "").strip() or None,
                    json.dumps(metadata, sort_keys=True),
                    self._now(),
                    int(existing["id"]),
                ),
            )
            connection.commit()
        return True

    def _serialize_row(self, row: sqlite3.Row) -> dict[str, Any]:
        body = str(row["body"] or "")
        preview = " ".join(body.split())
        phone_digits = str(row["phone_digits"] or "")
        metadata = self._load_metadata(row["metadata_json"])
        launch = metadata.get("launch") if isinstance(metadata.get("launch"), dict) else None
        direction = str(row["direction"] or "outbound")
        return {
            "id": int(row["id"]),
            "channel": str(row["channel"] or "whatsapp"),
            "direction": direction,
            "to": str(row["to_number"]),
            "phone_digits": phone_digits,
            "contact_name": str(row["contact_name"] or ""),
            "body": body,
            "body_preview": preview[:180],
            "body_length": len(body),
            "status": str(row["status"]),
            "source": str(row["source"] or "assistant"),
            "provider": str(row["provider"] or "browser_handoff"),
            "provider_message_id": str(row["provider_message_id"] or ""),
            "message_type": str(row["message_type"] or "text"),
            "remote_timestamp": str(row["remote_timestamp"] or ""),
            "metadata": metadata,
            "error": str(row["error"] or ""),
            "created_at": str(row["created_at"]),
            "updated_at": str(row["updated_at"]),
            "handed_off_at": str(row["handed_off_at"] or ""),
            "compose_url": self.build_whatsapp_url(phone_digits, body),
            "launch": launch,
            "display_label": str(row["contact_name"] or row["to_number"] or "WhatsApp message"),
        }

    def _load_metadata(self, raw: Any) -> dict[str, Any]:
        try:
            payload = json.loads(str(raw or "{}"))
            return payload if isinstance(payload, dict) else {}
        except json.JSONDecodeError:
            return {}

    def _normalize_phone_number(self, value: str) -> tuple[str, str]:
        cleaned = re.sub(r"\s+", " ", str(value or "")).strip()
        digits = re.sub(r"\D", "", cleaned)
        if len(digits) < 7:
            raise ValueError("A WhatsApp phone number with country code is required.")
        return cleaned or f"+{digits}", digits

    def _cloud_ready(self) -> bool:
        return self.cloud_client is not None and self.cloud_client.is_configured()

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _public_launch_payload(self, launch: dict[str, Any]) -> dict[str, Any]:
        return {
            "isolated_used": bool(launch.get("isolated_used")),
            "used_fallback": bool(launch.get("used_fallback")),
            "browser": str(launch.get("browser", "") or ""),
            "mode": str(launch.get("mode", "default_browser") or "default_browser"),
            "status_label": str(launch.get("status_label", "Browser handoff") or "Browser handoff"),
        }

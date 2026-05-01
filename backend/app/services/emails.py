from __future__ import annotations

import smtplib
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Callable

from app.core.config import Settings


class EmailService:
    def __init__(
        self,
        db_path: Path,
        *,
        settings: Settings,
        transport: Callable[[dict[str, str]], None] | None = None,
    ) -> None:
        self.db_path = db_path
        self.settings = settings
        self.transport = transport
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
                CREATE TABLE IF NOT EXISTS emails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    to_address TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    body TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'draft',
                    source TEXT NOT NULL DEFAULT 'assistant',
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    sent_at TEXT
                )
                """
            )
            connection.commit()

    def delivery_status(self) -> dict[str, Any]:
        from_email = self.settings.email_from_address or self.settings.smtp_username
        ready = bool(self.settings.smtp_host and from_email)
        return {
            "ready": ready,
            "host": self.settings.smtp_host,
            "port": self.settings.smtp_port,
            "use_tls": self.settings.smtp_use_tls,
            "use_ssl": self.settings.smtp_use_ssl,
            "from_email": from_email,
            "from_name": self.settings.email_from_name,
            "status_label": "Configured" if ready else "Not configured",
        }

    def summary(self) -> dict[str, int]:
        with closing(self._connect()) as connection:
            rows = connection.execute("SELECT status, COUNT(*) AS total FROM emails GROUP BY status").fetchall()

        summary = {"draft": 0, "sent": 0, "failed": 0}
        for row in rows:
            status = str(row["status"] or "draft")
            if status in summary:
                summary[status] = int(row["total"] or 0)
        return summary

    def list_emails(self, *, limit: int = 12, status: str | None = None) -> list[dict[str, Any]]:
        query = """
            SELECT
                id,
                to_address,
                subject,
                body,
                status,
                source,
                error,
                created_at,
                updated_at,
                sent_at
            FROM emails
        """
        parameters: list[Any] = []
        if status:
            query += " WHERE status = ?"
            parameters.append(status)
        query += " ORDER BY COALESCE(sent_at, updated_at, created_at) DESC, id DESC LIMIT ?"
        parameters.append(limit)

        with closing(self._connect()) as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [self._serialize_row(row) for row in rows]

    def get_email(self, email_id: int) -> dict[str, Any] | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    to_address,
                    subject,
                    body,
                    status,
                    source,
                    error,
                    created_at,
                    updated_at,
                    sent_at
                FROM emails
                WHERE id = ?
                """,
                (email_id,),
            ).fetchone()

        if row is None:
            return None
        return self._serialize_row(row)

    def create_draft(
        self,
        *,
        to_address: str,
        subject: str,
        body: str = "",
        source: str = "assistant",
    ) -> dict[str, Any]:
        now = self._now()
        cleaned_to = to_address.strip() or "recipient@example.com"
        cleaned_subject = subject.strip() or "Draft from Zivra"
        cleaned_body = body.strip()
        cleaned_source = source.strip() or "assistant"

        with closing(self._connect()) as connection:
            cursor = connection.execute(
                """
                INSERT INTO emails (to_address, subject, body, status, source, created_at, updated_at)
                VALUES (?, ?, ?, 'draft', ?, ?, ?)
                """,
                (cleaned_to, cleaned_subject, cleaned_body, cleaned_source, now, now),
            )
            connection.commit()
            email_id = int(cursor.lastrowid)

        email = self.get_email(email_id)
        if email is None:
            raise RuntimeError("Email draft creation completed but could not be reloaded.")
        return email

    def send_draft(self, email_id: int) -> dict[str, Any] | None:
        email = self.get_email(email_id)
        if email is None:
            return None
        if email["status"] == "sent":
            raise ValueError("This email has already been sent.")

        delivery = self.delivery_status()
        if not delivery["ready"]:
            raise ValueError("Email delivery is not configured. Set SMTP host and sender details first.")

        try:
            self._deliver(
                {
                    "to": str(email["to"]),
                    "subject": str(email["subject"]),
                    "body": str(email["body"]),
                }
            )
        except Exception as exc:
            self._update_status(email_id, status="failed", error=str(exc))
            failed_email = self.get_email(email_id)
            if failed_email is None:
                raise RuntimeError("Email delivery failed and the draft could not be reloaded.") from exc
            return failed_email

        sent_at = self._now()
        self._update_status(email_id, status="sent", sent_at=sent_at, error=None)
        return self.get_email(email_id)

    def create_and_send(
        self,
        *,
        to_address: str,
        subject: str,
        body: str = "",
        source: str = "assistant",
    ) -> dict[str, Any]:
        email = self.create_draft(
            to_address=to_address,
            subject=subject,
            body=body,
            source=source,
        )
        sent_email = self.send_draft(int(email["id"]))
        if sent_email is None:
            raise RuntimeError("Email send completed but could not be reloaded.")
        return sent_email

    def audit_payload(self, email: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": email["id"],
            "to": email["to"],
            "subject": email["subject"],
            "status": email["status"],
            "source": email["source"],
            "error": email["error"],
            "created_at": email["created_at"],
            "updated_at": email["updated_at"],
            "sent_at": email["sent_at"],
            "body_length": email["body_length"],
            "has_body": bool(email["body_length"]),
        }

    def _update_status(
        self,
        email_id: int,
        *,
        status: str,
        error: str | None = None,
        sent_at: str | None = None,
    ) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                UPDATE emails
                SET status = ?, error = ?, updated_at = ?, sent_at = COALESCE(?, sent_at)
                WHERE id = ?
                """,
                (status, error, self._now(), sent_at, email_id),
            )
            connection.commit()

    def _deliver(self, payload: dict[str, str]) -> None:
        if self.transport is not None:
            self.transport(payload)
            return

        message = EmailMessage()
        from_email = self.settings.email_from_address or self.settings.smtp_username
        from_name = self.settings.email_from_name.strip()
        message["From"] = f"{from_name} <{from_email}>" if from_name and from_email else from_email
        message["To"] = payload["to"]
        message["Subject"] = payload["subject"]
        message.set_content(payload["body"] or "")

        if self.settings.smtp_use_ssl:
            with smtplib.SMTP_SSL(self.settings.smtp_host, self.settings.smtp_port, timeout=20) as client:
                self._login_if_needed(client)
                client.send_message(message)
            return

        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=20) as client:
            client.ehlo()
            if self.settings.smtp_use_tls:
                client.starttls()
                client.ehlo()
            self._login_if_needed(client)
            client.send_message(message)

    def _login_if_needed(self, client: smtplib.SMTP) -> None:
        if self.settings.smtp_username:
            client.login(self.settings.smtp_username, self.settings.smtp_password)

    def _serialize_row(self, row: sqlite3.Row) -> dict[str, Any]:
        body = str(row["body"] or "")
        preview = " ".join(body.split())
        return {
            "id": int(row["id"]),
            "to": str(row["to_address"]),
            "subject": str(row["subject"]),
            "body": body,
            "body_preview": preview[:180],
            "body_length": len(body),
            "status": str(row["status"]),
            "source": str(row["source"] or "assistant"),
            "error": str(row["error"] or ""),
            "created_at": str(row["created_at"]),
            "updated_at": str(row["updated_at"]),
            "sent_at": str(row["sent_at"] or ""),
        }

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

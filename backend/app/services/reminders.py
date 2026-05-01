from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


class ReminderService:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
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
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    details TEXT NOT NULL DEFAULT '',
                    schedule_hint TEXT,
                    due_at TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT
                )
                """
            )
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(reminders)").fetchall()
            }
            if "archived_at" not in columns:
                connection.execute("ALTER TABLE reminders ADD COLUMN archived_at TEXT")
            if "recurrence_rule" not in columns:
                connection.execute("ALTER TABLE reminders ADD COLUMN recurrence_rule TEXT")
            if "recurrence_label" not in columns:
                connection.execute("ALTER TABLE reminders ADD COLUMN recurrence_label TEXT")
            connection.commit()

    def create_reminder(
        self,
        *,
        title: str,
        details: str = "",
        schedule_hint: str | None = None,
        due_at: str | None = None,
        recurrence_rule: str | None = None,
        recurrence_label: str | None = None,
    ) -> dict[str, Any]:
        cleaned_title = title.strip() or "Untitled reminder"
        cleaned_details = details.strip()
        cleaned_hint = schedule_hint.strip() if schedule_hint else None
        cleaned_due_at = due_at.strip() if due_at else None
        cleaned_rule, cleaned_label = self._normalize_recurrence(
            recurrence_rule=recurrence_rule,
            recurrence_label=recurrence_label,
        )
        if cleaned_rule and not cleaned_due_at:
            raise ValueError("Recurring reminders need an initial date and time.")

        with closing(self._connect()) as connection:
            cursor = connection.execute(
                """
                INSERT INTO reminders (title, details, schedule_hint, due_at, recurrence_rule, recurrence_label)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (cleaned_title, cleaned_details, cleaned_hint, cleaned_due_at, cleaned_rule, cleaned_label),
            )
            connection.commit()
            reminder_id = int(cursor.lastrowid)

        reminder = self.get_reminder(reminder_id)
        if reminder is None:
            raise RuntimeError("Reminder creation completed but could not be reloaded.")
        return reminder

    def list_upcoming(
        self,
        *,
        limit: int = 10,
        include_completed: bool = False,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        query = """
            SELECT
                id,
                title,
                details,
                schedule_hint,
                due_at,
                status,
                created_at,
                completed_at,
                archived_at,
                recurrence_rule,
                recurrence_label
            FROM reminders
        """
        parameters: list[Any] = []
        allowed_statuses = ["pending"]
        if include_completed:
            allowed_statuses.append("completed")
        if include_archived:
            allowed_statuses.append("archived")

        placeholders = ", ".join("?" for _ in allowed_statuses)
        query += f" WHERE status IN ({placeholders})"
        parameters.extend(allowed_statuses)

        query += """
            ORDER BY
                CASE status
                    WHEN 'pending' THEN 0
                    WHEN 'completed' THEN 1
                    ELSE 2
                END,
                CASE WHEN due_at IS NULL THEN 1 ELSE 0 END,
                due_at ASC,
                CASE
                    WHEN archived_at IS NOT NULL THEN archived_at
                    WHEN completed_at IS NOT NULL THEN completed_at
                    ELSE created_at
                END DESC,
                id DESC
            LIMIT ?
        """
        parameters.append(limit)

        with closing(self._connect()) as connection:
            rows = connection.execute(query, parameters).fetchall()

        return [self._serialize_row(row) for row in rows]

    def get_reminder(self, reminder_id: int) -> dict[str, Any] | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    title,
                    details,
                    schedule_hint,
                    due_at,
                    status,
                    created_at,
                    completed_at,
                    archived_at,
                    recurrence_rule,
                    recurrence_label
                FROM reminders
                WHERE id = ?
                """,
                (reminder_id,),
            ).fetchone()

        if row is None:
            return None
        return self._serialize_row(row)

    def count_pending(self) -> int:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS pending_count FROM reminders WHERE status = 'pending'"
            ).fetchone()
        return int(row["pending_count"])

    def summary(self) -> dict[str, int]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT status, due_at FROM reminders"
            ).fetchall()

        now_local = datetime.now().astimezone()
        today_local = now_local.date()
        summary = {
            "pending": 0,
            "overdue": 0,
            "due_today": 0,
            "unscheduled": 0,
            "completed": 0,
            "archived": 0,
        }

        for row in rows:
            status = str(row["status"] or "pending")
            if status == "completed":
                summary["completed"] += 1
                continue
            if status == "archived":
                summary["archived"] += 1
                continue

            summary["pending"] += 1
            due_at = row["due_at"]
            if not due_at:
                summary["unscheduled"] += 1
                continue

            due_time = self._parse_timestamp(due_at)
            if due_time is None:
                continue

            due_local = due_time.astimezone()
            if due_local < now_local:
                summary["overdue"] += 1
            if due_local.date() == today_local:
                summary["due_today"] += 1

        return summary

    def complete_reminder(self, reminder_id: int) -> dict[str, Any] | None:
        completed_at = datetime.now(timezone.utc).isoformat()
        with closing(self._connect()) as connection:
            cursor = connection.execute(
                """
                UPDATE reminders
                SET status = 'completed', completed_at = ?
                WHERE id = ? AND status = 'pending'
                """,
                (completed_at, reminder_id),
            )
            connection.commit()

        reminder = self.get_reminder(reminder_id)
        if reminder is None:
            return None

        if int(cursor.rowcount or 0) and reminder.get("recurrence_rule") and reminder.get("due_at"):
            next_occurrence = self._create_next_occurrence(reminder)
            if next_occurrence is not None:
                reminder["next_occurrence"] = next_occurrence

        return reminder

    def reopen_reminder(self, reminder_id: int) -> dict[str, Any] | None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                UPDATE reminders
                SET status = 'pending', completed_at = NULL, archived_at = NULL
                WHERE id = ?
                """,
                (reminder_id,),
            )
            connection.commit()
        return self.get_reminder(reminder_id)

    def archive_reminder(self, reminder_id: int) -> dict[str, Any] | None:
        archived_at = datetime.now(timezone.utc).isoformat()
        with closing(self._connect()) as connection:
            connection.execute(
                """
                UPDATE reminders
                SET status = 'archived', archived_at = ?
                WHERE id = ? AND status != 'archived'
                """,
                (archived_at, reminder_id),
            )
            connection.commit()
        return self.get_reminder(reminder_id)

    def restore_reminder(self, reminder_id: int) -> dict[str, Any] | None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                UPDATE reminders
                SET status = 'pending', archived_at = NULL, completed_at = NULL
                WHERE id = ?
                """,
                (reminder_id,),
            )
            connection.commit()
        return self.get_reminder(reminder_id)

    def archive_completed_reminders(self) -> int:
        archived_at = datetime.now(timezone.utc).isoformat()
        with closing(self._connect()) as connection:
            cursor = connection.execute(
                """
                UPDATE reminders
                SET status = 'archived', archived_at = ?
                WHERE status = 'completed'
                """,
                (archived_at,),
            )
            connection.commit()
        return int(cursor.rowcount or 0)

    def restore_archived_reminders(self) -> int:
        with closing(self._connect()) as connection:
            cursor = connection.execute(
                """
                UPDATE reminders
                SET status = 'pending', archived_at = NULL, completed_at = NULL
                WHERE status = 'archived'
                """
            )
            connection.commit()
        return int(cursor.rowcount or 0)

    def delete_archived_reminder(self, reminder_id: int) -> bool:
        with closing(self._connect()) as connection:
            cursor = connection.execute(
                """
                DELETE FROM reminders
                WHERE id = ? AND status = 'archived'
                """,
                (reminder_id,),
            )
            connection.commit()
        return int(cursor.rowcount or 0) > 0

    def purge_archived_reminders(self) -> int:
        with closing(self._connect()) as connection:
            cursor = connection.execute(
                """
                DELETE FROM reminders
                WHERE status = 'archived'
                """
            )
            connection.commit()
        return int(cursor.rowcount or 0)

    def set_recurrence(
        self,
        reminder_id: int,
        *,
        recurrence_rule: str,
        recurrence_label: str | None = None,
    ) -> dict[str, Any] | None:
        cleaned_rule, cleaned_label = self._normalize_recurrence(
            recurrence_rule=recurrence_rule,
            recurrence_label=recurrence_label,
        )
        with closing(self._connect()) as connection:
            connection.execute(
                """
                UPDATE reminders
                SET recurrence_rule = ?, recurrence_label = ?
                WHERE id = ?
                """,
                (cleaned_rule, cleaned_label, reminder_id),
            )
            connection.commit()
        return self.get_reminder(reminder_id)

    def clear_recurrence(self, reminder_id: int) -> dict[str, Any] | None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                UPDATE reminders
                SET recurrence_rule = NULL, recurrence_label = NULL
                WHERE id = ?
                """,
                (reminder_id,),
            )
            connection.commit()
        return self.get_reminder(reminder_id)

    def reschedule_reminder(
        self,
        reminder_id: int,
        *,
        due_at: str,
        schedule_hint: str,
    ) -> dict[str, Any] | None:
        cleaned_due_at = due_at.strip()
        cleaned_hint = schedule_hint.strip()
        with closing(self._connect()) as connection:
            connection.execute(
                """
                UPDATE reminders
                SET status = 'pending', due_at = ?, schedule_hint = ?, completed_at = NULL, archived_at = NULL
                WHERE id = ?
                """,
                (cleaned_due_at, cleaned_hint, reminder_id),
            )
            connection.commit()
        return self.get_reminder(reminder_id)

    def _serialize_row(self, row: sqlite3.Row) -> dict[str, Any]:
        due_at = row["due_at"]
        created_at = self._normalize_timestamp(row["created_at"])
        completed_at = self._normalize_timestamp(row["completed_at"])
        archived_at = self._normalize_timestamp(row["archived_at"])
        recurrence_rule = row["recurrence_rule"]
        recurrence_label = row["recurrence_label"]
        due_display = "Unscheduled"

        if due_at:
            due_display = self._display_timestamp(due_at)
        elif row["schedule_hint"]:
            due_display = str(row["schedule_hint"])

        is_overdue = False
        if due_at and row["status"] == "pending":
            try:
                is_overdue = datetime.fromisoformat(due_at) < datetime.now(timezone.utc)
            except ValueError:
                is_overdue = False

        return {
            "id": row["id"],
            "title": row["title"],
            "details": row["details"],
            "schedule_hint": row["schedule_hint"],
            "due_at": due_at,
            "due_display": due_display,
            "status": row["status"],
            "created_at": created_at,
            "completed_at": completed_at,
            "completed_display": self._display_timestamp(completed_at) if completed_at else None,
            "archived_at": archived_at,
            "archived_display": self._display_timestamp(archived_at) if archived_at else None,
            "recurrence_rule": recurrence_rule,
            "recurrence_label": recurrence_label,
            "is_recurring": bool(recurrence_rule),
            "is_overdue": is_overdue,
        }

    def _create_next_occurrence(self, reminder: dict[str, Any]) -> dict[str, Any] | None:
        recurrence_rule = str(reminder.get("recurrence_rule") or "").strip()
        due_at = str(reminder.get("due_at") or "").strip()
        if not recurrence_rule or not due_at:
            return None

        next_due_at = self._next_due_at(
            recurrence_rule=recurrence_rule,
            due_at=due_at,
        )
        return self.create_reminder(
            title=str(reminder.get("title") or "Untitled reminder"),
            details=str(reminder.get("details") or ""),
            schedule_hint=str(reminder.get("recurrence_label") or reminder.get("schedule_hint") or ""),
            due_at=next_due_at,
            recurrence_rule=recurrence_rule,
            recurrence_label=str(reminder.get("recurrence_label") or ""),
        )

    def _next_due_at(self, *, recurrence_rule: str, due_at: str) -> str:
        current_due = self._parse_timestamp(due_at)
        if current_due is None:
            return due_at

        next_due = self._advance_recurrence(current_due, recurrence_rule)
        now = datetime.now(current_due.tzinfo or timezone.utc)
        while next_due <= now:
            next_due = self._advance_recurrence(next_due, recurrence_rule)
        return next_due.isoformat()

    def _advance_recurrence(self, due_time: datetime, recurrence_rule: str) -> datetime:
        normalized_rule, _ = self._normalize_recurrence(recurrence_rule=recurrence_rule, recurrence_label=None)
        if normalized_rule == "daily":
            return due_time + timedelta(days=1)
        if normalized_rule == "weekly":
            return due_time + timedelta(days=7)
        if normalized_rule == "weekdays":
            next_due = due_time + timedelta(days=1)
            while next_due.weekday() >= 5:
                next_due = next_due + timedelta(days=1)
            return next_due
        return due_time + timedelta(days=1)

    def _normalize_recurrence(
        self,
        *,
        recurrence_rule: str | None,
        recurrence_label: str | None,
    ) -> tuple[str | None, str | None]:
        if recurrence_rule is None or not str(recurrence_rule).strip():
            return None, None

        normalized_rule = str(recurrence_rule).strip().lower()
        if normalized_rule not in {"daily", "weekdays", "weekly"}:
            raise ValueError(f"Unsupported recurrence rule: {recurrence_rule}")

        cleaned_label = str(recurrence_label).strip() if recurrence_label else self._default_recurrence_label(normalized_rule)
        return normalized_rule, cleaned_label

    def _default_recurrence_label(self, recurrence_rule: str) -> str:
        return {
            "daily": "every day",
            "weekdays": "every weekday",
            "weekly": "every week",
        }.get(recurrence_rule, "every day")

    def _normalize_timestamp(self, value: str | None) -> str | None:
        if not value:
            return None
        if value.endswith("Z") or "+" in value:
            return value

        parsed = self._parse_timestamp(value)
        if parsed is None:
            return value

        return parsed.isoformat()

    def _display_timestamp(self, value: str) -> str:
        parsed = self._parse_timestamp(value)
        if parsed is None:
            return value

        return parsed.astimezone().strftime("%b %d, %Y %I:%M %p")

    def _parse_timestamp(self, value: str | None) -> datetime | None:
        if not value:
            return None

        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed

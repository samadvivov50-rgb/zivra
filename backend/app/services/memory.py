from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any


class ConversationMemoryStore:
    def __init__(self, db_path: Path, *, enabled: bool = True) -> None:
        self.db_path = db_path
        self.enabled = enabled
        if self.enabled:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._initialize()

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        if self.enabled:
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
                CREATE TABLE IF NOT EXISTS conversation_turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    sensitivity TEXT NOT NULL DEFAULT 'normal',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.commit()

    def save_turn(
        self,
        *,
        session_id: str,
        role: str,
        content: str,
        sensitivity: str = "normal",
    ) -> None:
        if not self.enabled:
            return

        with closing(self._connect()) as connection:
            connection.execute(
                """
                INSERT INTO conversation_turns (session_id, role, content, sensitivity)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, role, content, sensitivity),
            )
            connection.commit()

    def recent_turns(self, *, session_id: str, limit: int = 8) -> list[dict[str, Any]]:
        if not self.enabled or not self.db_path.exists():
            return []

        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT role, content, sensitivity, created_at
                FROM conversation_turns
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()

        return [dict(row) for row in rows]

    def list_sessions(self, *, limit: int = 12) -> list[dict[str, Any]]:
        if not self.db_path.exists():
            return []

        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT
                    grouped.session_id,
                    grouped.turn_count,
                    grouped.last_seen_at,
                    turns.role AS last_role,
                    turns.content AS last_content,
                    turns.sensitivity AS last_sensitivity
                FROM (
                    SELECT
                        session_id,
                        COUNT(*) AS turn_count,
                        MAX(id) AS last_turn_id,
                        MAX(created_at) AS last_seen_at
                    FROM conversation_turns
                    GROUP BY session_id
                    ORDER BY last_turn_id DESC
                    LIMIT ?
                ) AS grouped
                JOIN conversation_turns AS turns
                    ON turns.id = grouped.last_turn_id
                ORDER BY grouped.last_turn_id DESC
                """,
                (limit,),
            ).fetchall()

        sessions: list[dict[str, Any]] = []
        for row in rows:
            last_content = str(row["last_content"] or "")
            preview = " ".join(last_content.split())
            sessions.append(
                {
                    "session_id": str(row["session_id"]),
                    "turn_count": int(row["turn_count"] or 0),
                    "last_seen_at": str(row["last_seen_at"] or ""),
                    "last_role": str(row["last_role"] or ""),
                    "last_sensitivity": str(row["last_sensitivity"] or "normal"),
                    "last_content_preview": preview[:160],
                }
            )
        return sessions

    def clear_session(self, *, session_id: str) -> None:
        if not self.db_path.exists():
            return

        with closing(self._connect()) as connection:
            connection.execute("DELETE FROM conversation_turns WHERE session_id = ?", (session_id,))
            connection.commit()

    def clear_all(self) -> None:
        if not self.db_path.exists():
            return

        with closing(self._connect()) as connection:
            connection.execute("DELETE FROM conversation_turns")
            connection.commit()

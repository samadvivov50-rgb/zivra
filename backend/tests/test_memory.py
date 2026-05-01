from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.api.routes.assistant import clear_all_sessions, list_sessions
from app.services.memory import ConversationMemoryStore


class ConversationMemoryStoreTests(unittest.TestCase):
    def test_can_enable_store_after_starting_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "memory.sqlite3"
            store = ConversationMemoryStore(db_path, enabled=False)

            store.set_enabled(True)
            store.save_turn(session_id="session-a", role="user", content="hello")

            history = store.recent_turns(session_id="session-a")

            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["content"], "hello")

    def test_clear_session_still_works_after_memory_is_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "memory.sqlite3"
            store = ConversationMemoryStore(db_path, enabled=True)
            store.save_turn(session_id="session-a", role="user", content="keep this temporary")

            store.set_enabled(False)
            store.clear_session(session_id="session-a")
            store.set_enabled(True)

            history = store.recent_turns(session_id="session-a")

            self.assertEqual(history, [])

    def test_list_sessions_returns_recent_session_summaries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "memory.sqlite3"
            store = ConversationMemoryStore(db_path, enabled=True)
            store.save_turn(session_id="session-a", role="user", content="first message")
            store.save_turn(session_id="session-a", role="assistant", content="assistant reply")
            store.save_turn(session_id="session-b", role="user", content="second session message")

            sessions = store.list_sessions(limit=5)

            self.assertEqual(len(sessions), 2)
            self.assertEqual(sessions[0]["session_id"], "session-b")
            self.assertEqual(sessions[0]["turn_count"], 1)
            self.assertEqual(sessions[1]["session_id"], "session-a")
            self.assertEqual(sessions[1]["turn_count"], 2)
            self.assertEqual(sessions[1]["last_content_preview"], "assistant reply")

    def test_clear_all_removes_stored_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "memory.sqlite3"
            store = ConversationMemoryStore(db_path, enabled=True)
            store.save_turn(session_id="session-a", role="user", content="first")
            store.save_turn(session_id="session-b", role="user", content="second")

            store.clear_all()

            self.assertEqual(store.list_sessions(limit=5), [])


class MemoryRouteTests(unittest.TestCase):
    def test_session_routes_list_and_clear_all(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "memory.sqlite3"
            memory_store = ConversationMemoryStore(db_path, enabled=True)
            memory_store.save_turn(session_id="session-a", role="user", content="first")
            memory_store.save_turn(session_id="session-b", role="assistant", content="second")
            request = SimpleNamespace(
                app=SimpleNamespace(
                    state=SimpleNamespace(
                        orchestrator=SimpleNamespace(memory=memory_store),
                    )
                )
            )

            listed = list_sessions(request, limit=10)
            cleared = clear_all_sessions(request)

            self.assertEqual(len(listed["sessions"]), 2)
            self.assertEqual(cleared["message"], "All stored session history cleared.")
            self.assertEqual(memory_store.list_sessions(limit=10), [])


if __name__ == "__main__":
    unittest.main()

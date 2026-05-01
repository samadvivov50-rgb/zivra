from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from app.services.notes import WorkspaceNotesService
from app.services.orchestrator import IntentRouter
from app.tools.safe import ReadNoteTool, SearchNotesTool, UpdateNoteTool


class WorkspaceNotesServiceTests(unittest.TestCase):
    def test_list_recent_returns_notes_with_title_and_preview(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            notes_dir = Path(temp_dir)
            older = notes_dir / "older-note.md"
            newer = notes_dir / "newer-note.md"

            older.write_text("# Older note\n\nThis came first.\n", encoding="utf-8")
            newer.write_text("# Newer note\n\nThis is the latest preview.\n", encoding="utf-8")

            os.utime(older, (1_700_000_000, 1_700_000_000))
            os.utime(newer, (1_800_000_000, 1_800_000_000))

            service = WorkspaceNotesService(notes_dir)
            notes = service.list_recent(limit=2)

            self.assertEqual(len(notes), 2)
            self.assertEqual(notes[0]["title"], "Newer note")
            self.assertEqual(notes[0]["preview"], "This is the latest preview.")
            self.assertEqual(notes[1]["title"], "Older note")

    def test_read_note_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            notes_dir = Path(temp_dir)
            service = WorkspaceNotesService(notes_dir)

            note = service.read_note("../secret.txt")

            self.assertIsNone(note)

    def test_update_note_persists_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            notes_dir = Path(temp_dir)
            note_path = notes_dir / "demo.md"
            note_path.write_text("# Demo\n\nOld content.\n", encoding="utf-8")

            service = WorkspaceNotesService(notes_dir)
            updated = service.update_note("demo.md", content="# Demo\n\nNew content.\n")

            self.assertIsNotNone(updated)
            self.assertEqual(updated["title"], "Demo")
            self.assertIn("New content.", updated["content"])
            self.assertEqual(note_path.read_text(encoding="utf-8"), "# Demo\n\nNew content.\n")

    def test_update_note_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            notes_dir = Path(temp_dir)
            service = WorkspaceNotesService(notes_dir)

            updated = service.update_note("../secret.txt", content="nope")

            self.assertIsNone(updated)

    def test_search_returns_ranked_matches_with_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            notes_dir = Path(temp_dir)
            titled = notes_dir / "launch-plan.md"
            content_match = notes_dir / "ops-notes.md"
            unrelated = notes_dir / "shopping.txt"

            titled.write_text("# Launch plan\n\nFinalize launch checklist and owners.\n", encoding="utf-8")
            content_match.write_text("# Ops notes\n\nWe should review the launch checklist this week.\n", encoding="utf-8")
            unrelated.write_text("Milk and tea\n", encoding="utf-8")

            service = WorkspaceNotesService(notes_dir)
            results = service.search(query="launch checklist", limit=5)

            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]["title"], "Launch plan")
            self.assertIn("launch checklist", results[0]["match_preview"].lower())
            self.assertGreaterEqual(results[0]["match_score"], results[1]["match_score"])

    def test_search_notes_tool_wraps_workspace_search(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            notes_dir = Path(temp_dir)
            (notes_dir / "demo.md").write_text("# Demo\n\nShip the launch demo.\n", encoding="utf-8")

            service = WorkspaceNotesService(notes_dir)
            tool = SearchNotesTool(service)
            result = tool.execute({"query": "launch demo"})

            self.assertTrue(result.success)
            self.assertEqual(result.data["query"], "launch demo")
            self.assertEqual(result.data["notes"][0]["title"], "Demo")

    def test_resolve_note_prefers_direct_name_and_returns_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            notes_dir = Path(temp_dir)
            note_path = notes_dir / "demo-note.md"
            note_path.write_text("# Demo note\n\nFull content for the note reader.\n", encoding="utf-8")

            service = WorkspaceNotesService(notes_dir)
            resolved = service.resolve_note("demo-note.md")

            self.assertIsNotNone(resolved)
            self.assertEqual(resolved["name"], "demo-note.md")
            self.assertIn("Full content for the note reader.", resolved["content"])

    def test_read_note_tool_returns_note_excerpt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            notes_dir = Path(temp_dir)
            (notes_dir / "launch-plan.md").write_text("# Launch plan\n\nShip the demo carefully.\n", encoding="utf-8")

            service = WorkspaceNotesService(notes_dir)
            tool = ReadNoteTool(service)
            result = tool.execute({"query": "launch plan"})

            self.assertTrue(result.success)
            self.assertIn("Launch plan", result.message)
            self.assertIn("Ship the demo carefully.", result.message)
            self.assertEqual(result.data["note"]["name"], "launch-plan.md")

    def test_update_note_tool_appends_to_existing_note(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            notes_dir = Path(temp_dir)
            note_path = notes_dir / "launch-plan.md"
            note_path.write_text("# Launch plan\n\nInitial checklist.\n", encoding="utf-8")

            service = WorkspaceNotesService(notes_dir)
            tool = UpdateNoteTool(service)
            result = tool.execute(
                {
                    "query": "launch plan",
                    "content": "Add rehearsal timing.",
                    "mode": "append",
                }
            )

            self.assertTrue(result.success)
            self.assertIn("Appended", result.message)
            self.assertIn("Add rehearsal timing.", note_path.read_text(encoding="utf-8"))

    def test_update_note_tool_can_replace_contents(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            notes_dir = Path(temp_dir)
            note_path = notes_dir / "launch-plan.md"
            note_path.write_text("# Launch plan\n\nInitial checklist.\n", encoding="utf-8")

            service = WorkspaceNotesService(notes_dir)
            tool = UpdateNoteTool(service)
            result = tool.execute(
                {
                    "query": "launch plan",
                    "content": "New plan goes here.",
                    "mode": "replace",
                }
            )

            self.assertTrue(result.success)
            replaced = note_path.read_text(encoding="utf-8")
            self.assertIn("# Launch plan", replaced)
            self.assertIn("New plan goes here.", replaced)
            self.assertNotIn("Initial checklist.", replaced)

    def test_router_routes_note_search_before_web_search(self) -> None:
        router = IntentRouter(now_provider=lambda: datetime(2026, 3, 20, 10, 0, tzinfo=timezone.utc))

        route = router.route("Search notes for launch demo")

        self.assertEqual(route.tool_name, "search_notes")
        self.assertEqual(route.arguments["query"], "launch demo")

    def test_router_routes_note_read_before_website_opening(self) -> None:
        router = IntentRouter(now_provider=lambda: datetime(2026, 3, 20, 10, 0, tzinfo=timezone.utc))

        route = router.route("Open note launch plan")

        self.assertEqual(route.tool_name, "read_note")
        self.assertEqual(route.arguments["query"], "launch plan")

    def test_router_routes_note_append_requests(self) -> None:
        router = IntentRouter(now_provider=lambda: datetime(2026, 3, 20, 10, 0, tzinfo=timezone.utc))

        route = router.route("Append to note launch plan with add rehearsal timing")

        self.assertEqual(route.tool_name, "update_note")
        self.assertEqual(route.arguments["mode"], "append")
        self.assertEqual(route.arguments["query"], "launch plan")
        self.assertEqual(route.arguments["content"], "add rehearsal timing")

    def test_router_routes_note_replace_requests(self) -> None:
        router = IntentRouter(now_provider=lambda: datetime(2026, 3, 20, 10, 0, tzinfo=timezone.utc))

        route = router.route("Replace note launch plan with new rollout draft")

        self.assertEqual(route.tool_name, "update_note")
        self.assertEqual(route.arguments["mode"], "replace")
        self.assertEqual(route.arguments["query"], "launch plan")


if __name__ == "__main__":
    unittest.main()

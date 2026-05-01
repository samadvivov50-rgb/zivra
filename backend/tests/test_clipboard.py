from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.api.routes.clipboard import UpdateClipboardRequest, read_clipboard, write_clipboard
from app.services.audit import AuditLogger
from app.services.clipboard import ClipboardService
from app.services.orchestrator import IntentRouter
from app.tools.safe import ReadClipboardTool, WriteClipboardTool


class ClipboardServiceTests(unittest.TestCase):
    def test_build_metadata_normalizes_newlines(self) -> None:
        service = ClipboardService(reader=lambda: "alpha\r\nbeta", writer=lambda text: None)

        text = service.read_text()
        metadata = service.build_metadata(text)

        self.assertEqual(text, "alpha\nbeta")
        self.assertEqual(metadata["length"], 10)
        self.assertEqual(metadata["line_count"], 2)
        self.assertFalse(metadata["empty"])

    def test_write_text_returns_normalized_text(self) -> None:
        writes: list[str] = []
        service = ClipboardService(reader=lambda: "", writer=lambda text: writes.append(text))

        written = service.write_text("hello\r\nworld")

        self.assertEqual(written, "hello\nworld")
        self.assertEqual(writes, ["hello\nworld"])


class ClipboardToolTests(unittest.TestCase):
    def test_read_clipboard_tool_reports_metadata_only(self) -> None:
        service = ClipboardService(reader=lambda: "super secret token", writer=lambda text: None)
        tool = ReadClipboardTool(service)

        result = tool.execute({})

        self.assertTrue(result.success)
        self.assertIn("clipboard", result.data)
        self.assertNotIn("super secret token", json.dumps(result.to_dict()))
        self.assertIn("characters", result.message)

    def test_write_clipboard_tool_reports_character_count(self) -> None:
        writes: list[str] = []
        service = ClipboardService(reader=lambda: "", writer=lambda text: writes.append(text))
        tool = WriteClipboardTool(service)

        result = tool.execute({"text": "deployment checklist"})

        self.assertTrue(result.success)
        self.assertEqual(writes, ["deployment checklist"])
        self.assertEqual(result.data["clipboard"]["length"], len("deployment checklist"))
        self.assertNotIn("deployment checklist", json.dumps(result.to_dict()))


class ClipboardRouterTests(unittest.TestCase):
    def test_router_routes_clipboard_reads(self) -> None:
        router = IntentRouter()

        route = router.route("Read my clipboard")

        self.assertEqual(route.tool_name, "read_clipboard")
        self.assertEqual(route.intent, "read_clipboard")

    def test_router_routes_clipboard_writes(self) -> None:
        router = IntentRouter()

        route = router.route("Copy deployment checklist to clipboard")

        self.assertEqual(route.tool_name, "write_clipboard")
        self.assertEqual(route.arguments["text"], "deployment checklist")


class ClipboardRouteTests(unittest.TestCase):
    def test_read_route_returns_text_but_audit_log_only_keeps_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            request = self._build_request(
                temp_dir,
                ClipboardService(reader=lambda: "super secret token", writer=lambda text: None),
            )

            response = read_clipboard(request)

            self.assertEqual(response["text"], "super secret token")
            events = request.app.state.audit_logger.recent(limit=5)
            self.assertEqual(len(events), 1)
            self.assertNotIn("super secret token", json.dumps(events[0]))
            self.assertEqual(events[0]["result"]["data"]["clipboard"]["length"], len("super secret token"))

    def test_write_route_updates_clipboard_and_audit_log_redacts_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            writes: list[str] = []
            request = self._build_request(
                temp_dir,
                ClipboardService(reader=lambda: "", writer=lambda text: writes.append(text)),
            )

            response = write_clipboard(UpdateClipboardRequest(text="release checklist"), request)

            self.assertEqual(response["metadata"]["length"], len("release checklist"))
            self.assertEqual(writes, ["release checklist"])
            events = request.app.state.audit_logger.recent(limit=5)
            self.assertEqual(len(events), 1)
            self.assertNotIn("release checklist", json.dumps(events[0]))
            self.assertEqual(events[0]["result"]["data"]["clipboard"]["length"], len("release checklist"))

    def _build_request(self, temp_dir: str, clipboard_service: ClipboardService):
        state = SimpleNamespace(
            clipboard_service=clipboard_service,
            audit_logger=AuditLogger(Path(temp_dir) / "audit" / "actions.jsonl"),
        )
        return SimpleNamespace(app=SimpleNamespace(state=state))


if __name__ == "__main__":
    unittest.main()

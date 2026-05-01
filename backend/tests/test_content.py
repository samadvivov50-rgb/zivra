from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.api.routes.content import ContentPackageRequest, build_content_package
from app.models import ActionStatus, ApprovalMode, PermissionLevel, ProposedAction, ToolCategory, ToolResult
from app.services.audit import AuditLogger
from app.services.content import ContentStrategyService
from app.services.orchestrator import IntentRouter
from app.services.policy import PolicyDecision
from app.tools.safe import GenerateContentPackageTool


class ContentStrategyServiceTests(unittest.TestCase):
    def test_build_package_generates_titles_descriptions_tags_and_chapters(self) -> None:
        service = ContentStrategyService()

        payload = service.build_package(
            topic="Local-first AI assistant demos",
            audience="indie builders",
            context="Show what makes approvals useful. Explain why local-first tools reduce risk. Share practical launch steps.",
        )

        package = payload["package"]
        self.assertEqual(payload["topic"], "Local-first AI assistant demos")
        self.assertGreaterEqual(len(package["youtube_titles"]), 4)
        self.assertGreaterEqual(len(package["tags"]), 4)
        self.assertGreaterEqual(len(package["chapters"]), 4)
        self.assertIn("local-first ai assistant demos", package["meta_description"].lower())

    def test_audit_payload_keeps_metadata_without_context_copy(self) -> None:
        service = ContentStrategyService()
        payload = service.build_package(
            topic="AI workflow videos",
            audience="ops teams",
            context="Internal rollout notes that should not land in audit logs.",
        )

        audit_payload = service.audit_payload(payload)

        self.assertEqual(audit_payload["topic"], "AI workflow videos")
        self.assertNotIn("Internal rollout notes", json.dumps(audit_payload))


class GenerateContentPackageToolTests(unittest.TestCase):
    def test_tool_returns_metadata_only(self) -> None:
        tool = GenerateContentPackageTool(ContentStrategyService())

        result = tool.execute(
            {
                "topic": "AI workflow videos",
                "context": "Private launch notes should stay out of the tool payload.",
            }
        )

        self.assertTrue(result.success)
        self.assertIn("Top ideas", result.message)
        self.assertNotIn("Private launch notes", json.dumps(result.to_dict()))


class ContentRouterTests(unittest.TestCase):
    def test_router_routes_youtube_idea_requests(self) -> None:
        router = IntentRouter()

        route = router.route("YouTube ideas for local-first AI assistant demos")

        self.assertEqual(route.tool_name, "generate_content_package")
        self.assertEqual(route.arguments["topic"], "local-first AI assistant demos")


class ContentRouteTests(unittest.TestCase):
    def test_route_logs_metadata_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            request = self._build_request(temp_dir)

            response = build_content_package(
                ContentPackageRequest(
                    topic="AI workflow videos",
                    audience="ops teams",
                    context="Sensitive internal positioning notes.",
                ),
                request,
            )

            self.assertIn("youtube_titles", response["package"])
            events = request.app.state.audit_logger.recent(limit=5)
            self.assertEqual(len(events), 1)
            self.assertNotIn("Sensitive internal positioning notes", json.dumps(events[0]))
            self.assertEqual(events[0]["result"]["data"]["content"]["topic"], "AI workflow videos")

    def test_audit_logger_redacts_content_context_argument(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            audit_logger = AuditLogger(Path(temp_dir) / "audit" / "actions.jsonl")
            action = ProposedAction(
                action_id="content-1",
                session_id="test",
                tool_name="generate_content_package",
                category=ToolCategory.COMMUNICATION,
                permission_level=PermissionLevel.SAFE_READ,
                approval_mode=ApprovalMode.NONE,
                summary="Generate content ideas.",
                arguments={"topic": "AI workflow videos", "context": "Private campaign notes"},
            )
            decision = PolicyDecision(
                allowed=True,
                requires_confirmation=False,
                approval_mode=ApprovalMode.NONE,
                reason="Safe read.",
            )
            result = ToolResult(success=True, message="Generated ideas.", data={"ok": True})

            audit_logger.record(action=action, status=ActionStatus.EXECUTED, decision=decision, result=result)

            events = audit_logger.recent(limit=5)
            self.assertEqual(events[0]["action"]["arguments"]["context"], "[redacted]")
            self.assertNotIn("Private campaign notes", json.dumps(events[0]))

    def _build_request(self, temp_dir: str):
        state = SimpleNamespace(
            content_service=ContentStrategyService(),
            audit_logger=AuditLogger(Path(temp_dir) / "audit" / "actions.jsonl"),
        )
        return SimpleNamespace(app=SimpleNamespace(state=state))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.api.routes.emails import EmailDraftRequest, create_email_draft, send_email
from app.core.config import Settings
from app.models import ActionStatus, ApprovalMode, PermissionLevel, ProposedAction, ToolCategory, ToolResult
from app.services.audit import AuditLogger
from app.services.emails import EmailService
from app.services.orchestrator import IntentRouter
from app.services.policy import PolicyDecision
from app.tools.safe import DraftEmailTool, SendEmailTool


def _build_settings(temp_dir: str) -> Settings:
    settings = Settings(repo_root=Path(temp_dir))
    settings.smtp_host = "smtp.example.com"
    settings.smtp_port = 587
    settings.smtp_use_tls = True
    settings.smtp_use_ssl = False
    settings.email_from_address = "zivra@example.com"
    settings.email_from_name = "Zivra"
    return settings


class EmailServiceTests(unittest.TestCase):
    def test_service_creates_and_lists_local_drafts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = _build_settings(temp_dir)
            service = EmailService(settings.emails_db_path, settings=settings)

            created = service.create_draft(
                to_address="team@example.com",
                subject="Weekly sync",
                body="Status attached",
            )

            self.assertEqual(created["status"], "draft")
            self.assertEqual(service.summary()["draft"], 1)
            self.assertEqual(service.list_emails(limit=5)[0]["subject"], "Weekly sync")

    def test_service_can_send_drafts_with_configured_transport(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            sent_payloads: list[dict[str, str]] = []
            settings = _build_settings(temp_dir)
            service = EmailService(
                settings.emails_db_path,
                settings=settings,
                transport=lambda payload: sent_payloads.append(payload),
            )
            draft = service.create_draft(
                to_address="team@example.com",
                subject="Weekly sync",
                body="Status attached",
            )

            sent = service.send_draft(int(draft["id"]))

            self.assertIsNotNone(sent)
            self.assertEqual(sent["status"], "sent")
            self.assertEqual(service.summary()["sent"], 1)
            self.assertEqual(sent_payloads[0]["to"], "team@example.com")

    def test_send_email_tool_reports_failed_delivery_without_body_in_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = _build_settings(temp_dir)
            service = EmailService(
                settings.emails_db_path,
                settings=settings,
                transport=lambda payload: (_ for _ in ()).throw(RuntimeError("Mailbox unavailable")),
            )
            tool = SendEmailTool(service)

            result = tool.execute(
                {"to": "team@example.com", "subject": "Weekly sync", "body": "Sensitive body text"}
            )

            self.assertFalse(result.success)
            self.assertIn("delivery failed", result.message.lower())
            self.assertEqual(result.data["email"]["status"], "failed")
            self.assertNotIn("Sensitive body text", json.dumps(result.to_dict()))

    def test_draft_email_tool_uses_local_outbox_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = _build_settings(temp_dir)
            service = EmailService(settings.emails_db_path, settings=settings)
            tool = DraftEmailTool(service)

            result = tool.execute(
                {"to": "team@example.com", "subject": "Weekly sync", "body": "Status attached"}
            )

            self.assertTrue(result.success)
            self.assertEqual(result.data["email"]["status"], "draft")
            self.assertNotIn("Status attached", json.dumps(result.to_dict()))


class EmailRouterTests(unittest.TestCase):
    def test_router_routes_email_drafts(self) -> None:
        router = IntentRouter()

        route = router.route("Draft an email to team@example.com subject Weekly sync")

        self.assertEqual(route.tool_name, "draft_email")
        self.assertEqual(route.arguments["to"], "team@example.com")
        self.assertEqual(route.arguments["subject"], "Weekly sync")
        self.assertEqual(route.arguments["body"], "")

    def test_router_routes_email_sends(self) -> None:
        router = IntentRouter()

        route = router.route("Send email to team@example.com subject Weekly sync body Status attached")

        self.assertEqual(route.tool_name, "send_email")
        self.assertEqual(route.arguments["to"], "team@example.com")
        self.assertEqual(route.arguments["subject"], "Weekly sync")
        self.assertEqual(route.arguments["body"], "Status attached")


class EmailRouteTests(unittest.TestCase):
    def test_create_draft_route_logs_without_full_body(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            request = self._build_request(temp_dir)

            response = create_email_draft(
                EmailDraftRequest(
                    to="team@example.com",
                    subject="Weekly sync",
                    body="Sensitive delivery notes",
                ),
                request,
            )

            self.assertEqual(response["email"]["status"], "draft")
            events = request.app.state.audit_logger.recent(limit=5)
            self.assertEqual(len(events), 1)
            self.assertNotIn("Sensitive delivery notes", json.dumps(events[0]))
            self.assertEqual(events[0]["result"]["data"]["email"]["status"], "draft")

    def test_send_route_logs_sent_email_without_full_body(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            sent_payloads: list[dict[str, str]] = []
            request = self._build_request(
                temp_dir,
                transport=lambda payload: sent_payloads.append(payload),
            )
            draft = request.app.state.email_service.create_draft(
                to_address="team@example.com",
                subject="Weekly sync",
                body="Sensitive delivery notes",
            )

            response = send_email(int(draft["id"]), request)

            self.assertEqual(response["email"]["status"], "sent")
            self.assertEqual(sent_payloads[0]["subject"], "Weekly sync")
            events = request.app.state.audit_logger.recent(limit=5)
            self.assertEqual(len(events), 1)
            self.assertNotIn("Sensitive delivery notes", json.dumps(events[0]))
            self.assertEqual(events[0]["result"]["data"]["email"]["status"], "sent")

    def test_audit_logger_redacts_email_action_bodies(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            audit_logger = AuditLogger(Path(temp_dir) / "audit" / "actions.jsonl")
            action = ProposedAction(
                action_id="a1",
                session_id="test",
                tool_name="send_email",
                category=ToolCategory.COMMUNICATION,
                permission_level=PermissionLevel.SENSITIVE,
                approval_mode=ApprovalMode.USER_CONFIRMATION,
                summary="Send a sensitive email.",
                arguments={"to": "team@example.com", "subject": "Weekly sync", "body": "Private launch numbers"},
            )
            decision = PolicyDecision(
                allowed=True,
                requires_confirmation=True,
                approval_mode=ApprovalMode.USER_CONFIRMATION,
                reason="Needs confirmation.",
            )
            result = ToolResult(success=True, message="Sent.", data={"ok": True})

            audit_logger.record(action=action, status=ActionStatus.EXECUTED, decision=decision, result=result)

            events = audit_logger.recent(limit=5)
            self.assertEqual(events[0]["action"]["arguments"]["body"], "[redacted]")
            self.assertEqual(events[0]["action"]["arguments"]["body_length"], len("Private launch numbers"))
            self.assertNotIn("Private launch numbers", json.dumps(events[0]))

    def _build_request(self, temp_dir: str, transport=None):
        settings = _build_settings(temp_dir)
        email_service = EmailService(settings.emails_db_path, settings=settings, transport=transport)
        state = SimpleNamespace(
            email_service=email_service,
            audit_logger=AuditLogger(Path(temp_dir) / "audit" / "actions.jsonl"),
        )
        return SimpleNamespace(app=SimpleNamespace(state=state))


if __name__ == "__main__":
    unittest.main()

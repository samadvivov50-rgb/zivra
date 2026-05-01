from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.api.routes.messages import (
    WhatsAppDraftRequest,
    create_whatsapp_draft,
    receive_whatsapp_webhook,
    send_whatsapp_message,
    verify_whatsapp_webhook,
)
from app.core.config import Settings
from app.models import ActionStatus, ApprovalMode, PermissionLevel, ProposedAction, ToolCategory, ToolResult
from app.services.audit import AuditLogger
from app.services.messages import MessagingService
from app.services.orchestrator import IntentRouter
from app.services.policy import PolicyDecision
from app.tools.safe import DraftWhatsAppMessageTool, SendWhatsAppMessageTool


def _build_settings(temp_dir: str, **overrides) -> Settings:
    return Settings(repo_root=Path(temp_dir), **overrides)


class FakeCloudClient:
    def __init__(self, *, configured: bool = True) -> None:
        self.configured = configured
        self.sent_payloads: list[tuple[str, str]] = []
        self.accept_signature = True
        self.events: list[dict] = []

    def is_configured(self) -> bool:
        return self.configured

    def status(self) -> dict:
        return {
            "cloud_configured": self.configured,
            "api_version": "v23.0",
            "phone_number_id_masked": "123...789",
            "verify_token_configured": True,
            "signature_validation": True,
            "webhook_path": "/messages/whatsapp/webhook",
        }

    def send_text_message(self, *, to_number: str, body: str) -> dict:
        self.sent_payloads.append((to_number, body))
        return {
            "message_id": "wamid.test-123",
            "response": {"messages": [{"id": "wamid.test-123"}]},
        }

    def verify_webhook(self, *, mode: str, verify_token: str, challenge: str) -> str:
        if mode != "subscribe" or verify_token != "verify-me":
            raise ValueError("bad verification")
        return challenge

    def validate_signature(self, body: bytes, signature_header: str | None) -> bool:
        del body, signature_header
        return self.accept_signature

    def parse_webhook_events(self, payload: dict) -> list[dict]:
        del payload
        return list(self.events)


class _WebhookRequest:
    def __init__(self, state: SimpleNamespace, body: bytes) -> None:
        self.app = SimpleNamespace(state=state)
        self._body = body

    async def body(self) -> bytes:
        return self._body


class MessagingServiceTests(unittest.TestCase):
    def test_service_creates_and_lists_whatsapp_drafts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = _build_settings(temp_dir)
            service = MessagingService(settings.messages_db_path, settings=settings, opener=lambda url: True)

            created = service.create_whatsapp_draft(
                to_number="+1 555 123 4567",
                body="Demo is ready for review.",
            )

            self.assertEqual(created["status"], "draft")
            self.assertEqual(service.summary()["draft"], 1)
            self.assertEqual(service.list_messages(limit=5)[0]["to"], "+1 555 123 4567")
            self.assertEqual(created["provider"], "browser_handoff")

    def test_service_opens_whatsapp_handoff_when_cloud_api_is_not_configured(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            opened_urls: list[str] = []
            settings = _build_settings(temp_dir)
            service = MessagingService(
                settings.messages_db_path,
                settings=settings,
                opener=lambda url: opened_urls.append(url) or True,
            )
            draft = service.create_whatsapp_draft(
                to_number="+1 555 123 4567",
                body="Demo is ready for review.",
            )

            handed_off = service.send_whatsapp_draft(int(draft["id"]))

            self.assertIsNotNone(handed_off)
            self.assertEqual(handed_off["status"], "opened")
            self.assertEqual(service.summary()["opened"], 1)
            self.assertIn("wa.me/15551234567", opened_urls[0])

    def test_service_sends_directly_via_cloud_api_when_configured(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = _build_settings(
                temp_dir,
                whatsapp_phone_number_id="123456789",
                whatsapp_access_token="token-1",
            )
            cloud = FakeCloudClient(configured=True)
            service = MessagingService(
                settings.messages_db_path,
                settings=settings,
                opener=lambda url: self.fail(f"Browser should not be used: {url}"),
                cloud_client=cloud,
            )
            draft = service.create_whatsapp_draft(
                to_number="+1 555 123 4567",
                body="Ship update",
            )

            sent = service.send_whatsapp_draft(int(draft["id"]))

            self.assertIsNotNone(sent)
            self.assertEqual(sent["status"], "sent")
            self.assertEqual(sent["provider"], "cloud_api")
            self.assertEqual(sent["provider_message_id"], "wamid.test-123")
            self.assertEqual(cloud.sent_payloads, [("15551234567", "Ship update")])
            self.assertEqual(service.summary()["sent"], 1)
            self.assertEqual(service.delivery_status()["delivery_mode"], "cloud_api")

    def test_service_processes_inbound_webhook_events(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = _build_settings(
                temp_dir,
                whatsapp_phone_number_id="123456789",
                whatsapp_access_token="token-1",
            )
            cloud = FakeCloudClient(configured=True)
            cloud.events = [
                {
                    "event_type": "message",
                    "provider": "cloud_api",
                    "provider_message_id": "wamid.inbound-1",
                    "direction": "inbound",
                    "status": "received",
                    "phone_digits": "15550001111",
                    "to_number": "+15550001111",
                    "contact_name": "Samad",
                    "body": "Hello from WhatsApp",
                    "message_type": "text",
                    "remote_timestamp": "2026-03-23T01:00:00+00:00",
                    "source": "whatsapp_cloud",
                    "metadata": {"display_phone_number": "+1 555 000 1111"},
                }
            ]
            service = MessagingService(
                settings.messages_db_path,
                settings=settings,
                cloud_client=cloud,
            )

            result = service.receive_whatsapp_webhook(b"{}", signature_header="sha256=test")

            self.assertEqual(result["received_messages"], 1)
            messages = service.list_messages(limit=5)
            self.assertEqual(messages[0]["direction"], "inbound")
            self.assertEqual(messages[0]["contact_name"], "Samad")
            self.assertEqual(messages[0]["body"], "Hello from WhatsApp")
            self.assertEqual(service.summary()["received"], 1)

    def test_service_applies_status_webhook_events_to_outbound_messages(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = _build_settings(
                temp_dir,
                whatsapp_phone_number_id="123456789",
                whatsapp_access_token="token-1",
            )
            cloud = FakeCloudClient(configured=True)
            service = MessagingService(
                settings.messages_db_path,
                settings=settings,
                cloud_client=cloud,
            )
            draft = service.create_whatsapp_draft(to_number="+15551234567", body="Status attached")
            sent = service.send_whatsapp_draft(int(draft["id"]))
            self.assertIsNotNone(sent)

            cloud.events = [
                {
                    "event_type": "status",
                    "provider": "cloud_api",
                    "provider_message_id": "wamid.test-123",
                    "status": "read",
                    "phone_digits": "15551234567",
                    "to_number": "+15551234567",
                    "error": "",
                    "remote_timestamp": "2026-03-23T01:05:00+00:00",
                    "metadata": {"conversation_id": "conv-1"},
                }
            ]

            result = service.receive_whatsapp_webhook(b"{}", signature_header="sha256=test")

            self.assertEqual(result["updated_messages"], 1)
            refreshed = service.get_message(int(sent["id"]))
            self.assertIsNotNone(refreshed)
            self.assertEqual(refreshed["status"], "read")
            self.assertEqual(service.summary()["read"], 1)

    def test_send_whatsapp_tool_reports_failed_dispatch_without_body_in_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = _build_settings(temp_dir)
            service = MessagingService(
                settings.messages_db_path,
                settings=settings,
                opener=lambda url: (_ for _ in ()).throw(RuntimeError("Browser unavailable")),
            )
            tool = SendWhatsAppMessageTool(service)

            result = tool.execute(
                {"to": "+15551234567", "body": "Sensitive launch note"}
            )

            self.assertFalse(result.success)
            self.assertIn("failed", result.message.lower())
            self.assertEqual(result.data["message"]["status"], "failed")
            self.assertNotIn("Sensitive launch note", json.dumps(result.to_dict()))

    def test_draft_whatsapp_tool_uses_local_outbox_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = _build_settings(temp_dir)
            service = MessagingService(settings.messages_db_path, settings=settings, opener=lambda url: True)
            tool = DraftWhatsAppMessageTool(service)

            result = tool.execute(
                {"to": "+15551234567", "body": "Status attached"}
            )

            self.assertTrue(result.success)
            self.assertEqual(result.data["message"]["status"], "draft")
            self.assertNotIn("Status attached", json.dumps(result.to_dict()))


class MessagingRouterTests(unittest.TestCase):
    def test_router_routes_whatsapp_drafts(self) -> None:
        router = IntentRouter()

        route = router.route("Draft WhatsApp to +15551234567 message Demo is ready")

        self.assertEqual(route.tool_name, "draft_whatsapp_message")
        self.assertEqual(route.arguments["to"], "+15551234567")
        self.assertEqual(route.arguments["body"], "Demo is ready")

    def test_router_routes_whatsapp_handoffs(self) -> None:
        router = IntentRouter()

        route = router.route("Send WhatsApp to +15551234567 message Demo is ready")

        self.assertEqual(route.tool_name, "send_whatsapp_message")
        self.assertEqual(route.arguments["to"], "+15551234567")
        self.assertEqual(route.arguments["body"], "Demo is ready")


class MessagingRouteTests(unittest.TestCase):
    def test_create_draft_route_logs_without_full_body(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            request = self._build_request(temp_dir)

            response = create_whatsapp_draft(
                WhatsAppDraftRequest(
                    to="+15551234567",
                    body="Sensitive delivery notes",
                ),
                request,
            )

            self.assertEqual(response["outbox_message"]["status"], "draft")
            events = request.app.state.audit_logger.recent(limit=5)
            self.assertEqual(len(events), 1)
            self.assertNotIn("Sensitive delivery notes", json.dumps(events[0]))
            self.assertEqual(events[0]["result"]["data"]["message"]["status"], "draft")

    def test_send_route_logs_cloud_dispatch_without_full_body(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            cloud = FakeCloudClient(configured=True)
            request = self._build_request(
                temp_dir,
                cloud_client=cloud,
                settings_overrides={
                    "whatsapp_phone_number_id": "123456789",
                    "whatsapp_access_token": "token-1",
                },
            )
            draft = request.app.state.messaging_service.create_whatsapp_draft(
                to_number="+15551234567",
                body="Sensitive delivery notes",
            )

            response = send_whatsapp_message(int(draft["id"]), request)

            self.assertEqual(response["outbox_message"]["status"], "sent")
            self.assertIn("Meta Cloud API", response["message"])
            events = request.app.state.audit_logger.recent(limit=5)
            self.assertEqual(len(events), 1)
            self.assertNotIn("Sensitive delivery notes", json.dumps(events[0]))
            self.assertEqual(events[0]["result"]["data"]["message"]["status"], "sent")

    def test_webhook_routes_verify_and_store_messages(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            cloud = FakeCloudClient(configured=True)
            cloud.events = [
                {
                    "event_type": "message",
                    "provider": "cloud_api",
                    "provider_message_id": "wamid.inbound-1",
                    "direction": "inbound",
                    "status": "received",
                    "phone_digits": "15550001111",
                    "to_number": "+15550001111",
                    "contact_name": "Samad",
                    "body": "Hello from WhatsApp",
                    "message_type": "text",
                    "remote_timestamp": "2026-03-23T01:00:00+00:00",
                    "source": "whatsapp_cloud",
                    "metadata": {"display_phone_number": "+1 555 000 1111"},
                }
            ]
            request = self._build_request(
                temp_dir,
                cloud_client=cloud,
                settings_overrides={
                    "whatsapp_phone_number_id": "123456789",
                    "whatsapp_access_token": "token-1",
                    "whatsapp_verify_token": "verify-me",
                },
            )

            challenge = verify_whatsapp_webhook(
                request,
                hub_mode="subscribe",
                hub_verify_token="verify-me",
                hub_challenge="challenge-123",
            )
            result = asyncio.run(receive_whatsapp_webhook(_WebhookRequest(request.app.state, b"{}"), "sha256=test"))

            self.assertEqual(challenge, "challenge-123")
            self.assertEqual(result["received_messages"], 1)
            messages = request.app.state.messaging_service.list_messages(limit=5)
            self.assertEqual(messages[0]["direction"], "inbound")

    def test_audit_logger_redacts_whatsapp_action_bodies(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            audit_logger = AuditLogger(Path(temp_dir) / "audit" / "actions.jsonl")
            action = ProposedAction(
                action_id="a1",
                session_id="test",
                tool_name="send_whatsapp_message",
                category=ToolCategory.COMMUNICATION,
                permission_level=PermissionLevel.SENSITIVE,
                approval_mode=ApprovalMode.USER_CONFIRMATION,
                summary="Open a sensitive WhatsApp handoff.",
                arguments={"to": "+15551234567", "body": "Private launch numbers"},
            )
            decision = PolicyDecision(
                allowed=True,
                requires_confirmation=True,
                approval_mode=ApprovalMode.USER_CONFIRMATION,
                reason="Needs confirmation.",
            )
            result = ToolResult(success=True, message="Opened.", data={"ok": True})

            audit_logger.record(action=action, status=ActionStatus.EXECUTED, decision=decision, result=result)

            events = audit_logger.recent(limit=5)
            self.assertEqual(events[0]["action"]["arguments"]["body"], "[redacted]")
            self.assertEqual(events[0]["action"]["arguments"]["body_length"], len("Private launch numbers"))
            self.assertNotIn("Private launch numbers", json.dumps(events[0]))

    def _build_request(self, temp_dir: str, opener=None, cloud_client=None, settings_overrides: dict | None = None):
        settings = _build_settings(temp_dir, **(settings_overrides or {}))
        messaging_service = MessagingService(
            settings.messages_db_path,
            settings=settings,
            opener=opener or (lambda url: True),
            cloud_client=cloud_client,
        )
        state = SimpleNamespace(
            messaging_service=messaging_service,
            audit_logger=AuditLogger(Path(temp_dir) / "audit" / "actions.jsonl"),
        )
        return SimpleNamespace(app=SimpleNamespace(state=state))


if __name__ == "__main__":
    unittest.main()

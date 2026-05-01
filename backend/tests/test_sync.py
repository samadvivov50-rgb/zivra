from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.api.routes.sync import companion_access_info, export_companion_snapshot, read_companion_snapshot
from app.core.config import Settings
from app.models import ActionStatus, ApprovalMode, PermissionLevel, ProposedAction, ToolCategory
from app.services.audit import AuditLogger
from app.services.emails import EmailService
from app.services.memory import ConversationMemoryStore
from app.services.messages import MessagingService
from app.services.notes import WorkspaceNotesService
from app.services.reminders import ReminderService
from app.services.sync import CompanionSyncService
from app.services.workflows import WorkflowService


class CompanionSyncRouteTests(unittest.TestCase):
    def test_companion_snapshot_contains_mobile_friendly_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            request = self._build_request(temp_dir)
            payload = read_companion_snapshot(request, note_limit=4, reminder_limit=4, workflow_limit=4, task_limit=4)

            self.assertEqual(payload["sync_mode"], "local_polling")
            self.assertEqual(payload["assistant"]["name"], "Zivra")
            self.assertEqual(payload["summary"]["pending_actions"], 1)
            self.assertEqual(len(payload["approvals"]), 1)
            self.assertEqual(len(payload["notes"]), 1)
            self.assertEqual(len(payload["reminders"]), 1)
            self.assertEqual(len(payload["workflows"]), 1)
            self.assertEqual(len(payload["workflow_tasks"]), 1)
            self.assertEqual(payload["ui"]["mobile_path"], "/mobile")

    def test_export_snapshot_can_include_note_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            request = self._build_request(temp_dir)
            payload = export_companion_snapshot(request, include_note_content=True, note_limit=4)

            self.assertTrue(payload["export"]["include_note_content"])
            self.assertIn("content", payload["notes"][0])
            self.assertEqual(payload["notes"][0]["title"], "Launch checklist")

    def test_access_info_returns_mobile_and_control_room_urls(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            request = self._build_request(temp_dir)
            request.base_url = "http://127.0.0.1:8000/"
            request.headers = {"host": "127.0.0.1:8000"}

            payload = companion_access_info(request, session_id="shared session")

            self.assertTrue(payload["candidates"])
            self.assertTrue(any(candidate["mobile_url"].endswith("/mobile") for candidate in payload["candidates"]))
            self.assertTrue(any(candidate["control_room_url"].endswith("/ui/") for candidate in payload["candidates"]))
            self.assertTrue(
                any(
                    candidate["mobile_session_url"].endswith("/mobile?session_id=shared%20session")
                    for candidate in payload["candidates"]
                )
            )
            self.assertTrue(
                any(
                    candidate["control_room_session_url"].endswith("/ui/?session_id=shared%20session")
                    for candidate in payload["candidates"]
                )
            )
            self.assertIn("preferred_candidate", payload)
            self.assertTrue(payload["preferred_candidate"])

    def test_access_info_prefers_lan_candidate_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            request = self._build_request(temp_dir)
            request.base_url = "http://127.0.0.1:8000/"
            request.headers = {"host": "127.0.0.1:8000"}

            from unittest.mock import patch

            with patch("app.api.routes.sync._lan_ipv4_candidates", return_value=["192.168.1.25"]):
                payload = companion_access_info(request, session_id="sync-session")

            self.assertEqual(payload["preferred_candidate"]["host"], "192.168.1.25")
            preferred_candidates = [candidate for candidate in payload["candidates"] if candidate["preferred"]]
            self.assertEqual(len(preferred_candidates), 1)
            self.assertEqual(preferred_candidates[0]["host"], "192.168.1.25")

    def test_companion_snapshot_preserves_grouped_pending_actions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            grouped_actions = [
                ProposedAction(
                    action_id="group-1-step-1",
                    session_id="sync-session",
                    tool_name="open_application",
                    category=ToolCategory.PRODUCTIVITY,
                    permission_level=PermissionLevel.LOW_RISK,
                    approval_mode=ApprovalMode.USER_CONFIRMATION,
                    summary="Open calculator.",
                    group_id="group-1",
                    group_summary="Open calculator and then open example.com.",
                    sequence_index=0,
                ),
                ProposedAction(
                    action_id="group-1-step-2",
                    session_id="sync-session",
                    tool_name="open_website",
                    category=ToolCategory.WEB,
                    permission_level=PermissionLevel.LOW_RISK,
                    approval_mode=ApprovalMode.USER_CONFIRMATION,
                    summary="Open example.com.",
                    group_id="group-1",
                    group_summary="Open calculator and then open example.com.",
                    sequence_index=1,
                    depends_on_action_id="group-1-step-1",
                    status=ActionStatus.QUEUED,
                ),
            ]
            request = self._build_request(temp_dir, pending_actions=grouped_actions)

            payload = read_companion_snapshot(request, approval_limit=10)

            self.assertEqual(len(payload["approvals"]), 2)
            self.assertEqual(payload["approvals"][0]["group_id"], "group-1")
            self.assertEqual(payload["approvals"][1]["depends_on_action_id"], "group-1-step-1")
            self.assertEqual(payload["approvals"][1]["status"], "queued")

    def _build_request(self, temp_dir: str, pending_actions: list[ProposedAction] | None = None):
        settings = Settings(repo_root=Path(temp_dir))
        settings.ensure_runtime_dirs()

        audit_logger = AuditLogger(settings.audit_log_path)
        memory_store = ConversationMemoryStore(settings.memory_db_path, enabled=True)
        notes_service = WorkspaceNotesService(settings.notes_dir)
        reminders_service = ReminderService(settings.reminders_db_path)
        workflow_service = WorkflowService(settings.workflows_db_path)
        email_service = EmailService(settings.emails_db_path, settings=settings, transport=lambda payload: None)
        messaging_service = MessagingService(settings.messages_db_path, opener=lambda url: {"success": True, "url": url})

        (settings.notes_dir / "launch.md").write_text("# Launch checklist\nShip the mobile companion.\n", encoding="utf-8")
        reminders_service.create_reminder(title="Review mobile companion", due_at="2026-03-23T09:00:00+05:00")
        workflow = workflow_service.create_workflow(
            name="Morning workflow",
            prompt="Show my system status",
            schedule_type="manual",
            active=True,
        )
        workflow_service.queue_workflow_now(int(workflow["id"]))
        memory_store.save_turn(session_id="sync-session", role="assistant", content="Recent summary")

        proposed_actions = pending_actions or [
            ProposedAction(
                action_id="pending-1",
                session_id="sync-session",
                tool_name="open_application",
                category=ToolCategory.PRODUCTIVITY,
                permission_level=PermissionLevel.LOW_RISK,
                approval_mode=ApprovalMode.USER_CONFIRMATION,
                summary="Open calculator.",
                arguments={"application": "calculator"},
            )
        ]

        orchestrator = SimpleNamespace(
            planner_info={"mode": "rule", "label": "Rule planner"},
            pending_count=len(proposed_actions),
            list_pending_actions=lambda: [proposed.to_dict() for proposed in proposed_actions],
        )

        sync_service = CompanionSyncService(
            settings=settings,
            orchestrator=orchestrator,
            audit_logger=audit_logger,
            reminders_service=reminders_service,
            workflow_service=workflow_service,
            notes_service=notes_service,
            email_service=email_service,
            messaging_service=messaging_service,
            memory_store=memory_store,
        )

        state = SimpleNamespace(sync_service=sync_service)
        return SimpleNamespace(
            app=SimpleNamespace(state=state),
            base_url="http://127.0.0.1:8000/",
            headers={"host": "127.0.0.1:8000"},
        )


if __name__ == "__main__":
    unittest.main()

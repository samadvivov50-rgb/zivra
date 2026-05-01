from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

from app.api.routes.workflows import (
    CreateWorkflowRequest,
    ToggleWorkflowRequest,
    cancel_workflow_task,
    create_workflow,
    list_workflow_tasks,
    list_workflows,
    queue_workflow_now,
    retry_workflow_task,
    run_workflow_task,
    run_workflow_supervisor,
    toggle_workflow,
)
from app.core.config import Settings
from app.services.audit import AuditLogger
from app.services.workflows import WorkflowService


class WorkflowServiceTests(unittest.TestCase):
    def test_dispatch_due_creates_queued_task_for_due_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = WorkflowService(Path(temp_dir) / "workflows.sqlite3")
            workflow = service.create_workflow(
                name="Hourly review",
                prompt="Review the queue.",
                schedule_type="hourly",
                interval_hours=1,
                active=True,
            )

            due_reference = datetime.fromisoformat(str(workflow["next_run_at"])) + timedelta(minutes=1)
            created = service.dispatch_due(reference=due_reference)

            self.assertEqual(len(created), 1)
            self.assertEqual(created[0]["workflow_name"], "Hourly review")
            self.assertEqual(service.summary()["queued_tasks"], 1)

    def test_run_task_marks_approval_pending_when_response_leaves_pending_actions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = WorkflowService(Path(temp_dir) / "workflows.sqlite3")
            workflow = service.create_workflow(
                name="Approval check",
                prompt="Open calculator",
                schedule_type="manual",
                active=True,
            )
            task = service.queue_workflow_now(int(workflow["id"]))
            self.assertIsNotNone(task)

            result = service.run_task(
                int(task["id"]),
                runner=lambda prompt, session_id: {
                    "assistant_text": "I staged an app launch for approval.",
                    "actions": [{"status": "proposed"}],
                    "outcomes": [],
                    "warnings": [],
                },
            )

            self.assertIsNotNone(result)
            self.assertEqual(result["task"]["status"], "approval_pending")
            self.assertEqual(result["task"]["pending_action_count"], 1)

    def test_cancel_and_retry_task_support_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = WorkflowService(Path(temp_dir) / "workflows.sqlite3")
            workflow = service.create_workflow(
                name="Recovery loop",
                prompt="Open calculator",
                schedule_type="manual",
                active=True,
            )
            task = service.queue_workflow_now(int(workflow["id"]))
            self.assertIsNotNone(task)

            canceled = service.cancel_task(int(task["id"]))
            self.assertIsNotNone(canceled)
            self.assertEqual(canceled["status"], "canceled")

            retried = service.retry_task(int(task["id"]))
            self.assertIsNotNone(retried)
            self.assertEqual(retried["status"], "queued")
            self.assertEqual(retried["source"], "retry")

    def test_supervisor_cycle_runs_with_limits_and_pauses_on_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = WorkflowService(Path(temp_dir) / "workflows.sqlite3")
            workflow = service.create_workflow(
                name="Guarded run",
                prompt="Open calculator",
                schedule_type="manual",
                active=True,
            )
            task = service.queue_workflow_now(int(workflow["id"]))
            self.assertIsNotNone(task)

            cycle = service.supervisor_cycle(
                runner=lambda prompt, session_id: {
                    "assistant_text": "That workflow failed.",
                    "actions": [],
                    "outcomes": [{"status": "failed"}],
                    "warnings": [],
                },
                enabled=True,
                max_tasks=1,
                max_pending_approvals=1,
                pause_workflows_on_failure=True,
            )

            self.assertEqual(cycle["run_count"], 1)
            self.assertEqual(cycle["stopped_reason"], "workflow_failed")
            self.assertEqual(cycle["executed_tasks"][0]["status"], "failed")
            self.assertEqual(len(cycle["paused_workflows"]), 1)
            self.assertFalse(service.get_workflow(int(workflow["id"]))["active"])


class WorkflowRouteTests(unittest.TestCase):
    def test_routes_create_toggle_queue_run_cancel_retry_and_supervise(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            request = self._build_request(temp_dir)

            created = create_workflow(
                CreateWorkflowRequest(
                    name="Morning brief",
                    prompt="Show my system status",
                    schedule_type="daily",
                    run_hour=9,
                    run_minute=0,
                ),
                request,
            )
            workflow_id = int(created["workflow"]["id"])
            self.assertEqual(created["workflow"]["schedule_type"], "daily")

            paused = toggle_workflow(workflow_id, ToggleWorkflowRequest(active=False), request)
            self.assertFalse(paused["workflow"]["active"])

            queued = queue_workflow_now(workflow_id, request)
            task_id = int(queued["task"]["id"])
            self.assertEqual(queued["task"]["status"], "queued")

            executed = run_workflow_task(task_id, request)
            self.assertEqual(executed["task"]["status"], "completed")
            self.assertEqual(executed["response"]["assistant_text"], "Workflow task completed.")

            manual = create_workflow(
                CreateWorkflowRequest(
                    name="Recovery queue",
                    prompt="Show my system status",
                    schedule_type="manual",
                ),
                request,
            )
            recovery_task = queue_workflow_now(int(manual["workflow"]["id"]), request)
            canceled = cancel_workflow_task(int(recovery_task["task"]["id"]), request)
            self.assertEqual(canceled["task"]["status"], "canceled")
            retried = retry_workflow_task(int(recovery_task["task"]["id"]), request)
            self.assertEqual(retried["task"]["status"], "queued")
            self.assertEqual(retried["task"]["source"], "retry")

            request.app.state.settings.workflow_supervisor_enabled = True
            request.app.state.settings.workflow_supervisor_max_tasks_per_cycle = 1
            request.app.state.settings.workflow_supervisor_max_pending_approvals = 1
            supervised = run_workflow_supervisor(request)
            self.assertIn("cycle", supervised)
            self.assertGreaterEqual(supervised["cycle"]["run_count"], 0)

            workflows_payload = list_workflows(request, limit=10)
            tasks_payload = list_workflow_tasks(request, limit=10)
            self.assertEqual(len(workflows_payload["workflows"]), 2)
            self.assertGreaterEqual(len(tasks_payload["tasks"]), 2)

    def _build_request(self, temp_dir: str):
        workflow_service = WorkflowService(Path(temp_dir) / "workflows.sqlite3")
        audit_logger = AuditLogger(Path(temp_dir) / "audit" / "actions.jsonl")
        settings = Settings(repo_root=Path(temp_dir))

        class FakeResponse:
            def __init__(self, payload):
                self._payload = payload

            def to_dict(self):
                return self._payload

        class FakeOrchestrator:
            def handle_message(self, message: str, *, session_id: str = "default"):
                return FakeResponse(
                    {
                        "assistant_text": "Workflow task completed.",
                        "intent": "system_status",
                        "task_type": "monitoring",
                        "actions": [],
                        "outcomes": [{"status": "executed"}],
                        "warnings": [],
                        "memory_enabled": True,
                    }
                )

        state = SimpleNamespace(
            workflow_service=workflow_service,
            audit_logger=audit_logger,
            orchestrator=FakeOrchestrator(),
            settings=settings,
        )
        return SimpleNamespace(app=SimpleNamespace(state=state))


if __name__ == "__main__":
    unittest.main()

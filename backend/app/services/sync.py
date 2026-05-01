from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class CompanionSyncService:
    def __init__(
        self,
        *,
        settings: Any,
        orchestrator: Any,
        audit_logger: Any,
        reminders_service: Any,
        workflow_service: Any,
        notes_service: Any,
        email_service: Any,
        messaging_service: Any,
        memory_store: Any,
    ) -> None:
        self.settings = settings
        self.orchestrator = orchestrator
        self.audit_logger = audit_logger
        self.reminders_service = reminders_service
        self.workflow_service = workflow_service
        self.notes_service = notes_service
        self.email_service = email_service
        self.messaging_service = messaging_service
        self.memory_store = memory_store

    def build_companion_snapshot(
        self,
        *,
        note_limit: int = 6,
        reminder_limit: int = 8,
        workflow_limit: int = 6,
        task_limit: int = 8,
        activity_limit: int = 6,
        session_limit: int = 4,
        approval_limit: int = 10,
    ) -> dict[str, Any]:
        self.workflow_service.dispatch_due()

        return {
            "generated_at": self._now(),
            "sync_mode": "local_polling",
            "assistant": {
                "name": self.settings.assistant_name,
                "safe_mode": self.settings.safe_mode,
                "memory_enabled": self.settings.memory_enabled,
                "planner_mode": str((self.orchestrator.planner_info or {}).get("mode", "rule")),
                "planner_label": str((self.orchestrator.planner_info or {}).get("label", "Rule planner")),
            },
            "supervisor": {
                "enabled": self.settings.workflow_supervisor_enabled,
                "max_tasks_per_cycle": self.settings.workflow_supervisor_max_tasks_per_cycle,
                "max_pending_approvals": self.settings.workflow_supervisor_max_pending_approvals,
                "pause_on_failure": self.settings.workflow_supervisor_pause_on_failure,
            },
            "summary": {
                "pending_actions": self.orchestrator.pending_count,
                "pending_reminders": self.reminders_service.count_pending(),
                "reminders": self.reminders_service.summary(),
                "workflows": self.workflow_service.summary(),
                "emails": self.email_service.summary(),
                "messages": self.messaging_service.summary(),
                "stored_sessions": len(self.memory_store.list_sessions(limit=session_limit)),
            },
            "transport": {
                "email_delivery": self.email_service.delivery_status(),
                "message_delivery": self.messaging_service.delivery_status(),
            },
            "approvals": self.orchestrator.list_pending_actions()[:approval_limit],
            "reminders": self.reminders_service.list_upcoming(
                limit=min(max(reminder_limit, 1), 20),
                include_completed=False,
                include_archived=False,
            ),
            "workflows": self.workflow_service.list_workflows(limit=min(max(workflow_limit, 1), 20)),
            "workflow_tasks": self.workflow_service.list_tasks(limit=min(max(task_limit, 1), 20)),
            "notes": self.notes_service.list_recent(limit=min(max(note_limit, 1), 20)),
            "sessions": self.memory_store.list_sessions(limit=min(max(session_limit, 1), 12)),
            "recent_flows": self.audit_logger.query_groups(limit=min(max(activity_limit, 1), 20))["groups"],
            "ui": {
                "control_room_path": "/ui/",
                "mobile_path": "/mobile",
                "manifest_path": "/ui/manifest.webmanifest",
            },
        }

    def build_export_snapshot(
        self,
        *,
        include_note_content: bool = False,
        note_limit: int = 10,
        reminder_limit: int = 20,
        workflow_limit: int = 20,
        task_limit: int = 20,
        activity_limit: int = 20,
        session_limit: int = 8,
    ) -> dict[str, Any]:
        snapshot = self.build_companion_snapshot(
            note_limit=note_limit,
            reminder_limit=reminder_limit,
            workflow_limit=workflow_limit,
            task_limit=task_limit,
            activity_limit=activity_limit,
            session_limit=session_limit,
            approval_limit=25,
        )
        if include_note_content:
            exported_notes: list[dict[str, Any]] = []
            for note in snapshot["notes"]:
                expanded = self.notes_service.read_note(str(note["name"]))
                if expanded is None:
                    continue
                exported_notes.append(expanded)
            snapshot["notes"] = exported_notes

        snapshot["export"] = {
            "include_note_content": include_note_content,
            "format": "json",
            "warning": (
                "This snapshot is a local export intended for trusted manual sync or backup flows."
            ),
        }
        return snapshot

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.core.config import Settings
from app.services.audit import AuditLogger
from app.services.documents import WorkspaceDocumentsService
from app.services.memory import ConversationMemoryStore
from app.services.notes import WorkspaceNotesService
from app.services.orchestrator import AssistantOrchestrator
from app.services.planning import PlanningResult, PlanningRoute
from app.services.policy import PolicyEngine
from app.services.reminders import ReminderService
from app.tools.registry import build_default_registry


class OrchestratorTests(unittest.TestCase):
    def test_system_requests_auto_execute(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(repo_root=Path(temp_dir))
            settings.ensure_runtime_dirs()
            orchestrator = AssistantOrchestrator(
                registry=build_default_registry(
                    settings,
                    notes_service=WorkspaceNotesService(settings.notes_dir),
                    documents_service=WorkspaceDocumentsService(settings.approved_document_roots),
                    reminder_service=ReminderService(settings.reminders_db_path),
                    website_opener=lambda url: True,
                    app_launcher=lambda command: None,
                ),
                policy=PolicyEngine(safe_mode=settings.safe_mode, approved_roots=settings.approved_roots),
                audit=AuditLogger(settings.audit_log_path),
                memory=ConversationMemoryStore(settings.memory_db_path, enabled=settings.memory_enabled),
            )

            response = orchestrator.handle_message("Show me my system status", session_id="test-session")

            self.assertEqual(response.intent, "system_status")
            self.assertEqual(len(response.outcomes), 1)
            self.assertEqual(response.outcomes[0].status.value, "executed")

    def test_notes_require_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(repo_root=Path(temp_dir))
            settings.ensure_runtime_dirs()
            orchestrator = AssistantOrchestrator(
                registry=build_default_registry(
                    settings,
                    notes_service=WorkspaceNotesService(settings.notes_dir),
                    documents_service=WorkspaceDocumentsService(settings.approved_document_roots),
                    reminder_service=ReminderService(settings.reminders_db_path),
                    website_opener=lambda url: True,
                    app_launcher=lambda command: None,
                ),
                policy=PolicyEngine(safe_mode=settings.safe_mode, approved_roots=settings.approved_roots),
                audit=AuditLogger(settings.audit_log_path),
                memory=ConversationMemoryStore(settings.memory_db_path, enabled=settings.memory_enabled),
            )

            response = orchestrator.handle_message("Write down note buy a better microphone", session_id="test-session")

            self.assertEqual(response.intent, "capture_note")
            self.assertEqual(len(response.actions), 1)
            self.assertEqual(response.actions[0].status.value, "proposed")
            self.assertEqual(len(response.outcomes), 0)

    def test_confirming_pending_action_executes_it(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(repo_root=Path(temp_dir))
            settings.ensure_runtime_dirs()
            orchestrator = AssistantOrchestrator(
                registry=build_default_registry(
                    settings,
                    notes_service=WorkspaceNotesService(settings.notes_dir),
                    documents_service=WorkspaceDocumentsService(settings.approved_document_roots),
                    reminder_service=ReminderService(settings.reminders_db_path),
                    website_opener=lambda url: True,
                    app_launcher=lambda command: None,
                ),
                policy=PolicyEngine(safe_mode=settings.safe_mode, approved_roots=settings.approved_roots),
                audit=AuditLogger(settings.audit_log_path),
                memory=ConversationMemoryStore(settings.memory_db_path, enabled=settings.memory_enabled),
            )

            first_response = orchestrator.handle_message("Open example.com", session_id="test-session")
            action_id = first_response.actions[0].action_id

            confirmation = orchestrator.confirm_action(action_id)

            self.assertEqual(confirmation.outcomes[0].status.value, "executed")
            self.assertEqual(orchestrator.pending_count, 0)

    def test_rejecting_pending_action_clears_queue(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(repo_root=Path(temp_dir))
            settings.ensure_runtime_dirs()
            orchestrator = AssistantOrchestrator(
                registry=build_default_registry(
                    settings,
                    notes_service=WorkspaceNotesService(settings.notes_dir),
                    documents_service=WorkspaceDocumentsService(settings.approved_document_roots),
                    reminder_service=ReminderService(settings.reminders_db_path),
                    website_opener=lambda url: True,
                    app_launcher=lambda command: None,
                ),
                policy=PolicyEngine(safe_mode=settings.safe_mode, approved_roots=settings.approved_roots),
                audit=AuditLogger(settings.audit_log_path),
                memory=ConversationMemoryStore(settings.memory_db_path, enabled=settings.memory_enabled),
            )

            first_response = orchestrator.handle_message("Write down note buy tea", session_id="test-session")
            action_id = first_response.actions[0].action_id

            rejection = orchestrator.reject_action(action_id)

            self.assertEqual(rejection.intent, "action_rejection")
            self.assertEqual(rejection.actions[0].status.value, "rejected")
            self.assertEqual(orchestrator.pending_count, 0)

    def test_note_updates_require_confirmation_and_apply_after_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(repo_root=Path(temp_dir))
            settings.ensure_runtime_dirs()
            note_path = settings.notes_dir / "launch-plan.md"
            note_path.write_text("# Launch plan\n\nInitial checklist.\n", encoding="utf-8")
            orchestrator = AssistantOrchestrator(
                registry=build_default_registry(
                    settings,
                    notes_service=WorkspaceNotesService(settings.notes_dir),
                    documents_service=WorkspaceDocumentsService(settings.approved_document_roots),
                    reminder_service=ReminderService(settings.reminders_db_path),
                    website_opener=lambda url: True,
                    app_launcher=lambda command: None,
                ),
                policy=PolicyEngine(safe_mode=settings.safe_mode, approved_roots=settings.approved_roots),
                audit=AuditLogger(settings.audit_log_path),
                memory=ConversationMemoryStore(settings.memory_db_path, enabled=settings.memory_enabled),
            )

            response = orchestrator.handle_message(
                "Append to note launch plan with add rehearsal timing",
                session_id="test-session",
            )

            self.assertEqual(response.intent, "update_note")
            self.assertEqual(response.actions[0].status.value, "proposed")
            self.assertNotIn("add rehearsal timing", note_path.read_text(encoding="utf-8"))

            confirmation = orchestrator.confirm_action(response.actions[0].action_id)

            self.assertEqual(confirmation.outcomes[0].status.value, "executed")
            self.assertIn("add rehearsal timing", note_path.read_text(encoding="utf-8").lower())

    def test_planner_warnings_flow_through_the_response(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(repo_root=Path(temp_dir))
            settings.ensure_runtime_dirs()
            (settings.docs_dir / "architecture.md").write_text("# Architecture\n\nPlanner notes.\n", encoding="utf-8")

            class FakePlanner:
                mode = "llm"
                label = "LLM planner"

                def plan(self, user_text, *, tools, history=None):
                    return PlanningResult(
                        routes=[
                            PlanningRoute(
                                intent="read_document",
                                task_type="files",
                                tool_name="read_document",
                                arguments={"query": "architecture"},
                                summary="Read the document 'architecture'.",
                            )
                        ],
                        warnings=["LLM planner fallback: simulated test path"],
                    )

                def to_dict(self):
                    return {"mode": self.mode, "label": self.label}

            orchestrator = AssistantOrchestrator(
                registry=build_default_registry(
                    settings,
                    notes_service=WorkspaceNotesService(settings.notes_dir),
                    documents_service=WorkspaceDocumentsService(settings.approved_document_roots),
                    reminder_service=ReminderService(settings.reminders_db_path),
                    website_opener=lambda url: True,
                    app_launcher=lambda command: None,
                ),
                policy=PolicyEngine(safe_mode=settings.safe_mode, approved_roots=settings.approved_roots),
                audit=AuditLogger(settings.audit_log_path),
                memory=ConversationMemoryStore(settings.memory_db_path, enabled=settings.memory_enabled),
                planner=FakePlanner(),
            )

            response = orchestrator.handle_message("Open the architecture doc", session_id="test-session")

            self.assertEqual(response.intent, "read_document")
            self.assertEqual(response.outcomes[0].status.value, "executed")
            self.assertTrue(any("LLM planner fallback" in warning for warning in response.warnings))

    def test_compound_request_executes_safe_reads_and_queues_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(repo_root=Path(temp_dir), planner_mode="rule")
            settings.ensure_runtime_dirs()
            orchestrator = AssistantOrchestrator(
                registry=build_default_registry(
                    settings,
                    notes_service=WorkspaceNotesService(settings.notes_dir),
                    documents_service=WorkspaceDocumentsService(settings.approved_document_roots),
                    reminder_service=ReminderService(settings.reminders_db_path),
                    website_opener=lambda url: True,
                    app_launcher=lambda command: None,
                ),
                policy=PolicyEngine(safe_mode=settings.safe_mode, approved_roots=settings.approved_roots),
                audit=AuditLogger(settings.audit_log_path),
                memory=ConversationMemoryStore(settings.memory_db_path, enabled=settings.memory_enabled),
            )

            response = orchestrator.handle_message(
                "Show me my system status and open calculator",
                session_id="test-session",
            )

            self.assertEqual(response.intent, "multi_action")
            self.assertEqual(response.task_type, "compound")
            self.assertEqual(len(response.actions), 2)
            self.assertEqual(len(response.outcomes), 1)
            self.assertEqual(response.outcomes[0].status.value, "executed")
            self.assertEqual(orchestrator.pending_count, 1)
            self.assertEqual(
                [action.status.value for action in response.actions],
                ["executed", "proposed"],
            )

    def test_group_confirmation_executes_all_pending_actions_in_compound_request(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(repo_root=Path(temp_dir), planner_mode="rule")
            settings.ensure_runtime_dirs()
            opened_urls: list[str] = []
            launched_apps: list[tuple[str, ...] | str] = []
            orchestrator = AssistantOrchestrator(
                registry=build_default_registry(
                    settings,
                    notes_service=WorkspaceNotesService(settings.notes_dir),
                    documents_service=WorkspaceDocumentsService(settings.approved_document_roots),
                    reminder_service=ReminderService(settings.reminders_db_path),
                    website_opener=lambda url: opened_urls.append(url) or True,
                    app_launcher=lambda command: launched_apps.append(command) or None,
                ),
                policy=PolicyEngine(safe_mode=settings.safe_mode, approved_roots=settings.approved_roots),
                audit=AuditLogger(settings.audit_log_path),
                memory=ConversationMemoryStore(settings.memory_db_path, enabled=settings.memory_enabled),
            )

            response = orchestrator.handle_message(
                "Open calculator and open example.com",
                session_id="test-session",
            )

            self.assertEqual(
                [action.status.value for action in response.actions],
                ["proposed", "queued"],
            )
            group_id = response.actions[0].group_id
            self.assertIsNotNone(group_id)
            self.assertEqual(orchestrator.pending_count, 2)

            confirmation = orchestrator.confirm_action_group(group_id or "")

            self.assertEqual(len(confirmation.outcomes), 2)
            self.assertEqual(orchestrator.pending_count, 0)
            self.assertEqual(opened_urls, ["https://example.com"])
            self.assertEqual(len(launched_apps), 1)

    def test_confirming_first_step_activates_next_queued_step(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(repo_root=Path(temp_dir), planner_mode="rule")
            settings.ensure_runtime_dirs()
            orchestrator = AssistantOrchestrator(
                registry=build_default_registry(
                    settings,
                    notes_service=WorkspaceNotesService(settings.notes_dir),
                    documents_service=WorkspaceDocumentsService(settings.approved_document_roots),
                    reminder_service=ReminderService(settings.reminders_db_path),
                    website_opener=lambda url: True,
                    app_launcher=lambda command: None,
                ),
                policy=PolicyEngine(safe_mode=settings.safe_mode, approved_roots=settings.approved_roots),
                audit=AuditLogger(settings.audit_log_path),
                memory=ConversationMemoryStore(settings.memory_db_path, enabled=settings.memory_enabled),
            )

            response = orchestrator.handle_message(
                "Open calculator and open example.com",
                session_id="test-session",
            )

            first_action_id = response.actions[0].action_id
            second_action_id = response.actions[1].action_id

            confirmation = orchestrator.confirm_action(first_action_id)

            self.assertEqual(confirmation.outcomes[0].status.value, "executed")
            self.assertEqual(orchestrator.pending_count, 1)
            pending_actions = orchestrator.list_pending_actions()
            self.assertEqual(len(pending_actions), 1)
            self.assertEqual(pending_actions[0]["action_id"], second_action_id)
            self.assertEqual(pending_actions[0]["status"], "proposed")

    def test_confirming_queued_step_is_blocked_until_dependency_resolves(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(repo_root=Path(temp_dir), planner_mode="rule")
            settings.ensure_runtime_dirs()
            orchestrator = AssistantOrchestrator(
                registry=build_default_registry(
                    settings,
                    notes_service=WorkspaceNotesService(settings.notes_dir),
                    documents_service=WorkspaceDocumentsService(settings.approved_document_roots),
                    reminder_service=ReminderService(settings.reminders_db_path),
                    website_opener=lambda url: True,
                    app_launcher=lambda command: None,
                ),
                policy=PolicyEngine(safe_mode=settings.safe_mode, approved_roots=settings.approved_roots),
                audit=AuditLogger(settings.audit_log_path),
                memory=ConversationMemoryStore(settings.memory_db_path, enabled=settings.memory_enabled),
            )

            response = orchestrator.handle_message(
                "Open calculator and open example.com",
                session_id="test-session",
            )

            queued_action_id = response.actions[1].action_id
            confirmation = orchestrator.confirm_action(queued_action_id)

            self.assertEqual(confirmation.intent, "action_confirmation")
            self.assertIn("waiting on an earlier approval step", confirmation.assistant_text.lower())
            self.assertEqual(orchestrator.pending_count, 2)

    def test_group_rejection_clears_all_pending_actions_in_compound_request(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(repo_root=Path(temp_dir), planner_mode="rule")
            settings.ensure_runtime_dirs()
            orchestrator = AssistantOrchestrator(
                registry=build_default_registry(
                    settings,
                    notes_service=WorkspaceNotesService(settings.notes_dir),
                    documents_service=WorkspaceDocumentsService(settings.approved_document_roots),
                    reminder_service=ReminderService(settings.reminders_db_path),
                    website_opener=lambda url: True,
                    app_launcher=lambda command: None,
                ),
                policy=PolicyEngine(safe_mode=settings.safe_mode, approved_roots=settings.approved_roots),
                audit=AuditLogger(settings.audit_log_path),
                memory=ConversationMemoryStore(settings.memory_db_path, enabled=settings.memory_enabled),
            )

            response = orchestrator.handle_message(
                "Open calculator and write down note buy tea",
                session_id="test-session",
            )

            group_id = response.actions[0].group_id
            self.assertIsNotNone(group_id)
            self.assertEqual(orchestrator.pending_count, 2)

            rejection = orchestrator.reject_action_group(group_id or "")

            self.assertEqual(rejection.intent, "action_rejection")
            self.assertEqual(orchestrator.pending_count, 0)
            self.assertEqual(
                [action.status.value for action in rejection.actions],
                ["rejected", "rejected"],
            )

    def test_rejecting_first_step_rejects_queued_dependents(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(repo_root=Path(temp_dir), planner_mode="rule")
            settings.ensure_runtime_dirs()
            orchestrator = AssistantOrchestrator(
                registry=build_default_registry(
                    settings,
                    notes_service=WorkspaceNotesService(settings.notes_dir),
                    documents_service=WorkspaceDocumentsService(settings.approved_document_roots),
                    reminder_service=ReminderService(settings.reminders_db_path),
                    website_opener=lambda url: True,
                    app_launcher=lambda command: None,
                ),
                policy=PolicyEngine(safe_mode=settings.safe_mode, approved_roots=settings.approved_roots),
                audit=AuditLogger(settings.audit_log_path),
                memory=ConversationMemoryStore(settings.memory_db_path, enabled=settings.memory_enabled),
            )

            response = orchestrator.handle_message(
                "Open calculator and open example.com",
                session_id="test-session",
            )

            first_action_id = response.actions[0].action_id
            rejection = orchestrator.reject_action(first_action_id)

            self.assertEqual(orchestrator.pending_count, 0)
            self.assertEqual(
                [action.status.value for action in rejection.actions],
                ["rejected", "rejected"],
            )

    def test_explicit_planner_dependencies_allow_independent_side_effects_to_stay_proposed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(repo_root=Path(temp_dir))
            settings.ensure_runtime_dirs()

            class FakePlanner:
                mode = "llm"
                label = "LLM planner"

                def plan(self, user_text, *, tools, history=None):
                    return PlanningResult(
                        routes=[
                            PlanningRoute(
                                intent="open_application",
                                task_type="desktop_control",
                                tool_name="open_application",
                                arguments={"application": "calculator"},
                                summary="Open the application 'calculator'.",
                            ),
                            PlanningRoute(
                                intent="open_resource",
                                task_type="browser",
                                tool_name="open_website",
                                arguments={"url": "example.com"},
                                summary="Open the website 'example.com'.",
                                depends_on_route_index=0,
                            ),
                            PlanningRoute(
                                intent="create_reminder",
                                task_type="productivity",
                                tool_name="create_reminder",
                                arguments={"title": "Ship follow-up", "details": "Track the launch"},
                                summary="Create a reminder titled 'Ship follow-up'.",
                            ),
                        ],
                        summary="Stage calculator, then website, while keeping the reminder independent.",
                        dependencies_explicit=True,
                    )

                def to_dict(self):
                    return {"mode": self.mode, "label": self.label}

            orchestrator = AssistantOrchestrator(
                registry=build_default_registry(
                    settings,
                    notes_service=WorkspaceNotesService(settings.notes_dir),
                    documents_service=WorkspaceDocumentsService(settings.approved_document_roots),
                    reminder_service=ReminderService(settings.reminders_db_path),
                    website_opener=lambda url: True,
                    app_launcher=lambda command: None,
                ),
                policy=PolicyEngine(safe_mode=settings.safe_mode, approved_roots=settings.approved_roots),
                audit=AuditLogger(settings.audit_log_path),
                memory=ConversationMemoryStore(settings.memory_db_path, enabled=settings.memory_enabled),
                planner=FakePlanner(),
            )

            response = orchestrator.handle_message("Compound dependency test", session_id="test-session")

            self.assertEqual(
                [action.status.value for action in response.actions],
                ["proposed", "queued", "proposed"],
            )
            self.assertEqual(orchestrator.pending_count, 3)
            self.assertEqual(response.actions[1].depends_on_action_id, response.actions[0].action_id)
            self.assertIsNone(response.actions[2].depends_on_action_id)

    def test_explicit_planner_dependency_fanout_queues_multiple_dependents(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(repo_root=Path(temp_dir))
            settings.ensure_runtime_dirs()

            class FakePlanner:
                mode = "llm"
                label = "LLM planner"

                def plan(self, user_text, *, tools, history=None):
                    return PlanningResult(
                        routes=[
                            PlanningRoute(
                                intent="open_application",
                                task_type="desktop_control",
                                tool_name="open_application",
                                arguments={"application": "calculator"},
                                summary="Open the application 'calculator'.",
                            ),
                            PlanningRoute(
                                intent="open_resource",
                                task_type="browser",
                                tool_name="open_website",
                                arguments={"url": "example.com"},
                                summary="Open the website 'example.com'.",
                                depends_on_route_index=0,
                            ),
                            PlanningRoute(
                                intent="create_reminder",
                                task_type="productivity",
                                tool_name="create_reminder",
                                arguments={"title": "Branch follow-up", "details": "Track the branch"},
                                summary="Create a reminder titled 'Branch follow-up'.",
                                depends_on_route_index=0,
                            ),
                        ],
                        summary="Branch fanout test.",
                        dependencies_explicit=True,
                    )

                def to_dict(self):
                    return {"mode": self.mode, "label": self.label}

            orchestrator = AssistantOrchestrator(
                registry=build_default_registry(
                    settings,
                    notes_service=WorkspaceNotesService(settings.notes_dir),
                    documents_service=WorkspaceDocumentsService(settings.approved_document_roots),
                    reminder_service=ReminderService(settings.reminders_db_path),
                    website_opener=lambda url: True,
                    app_launcher=lambda command: None,
                ),
                policy=PolicyEngine(safe_mode=settings.safe_mode, approved_roots=settings.approved_roots),
                audit=AuditLogger(settings.audit_log_path),
                memory=ConversationMemoryStore(settings.memory_db_path, enabled=settings.memory_enabled),
                planner=FakePlanner(),
            )

            response = orchestrator.handle_message("branch fanout", session_id="test-session")

            self.assertEqual(
                [action.status.value for action in response.actions],
                ["proposed", "queued", "queued"],
            )
            self.assertEqual(
                [bool(action.depends_on_action_id) for action in response.actions],
                [False, True, True],
            )

    def test_confirming_prerequisite_activates_all_fanout_dependents(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(repo_root=Path(temp_dir))
            settings.ensure_runtime_dirs()

            class FakePlanner:
                mode = "llm"
                label = "LLM planner"

                def plan(self, user_text, *, tools, history=None):
                    return PlanningResult(
                        routes=[
                            PlanningRoute(
                                intent="open_application",
                                task_type="desktop_control",
                                tool_name="open_application",
                                arguments={"application": "calculator"},
                                summary="Open the application 'calculator'.",
                            ),
                            PlanningRoute(
                                intent="open_resource",
                                task_type="browser",
                                tool_name="open_website",
                                arguments={"url": "example.com"},
                                summary="Open the website 'example.com'.",
                                depends_on_route_index=0,
                            ),
                            PlanningRoute(
                                intent="create_reminder",
                                task_type="productivity",
                                tool_name="create_reminder",
                                arguments={"title": "Branch follow-up", "details": "Track the branch"},
                                summary="Create a reminder titled 'Branch follow-up'.",
                                depends_on_route_index=0,
                            ),
                        ],
                        summary="Branch fanout activation test.",
                        dependencies_explicit=True,
                    )

                def to_dict(self):
                    return {"mode": self.mode, "label": self.label}

            orchestrator = AssistantOrchestrator(
                registry=build_default_registry(
                    settings,
                    notes_service=WorkspaceNotesService(settings.notes_dir),
                    documents_service=WorkspaceDocumentsService(settings.approved_document_roots),
                    reminder_service=ReminderService(settings.reminders_db_path),
                    website_opener=lambda url: True,
                    app_launcher=lambda command: None,
                ),
                policy=PolicyEngine(safe_mode=settings.safe_mode, approved_roots=settings.approved_roots),
                audit=AuditLogger(settings.audit_log_path),
                memory=ConversationMemoryStore(settings.memory_db_path, enabled=settings.memory_enabled),
                planner=FakePlanner(),
            )

            response = orchestrator.handle_message("branch fanout", session_id="test-session")
            confirmation = orchestrator.confirm_action(response.actions[0].action_id)

            self.assertEqual(confirmation.outcomes[0].status.value, "executed")
            pending_actions = orchestrator.list_pending_actions()
            self.assertEqual(len(pending_actions), 2)
            self.assertEqual([action["status"] for action in pending_actions], ["proposed", "proposed"])

    def test_group_confirmation_respects_explicit_dependency_failures(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(repo_root=Path(temp_dir))
            settings.ensure_runtime_dirs()
            reminder_service = ReminderService(settings.reminders_db_path)

            class FakePlanner:
                mode = "llm"
                label = "LLM planner"

                def plan(self, user_text, *, tools, history=None):
                    return PlanningResult(
                        routes=[
                            PlanningRoute(
                                intent="open_application",
                                task_type="desktop_control",
                                tool_name="open_application",
                                arguments={"application": "calculator"},
                                summary="Open the application 'calculator'.",
                            ),
                            PlanningRoute(
                                intent="open_resource",
                                task_type="browser",
                                tool_name="open_website",
                                arguments={"url": "example.com"},
                                summary="Open the website 'example.com'.",
                                depends_on_route_index=0,
                            ),
                            PlanningRoute(
                                intent="create_reminder",
                                task_type="productivity",
                                tool_name="create_reminder",
                                arguments={"title": "Ship follow-up", "details": "Track the launch"},
                                summary="Create a reminder titled 'Ship follow-up'.",
                            ),
                        ],
                        summary="Dependency failure batch test.",
                        dependencies_explicit=True,
                    )

                def to_dict(self):
                    return {"mode": self.mode, "label": self.label}

            def failing_launcher(command):
                raise RuntimeError("launch failed")

            orchestrator = AssistantOrchestrator(
                registry=build_default_registry(
                    settings,
                    notes_service=WorkspaceNotesService(settings.notes_dir),
                    documents_service=WorkspaceDocumentsService(settings.approved_document_roots),
                    reminder_service=reminder_service,
                    website_opener=lambda url: True,
                    app_launcher=failing_launcher,
                ),
                policy=PolicyEngine(safe_mode=settings.safe_mode, approved_roots=settings.approved_roots),
                audit=AuditLogger(settings.audit_log_path),
                memory=ConversationMemoryStore(settings.memory_db_path, enabled=settings.memory_enabled),
                planner=FakePlanner(),
            )

            response = orchestrator.handle_message("dependency batch fail", session_id="test-session")
            group_id = response.actions[0].group_id
            self.assertIsNotNone(group_id)
            self.assertEqual(
                [action.status.value for action in response.actions],
                ["proposed", "queued", "proposed"],
            )

            confirmation = orchestrator.confirm_action_group(group_id or "")

            self.assertEqual(
                [outcome.status.value for outcome in confirmation.outcomes],
                ["failed", "blocked", "executed"],
            )
            self.assertEqual(orchestrator.pending_count, 0)
            self.assertEqual(reminder_service.count_pending(), 1)

    def test_audit_recent_includes_dependency_trace_for_executed_dependent_step(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(repo_root=Path(temp_dir))
            settings.ensure_runtime_dirs()
            audit_logger = AuditLogger(settings.audit_log_path)

            class FakePlanner:
                mode = "llm"
                label = "LLM planner"

                def plan(self, user_text, *, tools, history=None):
                    return PlanningResult(
                        routes=[
                            PlanningRoute(
                                intent="open_application",
                                task_type="desktop_control",
                                tool_name="open_application",
                                arguments={"application": "calculator"},
                                summary="Open the application 'calculator'.",
                            ),
                            PlanningRoute(
                                intent="open_resource",
                                task_type="browser",
                                tool_name="open_website",
                                arguments={"url": "example.com"},
                                summary="Open the website 'example.com'.",
                                depends_on_route_index=0,
                            ),
                        ],
                        summary="Executed dependency trace test.",
                        dependencies_explicit=True,
                    )

                def to_dict(self):
                    return {"mode": self.mode, "label": self.label}

            orchestrator = AssistantOrchestrator(
                registry=build_default_registry(
                    settings,
                    notes_service=WorkspaceNotesService(settings.notes_dir),
                    documents_service=WorkspaceDocumentsService(settings.approved_document_roots),
                    reminder_service=ReminderService(settings.reminders_db_path),
                    website_opener=lambda url: True,
                    app_launcher=lambda command: None,
                ),
                policy=PolicyEngine(safe_mode=settings.safe_mode, approved_roots=settings.approved_roots),
                audit=audit_logger,
                memory=ConversationMemoryStore(settings.memory_db_path, enabled=settings.memory_enabled),
                planner=FakePlanner(),
            )

            response = orchestrator.handle_message("executed trace", session_id="test-session")
            orchestrator.confirm_action_group(response.actions[0].group_id or "")

            recent_events = audit_logger.recent(limit=10)
            dependent_event = next(
                event
                for event in recent_events
                if event["status"] == "executed" and event["action"]["summary"] == "Open the website 'example.com'."
            )

            self.assertEqual(dependent_event["trace"]["step_number"], 2)
            self.assertEqual(dependent_event["trace"]["prerequisite_step_number"], 1)
            self.assertEqual(dependent_event["trace"]["prerequisite_summary"], "Open the application 'calculator'.")
            self.assertEqual(dependent_event["trace"]["prerequisite_status"], "executed")

    def test_audit_recent_includes_dependency_trace_for_blocked_dependent_step(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(repo_root=Path(temp_dir))
            settings.ensure_runtime_dirs()
            audit_logger = AuditLogger(settings.audit_log_path)

            class FakePlanner:
                mode = "llm"
                label = "LLM planner"

                def plan(self, user_text, *, tools, history=None):
                    return PlanningResult(
                        routes=[
                            PlanningRoute(
                                intent="open_application",
                                task_type="desktop_control",
                                tool_name="open_application",
                                arguments={"application": "calculator"},
                                summary="Open the application 'calculator'.",
                            ),
                            PlanningRoute(
                                intent="open_resource",
                                task_type="browser",
                                tool_name="open_website",
                                arguments={"url": "example.com"},
                                summary="Open the website 'example.com'.",
                                depends_on_route_index=0,
                            ),
                        ],
                        summary="Blocked dependency trace test.",
                        dependencies_explicit=True,
                    )

                def to_dict(self):
                    return {"mode": self.mode, "label": self.label}

            def failing_launcher(command):
                raise RuntimeError("launch failed")

            orchestrator = AssistantOrchestrator(
                registry=build_default_registry(
                    settings,
                    notes_service=WorkspaceNotesService(settings.notes_dir),
                    documents_service=WorkspaceDocumentsService(settings.approved_document_roots),
                    reminder_service=ReminderService(settings.reminders_db_path),
                    website_opener=lambda url: True,
                    app_launcher=failing_launcher,
                ),
                policy=PolicyEngine(safe_mode=settings.safe_mode, approved_roots=settings.approved_roots),
                audit=audit_logger,
                memory=ConversationMemoryStore(settings.memory_db_path, enabled=settings.memory_enabled),
                planner=FakePlanner(),
            )

            response = orchestrator.handle_message("blocked trace", session_id="test-session")
            orchestrator.confirm_action_group(response.actions[0].group_id or "")

            recent_events = audit_logger.recent(limit=10)
            dependent_event = next(
                event
                for event in recent_events
                if event["status"] == "blocked" and event["action"]["summary"] == "Open the website 'example.com'."
            )

            self.assertEqual(dependent_event["trace"]["step_number"], 2)
            self.assertEqual(dependent_event["trace"]["prerequisite_step_number"], 1)
            self.assertEqual(dependent_event["trace"]["prerequisite_status"], "failed")
            self.assertIn("did not complete", dependent_event["trace"]["dependency_reason"])

    def test_audit_recent_includes_dependency_trace_for_rejected_dependent_step(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(repo_root=Path(temp_dir), planner_mode="rule")
            settings.ensure_runtime_dirs()
            audit_logger = AuditLogger(settings.audit_log_path)
            orchestrator = AssistantOrchestrator(
                registry=build_default_registry(
                    settings,
                    notes_service=WorkspaceNotesService(settings.notes_dir),
                    documents_service=WorkspaceDocumentsService(settings.approved_document_roots),
                    reminder_service=ReminderService(settings.reminders_db_path),
                    website_opener=lambda url: True,
                    app_launcher=lambda command: None,
                ),
                policy=PolicyEngine(safe_mode=settings.safe_mode, approved_roots=settings.approved_roots),
                audit=audit_logger,
                memory=ConversationMemoryStore(settings.memory_db_path, enabled=settings.memory_enabled),
            )

            response = orchestrator.handle_message(
                "Open calculator and open example.com",
                session_id="test-session",
            )
            orchestrator.reject_action(response.actions[0].action_id)

            recent_events = audit_logger.recent(limit=10)
            dependent_event = next(
                event
                for event in recent_events
                if event["status"] == "rejected" and event["action"]["summary"] == "Open the website 'example.com'."
            )

            self.assertEqual(dependent_event["trace"]["step_number"], 2)
            self.assertEqual(dependent_event["trace"]["prerequisite_step_number"], 1)
            self.assertEqual(dependent_event["trace"]["prerequisite_status"], "rejected")
            self.assertEqual(dependent_event["trace"]["prerequisite_summary"], "Open the application 'calculator'.")


if __name__ == "__main__":
    unittest.main()

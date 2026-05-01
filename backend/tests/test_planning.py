from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.core.config import Settings
from app.services.documents import WorkspaceDocumentsService
from app.services.notes import WorkspaceNotesService
from app.services.orchestrator import IntentRouter
from app.services.planning import build_planner
from app.services.reminders import ReminderService
from app.tools.registry import build_default_registry


class PlanningTests(unittest.TestCase):
    def _tool_definitions(self, temp_dir: str):
        settings = Settings(repo_root=Path(temp_dir))
        settings.ensure_runtime_dirs()
        registry = build_default_registry(
            settings,
            notes_service=WorkspaceNotesService(settings.notes_dir),
            documents_service=WorkspaceDocumentsService(settings.approved_document_roots),
            reminder_service=ReminderService(settings.reminders_db_path),
            website_opener=lambda url: True,
            app_launcher=lambda command: None,
        )
        return registry.list_tools()

    def test_build_planner_uses_rule_fallback_when_llm_is_not_configured(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(
                repo_root=Path(temp_dir),
                planner_mode="auto",
                llm_api_key="",
                llm_model="",
            )

            planner = build_planner(settings, fallback_router=IntentRouter())

            self.assertEqual(planner.mode, "rule")
            self.assertIn("not configured", planner.to_dict().get("reason", ""))

    def test_build_planner_uses_llm_planner_when_configured(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(
                repo_root=Path(temp_dir),
                planner_mode="llm",
                llm_api_key="test-key",
                llm_model="gpt-test",
                llm_base_url="https://example.test/v1",
            )
            tools = self._tool_definitions(temp_dir)
            planner = build_planner(
                settings,
                fallback_router=IntentRouter(),
                request_executor=lambda payload: {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "intent": "read_document",
                                        "task_type": "files",
                                        "tool_name": "read_document",
                                        "arguments": {"query": "architecture"},
                                        "summary": "Read the architecture document.",
                                    }
                                )
                            }
                        }
                    ]
                },
            )

            result = planner.plan("Can you pull up the architecture doc?", tools=tools, history=[])

            self.assertEqual(planner.mode, "llm")
            self.assertEqual(result.route.tool_name, "read_document")
            self.assertEqual(result.route.arguments["query"], "architecture")
            self.assertEqual(result.warnings, [])

    def test_rule_planner_splits_compound_requests(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(
                repo_root=Path(temp_dir),
                planner_mode="rule",
            )
            tools = self._tool_definitions(temp_dir)
            planner = build_planner(settings, fallback_router=IntentRouter())

            result = planner.plan(
                "Show me my system status and open calculator",
                tools=tools,
                history=[],
            )

            self.assertEqual(len(result.routes), 2)
            self.assertEqual(result.routes[0].tool_name, "system_snapshot")
            self.assertEqual(result.routes[1].tool_name, "open_application")
            self.assertEqual(result.routes[1].arguments["application"], "calculator")

    def test_llm_planner_accepts_actions_array(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(
                repo_root=Path(temp_dir),
                planner_mode="llm",
                llm_api_key="test-key",
                llm_model="gpt-test",
                llm_base_url="https://example.test/v1",
            )
            tools = self._tool_definitions(temp_dir)
            planner = build_planner(
                settings,
                fallback_router=IntentRouter(),
                request_executor=lambda payload: {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "summary": "Prepare the research workspace and calculator.",
                                        "actions": [
                                            {
                                                "intent": "launch_workspace",
                                                "task_type": "productivity",
                                                "tool_name": "launch_workspace",
                                                "arguments": {"workspace": "research"},
                                                "summary": "Launch the workspace 'research'.",
                                                "depends_on": None,
                                            },
                                            {
                                                "intent": "open_application",
                                                "task_type": "desktop_control",
                                                "tool_name": "open_application",
                                                "arguments": {"application": "calculator"},
                                                "summary": "Open the application 'calculator'.",
                                                "depends_on": 1,
                                            },
                                        ],
                                    }
                                )
                            }
                        }
                    ]
                },
            )

            result = planner.plan("Launch research workspace and open calculator", tools=tools, history=[])

            self.assertEqual(len(result.routes), 2)
            self.assertEqual(result.routes[0].tool_name, "launch_workspace")
            self.assertEqual(result.routes[1].tool_name, "open_application")
            self.assertEqual(result.routes[1].depends_on_route_index, 0)
            self.assertEqual(result.summary, "Prepare the research workspace and calculator.")
            self.assertTrue(result.dependencies_explicit)

    def test_llm_planner_falls_back_when_dependency_reference_is_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(
                repo_root=Path(temp_dir),
                planner_mode="llm",
                llm_api_key="test-key",
                llm_model="gpt-test",
                llm_base_url="https://example.test/v1",
            )
            tools = self._tool_definitions(temp_dir)
            planner = build_planner(
                settings,
                fallback_router=IntentRouter(),
                request_executor=lambda payload: {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "summary": "Broken dependency example.",
                                        "actions": [
                                            {
                                                "intent": "open_application",
                                                "task_type": "desktop_control",
                                                "tool_name": "open_application",
                                                "arguments": {"application": "calculator"},
                                                "summary": "Open the application 'calculator'.",
                                                "depends_on": 2,
                                            }
                                        ],
                                    }
                                )
                            }
                        }
                    ]
                },
            )

            result = planner.plan("Open calculator", tools=tools, history=[])

            self.assertEqual(result.route.tool_name, "open_application")
            self.assertTrue(any("LLM planner fallback" in warning for warning in result.warnings))

    def test_llm_planner_falls_back_to_rule_route_for_invalid_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(
                repo_root=Path(temp_dir),
                planner_mode="llm",
                llm_api_key="test-key",
                llm_model="gpt-test",
                llm_base_url="https://example.test/v1",
            )
            tools = self._tool_definitions(temp_dir)
            planner = build_planner(
                settings,
                fallback_router=IntentRouter(),
                request_executor=lambda payload: {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "intent": "unknown",
                                        "task_type": "mystery",
                                        "tool_name": "teleport_user",
                                        "arguments": {},
                                        "summary": "Do magic.",
                                    }
                                )
                            }
                        }
                    ]
                },
            )

            result = planner.plan("Show me my system status", tools=tools, history=[])

            self.assertEqual(result.route.tool_name, "system_snapshot")
            self.assertTrue(any("LLM planner fallback" in warning for warning in result.warnings))


if __name__ == "__main__":
    unittest.main()

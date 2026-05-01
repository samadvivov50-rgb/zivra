from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.api.routes.runtime import MemoryRequest, SafeModeRequest, set_memory, set_safe_mode
from app.api.routes.settings import UpdateSettingsRequest, read_settings, reset_settings, update_settings
from app.core.config import Settings
from app.services.memory import ConversationMemoryStore
from app.services.orchestrator import IntentRouter
from app.services.planning import build_planner
from app.services.preferences import PreferencesService


class PreferencesServiceTests(unittest.TestCase):
    def test_update_persists_normalized_preferences(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(repo_root=Path(temp_dir))
            service = PreferencesService(
                settings.preferences_path,
                defaults={
                    "assistant_name": settings.assistant_name,
                    "safe_mode": settings.safe_mode,
                    "memory_enabled": settings.memory_enabled,
                    "voice_auto_speak": settings.voice_auto_speak,
                    "voice_auto_send": settings.voice_auto_send,
                    "voice_wake_phrase_enabled": settings.voice_wake_phrase_enabled,
                    "voice_wake_phrase": settings.voice_wake_phrase,
                    "workflow_supervisor_enabled": settings.workflow_supervisor_enabled,
                    "workflow_supervisor_max_tasks_per_cycle": settings.workflow_supervisor_max_tasks_per_cycle,
                    "workflow_supervisor_max_pending_approvals": settings.workflow_supervisor_max_pending_approvals,
                    "workflow_supervisor_pause_on_failure": settings.workflow_supervisor_pause_on_failure,
                    "live_search_result_limit": settings.live_search_result_limit,
                    "dashboard_refresh_seconds": settings.dashboard_refresh_seconds,
                    "whatsapp_api_version": settings.whatsapp_api_version,
                    "whatsapp_phone_number_id": settings.whatsapp_phone_number_id,
                    "whatsapp_verify_token": settings.whatsapp_verify_token,
                },
            )

            applied = service.update(
                settings,
                {
                    "assistant_name": "  Atlas  ",
                    "safe_mode": True,
                    "memory_enabled": False,
                    "voice_auto_speak": True,
                    "voice_auto_send": True,
                    "voice_wake_phrase_enabled": True,
                    "voice_wake_phrase": "  hey atlas  ",
                    "workflow_supervisor_enabled": True,
                    "workflow_supervisor_max_tasks_per_cycle": 9,
                    "workflow_supervisor_max_pending_approvals": 0,
                    "workflow_supervisor_pause_on_failure": False,
                    "live_search_result_limit": 99,
                    "dashboard_refresh_seconds": 5,
                    "whatsapp_api_version": " v99.0 ",
                    "whatsapp_phone_number_id": " 1234567890 ",
                    "whatsapp_verify_token": "  verify-me  ",
                },
            )

            self.assertEqual(applied["assistant_name"], "Atlas")
            self.assertTrue(applied["safe_mode"])
            self.assertFalse(applied["memory_enabled"])
            self.assertTrue(applied["voice_auto_speak"])
            self.assertTrue(applied["voice_auto_send"])
            self.assertTrue(applied["voice_wake_phrase_enabled"])
            self.assertEqual(applied["voice_wake_phrase"], "hey atlas")
            self.assertTrue(applied["workflow_supervisor_enabled"])
            self.assertEqual(applied["workflow_supervisor_max_tasks_per_cycle"], 5)
            self.assertEqual(applied["workflow_supervisor_max_pending_approvals"], 1)
            self.assertFalse(applied["workflow_supervisor_pause_on_failure"])
            self.assertEqual(applied["live_search_result_limit"], 10)
            self.assertEqual(applied["dashboard_refresh_seconds"], 15)
            self.assertEqual(applied["whatsapp_api_version"], "v99.0")
            self.assertEqual(applied["whatsapp_phone_number_id"], "1234567890")
            self.assertEqual(applied["whatsapp_verify_token"], "verify-me")

            reloaded = service.load()
            self.assertEqual(reloaded, applied)

    def test_reset_restores_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(repo_root=Path(temp_dir))
            service = PreferencesService(
                settings.preferences_path,
                defaults={
                    "assistant_name": settings.assistant_name,
                    "safe_mode": settings.safe_mode,
                    "memory_enabled": settings.memory_enabled,
                    "voice_auto_speak": settings.voice_auto_speak,
                    "voice_auto_send": settings.voice_auto_send,
                    "voice_wake_phrase_enabled": settings.voice_wake_phrase_enabled,
                    "voice_wake_phrase": settings.voice_wake_phrase,
                    "workflow_supervisor_enabled": settings.workflow_supervisor_enabled,
                    "workflow_supervisor_max_tasks_per_cycle": settings.workflow_supervisor_max_tasks_per_cycle,
                    "workflow_supervisor_max_pending_approvals": settings.workflow_supervisor_max_pending_approvals,
                    "workflow_supervisor_pause_on_failure": settings.workflow_supervisor_pause_on_failure,
                    "live_search_result_limit": settings.live_search_result_limit,
                    "dashboard_refresh_seconds": settings.dashboard_refresh_seconds,
                    "whatsapp_api_version": settings.whatsapp_api_version,
                    "whatsapp_phone_number_id": settings.whatsapp_phone_number_id,
                    "whatsapp_verify_token": settings.whatsapp_verify_token,
                },
            )
            service.update(
                settings,
                {
                    "assistant_name": "Atlas",
                    "safe_mode": True,
                    "memory_enabled": False,
                    "voice_auto_speak": True,
                    "voice_wake_phrase_enabled": True,
                    "voice_wake_phrase": "hey atlas",
                    "workflow_supervisor_enabled": True,
                    "whatsapp_api_version": "v24.0",
                    "whatsapp_phone_number_id": "9999",
                    "whatsapp_verify_token": "token-1",
                },
            )

            restored = service.reset(settings)

            self.assertEqual(restored["assistant_name"], "Zivra")
            self.assertFalse(restored["safe_mode"])
            self.assertTrue(restored["memory_enabled"])
            self.assertFalse(restored["voice_auto_speak"])
            self.assertFalse(restored["voice_auto_send"])
            self.assertFalse(restored["voice_wake_phrase_enabled"])
            self.assertEqual(restored["voice_wake_phrase"], "hey zivra")
            self.assertFalse(restored["workflow_supervisor_enabled"])
            self.assertEqual(restored["workflow_supervisor_max_tasks_per_cycle"], 1)
            self.assertEqual(restored["workflow_supervisor_max_pending_approvals"], 1)
            self.assertTrue(restored["workflow_supervisor_pause_on_failure"])
            self.assertEqual(restored["whatsapp_api_version"], "v23.0")
            self.assertEqual(restored["whatsapp_phone_number_id"], "")
            self.assertEqual(restored["whatsapp_verify_token"], "")


class SettingsRouteTests(unittest.TestCase):
    def test_update_route_applies_runtime_preferences(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            request = self._build_request(temp_dir)

            response = update_settings(
                UpdateSettingsRequest(
                    assistant_name="Atlas",
                    safe_mode=True,
                    memory_enabled=False,
                    voice_auto_speak=True,
                    voice_auto_send=True,
                    voice_wake_phrase_enabled=True,
                    voice_wake_phrase="hey atlas",
                    workflow_supervisor_enabled=True,
                    workflow_supervisor_max_tasks_per_cycle=3,
                    workflow_supervisor_max_pending_approvals=2,
                    workflow_supervisor_pause_on_failure=False,
                    live_search_result_limit=8,
                    dashboard_refresh_seconds=90,
                    whatsapp_api_version="v24.0",
                    whatsapp_phone_number_id="12345",
                    whatsapp_verify_token="verify-me",
                ),
                request,
            )

            self.assertEqual(response["assistant_name"], "Atlas")
            self.assertTrue(request.app.state.settings.safe_mode)
            self.assertFalse(request.app.state.settings.memory_enabled)
            self.assertTrue(request.app.state.settings.voice_auto_speak)
            self.assertTrue(request.app.state.settings.voice_auto_send)
            self.assertTrue(request.app.state.settings.voice_wake_phrase_enabled)
            self.assertEqual(request.app.state.settings.voice_wake_phrase, "hey atlas")
            self.assertTrue(request.app.state.settings.workflow_supervisor_enabled)
            self.assertEqual(request.app.state.settings.workflow_supervisor_max_tasks_per_cycle, 3)
            self.assertEqual(request.app.state.settings.workflow_supervisor_max_pending_approvals, 2)
            self.assertFalse(request.app.state.settings.workflow_supervisor_pause_on_failure)
            self.assertTrue(request.app.state.policy_engine.safe_mode)
            self.assertFalse(request.app.state.memory_store.enabled)
            self.assertEqual(request.app.state.settings.live_search_result_limit, 8)
            self.assertEqual(request.app.state.settings.dashboard_refresh_seconds, 90)
            self.assertEqual(request.app.state.settings.whatsapp_api_version, "v24.0")
            self.assertEqual(request.app.state.settings.whatsapp_phone_number_id, "12345")
            self.assertEqual(request.app.state.settings.whatsapp_verify_token, "verify-me")

    def test_runtime_routes_persist_safe_mode_and_memory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            request = self._build_request(temp_dir)

            set_safe_mode(SafeModeRequest(enabled=True), request)
            set_memory(MemoryRequest(enabled=False), request)
            snapshot = read_settings(request)

            self.assertTrue(snapshot["safe_mode"])
            self.assertFalse(snapshot["memory_enabled"])
            self.assertFalse(snapshot["voice_auto_speak"])
            self.assertFalse(snapshot["voice_auto_send"])
            self.assertFalse(snapshot["voice_wake_phrase_enabled"])
            self.assertEqual(snapshot["voice_wake_phrase"], "hey zivra")
            self.assertFalse(snapshot["workflow_supervisor_enabled"])
            self.assertEqual(snapshot["workflow_supervisor_max_tasks_per_cycle"], 1)
            self.assertEqual(snapshot["workflow_supervisor_max_pending_approvals"], 1)
            self.assertTrue(snapshot["workflow_supervisor_pause_on_failure"])
            self.assertEqual(snapshot["whatsapp_api_version"], "v23.0")
            self.assertEqual(snapshot["whatsapp_phone_number_id"], "")
            self.assertEqual(snapshot["whatsapp_verify_token"], "")
            self.assertTrue(request.app.state.policy_engine.safe_mode)
            self.assertFalse(request.app.state.memory_store.enabled)

    def test_reset_route_restores_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            request = self._build_request(temp_dir)
            update_settings(
                UpdateSettingsRequest(
                    assistant_name="Atlas",
                    safe_mode=True,
                    memory_enabled=False,
                    voice_auto_speak=True,
                    voice_auto_send=True,
                    voice_wake_phrase_enabled=True,
                    voice_wake_phrase="hey atlas",
                    workflow_supervisor_enabled=True,
                    workflow_supervisor_max_tasks_per_cycle=3,
                    workflow_supervisor_max_pending_approvals=2,
                    workflow_supervisor_pause_on_failure=False,
                    live_search_result_limit=8,
                    dashboard_refresh_seconds=90,
                    whatsapp_api_version="v24.0",
                    whatsapp_phone_number_id="12345",
                    whatsapp_verify_token="verify-me",
                ),
                request,
            )

            response = reset_settings(request)

            self.assertEqual(response["assistant_name"], "Zivra")
            self.assertTrue(request.app.state.settings.safe_mode)
            self.assertFalse(request.app.state.settings.memory_enabled)
            self.assertFalse(request.app.state.settings.voice_auto_speak)
            self.assertFalse(request.app.state.settings.voice_auto_send)
            self.assertFalse(request.app.state.settings.voice_wake_phrase_enabled)
            self.assertEqual(request.app.state.settings.voice_wake_phrase, "hey zivra")
            self.assertFalse(request.app.state.settings.workflow_supervisor_enabled)
            self.assertEqual(request.app.state.settings.workflow_supervisor_max_tasks_per_cycle, 1)
            self.assertEqual(request.app.state.settings.workflow_supervisor_max_pending_approvals, 1)
            self.assertTrue(request.app.state.settings.workflow_supervisor_pause_on_failure)
            self.assertEqual(request.app.state.settings.live_search_result_limit, 6)
            self.assertEqual(request.app.state.settings.dashboard_refresh_seconds, 60)
            self.assertEqual(request.app.state.settings.whatsapp_api_version, "v23.0")
            self.assertEqual(request.app.state.settings.whatsapp_phone_number_id, "")
            self.assertEqual(request.app.state.settings.whatsapp_verify_token, "")
            self.assertTrue(request.app.state.policy_engine.safe_mode)
            self.assertFalse(request.app.state.memory_store.enabled)

    def _build_request(self, temp_dir: str):
        settings = Settings(repo_root=Path(temp_dir))
        settings.ensure_runtime_dirs()
        preferences_service = PreferencesService(
            settings.preferences_path,
            defaults={
                "assistant_name": settings.assistant_name,
                "safe_mode": settings.safe_mode,
                "memory_enabled": settings.memory_enabled,
                "voice_auto_speak": settings.voice_auto_speak,
                "voice_auto_send": settings.voice_auto_send,
                "voice_wake_phrase_enabled": settings.voice_wake_phrase_enabled,
                "voice_wake_phrase": settings.voice_wake_phrase,
                "workflow_supervisor_enabled": settings.workflow_supervisor_enabled,
                "workflow_supervisor_max_tasks_per_cycle": settings.workflow_supervisor_max_tasks_per_cycle,
                "workflow_supervisor_max_pending_approvals": settings.workflow_supervisor_max_pending_approvals,
                "workflow_supervisor_pause_on_failure": settings.workflow_supervisor_pause_on_failure,
                "live_search_result_limit": settings.live_search_result_limit,
                "dashboard_refresh_seconds": settings.dashboard_refresh_seconds,
                "whatsapp_api_version": settings.whatsapp_api_version,
                "whatsapp_phone_number_id": settings.whatsapp_phone_number_id,
                "whatsapp_verify_token": settings.whatsapp_verify_token,
            },
        )
        memory_store = ConversationMemoryStore(settings.memory_db_path, enabled=settings.memory_enabled)
        state = SimpleNamespace(
            settings=settings,
            preferences_service=preferences_service,
            policy_engine=SimpleNamespace(safe_mode=settings.safe_mode),
            memory_store=memory_store,
            orchestrator=SimpleNamespace(
                router=IntentRouter(),
                planner=build_planner(settings, fallback_router=IntentRouter()),
            ),
        )
        return SimpleNamespace(app=SimpleNamespace(state=state))


if __name__ == "__main__":
    unittest.main()

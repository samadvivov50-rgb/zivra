from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.config import Settings


class PreferencesService:
    def __init__(self, path: Path, *, defaults: dict[str, Any]) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.defaults = self._normalize(defaults)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return dict(self.defaults)

        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return dict(self.defaults)

        normalized = self._normalize(payload)
        if normalized != payload:
            self._write(normalized)
        return normalized

    def snapshot(self, settings: Settings) -> dict[str, Any]:
        return {
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
        }

    def apply_to_settings(self, settings: Settings, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        normalized = self._normalize(payload or self.load())
        settings.assistant_name = normalized["assistant_name"]
        settings.safe_mode = normalized["safe_mode"]
        settings.memory_enabled = normalized["memory_enabled"]
        settings.voice_auto_speak = normalized["voice_auto_speak"]
        settings.voice_auto_send = normalized["voice_auto_send"]
        settings.voice_wake_phrase_enabled = normalized["voice_wake_phrase_enabled"]
        settings.voice_wake_phrase = normalized["voice_wake_phrase"]
        settings.workflow_supervisor_enabled = normalized["workflow_supervisor_enabled"]
        settings.workflow_supervisor_max_tasks_per_cycle = normalized["workflow_supervisor_max_tasks_per_cycle"]
        settings.workflow_supervisor_max_pending_approvals = normalized["workflow_supervisor_max_pending_approvals"]
        settings.workflow_supervisor_pause_on_failure = normalized["workflow_supervisor_pause_on_failure"]
        settings.live_search_result_limit = normalized["live_search_result_limit"]
        settings.dashboard_refresh_seconds = normalized["dashboard_refresh_seconds"]
        settings.whatsapp_api_version = normalized["whatsapp_api_version"]
        settings.whatsapp_phone_number_id = normalized["whatsapp_phone_number_id"]
        settings.whatsapp_verify_token = normalized["whatsapp_verify_token"]
        return normalized

    def update(self, settings: Settings, updates: dict[str, Any]) -> dict[str, Any]:
        current = self.load()
        current.update(updates)
        normalized = self._normalize(current)
        self._write(normalized)
        return self.apply_to_settings(settings, normalized)

    def reset(self, settings: Settings) -> dict[str, Any]:
        normalized = dict(self.defaults)
        self._write(normalized)
        return self.apply_to_settings(settings, normalized)

    def _write(self, payload: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def _normalize(self, payload: dict[str, Any]) -> dict[str, Any]:
        defaults = self.defaults if hasattr(self, "defaults") else {}
        assistant_name = str(payload.get("assistant_name", defaults.get("assistant_name", "Zivra"))).strip()
        assistant_name = assistant_name[:32] or str(defaults.get("assistant_name", "Zivra"))

        return {
            "assistant_name": assistant_name,
            "safe_mode": self._normalize_bool(payload.get("safe_mode", defaults.get("safe_mode", False))),
            "memory_enabled": self._normalize_bool(
                payload.get("memory_enabled", defaults.get("memory_enabled", True))
            ),
            "voice_auto_speak": self._normalize_bool(
                payload.get("voice_auto_speak", defaults.get("voice_auto_speak", False))
            ),
            "voice_auto_send": self._normalize_bool(
                payload.get("voice_auto_send", defaults.get("voice_auto_send", False))
            ),
            "voice_wake_phrase_enabled": self._normalize_bool(
                payload.get("voice_wake_phrase_enabled", defaults.get("voice_wake_phrase_enabled", False))
            ),
            "voice_wake_phrase": self._normalize_text(
                payload.get("voice_wake_phrase", defaults.get("voice_wake_phrase", "hey zivra")),
                fallback="hey zivra",
                maximum=48,
            ),
            "workflow_supervisor_enabled": self._normalize_bool(
                payload.get("workflow_supervisor_enabled", defaults.get("workflow_supervisor_enabled", False))
            ),
            "workflow_supervisor_max_tasks_per_cycle": self._normalize_int(
                payload.get(
                    "workflow_supervisor_max_tasks_per_cycle",
                    defaults.get("workflow_supervisor_max_tasks_per_cycle", 1),
                ),
                minimum=1,
                maximum=5,
                fallback=1,
            ),
            "workflow_supervisor_max_pending_approvals": self._normalize_int(
                payload.get(
                    "workflow_supervisor_max_pending_approvals",
                    defaults.get("workflow_supervisor_max_pending_approvals", 1),
                ),
                minimum=1,
                maximum=10,
                fallback=1,
            ),
            "workflow_supervisor_pause_on_failure": self._normalize_bool(
                payload.get(
                    "workflow_supervisor_pause_on_failure",
                    defaults.get("workflow_supervisor_pause_on_failure", True),
                )
            ),
            "live_search_result_limit": self._normalize_int(
                payload.get("live_search_result_limit", defaults.get("live_search_result_limit", 6)),
                minimum=1,
                maximum=10,
                fallback=6,
            ),
            "dashboard_refresh_seconds": self._normalize_int(
                payload.get("dashboard_refresh_seconds", defaults.get("dashboard_refresh_seconds", 60)),
                minimum=15,
                maximum=300,
                fallback=60,
            ),
            "whatsapp_api_version": self._normalize_text(
                payload.get("whatsapp_api_version", defaults.get("whatsapp_api_version", "v23.0")),
                fallback="v23.0",
                maximum=16,
            ),
            "whatsapp_phone_number_id": self._normalize_text(
                payload.get("whatsapp_phone_number_id", defaults.get("whatsapp_phone_number_id", "")),
                fallback="",
                maximum=64,
            ),
            "whatsapp_verify_token": self._normalize_text(
                payload.get("whatsapp_verify_token", defaults.get("whatsapp_verify_token", "")),
                fallback="",
                maximum=128,
            ),
        }

    def _normalize_bool(self, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on"}:
                return True
            if normalized in {"0", "false", "no", "off"}:
                return False
        return bool(value)

    def _normalize_int(self, value: Any, *, minimum: int, maximum: int, fallback: int) -> int:
        try:
            normalized = int(value)
        except (TypeError, ValueError):
            normalized = fallback
        return min(max(normalized, minimum), maximum)

    def _normalize_text(self, value: Any, *, fallback: str, maximum: int) -> str:
        normalized = str(value or "").strip()
        return (normalized[:maximum] or fallback).strip()


def synchronize_runtime_preferences(*, settings: Settings, policy_engine: Any, memory_store: Any) -> None:
    policy_engine.safe_mode = settings.safe_mode
    memory_store.set_enabled(settings.memory_enabled)

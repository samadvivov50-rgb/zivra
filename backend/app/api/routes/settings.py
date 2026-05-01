from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.services.planning import build_planner
from app.services.preferences import synchronize_runtime_preferences
from app.services.secrets import SecretStoreUnavailableError

router = APIRouter(prefix="/settings", tags=["settings"])


class UpdateSettingsRequest(BaseModel):
    assistant_name: str | None = Field(default=None, max_length=32)
    safe_mode: bool | None = None
    memory_enabled: bool | None = None
    voice_auto_speak: bool | None = None
    voice_auto_send: bool | None = None
    voice_wake_phrase_enabled: bool | None = None
    voice_wake_phrase: str | None = Field(default=None, max_length=48)
    workflow_supervisor_enabled: bool | None = None
    workflow_supervisor_max_tasks_per_cycle: int | None = Field(default=None, ge=1, le=5)
    workflow_supervisor_max_pending_approvals: int | None = Field(default=None, ge=1, le=10)
    workflow_supervisor_pause_on_failure: bool | None = None
    live_search_result_limit: int | None = Field(default=None, ge=1, le=10)
    dashboard_refresh_seconds: int | None = Field(default=None, ge=15, le=300)
    whatsapp_api_version: str | None = Field(default=None, max_length=16)
    whatsapp_phone_number_id: str | None = Field(default=None, max_length=64)
    whatsapp_verify_token: str | None = Field(default=None, max_length=128)


class UpdateSecretsRequest(BaseModel):
    llm_api_key: str | None = Field(default=None, max_length=512)
    smtp_username: str | None = Field(default=None, max_length=320)
    smtp_password: str | None = Field(default=None, max_length=512)
    whatsapp_access_token: str | None = Field(default=None, max_length=1024)
    whatsapp_app_secret: str | None = Field(default=None, max_length=512)


def get_settings(request: Request) -> dict:
    preferences_service = request.app.state.preferences_service
    settings = request.app.state.settings
    return preferences_service.snapshot(settings)


@router.get("")
def read_settings(request: Request) -> dict:
    return get_settings(request)


@router.put("")
def update_settings(payload: UpdateSettingsRequest, request: Request) -> dict:
    preferences_service = request.app.state.preferences_service
    settings = request.app.state.settings
    updates = _payload_updates(payload)
    applied = preferences_service.update(settings, updates)
    synchronize_runtime_preferences(
        settings=settings,
        policy_engine=request.app.state.policy_engine,
        memory_store=request.app.state.memory_store,
    )
    _refresh_planner(request)
    return {
        **applied,
        "message": "Settings updated.",
    }


@router.post("/reset")
def reset_settings(request: Request) -> dict:
    preferences_service = request.app.state.preferences_service
    settings = request.app.state.settings
    applied = preferences_service.update(
        settings,
        {
            "assistant_name": preferences_service.defaults["assistant_name"],
            "voice_auto_speak": preferences_service.defaults["voice_auto_speak"],
            "voice_auto_send": preferences_service.defaults["voice_auto_send"],
            "voice_wake_phrase_enabled": preferences_service.defaults["voice_wake_phrase_enabled"],
            "voice_wake_phrase": preferences_service.defaults["voice_wake_phrase"],
            "workflow_supervisor_enabled": preferences_service.defaults["workflow_supervisor_enabled"],
            "workflow_supervisor_max_tasks_per_cycle": preferences_service.defaults[
                "workflow_supervisor_max_tasks_per_cycle"
            ],
            "workflow_supervisor_max_pending_approvals": preferences_service.defaults[
                "workflow_supervisor_max_pending_approvals"
            ],
            "workflow_supervisor_pause_on_failure": preferences_service.defaults[
                "workflow_supervisor_pause_on_failure"
            ],
            "live_search_result_limit": preferences_service.defaults["live_search_result_limit"],
            "dashboard_refresh_seconds": preferences_service.defaults["dashboard_refresh_seconds"],
            "whatsapp_api_version": preferences_service.defaults["whatsapp_api_version"],
            "whatsapp_phone_number_id": preferences_service.defaults["whatsapp_phone_number_id"],
            "whatsapp_verify_token": preferences_service.defaults["whatsapp_verify_token"],
        },
    )
    synchronize_runtime_preferences(
        settings=settings,
        policy_engine=request.app.state.policy_engine,
        memory_store=request.app.state.memory_store,
    )
    _refresh_planner(request)
    return {
        **applied,
        "message": "Settings reset to defaults.",
    }


@router.get("/secrets")
def read_secret_settings(request: Request) -> dict:
    settings = request.app.state.settings
    secrets_service = request.app.state.secrets_service
    return secrets_service.snapshot(settings)


@router.put("/secrets")
def update_secret_settings(payload: UpdateSecretsRequest, request: Request) -> dict:
    settings = request.app.state.settings
    secrets_service = request.app.state.secrets_service
    updates = _payload_updates(payload)
    try:
        snapshot = secrets_service.update(settings, updates)
    except SecretStoreUnavailableError as exc:
        return {
            **secrets_service.snapshot(settings),
            "message": str(exc),
        }
    _refresh_planner(request)
    return {
        **snapshot,
        "message": "Encrypted secrets updated.",
    }


@router.post("/secrets/clear")
def clear_secret_settings(request: Request) -> dict:
    settings = request.app.state.settings
    secrets_service = request.app.state.secrets_service
    snapshot = secrets_service.clear(settings)
    _refresh_planner(request)
    return {
        **snapshot,
        "message": "Stored encrypted secrets cleared.",
    }


def _payload_updates(payload: UpdateSettingsRequest) -> dict:
    if hasattr(payload, "model_dump"):
        return payload.model_dump(exclude_unset=True)
    return payload.dict(exclude_unset=True)


def _refresh_planner(request: Request) -> None:
    orchestrator = request.app.state.orchestrator
    orchestrator.planner = build_planner(
        request.app.state.settings,
        fallback_router=orchestrator.router,
    )

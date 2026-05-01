from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.services.preferences import synchronize_runtime_preferences

router = APIRouter(prefix="/runtime", tags=["runtime"])


class SafeModeRequest(BaseModel):
    enabled: bool


class MemoryRequest(BaseModel):
    enabled: bool


@router.get("/state")
def runtime_state(request: Request) -> dict:
    settings = request.app.state.settings
    orchestrator = request.app.state.orchestrator

    return {
        "assistant_name": settings.assistant_name,
        "safe_mode": settings.safe_mode,
        "memory_enabled": settings.memory_enabled,
        "live_search_result_limit": settings.live_search_result_limit,
        "dashboard_refresh_seconds": settings.dashboard_refresh_seconds,
        "planner": orchestrator.planner_info,
        "pending_actions": orchestrator.pending_count,
        "approved_roots": [str(path) for path in settings.approved_roots],
    }


@router.post("/safe-mode")
def set_safe_mode(payload: SafeModeRequest, request: Request) -> dict:
    settings = request.app.state.settings
    preferences_service = request.app.state.preferences_service

    preferences_service.update(settings, {"safe_mode": payload.enabled})
    synchronize_runtime_preferences(
        settings=settings,
        policy_engine=request.app.state.policy_engine,
        memory_store=request.app.state.memory_store,
    )

    return {
        "safe_mode": settings.safe_mode,
        "message": "Safe mode updated.",
    }


@router.post("/memory")
def set_memory(payload: MemoryRequest, request: Request) -> dict:
    settings = request.app.state.settings
    preferences_service = request.app.state.preferences_service

    preferences_service.update(settings, {"memory_enabled": payload.enabled})
    synchronize_runtime_preferences(
        settings=settings,
        policy_engine=request.app.state.policy_engine,
        memory_store=request.app.state.memory_store,
    )

    return {
        "memory_enabled": settings.memory_enabled,
        "message": "Memory setting updated.",
    }

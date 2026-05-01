from __future__ import annotations

from fastapi import APIRouter, Request

from app.api.routes.workflows import run_supervisor_cycle_for_request

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview")
def dashboard_overview(request: Request, run_supervisor: bool = True) -> dict:
    orchestrator = request.app.state.orchestrator
    audit_logger = request.app.state.audit_logger
    reminders_service = request.app.state.reminders_service
    settings = request.app.state.settings
    registry = request.app.state.registry
    workflow_service = request.app.state.workflow_service
    workflow_cycle = (
        run_supervisor_cycle_for_request(request)
        if run_supervisor
        else {
            "enabled": settings.workflow_supervisor_enabled,
            "dispatched_count": 0,
            "run_count": 0,
            "stopped_reason": "manual_refresh",
            "tasks": [],
            "paused_workflows": [],
        }
    )

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
        "planner": orchestrator.planner_info,
        "approved_roots": [str(path) for path in settings.approved_read_roots],
        "approved_write_roots": [str(path) for path in settings.approved_write_roots],
        "pending_actions": orchestrator.pending_count,
        "pending_queue": orchestrator.list_pending_actions(),
        "pending_reminders": reminders_service.count_pending(),
        "reminder_summary": reminders_service.summary(),
        "workflow_summary": workflow_service.summary(),
        "workflow_supervisor_cycle": workflow_cycle,
        "recent_actions": audit_logger.recent(limit=10),
        "tools": [tool.to_dict() for tool in registry.list_tools()],
        "modules": [
            "interaction",
            "intelligence",
            "desktop_control",
            "file_data",
            "browser_web",
            "communication",
            "productivity",
            "monitoring",
            "safety",
        ],
    }


@router.get("/activity")
def dashboard_activity(
    request: Request,
    limit: int = 20,
    offset: int = 0,
    q: str | None = None,
    status: str | None = None,
    start: str | None = None,
    end: str | None = None,
) -> dict:
    audit_logger = request.app.state.audit_logger
    return audit_logger.query(
        limit=min(max(limit, 1), 100),
        offset=max(offset, 0),
        search_query=q,
        status_scope=status,
        started_after=start,
        ended_before=end,
    )


@router.get("/activity/export")
def dashboard_activity_export(
    request: Request,
    limit: int = 500,
    q: str | None = None,
    status: str | None = None,
    start: str | None = None,
    end: str | None = None,
) -> dict:
    audit_logger = request.app.state.audit_logger
    return audit_logger.export(
        limit=min(max(limit, 1), 2000),
        search_query=q,
        status_scope=status,
        started_after=start,
        ended_before=end,
    )


@router.get("/activity/groups")
def dashboard_activity_groups(
    request: Request,
    limit: int = 10,
    offset: int = 0,
    q: str | None = None,
    status: str | None = None,
    start: str | None = None,
    end: str | None = None,
) -> dict:
    audit_logger = request.app.state.audit_logger
    return audit_logger.query_groups(
        limit=min(max(limit, 1), 100),
        offset=max(offset, 0),
        search_query=q,
        status_scope=status,
        started_after=start,
        ended_before=end,
    )

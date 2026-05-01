from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.models import ActionStatus, ApprovalMode, PermissionLevel, ProposedAction, ToolCategory, ToolResult
from app.services.policy import PolicyDecision

router = APIRouter(prefix="/reminders", tags=["reminders"])


class SnoozeRequest(BaseModel):
    preset: str


class ScheduleRequest(BaseModel):
    due_at: str
    schedule_hint: str | None = None


class RecurrenceRequest(BaseModel):
    preset: str


@router.get("")
def list_reminders(
    request: Request,
    limit: int = 8,
    include_completed: bool = False,
    include_archived: bool = False,
) -> dict:
    reminders_service = request.app.state.reminders_service
    return {
        "count": reminders_service.count_pending(),
        "reminders": reminders_service.list_upcoming(
            limit=limit,
            include_completed=include_completed,
            include_archived=include_archived,
        ),
    }


@router.get("/summary")
def reminder_summary(request: Request) -> dict:
    reminders_service = request.app.state.reminders_service
    return {
        "summary": reminders_service.summary(),
    }


@router.post("/{reminder_id}/complete")
def complete_reminder(reminder_id: int, request: Request) -> dict:
    reminders_service = request.app.state.reminders_service
    reminder = reminders_service.complete_reminder(reminder_id)
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found.")
    message = "Reminder marked as completed."
    next_occurrence = reminder.get("next_occurrence")
    if isinstance(next_occurrence, dict) and next_occurrence.get("due_display"):
        message = f"Recurring reminder completed. Next occurrence scheduled for {next_occurrence['due_display']}."
    _record_reminder_update(
        request=request,
        reminder_id=reminder_id,
        tool_name="complete_reminder",
        summary=f"Mark reminder {reminder_id} as completed.",
        message=message,
        reminder=reminder,
    )
    return {
        "message": message,
        "reminder": reminder,
    }


@router.post("/{reminder_id}/reopen")
def reopen_reminder(reminder_id: int, request: Request) -> dict:
    reminders_service = request.app.state.reminders_service
    reminder = reminders_service.reopen_reminder(reminder_id)
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found.")
    _record_reminder_update(
        request=request,
        reminder_id=reminder_id,
        tool_name="reopen_reminder",
        summary=f"Reopen reminder {reminder_id}.",
        message="Reminder reopened.",
        reminder=reminder,
    )
    return {
        "message": "Reminder reopened.",
        "reminder": reminder,
    }


@router.post("/{reminder_id}/archive")
def archive_reminder(reminder_id: int, request: Request) -> dict:
    reminders_service = request.app.state.reminders_service
    reminder = reminders_service.archive_reminder(reminder_id)
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found.")
    _record_reminder_update(
        request=request,
        reminder_id=reminder_id,
        tool_name="archive_reminder",
        summary=f"Archive reminder {reminder_id}.",
        message="Reminder archived.",
        reminder=reminder,
    )
    return {
        "message": "Reminder archived.",
        "reminder": reminder,
    }


@router.post("/{reminder_id}/restore")
def restore_reminder(reminder_id: int, request: Request) -> dict:
    reminders_service = request.app.state.reminders_service
    reminder = reminders_service.restore_reminder(reminder_id)
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found.")
    _record_reminder_update(
        request=request,
        reminder_id=reminder_id,
        tool_name="restore_reminder",
        summary=f"Restore reminder {reminder_id}.",
        message="Reminder restored to pending.",
        reminder=reminder,
    )
    return {
        "message": "Reminder restored to pending.",
        "reminder": reminder,
    }


@router.post("/{reminder_id}/delete")
def delete_archived_reminder(reminder_id: int, request: Request) -> dict:
    reminders_service = request.app.state.reminders_service
    deleted = reminders_service.delete_archived_reminder(reminder_id)
    if not deleted:
        reminder = reminders_service.get_reminder(reminder_id)
        if reminder is None:
            raise HTTPException(status_code=404, detail="Reminder not found.")
        raise HTTPException(status_code=400, detail="Only archived reminders can be deleted.")
    _record_bulk_reminder_update(
        request=request,
        tool_name="delete_archived_reminder",
        summary=f"Delete archived reminder {reminder_id}.",
        message="Archived reminder deleted permanently.",
        result={"deleted_count": 1},
        arguments={"reminder_id": reminder_id},
        permission_level=PermissionLevel.SENSITIVE,
    )
    return {
        "message": "Archived reminder deleted permanently.",
        "deleted_count": 1,
    }


@router.post("/{reminder_id}/snooze")
def snooze_reminder(reminder_id: int, payload: SnoozeRequest, request: Request) -> dict:
    reminders_service = request.app.state.reminders_service
    due_at, schedule_hint = _resolve_snooze_preset(payload.preset)
    reminder = reminders_service.reschedule_reminder(
        reminder_id,
        due_at=due_at,
        schedule_hint=schedule_hint,
    )
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found.")
    _record_reminder_update(
        request=request,
        reminder_id=reminder_id,
        tool_name="snooze_reminder",
        summary=f"Snooze reminder {reminder_id} to {schedule_hint}.",
        message=f"Reminder snoozed to {schedule_hint}.",
        reminder=reminder,
    )
    return {
        "message": f"Reminder snoozed to {schedule_hint}.",
        "reminder": reminder,
    }


@router.post("/{reminder_id}/schedule")
def schedule_reminder(reminder_id: int, payload: ScheduleRequest, request: Request) -> dict:
    reminders_service = request.app.state.reminders_service
    due_at = _normalize_due_at(payload.due_at)
    schedule_hint = payload.schedule_hint.strip() if payload.schedule_hint else "custom schedule"
    reminder = reminders_service.reschedule_reminder(
        reminder_id,
        due_at=due_at,
        schedule_hint=schedule_hint,
    )
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found.")
    _record_reminder_update(
        request=request,
        reminder_id=reminder_id,
        tool_name="schedule_reminder",
        summary=f"Schedule reminder {reminder_id} for {reminder['due_display']}.",
        message=f"Reminder scheduled for {reminder['due_display']}.",
        reminder=reminder,
    )
    return {
        "message": f"Reminder scheduled for {reminder['due_display']}.",
        "reminder": reminder,
    }


@router.post("/{reminder_id}/recurrence")
def set_recurrence(reminder_id: int, payload: RecurrenceRequest, request: Request) -> dict:
    reminders_service = request.app.state.reminders_service
    existing = reminders_service.get_reminder(reminder_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Reminder not found.")
    if existing.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Only pending reminders can be made recurring.")
    if not existing.get("due_at"):
        raise HTTPException(status_code=400, detail="Schedule the reminder before enabling recurrence.")

    recurrence_rule, recurrence_label = _resolve_recurrence_preset(payload.preset)
    try:
        reminder = reminders_service.set_recurrence(
            reminder_id,
            recurrence_rule=recurrence_rule,
            recurrence_label=recurrence_label,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found.")

    message = f"Reminder will repeat {recurrence_label}."
    _record_reminder_update(
        request=request,
        reminder_id=reminder_id,
        tool_name="set_recurrence",
        summary=f"Set reminder {reminder_id} to repeat {recurrence_label}.",
        message=message,
        reminder=reminder,
    )
    return {
        "message": message,
        "reminder": reminder,
    }


@router.post("/{reminder_id}/recurrence/clear")
def clear_recurrence(reminder_id: int, request: Request) -> dict:
    reminders_service = request.app.state.reminders_service
    existing = reminders_service.get_reminder(reminder_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Reminder not found.")
    if existing.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Only pending reminders can be updated here.")

    reminder = reminders_service.clear_recurrence(reminder_id)
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found.")

    _record_reminder_update(
        request=request,
        reminder_id=reminder_id,
        tool_name="clear_recurrence",
        summary=f"Clear recurrence for reminder {reminder_id}.",
        message="Reminder recurrence removed.",
        reminder=reminder,
    )
    return {
        "message": "Reminder recurrence removed.",
        "reminder": reminder,
    }


@router.post("/archive-completed")
def archive_completed_reminders(request: Request) -> dict:
    reminders_service = request.app.state.reminders_service
    archived_count = reminders_service.archive_completed_reminders()
    _record_bulk_reminder_update(
        request=request,
        tool_name="archive_completed_reminders",
        summary="Archive completed reminders.",
        message=f"Archived {archived_count} completed reminders.",
        result={"archived_count": archived_count},
    )
    return {
        "message": f"Archived {archived_count} completed reminders.",
        "archived_count": archived_count,
    }


@router.post("/restore-archived")
def restore_archived_reminders(request: Request) -> dict:
    reminders_service = request.app.state.reminders_service
    restored_count = reminders_service.restore_archived_reminders()
    _record_bulk_reminder_update(
        request=request,
        tool_name="restore_archived_reminders",
        summary="Restore archived reminders.",
        message=f"Restored {restored_count} archived reminders.",
        result={"restored_count": restored_count},
    )
    return {
        "message": f"Restored {restored_count} archived reminders.",
        "restored_count": restored_count,
    }


@router.post("/purge-archived")
def purge_archived_reminders(request: Request) -> dict:
    reminders_service = request.app.state.reminders_service
    deleted_count = reminders_service.purge_archived_reminders()
    _record_bulk_reminder_update(
        request=request,
        tool_name="purge_archived_reminders",
        summary="Delete archived reminders permanently.",
        message=f"Deleted {deleted_count} archived reminders permanently.",
        result={"deleted_count": deleted_count},
        permission_level=PermissionLevel.SENSITIVE,
    )
    return {
        "message": f"Deleted {deleted_count} archived reminders permanently.",
        "deleted_count": deleted_count,
    }


def _record_reminder_update(
    *,
    request: Request,
    reminder_id: int,
    tool_name: str,
    summary: str,
    message: str,
    reminder: dict,
) -> None:
    audit_logger = request.app.state.audit_logger
    action = ProposedAction(
        action_id=str(uuid4()),
        session_id="dashboard",
        tool_name=tool_name,
        category=ToolCategory.PRODUCTIVITY,
        permission_level=PermissionLevel.LOW_RISK,
        approval_mode=ApprovalMode.NONE,
        summary=summary,
        arguments={"reminder_id": reminder_id},
    )
    decision = PolicyDecision(
        allowed=True,
        requires_confirmation=False,
        approval_mode=ApprovalMode.NONE,
        reason="The user initiated this reminder update directly from the dashboard.",
    )
    result = ToolResult(success=True, message=message, data=reminder)
    audit_logger.record(action=action, status=ActionStatus.EXECUTED, decision=decision, result=result)


def _record_bulk_reminder_update(
    *,
    request: Request,
    tool_name: str,
    summary: str,
    message: str,
    result: dict,
    arguments: dict | None = None,
    permission_level: PermissionLevel = PermissionLevel.LOW_RISK,
) -> None:
    audit_logger = request.app.state.audit_logger
    action = ProposedAction(
        action_id=str(uuid4()),
        session_id="dashboard",
        tool_name=tool_name,
        category=ToolCategory.PRODUCTIVITY,
        permission_level=permission_level,
        approval_mode=ApprovalMode.NONE,
        summary=summary,
        arguments=arguments or {},
    )
    decision = PolicyDecision(
        allowed=True,
        requires_confirmation=False,
        approval_mode=ApprovalMode.NONE,
        reason="The user initiated this reminder update directly from the dashboard.",
    )
    tool_result = ToolResult(success=True, message=message, data=result)
    audit_logger.record(action=action, status=ActionStatus.EXECUTED, decision=decision, result=tool_result)


def _resolve_snooze_preset(preset: str) -> tuple[str, str]:
    normalized = preset.strip().lower()
    now = _local_now()

    if normalized in {"hour", "1h", "one_hour"}:
        due_time = now + timedelta(hours=1)
        return due_time.isoformat(), "in 1 hour"

    if normalized in {"tomorrow", "tomorrow_morning"}:
        due_time = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
        return due_time.isoformat(), "tomorrow at 9am"

    raise HTTPException(status_code=400, detail="Unsupported snooze preset.")


def _resolve_recurrence_preset(preset: str) -> tuple[str, str]:
    normalized = preset.strip().lower()
    if normalized == "daily":
        return "daily", "every day"
    if normalized in {"weekdays", "weekday"}:
        return "weekdays", "every weekday"
    if normalized == "weekly":
        return "weekly", "every week"
    raise HTTPException(status_code=400, detail="Unsupported recurrence preset.")


def _local_now() -> datetime:
    return datetime.now().astimezone()


def _normalize_due_at(value: str) -> str:
    raw = value.strip()
    if not raw:
        raise HTTPException(status_code=400, detail="A reminder date and time is required.")

    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid reminder date and time.") from exc

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=_local_now().tzinfo)
    return parsed.isoformat()

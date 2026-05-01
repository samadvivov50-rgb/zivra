from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.models import ActionStatus, ApprovalMode, PermissionLevel, ProposedAction, ToolCategory, ToolResult
from app.services.policy import PolicyDecision

router = APIRouter(prefix="/workflows", tags=["workflows"])


class CreateWorkflowRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    prompt: str = Field(min_length=1, max_length=600)
    schedule_type: str = Field(default="manual")
    interval_hours: int | None = Field(default=None, ge=1, le=24)
    run_hour: int | None = Field(default=None, ge=0, le=23)
    run_minute: int | None = Field(default=None, ge=0, le=59)
    run_weekday: int | None = Field(default=None, ge=0, le=6)
    active: bool = True


class ToggleWorkflowRequest(BaseModel):
    active: bool


@router.get("")
def list_workflows(request: Request, limit: int = 20) -> dict:
    workflow_service = request.app.state.workflow_service
    workflow_service.dispatch_due()
    return {
        "workflows": workflow_service.list_workflows(limit=min(max(limit, 1), 50)),
        "summary": workflow_service.summary(),
    }


@router.get("/tasks")
def list_workflow_tasks(request: Request, limit: int = 20, status: str = "") -> dict:
    workflow_service = request.app.state.workflow_service
    workflow_service.dispatch_due()
    return {
        "tasks": workflow_service.list_tasks(limit=min(max(limit, 1), 50), status=status or None),
        "summary": workflow_service.summary(),
    }


@router.post("")
def create_workflow(payload: CreateWorkflowRequest, request: Request) -> dict:
    workflow_service = request.app.state.workflow_service
    try:
        workflow = workflow_service.create_workflow(
            name=payload.name,
            prompt=payload.prompt,
            schedule_type=payload.schedule_type,
            interval_hours=payload.interval_hours,
            run_hour=payload.run_hour,
            run_minute=payload.run_minute,
            run_weekday=payload.run_weekday,
            active=payload.active,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    message = f"Saved workflow '{workflow['name']}' with schedule {workflow['schedule_label']}."
    _record_workflow_event(
        request=request,
        tool_name="create_workflow",
        summary=f"Create workflow {workflow['name']}.",
        message=message,
        workflow=workflow,
        permission_level=PermissionLevel.LOW_RISK,
        decision_reason="The user created a local scheduled workflow from the dashboard.",
    )
    return {
        "message": message,
        "workflow": workflow,
        "summary": workflow_service.summary(),
    }


@router.post("/{workflow_id}/toggle")
def toggle_workflow(workflow_id: int, payload: ToggleWorkflowRequest, request: Request) -> dict:
    workflow_service = request.app.state.workflow_service
    workflow = workflow_service.set_workflow_active(workflow_id, active=payload.active)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found.")
    message = (
        f"Workflow '{workflow['name']}' resumed."
        if workflow["active"]
        else f"Workflow '{workflow['name']}' paused."
    )
    _record_workflow_event(
        request=request,
        tool_name="toggle_workflow",
        summary=f"{'Resume' if workflow['active'] else 'Pause'} workflow {workflow['name']}.",
        message=message,
        workflow=workflow,
        permission_level=PermissionLevel.LOW_RISK,
        decision_reason="The user changed a workflow schedule directly from the dashboard.",
    )
    return {
        "message": message,
        "workflow": workflow,
        "summary": workflow_service.summary(),
    }


@router.post("/{workflow_id}/queue")
def queue_workflow_now(workflow_id: int, request: Request) -> dict:
    workflow_service = request.app.state.workflow_service
    task = workflow_service.queue_workflow_now(workflow_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Workflow not found.")
    message = f"Queued workflow '{task['workflow_name']}' for execution."
    _record_task_event(
        request=request,
        tool_name="queue_workflow_task",
        summary=f"Queue workflow {task['workflow_name']}.",
        message=message,
        task=task,
        permission_level=PermissionLevel.LOW_RISK,
        decision_reason="The user queued a workflow task directly from the dashboard.",
    )
    return {
        "message": message,
        "task": task,
        "summary": workflow_service.summary(),
    }


@router.post("/tasks/{task_id}/run")
def run_workflow_task(task_id: int, request: Request) -> dict:
    workflow_service = request.app.state.workflow_service
    orchestrator = request.app.state.orchestrator
    try:
        task_result = workflow_service.run_task(
            task_id,
            runner=lambda prompt, session_id: orchestrator.handle_message(prompt, session_id=session_id).to_dict(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if task_result is None:
        raise HTTPException(status_code=404, detail="Workflow task not found.")
    task = task_result["task"]
    status = ActionStatus.EXECUTED if task["status"] != "failed" else ActionStatus.FAILED
    success = task["status"] != "failed"
    message = _task_run_message(task)
    _record_task_event(
        request=request,
        tool_name="run_workflow_task",
        summary=f"Run queued task {task['id']} for workflow {task['workflow_name']}.",
        message=message,
        task=task,
        permission_level=PermissionLevel.LOW_RISK,
        decision_reason="The user executed a queued workflow task from the dashboard.",
        status=status,
        success=success,
    )
    return {
        "message": message,
        "task": task,
        "response": task_result["response"],
        "summary": workflow_service.summary(),
    }


@router.post("/tasks/{task_id}/cancel")
def cancel_workflow_task(task_id: int, request: Request) -> dict:
    workflow_service = request.app.state.workflow_service
    try:
        task = workflow_service.cancel_task(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if task is None:
        raise HTTPException(status_code=404, detail="Workflow task not found.")
    message = f"Canceled queued task {task['id']} for workflow '{task['workflow_name']}'."
    _record_task_event(
        request=request,
        tool_name="cancel_workflow_task",
        summary=f"Cancel queued task {task['id']} for workflow {task['workflow_name']}.",
        message=message,
        task=task,
        permission_level=PermissionLevel.LOW_RISK,
        decision_reason="The user canceled a queued workflow task from the dashboard.",
    )
    return {
        "message": message,
        "task": task,
        "summary": workflow_service.summary(),
    }


@router.post("/tasks/{task_id}/retry")
def retry_workflow_task(task_id: int, request: Request) -> dict:
    workflow_service = request.app.state.workflow_service
    try:
        task = workflow_service.retry_task(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if task is None:
        raise HTTPException(status_code=404, detail="Workflow task not found.")
    message = f"Re-queued workflow '{task['workflow_name']}' for recovery."
    _record_task_event(
        request=request,
        tool_name="retry_workflow_task",
        summary=f"Retry workflow {task['workflow_name']} from task {task['id']}.",
        message=message,
        task=task,
        permission_level=PermissionLevel.LOW_RISK,
        decision_reason="The user re-queued a workflow task for recovery from the dashboard.",
    )
    return {
        "message": message,
        "task": task,
        "summary": workflow_service.summary(),
    }


@router.post("/supervisor/run")
def run_workflow_supervisor(request: Request) -> dict:
    cycle = run_supervisor_cycle_for_request(request)
    return {
        "message": _supervisor_cycle_message(cycle),
        "cycle": cycle,
        "summary": request.app.state.workflow_service.summary(),
    }


def _task_run_message(task: dict) -> str:
    if task["status"] == "approval_pending":
        return (
            f"Workflow '{task['workflow_name']}' ran and staged {task['pending_action_count']} "
            f"approval{'s' if task['pending_action_count'] != 1 else ''}."
        )
    if task["status"] == "failed":
        return f"Workflow '{task['workflow_name']}' failed: {task['error'] or 'Unknown error.'}"
    if task["status"] == "canceled":
        return f"Workflow '{task['workflow_name']}' was canceled before it ran."
    return f"Workflow '{task['workflow_name']}' completed."


def _supervisor_cycle_message(cycle: dict) -> str:
    if not cycle.get("enabled"):
        if cycle.get("dispatched_count"):
            return (
                f"Supervisor is paused. {cycle['dispatched_count']} scheduled "
                f"task{'s' if cycle['dispatched_count'] != 1 else ''} were queued for later review."
            )
        return "Supervisor is paused. Queued workflow tasks remain available for manual review."

    run_count = int(cycle.get("run_count") or 0)
    paused_count = len(cycle.get("paused_workflows") or [])
    if run_count == 0 and not cycle.get("dispatched_count"):
        return "Supervisor cycle found no queued workflow tasks."

    segments: list[str] = []
    if cycle.get("dispatched_count"):
        segments.append(
            f"Queued {cycle['dispatched_count']} scheduled task{'s' if cycle['dispatched_count'] != 1 else ''}"
        )
    if run_count:
        segments.append(f"ran {run_count} queued task{'s' if run_count != 1 else ''}")
    if paused_count:
        segments.append(
            f"paused {paused_count} workflow{'s' if paused_count != 1 else ''} after a failure"
        )
    if not segments:
        segments.append("Supervisor cycle completed without running any tasks")

    reason = str(cycle.get("stopped_reason") or "")
    if reason == "approval_limit_reached":
        segments.append("stopped at the approval limit")
    elif reason == "cycle_limit_reached":
        segments.append("reached the cycle limit")
    elif reason == "workflow_failed":
        segments.append("stopped after a workflow failure")
    return ". ".join(segment[:1].upper() + segment[1:] for segment in segments) + "."


def run_supervisor_cycle_for_request(request: Request) -> dict:
    workflow_service = request.app.state.workflow_service
    settings = request.app.state.settings
    orchestrator = request.app.state.orchestrator

    cycle = workflow_service.supervisor_cycle(
        runner=lambda prompt, session_id: orchestrator.handle_message(prompt, session_id=session_id).to_dict(),
        enabled=settings.workflow_supervisor_enabled,
        max_tasks=settings.workflow_supervisor_max_tasks_per_cycle,
        max_pending_approvals=settings.workflow_supervisor_max_pending_approvals,
        pause_workflows_on_failure=settings.workflow_supervisor_pause_on_failure,
    )

    for task in cycle.get("executed_tasks", []):
        status = ActionStatus.EXECUTED if task["status"] != "failed" else ActionStatus.FAILED
        _record_task_event(
            request=request,
            tool_name="supervisor_run_workflow_task",
            summary=f"Supervisor ran task {task['id']} for workflow {task['workflow_name']}.",
            message=_task_run_message(task),
            task=task,
            permission_level=PermissionLevel.LOW_RISK,
            decision_reason="The local workflow supervisor ran a queued task within configured limits.",
            status=status,
            success=task["status"] != "failed",
        )

    for workflow in cycle.get("paused_workflows", []):
        _record_workflow_event(
            request=request,
            tool_name="supervisor_pause_workflow",
            summary=f"Pause workflow {workflow['name']} after supervisor failure.",
            message=f"Workflow '{workflow['name']}' was paused after a supervisor-run task failed.",
            workflow=workflow,
            permission_level=PermissionLevel.LOW_RISK,
            decision_reason="The local workflow supervisor paused a workflow after a failed task.",
        )

    return {
        "enabled": bool(cycle.get("enabled")),
        "dispatched_count": int(cycle.get("dispatched_count") or 0),
        "run_count": int(cycle.get("run_count") or 0),
        "stopped_reason": str(cycle.get("stopped_reason") or ""),
        "tasks": [workflow_service.audit_task_payload(task) for task in cycle.get("executed_tasks", [])],
        "paused_workflows": [
            workflow_service.audit_workflow_payload(workflow) for workflow in cycle.get("paused_workflows", [])
        ],
    }


def _record_workflow_event(
    *,
    request: Request,
    tool_name: str,
    summary: str,
    message: str,
    workflow: dict,
    permission_level: PermissionLevel,
    decision_reason: str,
    status: ActionStatus = ActionStatus.EXECUTED,
    success: bool = True,
) -> None:
    workflow_service = request.app.state.workflow_service
    action = ProposedAction(
        action_id=str(uuid4()),
        session_id="dashboard",
        tool_name=tool_name,
        category=ToolCategory.PRODUCTIVITY,
        permission_level=permission_level,
        approval_mode=ApprovalMode.NONE,
        summary=summary,
        arguments={
            "workflow_id": workflow["id"],
            "name": workflow["name"],
            "schedule_type": workflow["schedule_type"],
        },
    )
    decision = PolicyDecision(
        allowed=True,
        requires_confirmation=False,
        approval_mode=ApprovalMode.NONE,
        reason=decision_reason,
    )
    result = ToolResult(
        success=success,
        message=message,
        data={"workflow": workflow_service.audit_workflow_payload(workflow)},
    )
    request.app.state.audit_logger.record(action=action, status=status, decision=decision, result=result)


def _record_task_event(
    *,
    request: Request,
    tool_name: str,
    summary: str,
    message: str,
    task: dict,
    permission_level: PermissionLevel,
    decision_reason: str,
    status: ActionStatus = ActionStatus.EXECUTED,
    success: bool = True,
) -> None:
    workflow_service = request.app.state.workflow_service
    action = ProposedAction(
        action_id=str(uuid4()),
        session_id="dashboard",
        tool_name=tool_name,
        category=ToolCategory.PRODUCTIVITY,
        permission_level=permission_level,
        approval_mode=ApprovalMode.NONE,
        summary=summary,
        arguments={
            "task_id": task["id"],
            "workflow_id": task["workflow_id"],
            "workflow_name": task["workflow_name"],
            "source": task["source"],
        },
    )
    decision = PolicyDecision(
        allowed=True,
        requires_confirmation=False,
        approval_mode=ApprovalMode.NONE,
        reason=decision_reason,
    )
    result = ToolResult(
        success=success,
        message=message,
        data={"task": workflow_service.audit_task_payload(task)},
    )
    request.app.state.audit_logger.record(action=action, status=status, decision=decision, result=result)

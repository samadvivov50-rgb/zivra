from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.models import ActionStatus, ApprovalMode, PermissionLevel, ProposedAction, ToolCategory, ToolResult
from app.services.clipboard import ClipboardUnavailableError
from app.services.policy import PolicyDecision

router = APIRouter(prefix="/clipboard", tags=["clipboard"])


class UpdateClipboardRequest(BaseModel):
    text: str


@router.get("")
def read_clipboard(request: Request) -> dict:
    clipboard_service = request.app.state.clipboard_service
    try:
        text = clipboard_service.read_text()
    except ClipboardUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    metadata = clipboard_service.build_metadata(text)
    message = "Clipboard loaded from the local desktop."
    _record_clipboard_event(
        request=request,
        tool_name="read_clipboard",
        permission_level=PermissionLevel.SENSITIVE,
        summary="Read the current clipboard from the dashboard.",
        reason="The user explicitly opened the clipboard from the dashboard.",
        message=message,
        arguments={"source": "dashboard"},
        result_data={"clipboard": metadata},
    )
    return {
        "message": message,
        "text": text,
        "metadata": metadata,
    }


@router.post("")
def write_clipboard(payload: UpdateClipboardRequest, request: Request) -> dict:
    clipboard_service = request.app.state.clipboard_service
    try:
        text = clipboard_service.write_text(payload.text)
    except ClipboardUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    metadata = clipboard_service.build_metadata(text)
    message = "Clipboard cleared from the dashboard." if metadata["empty"] else "Clipboard updated from the dashboard."
    _record_clipboard_event(
        request=request,
        tool_name="write_clipboard",
        permission_level=PermissionLevel.LOW_RISK,
        summary="Write text to the clipboard from the dashboard.",
        reason="The user explicitly updated the clipboard from the dashboard.",
        message=message,
        arguments={"source": "dashboard", "length": metadata["length"]},
        result_data={"clipboard": metadata},
    )
    return {
        "message": message,
        "metadata": metadata,
    }


def _record_clipboard_event(
    *,
    request: Request,
    tool_name: str,
    permission_level: PermissionLevel,
    summary: str,
    reason: str,
    message: str,
    arguments: dict,
    result_data: dict,
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
        arguments=arguments,
    )
    decision = PolicyDecision(
        allowed=True,
        requires_confirmation=False,
        approval_mode=ApprovalMode.NONE,
        reason=reason,
    )
    result = ToolResult(success=True, message=message, data=result_data)
    audit_logger.record(action=action, status=ActionStatus.EXECUTED, decision=decision, result=result)

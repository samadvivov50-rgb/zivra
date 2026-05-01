from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.models import ActionStatus, ApprovalMode, PermissionLevel, ProposedAction, ToolCategory, ToolResult
from app.services.policy import PolicyDecision

router = APIRouter(prefix="/notes", tags=["notes"])


class UpdateNoteRequest(BaseModel):
    content: str


@router.get("")
def list_notes(request: Request, limit: int = 8) -> dict:
    notes_service = request.app.state.notes_service
    return {
        "notes": notes_service.list_recent(limit=limit),
    }


@router.get("/search")
def search_notes(request: Request, q: str = "", limit: int = 8) -> dict:
    notes_service = request.app.state.notes_service
    return {
        "query": q,
        "notes": notes_service.search(query=q, limit=limit),
    }


@router.get("/{name}")
def read_note(name: str, request: Request) -> dict:
    notes_service = request.app.state.notes_service
    note = notes_service.read_note(name)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found.")
    return note


@router.put("/{name}")
def update_note(name: str, payload: UpdateNoteRequest, request: Request) -> dict:
    notes_service = request.app.state.notes_service
    note = notes_service.update_note(name, content=payload.content)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found.")

    message = f"Saved changes to '{note['title']}'."
    _record_note_update(
        request=request,
        note_name=note["name"],
        tool_name="update_note",
        summary=f"Update note '{note['name']}'.",
        message=message,
        note=note,
    )
    return {
        "message": message,
        "note": note,
    }


def _record_note_update(
    *,
    request: Request,
    note_name: str,
    tool_name: str,
    summary: str,
    message: str,
    note: dict,
) -> None:
    audit_logger = request.app.state.audit_logger
    action = ProposedAction(
        action_id=str(uuid4()),
        session_id="dashboard",
        tool_name=tool_name,
        category=ToolCategory.FILES,
        permission_level=PermissionLevel.SENSITIVE,
        approval_mode=ApprovalMode.NONE,
        summary=summary,
        arguments={"name": note_name},
    )
    decision = PolicyDecision(
        allowed=True,
        requires_confirmation=False,
        approval_mode=ApprovalMode.NONE,
        reason="The user edited this note directly from the dashboard.",
    )
    result = ToolResult(success=True, message=message, data=note)
    audit_logger.record(action=action, status=ActionStatus.EXECUTED, decision=decision, result=result)

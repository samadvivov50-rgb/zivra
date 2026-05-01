from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.services.orchestrator import AssistantOrchestrator

router = APIRouter(prefix="/assistant", tags=["assistant"])


class MessageRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str = Field(default="default")


class ConfirmationRequest(BaseModel):
    confirmation: str | None = None


class RejectionRequest(BaseModel):
    reason: str | None = None


def _get_orchestrator(request: Request) -> AssistantOrchestrator:
    return request.app.state.orchestrator


@router.post("/message")
def handle_message(payload: MessageRequest, request: Request) -> dict:
    orchestrator = _get_orchestrator(request)
    return orchestrator.handle_message(payload.message, session_id=payload.session_id).to_dict()


@router.post("/actions/{action_id}/confirm")
def confirm_action(action_id: str, payload: ConfirmationRequest, request: Request) -> dict:
    orchestrator = _get_orchestrator(request)
    return orchestrator.confirm_action(action_id, confirmation=payload.confirmation).to_dict()


@router.post("/action-groups/{group_id}/confirm")
def confirm_action_group(group_id: str, payload: ConfirmationRequest, request: Request) -> dict:
    orchestrator = _get_orchestrator(request)
    return orchestrator.confirm_action_group(group_id, confirmation=payload.confirmation).to_dict()


@router.post("/actions/{action_id}/reject")
def reject_action(action_id: str, payload: RejectionRequest, request: Request) -> dict:
    orchestrator = _get_orchestrator(request)
    return orchestrator.reject_action(action_id, reason=payload.reason).to_dict()


@router.post("/action-groups/{group_id}/reject")
def reject_action_group(group_id: str, payload: RejectionRequest, request: Request) -> dict:
    orchestrator = _get_orchestrator(request)
    return orchestrator.reject_action_group(group_id, reason=payload.reason).to_dict()


@router.get("/pending")
def pending_actions(request: Request) -> dict:
    orchestrator = _get_orchestrator(request)
    return {
        "count": orchestrator.pending_count,
        "actions": orchestrator.list_pending_actions(),
    }


@router.get("/sessions")
def list_sessions(request: Request, limit: int = 12) -> dict:
    orchestrator = _get_orchestrator(request)
    normalized_limit = min(max(limit, 1), 50)
    return {
        "sessions": orchestrator.memory.list_sessions(limit=normalized_limit),
    }


@router.get("/sessions/{session_id}/history")
def session_history(session_id: str, request: Request, limit: int = 12) -> dict:
    orchestrator = _get_orchestrator(request)
    return {
        "session_id": session_id,
        "history": orchestrator.recent_history(session_id=session_id, limit=limit),
    }


@router.post("/sessions/{session_id}/clear")
def clear_session(session_id: str, request: Request) -> dict:
    orchestrator = _get_orchestrator(request)
    orchestrator.memory.clear_session(session_id=session_id)
    return {
        "session_id": session_id,
        "message": "Session history cleared.",
    }


@router.post("/sessions/clear-all")
def clear_all_sessions(request: Request) -> dict:
    orchestrator = _get_orchestrator(request)
    orchestrator.memory.clear_all()
    return {
        "message": "All stored session history cleared.",
    }

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from app.models import ActionStatus, ApprovalMode, PermissionLevel, ProposedAction, ToolCategory, ToolResult
from app.services.policy import PolicyDecision

router = APIRouter(prefix="/messages", tags=["messages"])


class WhatsAppDraftRequest(BaseModel):
    to: str = Field(min_length=7)
    body: str = Field(min_length=1)
    source: str = Field(default="dashboard")


@router.get("")
def list_messages(request: Request, limit: int = 12, status: str = "", direction: str = "") -> dict:
    messaging_service = request.app.state.messaging_service
    return {
        "messages": messaging_service.list_messages(
            limit=min(max(limit, 1), 50),
            status=status or None,
            direction=direction or None,
        ),
        "summary": messaging_service.summary(),
        "delivery": messaging_service.delivery_status(),
    }


@router.post("/whatsapp/drafts")
def create_whatsapp_draft(payload: WhatsAppDraftRequest, request: Request) -> dict:
    messaging_service = request.app.state.messaging_service
    try:
        message = messaging_service.create_whatsapp_draft(
            to_number=payload.to,
            body=payload.body,
            source=payload.source,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    response_message = f"Saved a local WhatsApp draft for {message['to']}."
    _record_message_event(
        request=request,
        tool_name="draft_whatsapp_message",
        summary=f"Draft a WhatsApp message for {message['to']}.",
        message=response_message,
        outbox_message=message,
        permission_level=PermissionLevel.LOW_RISK,
        decision_reason="The user saved this WhatsApp draft directly from the dashboard.",
    )
    return {
        "message": response_message,
        "outbox_message": message,
        "summary": messaging_service.summary(),
        "delivery": messaging_service.delivery_status(),
    }


@router.post("/{message_id}/send")
def send_whatsapp_message(message_id: int, request: Request) -> dict:
    messaging_service = request.app.state.messaging_service
    message = messaging_service.send_whatsapp_draft(message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="WhatsApp draft not found.")

    summary = (
        f"Send a WhatsApp message to {message['to']} through Meta Cloud API."
        if message.get("provider") == "cloud_api" and message["status"] in {"sent", "delivered", "read"}
        else f"Open a WhatsApp compose handoff for {message['to']}."
    )
    if message["status"] == "failed":
        response_message = messaging_service.format_dispatch_message(message)
        _record_message_event(
            request=request,
            tool_name="send_whatsapp_message",
            summary=summary,
            message=response_message,
            outbox_message=message,
            permission_level=PermissionLevel.SENSITIVE,
            decision_reason="The user explicitly dispatched this WhatsApp message from the dashboard.",
            status=ActionStatus.FAILED,
            success=False,
        )
        raise HTTPException(status_code=502, detail=response_message)

    response_message = messaging_service.format_dispatch_message(message)
    _record_message_event(
        request=request,
        tool_name="send_whatsapp_message",
        summary=summary,
        message=response_message,
        outbox_message=message,
        permission_level=PermissionLevel.SENSITIVE,
        decision_reason="The user explicitly dispatched this WhatsApp message from the dashboard.",
    )
    return {
        "message": response_message,
        "outbox_message": message,
        "summary": messaging_service.summary(),
        "delivery": messaging_service.delivery_status(),
    }


@router.get("/whatsapp/webhook", response_class=PlainTextResponse)
def verify_whatsapp_webhook(
    request: Request,
    hub_mode: str = Query(default="", alias="hub.mode"),
    hub_verify_token: str = Query(default="", alias="hub.verify_token"),
    hub_challenge: str = Query(default="", alias="hub.challenge"),
) -> str:
    messaging_service = request.app.state.messaging_service
    try:
        return messaging_service.verify_whatsapp_webhook(
            mode=hub_mode,
            verify_token=hub_verify_token,
            challenge=hub_challenge,
        )
    except ValueError as exc:
        detail = str(exc)
        if "not configured" in detail.lower():
            raise HTTPException(status_code=503, detail=detail) from exc
        raise HTTPException(status_code=403, detail=detail) from exc


@router.post("/whatsapp/webhook")
async def receive_whatsapp_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None, alias="X-Hub-Signature-256"),
) -> dict:
    messaging_service = request.app.state.messaging_service
    raw_body = await request.body()
    try:
        result = messaging_service.receive_whatsapp_webhook(raw_body, signature_header=x_hub_signature_256)
    except ValueError as exc:
        detail = str(exc)
        status_code = 403 if "signature" in detail.lower() else 400
        if "not configured" in detail.lower():
            status_code = 503
        raise HTTPException(status_code=status_code, detail=detail) from exc

    return {
        "message": "WhatsApp webhook processed.",
        **result,
    }


def _record_message_event(
    *,
    request: Request,
    tool_name: str,
    summary: str,
    message: str,
    outbox_message: dict,
    permission_level: PermissionLevel,
    decision_reason: str,
    status: ActionStatus = ActionStatus.EXECUTED,
    success: bool = True,
) -> None:
    audit_logger = request.app.state.audit_logger
    messaging_service = request.app.state.messaging_service
    action = ProposedAction(
        action_id=str(uuid4()),
        session_id="dashboard",
        tool_name=tool_name,
        category=ToolCategory.COMMUNICATION,
        permission_level=permission_level,
        approval_mode=ApprovalMode.NONE,
        summary=summary,
        arguments={
            "message_id": outbox_message["id"],
            "to": outbox_message["to"],
            "channel": outbox_message["channel"],
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
        data={"message": messaging_service.audit_payload(outbox_message)},
    )
    audit_logger.record(action=action, status=status, decision=decision, result=result)

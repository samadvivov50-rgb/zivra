from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.models import ActionStatus, ApprovalMode, PermissionLevel, ProposedAction, ToolCategory, ToolResult
from app.services.policy import PolicyDecision

router = APIRouter(prefix="/emails", tags=["emails"])


class EmailDraftRequest(BaseModel):
    to: str = Field(default="recipient@example.com")
    subject: str = Field(default="Draft from Zivra")
    body: str = Field(default="")
    source: str = Field(default="dashboard")


@router.get("")
def list_emails(request: Request, limit: int = 12, status: str = "") -> dict:
    email_service = request.app.state.email_service
    return {
        "emails": email_service.list_emails(limit=min(max(limit, 1), 50), status=status or None),
        "summary": email_service.summary(),
        "delivery": email_service.delivery_status(),
    }


@router.post("/drafts")
def create_email_draft(payload: EmailDraftRequest, request: Request) -> dict:
    email_service = request.app.state.email_service
    email = email_service.create_draft(
        to_address=payload.to,
        subject=payload.subject,
        body=payload.body,
        source=payload.source,
    )
    message = f"Saved a local email draft for {email['to']}."
    _record_email_event(
        request=request,
        tool_name="draft_email",
        summary=f"Draft an email with subject '{email['subject']}'.",
        message=message,
        email=email,
        permission_level=PermissionLevel.LOW_RISK,
        decision_reason="The user saved this email draft directly from the dashboard.",
    )
    return {
        "message": message,
        "email": email,
        "summary": email_service.summary(),
        "delivery": email_service.delivery_status(),
    }


@router.post("/{email_id}/send")
def send_email(email_id: int, request: Request) -> dict:
    email_service = request.app.state.email_service
    try:
        email = email_service.send_draft(email_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if email is None:
        raise HTTPException(status_code=404, detail="Email draft not found.")

    if email["status"] == "failed":
        message = f"Email delivery failed: {email['error'] or 'Unknown delivery error.'}"
        _record_email_event(
            request=request,
            tool_name="send_email",
            summary=f"Send email {email_id} to {email['to']}.",
            message=message,
            email=email,
            permission_level=PermissionLevel.SENSITIVE,
            decision_reason="The user explicitly sent this email from the dashboard.",
            status=ActionStatus.FAILED,
            success=False,
        )
        raise HTTPException(status_code=502, detail=message)

    message = f"Sent the email to {email['to']}."
    _record_email_event(
        request=request,
        tool_name="send_email",
        summary=f"Send email {email_id} to {email['to']}.",
        message=message,
        email=email,
        permission_level=PermissionLevel.SENSITIVE,
        decision_reason="The user explicitly sent this email from the dashboard.",
    )
    return {
        "message": message,
        "email": email,
        "summary": email_service.summary(),
        "delivery": email_service.delivery_status(),
    }


def _record_email_event(
    *,
    request: Request,
    tool_name: str,
    summary: str,
    message: str,
    email: dict,
    permission_level: PermissionLevel,
    decision_reason: str,
    status: ActionStatus = ActionStatus.EXECUTED,
    success: bool = True,
) -> None:
    audit_logger = request.app.state.audit_logger
    email_service = request.app.state.email_service
    action = ProposedAction(
        action_id=str(uuid4()),
        session_id="dashboard",
        tool_name=tool_name,
        category=ToolCategory.COMMUNICATION,
        permission_level=permission_level,
        approval_mode=ApprovalMode.NONE,
        summary=summary,
        arguments={"email_id": email["id"], "to": email["to"], "subject": email["subject"]},
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
        data={"email": email_service.audit_payload(email)},
    )
    audit_logger.record(action=action, status=status, decision=decision, result=result)

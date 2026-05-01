from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.models import ActionStatus, ApprovalMode, PermissionLevel, ProposedAction, ToolCategory, ToolResult
from app.services.policy import PolicyDecision

router = APIRouter(prefix="/content", tags=["content"])


class ContentPackageRequest(BaseModel):
    topic: str = Field(min_length=1)
    audience: str = ""
    context: str = ""


@router.post("/youtube-seo")
def build_content_package(payload: ContentPackageRequest, request: Request) -> dict:
    content_service = request.app.state.content_service
    generated = content_service.build_package(
        topic=payload.topic,
        audience=payload.audience,
        context=payload.context,
    )

    _record_content_event(
        request=request,
        summary=f"Generate a YouTube and SEO package for '{generated['topic']}' from the dashboard.",
        message=f"Generated a YouTube and SEO package for '{generated['topic']}' from the dashboard.",
        payload=content_service.audit_payload(generated),
        arguments={
            "topic": generated["topic"],
            "audience": generated.get("audience", ""),
            "context_length": len(payload.context or ""),
        },
    )
    return generated


def _record_content_event(
    *,
    request: Request,
    summary: str,
    message: str,
    payload: dict,
    arguments: dict,
) -> None:
    audit_logger = request.app.state.audit_logger
    action = ProposedAction(
        action_id=str(uuid4()),
        session_id="dashboard",
        tool_name="generate_content_package",
        category=ToolCategory.COMMUNICATION,
        permission_level=PermissionLevel.SAFE_READ,
        approval_mode=ApprovalMode.NONE,
        summary=summary,
        arguments=arguments,
    )
    decision = PolicyDecision(
        allowed=True,
        requires_confirmation=False,
        approval_mode=ApprovalMode.NONE,
        reason="The user explicitly used the dashboard creator helper.",
    )
    result = ToolResult(
        success=True,
        message=message,
        data={"content": payload},
    )
    audit_logger.record(action=action, status=ActionStatus.EXECUTED, decision=decision, result=result)

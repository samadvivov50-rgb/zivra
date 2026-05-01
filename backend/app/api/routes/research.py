from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Request

from app.models import ActionStatus, ApprovalMode, PermissionLevel, ProposedAction, ToolCategory, ToolResult
from app.services.policy import PolicyDecision
from app.services.webpages import WebPageUnavailableError
from app.services.websearch import WebSearchUnavailableError

router = APIRouter(prefix="/research", tags=["research"])


@router.get("/summary")
def research_summary(
    request: Request,
    q: str = Query(min_length=1),
    search_limit: int = 5,
    source_limit: int = 3,
) -> dict:
    research_service = request.app.state.research_service
    try:
        payload = research_service.build_summary(
            q,
            search_limit=min(max(search_limit, 1), 10),
            source_limit=min(max(source_limit, 1), 5),
        )
    except (WebSearchUnavailableError, WebPageUnavailableError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    _record_research_event(
        request=request,
        summary=f"Build a research brief for '{payload['query']}' from the dashboard.",
        message=f"Built a research brief for '{payload['query']}' from the dashboard.",
        payload=research_service.audit_payload(payload),
        arguments={
            "query": payload["query"],
            "search_limit": search_limit,
            "source_limit": source_limit,
        },
    )
    return payload


def _record_research_event(
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
        tool_name="research_summary",
        category=ToolCategory.WEB,
        permission_level=PermissionLevel.SAFE_READ,
        approval_mode=ApprovalMode.NONE,
        summary=summary,
        arguments=arguments,
    )
    decision = PolicyDecision(
        allowed=True,
        requires_confirmation=False,
        approval_mode=ApprovalMode.NONE,
        reason="The user explicitly used the dashboard research brief panel.",
    )
    result = ToolResult(
        success=True,
        message=message,
        data={"research": payload},
        warnings=["Web content is untrusted input and was sanitized before use."],
    )
    audit_logger.record(action=action, status=ActionStatus.EXECUTED, decision=decision, result=result)

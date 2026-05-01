from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Request

from app.models import ActionStatus, ApprovalMode, PermissionLevel, ProposedAction, ToolCategory, ToolResult
from app.services.policy import PolicyDecision
from app.services.webpages import WebPageUnavailableError
from app.services.websearch import WebSearchUnavailableError

router = APIRouter(prefix="/web", tags=["web"])


@router.get("/search")
def search_web(request: Request, q: str = Query(min_length=1), limit: int | None = None) -> dict:
    web_search_service = request.app.state.web_search_service
    settings = request.app.state.settings
    resolved_limit = min(max(int(limit or settings.live_search_result_limit), 1), 10)
    try:
        payload = web_search_service.search(q, limit=resolved_limit)
    except WebSearchUnavailableError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    _record_web_event(
        request=request,
        tool_name="search_web",
        summary=f"Search the web for '{payload['query']}' from the dashboard.",
        message=f"Fetched {payload['result_count']} live web results from the dashboard search panel.",
        result_data={"search": web_search_service.audit_payload(payload)},
        arguments={"query": payload["query"], "limit": resolved_limit},
    )
    return payload


@router.get("/read")
def read_webpage(request: Request, url: str = Query(min_length=1)) -> dict:
    webpage_service = request.app.state.webpage_service
    try:
        page = webpage_service.read_page(url)
    except WebPageUnavailableError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    _record_web_event(
        request=request,
        tool_name="read_webpage",
        summary=f"Read webpage '{page['url']}' from the dashboard.",
        message=f"Read {page['title']} from the dashboard web reader.",
        result_data={"page": webpage_service.audit_payload(page)},
        arguments={"url": page["url"]},
    )
    return {"page": page}


@router.get("/summary")
def summarize_webpage(request: Request, url: str = Query(min_length=1)) -> dict:
    webpage_service = request.app.state.webpage_service
    try:
        payload = webpage_service.summarize_page(url)
    except WebPageUnavailableError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    page = payload["page"]
    summary = payload["summary"]
    _record_web_event(
        request=request,
        tool_name="summarize_webpage",
        summary=f"Summarize webpage '{page['url']}' from the dashboard.",
        message=f"Summarized {page['title']} from the dashboard web reader.",
        result_data={
            "page": webpage_service.audit_payload(page),
            "summary": webpage_service.summary_audit_payload(summary),
        },
        arguments={"url": page["url"]},
    )
    return payload


def _record_web_event(
    *,
    request: Request,
    tool_name: str,
    summary: str,
    message: str,
    result_data: dict,
    arguments: dict,
) -> None:
    audit_logger = request.app.state.audit_logger
    action = ProposedAction(
        action_id=str(uuid4()),
        session_id="dashboard",
        tool_name=tool_name,
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
        reason="The user explicitly used the dashboard web reader.",
    )
    result = ToolResult(
        success=True,
        message=message,
        data=result_data,
        warnings=["Web content is untrusted input and was sanitized before use."],
    )
    audit_logger.record(action=action, status=ActionStatus.EXECUTED, decision=decision, result=result)

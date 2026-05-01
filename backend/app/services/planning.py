from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Mapping, Protocol, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import Settings
from app.tools.base import ToolDefinition
from app.tools.safe import normalize_app_name, normalize_workspace_name


@dataclass(slots=True)
class PlanningRoute:
    intent: str
    task_type: str
    tool_name: str | None
    arguments: dict[str, Any]
    summary: str
    depends_on_route_index: int | None = None


@dataclass(slots=True)
class PlanningResult:
    routes: list[PlanningRoute]
    summary: str | None = None
    dependencies_explicit: bool = False
    warnings: list[str] = field(default_factory=list)

    @property
    def route(self) -> PlanningRoute:
        if self.routes:
            return self.routes[0]
        return default_chat_route()


class AssistantPlanner(Protocol):
    mode: str
    label: str

    def plan(
        self,
        user_text: str,
        *,
        tools: Sequence[ToolDefinition],
        history: Sequence[Mapping[str, Any]] | None = None,
    ) -> PlanningResult:
        raise NotImplementedError

    def to_dict(self) -> dict[str, Any]:
        raise NotImplementedError


DEFAULT_INTENTS = {
    "system_snapshot": "system_status",
    "launch_workspace": "launch_workspace",
    "create_reminder": "create_reminder",
    "update_note": "update_note",
    "search_notes": "search_notes",
    "read_note": "read_note",
    "search_documents": "search_documents",
    "read_document": "read_document",
    "summarize_document": "summarize_document",
    "inspect_document": "inspect_document",
    "search_web": "web_search",
    "research_summary": "research_summary",
    "generate_content_package": "generate_content_package",
    "open_application": "open_application",
    "open_website": "open_resource",
    "create_note": "capture_note",
    "draft_email": "draft_email",
    "send_email": "send_email",
    "draft_whatsapp_message": "draft_whatsapp_message",
    "send_whatsapp_message": "send_whatsapp_message",
}

DEFAULT_TASK_TYPES = {
    "system_snapshot": "monitoring",
    "launch_workspace": "productivity",
    "create_reminder": "productivity",
    "update_note": "files",
    "search_notes": "productivity",
    "read_note": "productivity",
    "search_documents": "files",
    "read_document": "files",
    "summarize_document": "files",
    "inspect_document": "files",
    "search_web": "research",
    "research_summary": "research",
    "generate_content_package": "communication",
    "open_application": "desktop_control",
    "open_website": "browser",
    "create_note": "productivity",
    "draft_email": "communication",
    "send_email": "communication",
    "draft_whatsapp_message": "communication",
    "send_whatsapp_message": "communication",
}

QUERY_TOOLS = {
    "search_web",
    "research_summary",
    "generate_content_package",
    "search_notes",
    "read_note",
    "search_documents",
    "read_document",
    "summarize_document",
}

REQUIRED_ARGUMENTS = {
    "search_web": ("query",),
    "research_summary": ("query",),
    "generate_content_package": ("topic",),
    "search_notes": ("query",),
    "read_note": ("query",),
    "search_documents": ("query",),
    "read_document": ("query",),
    "summarize_document": ("query",),
    "inspect_document": ("query",),
    "open_application": ("application",),
    "launch_workspace": ("workspace",),
    "open_website": ("url",),
    "update_note": ("query", "content"),
    "draft_email": ("to", "subject"),
    "send_email": ("to", "subject"),
    "draft_whatsapp_message": ("to", "body"),
    "send_whatsapp_message": ("to", "body"),
}

COMMAND_SPLIT_VERBS = (
    "open",
    "launch",
    "start",
    "search",
    "look up",
    "research",
    "find",
    "read",
    "show",
    "view",
    "summarize",
    "summarise",
    "inspect",
    "analyze",
    "analyse",
    "filter",
    "send",
    "draft",
    "email",
    "write",
    "remember",
    "append",
    "add",
    "update",
    "replace",
    "rewrite",
    "remind",
    "set",
    "create",
    "go to",
)

MAX_PLANNED_ACTIONS = 3


def default_chat_route() -> PlanningRoute:
    return PlanningRoute(
        intent="general_chat",
        task_type="conversation",
        tool_name=None,
        arguments={},
        summary="Respond conversationally without taking action.",
    )


def summarize_reminder(reminder_request: Mapping[str, Any]) -> str:
    title = str(reminder_request.get("title", "Untitled reminder"))
    recurrence_label = str(reminder_request.get("recurrence_label", "")).strip()
    if recurrence_label:
        return f"Create a recurring reminder titled '{title}' for {recurrence_label}."
    schedule_hint = str(reminder_request.get("schedule_hint", "")).strip()
    if schedule_hint:
        return f"Create a reminder titled '{title}' for {schedule_hint}."
    due_at = str(reminder_request.get("due_at", "")).strip()
    if due_at:
        return f"Create a reminder titled '{title}' for {due_at}."
    return f"Create a reminder titled '{title}'."


def summarize_note_update(note_update_request: Mapping[str, Any]) -> str:
    query = str(note_update_request.get("query", "note"))
    mode = str(note_update_request.get("mode", "append"))
    if mode == "replace":
        return f"Replace the contents of the note '{query}'."
    return f"Append to the note '{query}'."


def summarize_document_inspection(document_inspection_request: Mapping[str, Any]) -> str:
    query = str(document_inspection_request.get("query", "document"))
    filter_text = str(document_inspection_request.get("filter", "")).strip()
    schema_depth = document_inspection_request.get("schema_depth")
    schema_path = str(document_inspection_request.get("schema_path", "")).strip()
    parts = [f"Inspect the structure of the document '{query}'"]
    if schema_path:
        parts.append(f"at path '{schema_path}'")
    if schema_depth:
        parts.append(f"at depth {schema_depth}")
    if filter_text:
        parts.append(f"filtered by '{filter_text}'")
    if len(parts) > 1:
        return " ".join(parts) + "."
    return f"Inspect the structure of the document '{query}'."


def summarize_action(tool_name: str | None, arguments: Mapping[str, Any], *, fallback: str | None = None) -> str:
    if fallback:
        cleaned = fallback.strip()
        if cleaned:
            return cleaned

    if tool_name is None:
        return "Respond conversationally without taking action."

    if tool_name == "system_snapshot":
        return "Collect a system snapshot."
    if tool_name == "launch_workspace":
        return f"Launch the workspace '{arguments.get('workspace', 'workspace')}'."
    if tool_name == "create_reminder":
        return summarize_reminder(arguments)
    if tool_name == "update_note":
        return summarize_note_update(arguments)
    if tool_name == "search_notes":
        return f"Search notes for '{arguments.get('query', '')}'."
    if tool_name == "read_note":
        return f"Read the note '{arguments.get('query', '')}'."
    if tool_name == "search_documents":
        return f"Search approved documents for '{arguments.get('query', '')}'."
    if tool_name == "read_document":
        return f"Read the document '{arguments.get('query', '')}'."
    if tool_name == "summarize_document":
        return f"Summarize the document '{arguments.get('query', '')}'."
    if tool_name == "inspect_document":
        return summarize_document_inspection(arguments)
    if tool_name == "search_web":
        return f"Search the web for '{arguments.get('query', '')}'."
    if tool_name == "research_summary":
        return f"Build a research brief for '{arguments.get('query', '')}'."
    if tool_name == "generate_content_package":
        return f"Generate YouTube and SEO ideas for '{arguments.get('topic', '')}'."
    if tool_name == "open_application":
        return f"Open the application '{arguments.get('application', 'application')}'."
    if tool_name == "open_website":
        return f"Open the website '{arguments.get('url', 'website')}'."
    if tool_name == "create_note":
        return f"Create a note titled '{arguments.get('title', 'note')}'."
    if tool_name == "draft_email":
        return f"Draft an email with subject '{arguments.get('subject', 'Draft from Zivra')}'."
    if tool_name == "send_email":
        return f"Send an email with subject '{arguments.get('subject', 'Draft from Zivra')}'."
    if tool_name == "draft_whatsapp_message":
        return f"Draft a WhatsApp message for '{arguments.get('to', 'recipient')}'."
    if tool_name == "send_whatsapp_message":
        return f"Open a WhatsApp handoff for '{arguments.get('to', 'recipient')}'."
    return "Plan the next assistant action."


class RuleBasedPlanner:
    mode = "rule"
    label = "Rule planner"

    def __init__(self, router: Any, *, reason: str | None = None) -> None:
        self.router = router
        self.reason = reason

    def plan(
        self,
        user_text: str,
        *,
        tools: Sequence[ToolDefinition],
        history: Sequence[Mapping[str, Any]] | None = None,
    ) -> PlanningResult:
        warnings: list[str] = []
        segments = self._split_compound_request(user_text)
        if len(segments) > MAX_PLANNED_ACTIONS:
            warnings.append(f"I planned the first {MAX_PLANNED_ACTIONS} actions from that request.")
            segments = segments[:MAX_PLANNED_ACTIONS]

        routes = [self._route_to_planning_route(segment) for segment in segments]
        actionable_routes = [route for route in routes if route.tool_name is not None]
        if actionable_routes:
            routes = actionable_routes
        elif not routes:
            routes = [default_chat_route()]

        summary = self._build_group_summary(routes) if len(routes) > 1 else None
        return PlanningResult(routes=routes, summary=summary, dependencies_explicit=False, warnings=warnings)

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "mode": self.mode,
            "label": self.label,
            "provider": "local_rules",
            "configured": True,
        }
        if self.reason:
            payload["reason"] = self.reason
        return payload

    def _route_to_planning_route(self, user_text: str) -> PlanningRoute:
        route = self.router.route(user_text)
        return PlanningRoute(
            intent=getattr(route, "intent", "general_chat"),
            task_type=getattr(route, "task_type", "conversation"),
            tool_name=getattr(route, "tool_name", None),
            arguments=dict(getattr(route, "arguments", {}) or {}),
            summary=getattr(route, "summary", "Respond conversationally without taking action."),
        )

    def _split_compound_request(self, user_text: str) -> list[str]:
        stripped = user_text.strip()
        if not stripped:
            return [user_text]

        separator_pattern = r"(?:and then|then|also)"
        split_verbs = "|".join(re.escape(verb) for verb in COMMAND_SPLIT_VERBS)
        normalized = re.sub(
            rf"\s*(?:,|;)\s*(?={split_verbs}\b)",
            "\n",
            stripped,
            flags=re.IGNORECASE,
        )
        normalized = re.sub(
            rf"\s+(?:{separator_pattern})\s+",
            "\n",
            normalized,
            flags=re.IGNORECASE,
        )
        normalized = re.sub(
            rf"\s+and\s+(?={split_verbs}\b)",
            "\n",
            normalized,
            flags=re.IGNORECASE,
        )

        segments = [segment.strip(" ,;") for segment in normalized.splitlines() if segment.strip(" ,;")]
        return segments or [stripped]

    def _build_group_summary(self, routes: Sequence[PlanningRoute]) -> str | None:
        fragments = [route.summary.strip().rstrip(".") for route in routes if route.summary.strip()]
        if not fragments:
            return None
        if len(fragments) == 1:
            return fragments[0] + "."
        if len(fragments) == 2:
            return f"{fragments[0]} and {fragments[1]}."
        return f"{', '.join(fragments[:2])}, and more."


class OpenAIPlanner:
    mode = "llm"
    label = "LLM planner"

    def __init__(
        self,
        *,
        model: str,
        api_key: str,
        base_url: str,
        timeout_seconds: float,
        fallback: AssistantPlanner,
        now_provider: Callable[[], datetime] | None = None,
        request_executor: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    ) -> None:
        self.model = model
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.fallback = fallback
        self._now_provider = now_provider or (lambda: datetime.now().astimezone())
        self._request_executor = request_executor

    def plan(
        self,
        user_text: str,
        *,
        tools: Sequence[ToolDefinition],
        history: Sequence[Mapping[str, Any]] | None = None,
    ) -> PlanningResult:
        try:
            response_payload = (
                self._request_executor(self._build_request_payload(user_text=user_text, tools=tools, history=history))
                if self._request_executor is not None
                else self._send_request(user_text=user_text, tools=tools, history=history)
            )
            result = self._coerce_result(
                response_payload=response_payload,
                user_text=user_text,
                tools=tools,
            )
            return result
        except Exception as exc:
            fallback = self.fallback.plan(user_text, tools=tools, history=history)
            fallback.warnings.append(f"LLM planner fallback: {self._format_exception(exc)}")
            return fallback

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "label": self.label,
            "provider": "openai_compatible",
            "configured": True,
            "model": self.model,
            "base_url": self.base_url,
            "fallback_mode": getattr(self.fallback, "mode", "rule"),
        }

    def _build_request_payload(
        self,
        *,
        user_text: str,
        tools: Sequence[ToolDefinition],
        history: Sequence[Mapping[str, Any]] | None,
    ) -> dict[str, Any]:
        now_value = self._now_provider().isoformat()
        tool_catalog = [
            {
                "name": tool.name,
                "category": tool.category.value,
                "permission_level": tool.permission_level.value,
                "description": tool.description,
            }
            for tool in tools
        ]
        history_lines = []
        for item in list(history or [])[-6:]:
            role = str(item.get("role", "unknown"))
            content = str(item.get("content", "")).strip()
            if content:
                history_lines.append(f"{role}: {content}")
        history_block = "\n".join(history_lines) if history_lines else "No prior conversation context."

        prompt = (
            "You are the planning layer for a local-first desktop assistant.\n"
            "Return exactly one JSON object.\n"
            "Preferred shape: {\"summary\": string, \"actions\": [{\"intent\": string, \"task_type\": string, "
            "\"tool_name\": string|null, \"arguments\": object, \"summary\": string, \"depends_on\": number|null}, ...]}.\n"
            "Use 1 to 3 actions only. Use tool_name null only for a conversational reply with no action.\n"
            "When one action must wait for an earlier action, set depends_on to that earlier step number starting at 1. "
            "Use null when the action is independent.\n"
            "You may also return a single action object with intent, task_type, tool_name, arguments, and summary.\n"
            "Never invent tool names or extra keys.\n"
            "Prefer local notes and approved documents over web search when the request references local content.\n"
            "For reminders, convert relative scheduling language into an exact ISO 8601 timestamp with timezone in arguments.due_at when you can.\n"
            "Keep summary short and actionable.\n"
            f"Current local time: {now_value}\n"
            f"Available tools: {json.dumps(tool_catalog, ensure_ascii=True)}\n"
            f"Recent conversation:\n{history_block}\n"
            f"User request: {user_text}"
        )

        return {
            "model": self.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": "Plan assistant actions as strict JSON only.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        }

    def _send_request(
        self,
        *,
        user_text: str,
        tools: Sequence[ToolDefinition],
        history: Sequence[Mapping[str, Any]] | None,
    ) -> dict[str, Any]:
        payload = self._build_request_payload(user_text=user_text, tools=tools, history=history)
        request = Request(
            url=f"{self.base_url}/chat/completions",
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            data=json.dumps(payload).encode("utf-8"),
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {body or exc.reason}") from exc
        except URLError as exc:
            raise RuntimeError(str(exc.reason)) from exc

    def _coerce_result(
        self,
        *,
        response_payload: Mapping[str, Any],
        user_text: str,
        tools: Sequence[ToolDefinition],
    ) -> PlanningResult:
        content = self._extract_content(response_payload)
        data = self._extract_json_object(content)
        if not isinstance(data, dict):
            raise ValueError("Planner response was not a JSON object.")

        summary = str(data.get("summary", "")).strip() or None
        action_payloads = self._extract_action_payloads(data)
        warnings: list[str] = []
        if len(action_payloads) > MAX_PLANNED_ACTIONS:
            warnings.append(f"I planned the first {MAX_PLANNED_ACTIONS} actions from that request.")
        routes = [
            self._coerce_route_payload(
                data=action_payload,
                user_text=user_text,
                tools=tools,
            )
            for action_payload in action_payloads[:MAX_PLANNED_ACTIONS]
        ]
        for index, action_payload in enumerate(action_payloads[:MAX_PLANNED_ACTIONS]):
            routes[index].depends_on_route_index = self._coerce_dependency_index(
                action_payload,
                route_index=index,
                route_count=len(routes),
            )
        if routes and all(route.tool_name is None for route in routes):
            routes = [routes[0]]
        if not routes:
            routes = [default_chat_route()]
        return PlanningResult(
            routes=routes,
            summary=summary,
            dependencies_explicit=True,
            warnings=warnings,
        )

    def _coerce_route_payload(
        self,
        *,
        data: Mapping[str, Any],
        user_text: str,
        tools: Sequence[ToolDefinition],
    ) -> PlanningRoute:
        tool_map = {tool.name: tool for tool in tools}
        tool_name = data.get("tool_name")
        if tool_name in ("", None):
            return PlanningRoute(
                intent=str(data.get("intent") or "general_chat"),
                task_type=str(data.get("task_type") or "conversation"),
                tool_name=None,
                arguments={},
                summary=summarize_action(None, {}, fallback=str(data.get("summary") or "")),
            )

        normalized_tool_name = str(tool_name).strip()
        if normalized_tool_name not in tool_map:
            raise ValueError(f"Unknown tool '{normalized_tool_name}'.")

        arguments = self._normalize_arguments(
            tool_name=normalized_tool_name,
            arguments=data.get("arguments"),
            user_text=user_text,
        )
        if not self._has_required_arguments(normalized_tool_name, arguments):
            raise ValueError(f"Missing required arguments for '{normalized_tool_name}'.")

        return PlanningRoute(
            intent=str(data.get("intent") or DEFAULT_INTENTS.get(normalized_tool_name, normalized_tool_name)),
            task_type=str(data.get("task_type") or DEFAULT_TASK_TYPES.get(normalized_tool_name, "conversation")),
            tool_name=normalized_tool_name,
            arguments=arguments,
            summary=summarize_action(
                normalized_tool_name,
                arguments,
                fallback=str(data.get("summary") or ""),
            ),
        )

    def _extract_action_payloads(self, data: Mapping[str, Any]) -> list[Mapping[str, Any]]:
        actions = data.get("actions")
        if isinstance(actions, list):
            payloads = [item for item in actions if isinstance(item, Mapping)]
            if payloads:
                return payloads
        if isinstance(data.get("action"), Mapping):
            return [data["action"]]
        return [data]

    def _coerce_dependency_index(
        self,
        data: Mapping[str, Any],
        *,
        route_index: int,
        route_count: int,
    ) -> int | None:
        raw = data.get("depends_on")
        if raw in ("", None):
            return None
        if isinstance(raw, list):
            if len(raw) != 1:
                raise ValueError("Each action may depend on at most one earlier step.")
            raw = raw[0]

        try:
            step_number = int(raw)
        except (TypeError, ValueError) as exc:
            raise ValueError("depends_on must be a prior step number or null.") from exc

        dependency_index = step_number - 1
        if dependency_index < 0 or dependency_index >= route_count:
            raise ValueError("depends_on referenced a step outside the planned range.")
        if dependency_index >= route_index:
            raise ValueError("depends_on must reference an earlier step.")
        return dependency_index

    def _extract_content(self, response_payload: Mapping[str, Any]) -> str:
        choices = response_payload.get("choices")
        if isinstance(choices, list) and choices:
            message = choices[0].get("message", {})
            content = message.get("content", "")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                parts = []
                for item in content:
                    if not isinstance(item, Mapping):
                        continue
                    text = item.get("text")
                    if text:
                        parts.append(str(text))
                if parts:
                    return "\n".join(parts)
        raise ValueError("Planner response did not contain assistant content.")

    def _extract_json_object(self, content: str) -> dict[str, Any]:
        stripped = content.strip()
        if not stripped:
            raise ValueError("Planner response was empty.")
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            fenced_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", stripped, flags=re.DOTALL)
            if fenced_match is not None:
                return json.loads(fenced_match.group(1))
            start = stripped.find("{")
            end = stripped.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(stripped[start : end + 1])
            raise

    def _normalize_arguments(
        self,
        *,
        tool_name: str,
        arguments: Any,
        user_text: str,
    ) -> dict[str, Any]:
        raw = dict(arguments) if isinstance(arguments, Mapping) else {}
        normalized: dict[str, Any] = {}

        def as_text(value: Any) -> str:
            if value is None:
                return ""
            return str(value).strip()

        if tool_name in QUERY_TOOLS:
            query = as_text(raw.get("query") or raw.get("document") or raw.get("note") or raw.get("topic"))
            normalized["query"] = query or user_text.strip()
            return normalized

        if tool_name == "inspect_document":
            normalized["query"] = as_text(raw.get("query") or raw.get("document")) or user_text.strip()
            filter_text = as_text(raw.get("filter"))
            schema_path = as_text(raw.get("schema_path") or raw.get("path"))
            schema_depth = raw.get("schema_depth", raw.get("depth"))
            if filter_text:
                normalized["filter"] = filter_text
            if schema_path:
                normalized["schema_path"] = schema_path
            try:
                if schema_depth is not None and str(schema_depth).strip():
                    normalized["schema_depth"] = max(1, min(int(schema_depth), 4))
            except (TypeError, ValueError):
                pass
            return normalized

        if tool_name == "open_application":
            application = as_text(raw.get("application") or raw.get("app"))
            normalized["application"] = normalize_app_name(application)
            return normalized

        if tool_name == "launch_workspace":
            workspace = as_text(raw.get("workspace") or raw.get("mode"))
            normalized["workspace"] = normalize_workspace_name(workspace)
            return normalized

        if tool_name == "open_website":
            normalized["url"] = as_text(raw.get("url") or raw.get("website") or raw.get("link"))
            return normalized

        if tool_name == "create_note":
            title = as_text(raw.get("title"))
            content = as_text(raw.get("content") or raw.get("body"))
            normalized["title"] = title or user_text[:40].strip() or "New note"
            normalized["content"] = content or user_text.strip()
            return normalized

        if tool_name in {"draft_email", "send_email"}:
            normalized["to"] = as_text(raw.get("to") or raw.get("recipient"))
            normalized["subject"] = as_text(raw.get("subject")) or user_text[:50].strip()
            normalized["body"] = as_text(raw.get("body") or raw.get("content"))
            return normalized

        if tool_name in {"draft_whatsapp_message", "send_whatsapp_message"}:
            normalized["to"] = as_text(raw.get("to") or raw.get("recipient") or raw.get("phone"))
            normalized["body"] = as_text(raw.get("body") or raw.get("message") or raw.get("content"))
            return normalized

        if tool_name == "generate_content_package":
            normalized["topic"] = as_text(raw.get("topic") or raw.get("query") or raw.get("title")) or user_text.strip()
            audience = as_text(raw.get("audience"))
            context = as_text(raw.get("context") or raw.get("notes"))
            if audience:
                normalized["audience"] = audience
            if context:
                normalized["context"] = context
            return normalized

        if tool_name == "update_note":
            normalized["query"] = as_text(raw.get("query") or raw.get("note"))
            normalized["content"] = as_text(raw.get("content") or raw.get("body"))
            mode = as_text(raw.get("mode") or "append").lower()
            normalized["mode"] = mode if mode in {"append", "replace"} else "append"
            return normalized

        if tool_name == "create_reminder":
            normalized["title"] = as_text(raw.get("title")) or "Untitled reminder"
            details = as_text(raw.get("details") or raw.get("body"))
            schedule_hint = as_text(raw.get("schedule_hint"))
            due_at = as_text(raw.get("due_at"))
            recurrence_rule = as_text(raw.get("recurrence_rule"))
            recurrence_label = as_text(raw.get("recurrence_label"))
            if details:
                normalized["details"] = details
            if schedule_hint:
                normalized["schedule_hint"] = schedule_hint
            if due_at:
                normalized["due_at"] = due_at
            if recurrence_rule:
                normalized["recurrence_rule"] = recurrence_rule
            if recurrence_label:
                normalized["recurrence_label"] = recurrence_label
            return normalized

        return normalized

    def _has_required_arguments(self, tool_name: str, arguments: Mapping[str, Any]) -> bool:
        required = REQUIRED_ARGUMENTS.get(tool_name, ())
        return all(str(arguments.get(key, "")).strip() for key in required)

    def _format_exception(self, exc: Exception) -> str:
        message = str(exc).strip()
        return message or exc.__class__.__name__


def build_planner(
    settings: Settings,
    *,
    fallback_router: Any,
    request_executor: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> AssistantPlanner:
    fallback = RuleBasedPlanner(fallback_router)
    planner_mode = settings.planner_mode.lower().strip()
    api_key = settings.llm_api_key.strip()
    model = settings.llm_model.strip()

    if planner_mode == "rule":
        return fallback

    if not api_key or not model:
        reason = "LLM planner is not configured. Falling back to local rules."
        return RuleBasedPlanner(fallback_router, reason=reason)

    return OpenAIPlanner(
        model=model,
        api_key=api_key,
        base_url=settings.llm_base_url,
        timeout_seconds=settings.llm_timeout_seconds,
        fallback=fallback,
        request_executor=request_executor,
    )

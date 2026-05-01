from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable
from uuid import uuid4

from app.models import ActionOutcome, ActionStatus, ApprovalMode, OrchestratorResponse, ProposedAction
from app.services.audit import AuditLogger
from app.services.memory import ConversationMemoryStore
from app.services.planning import AssistantPlanner, PlanningRoute, RuleBasedPlanner
from app.services.policy import PolicyDecision, PolicyEngine
from app.tools.registry import ToolRegistry
from app.tools.safe import normalize_app_name, normalize_workspace_name


@dataclass(slots=True)
class RouteResult:
    intent: str
    task_type: str
    tool_name: str | None
    arguments: dict[str, Any]
    summary: str


@dataclass(slots=True)
class ParsedReminderSchedule:
    title: str
    due_at: str | None
    schedule_hint: str | None
    recurrence_rule: str | None = None
    recurrence_label: str | None = None


class IntentRouter:
    def __init__(self, now_provider: Callable[[], datetime] | None = None) -> None:
        self._now_provider = now_provider or (lambda: datetime.now().astimezone())

    def route(self, user_text: str) -> RouteResult:
        normalized = user_text.strip()
        lowered = normalized.lower()

        if any(keyword in lowered for keyword in ("battery", "cpu", "ram", "system", "storage")):
            return RouteResult(
                intent="system_status",
                task_type="monitoring",
                tool_name="system_snapshot",
                arguments={},
                summary="Collect a system snapshot.",
            )

        clipboard_write_request = self._extract_clipboard_write_request(normalized)
        if clipboard_write_request is not None:
            return RouteResult(
                intent="write_clipboard",
                task_type="productivity",
                tool_name="write_clipboard",
                arguments=clipboard_write_request,
                summary="Copy text into the local clipboard.",
            )

        if self._is_clipboard_read_request(normalized):
            return RouteResult(
                intent="read_clipboard",
                task_type="productivity",
                tool_name="read_clipboard",
                arguments={},
                summary="Read the current local clipboard.",
            )

        workspace_name = self._extract_workspace_name(normalized)
        if workspace_name is not None and any(keyword in lowered for keyword in ("workspace", "mode")):
            return RouteResult(
                intent="launch_workspace",
                task_type="productivity",
                tool_name="launch_workspace",
                arguments={"workspace": workspace_name},
                summary=f"Launch the workspace '{workspace_name}'.",
            )

        reminder_request = self._extract_reminder_request(normalized)
        if reminder_request is not None:
            return RouteResult(
                intent="create_reminder",
                task_type="productivity",
                tool_name="create_reminder",
                arguments=reminder_request,
                summary=self._summarize_reminder(reminder_request),
            )

        note_update_request = self._extract_note_update_request(normalized)
        if note_update_request is not None:
            return RouteResult(
                intent="update_note",
                task_type="files",
                tool_name="update_note",
                arguments=note_update_request,
                summary=self._summarize_note_update(note_update_request),
            )

        note_search_query = self._extract_note_search_query(normalized)
        if note_search_query is not None:
            return RouteResult(
                intent="search_notes",
                task_type="productivity",
                tool_name="search_notes",
                arguments={"query": note_search_query},
                summary=f"Search notes for '{note_search_query}'.",
            )

        note_read_query = self._extract_note_read_query(normalized)
        if note_read_query is not None:
            return RouteResult(
                intent="read_note",
                task_type="productivity",
                tool_name="read_note",
                arguments={"query": note_read_query},
                summary=f"Read the note '{note_read_query}'.",
            )

        file_search_query = self._extract_file_search_query(normalized)
        if file_search_query is not None:
            return RouteResult(
                intent="search_files",
                task_type="files",
                tool_name="search_files",
                arguments={"query": file_search_query},
                summary=f"Search approved files for '{file_search_query}'.",
            )

        folder_browse_query = self._extract_folder_browse_query(normalized)
        if folder_browse_query is not None:
            folder_label = folder_browse_query or "approved roots"
            return RouteResult(
                intent="browse_folder",
                task_type="files",
                tool_name="browse_folder",
                arguments={"folder": folder_browse_query},
                summary=f"Browse the folder '{folder_label}'.",
            )

        document_search_query = self._extract_document_search_query(normalized)
        if document_search_query is not None:
            return RouteResult(
                intent="search_documents",
                task_type="files",
                tool_name="search_documents",
                arguments={"query": document_search_query},
                summary=f"Search approved documents for '{document_search_query}'.",
            )

        document_read_query = self._extract_document_read_query(normalized)
        if document_read_query is not None:
            return RouteResult(
                intent="read_document",
                task_type="files",
                tool_name="read_document",
                arguments={"query": document_read_query},
                summary=f"Read the document '{document_read_query}'.",
            )

        document_summary_query = self._extract_document_summary_query(normalized)
        if document_summary_query is not None:
            return RouteResult(
                intent="summarize_document",
                task_type="files",
                tool_name="summarize_document",
                arguments={"query": document_summary_query},
                summary=f"Summarize the document '{document_summary_query}'.",
            )

        document_analysis_request = self._extract_document_analysis_request(normalized)
        if document_analysis_request is not None:
            return RouteResult(
                intent="analyze_document",
                task_type="files",
                tool_name="analyze_document",
                arguments=document_analysis_request,
                summary=self._summarize_document_analysis(document_analysis_request),
            )

        webpage_summary_url = self._extract_webpage_summary_url(normalized)
        if webpage_summary_url is not None:
            return RouteResult(
                intent="summarize_webpage",
                task_type="browser",
                tool_name="summarize_webpage",
                arguments={"url": webpage_summary_url},
                summary=f"Summarize the webpage '{webpage_summary_url}'.",
            )

        webpage_read_url = self._extract_webpage_read_url(normalized)
        if webpage_read_url is not None:
            return RouteResult(
                intent="read_webpage",
                task_type="browser",
                tool_name="read_webpage",
                arguments={"url": webpage_read_url},
                summary=f"Read the webpage '{webpage_read_url}'.",
            )

        document_inspection_request = self._extract_document_inspection_request(normalized)
        if document_inspection_request is not None:
            return RouteResult(
                intent="inspect_document",
                task_type="files",
                tool_name="inspect_document",
                arguments=document_inspection_request,
                summary=self._summarize_document_inspection(document_inspection_request),
            )

        research_summary_query = self._extract_research_summary_query(normalized)
        if research_summary_query is not None:
            return RouteResult(
                intent="research_summary",
                task_type="research",
                tool_name="research_summary",
                arguments={"query": research_summary_query},
                summary=f"Build a research brief for '{research_summary_query}'.",
            )

        content_request = self._extract_content_package_request(normalized)
        if content_request is not None:
            return RouteResult(
                intent="generate_content_package",
                task_type="communication",
                tool_name="generate_content_package",
                arguments=content_request,
                summary=f"Generate YouTube and SEO ideas for '{content_request['topic']}'.",
            )

        if any(keyword in lowered for keyword in ("search", "look up", "research", "find on web")):
            query = self._extract_search_query(normalized)
            return RouteResult(
                intent="web_search",
                task_type="research",
                tool_name="search_web",
                arguments={"query": query},
                summary=f"Search the web for '{query}'.",
            )

        app_name = self._extract_application_name(normalized)
        if app_name is not None and any(keyword in lowered for keyword in ("open", "launch", "start")):
            return RouteResult(
                intent="open_application",
                task_type="desktop_control",
                tool_name="open_application",
                arguments={"application": app_name},
                summary=f"Open the application '{app_name}'.",
            )

        if any(keyword in lowered for keyword in ("open", "website", "go to", "launch")):
            url = self._extract_url(normalized)
            return RouteResult(
                intent="open_resource",
                task_type="browser",
                tool_name="open_website",
                arguments={"url": url},
                summary=f"Open the website '{url}'.",
            )

        if any(keyword in lowered for keyword in ("note", "write down", "remember this")):
            title = self._extract_note_title(normalized)
            return RouteResult(
                intent="capture_note",
                task_type="productivity",
                tool_name="create_note",
                arguments={"title": title, "content": normalized},
                summary=f"Create a note titled '{title}'.",
            )

        email_request = self._extract_email_request(normalized)
        if email_request is not None and self._is_send_email_request(normalized):
            return RouteResult(
                intent="send_email",
                task_type="communication",
                tool_name="send_email",
                arguments=email_request,
                summary=self._summarize_email_request(email_request, send=True),
            )

        if email_request is not None and ("email" in lowered or "draft" in lowered):
            return RouteResult(
                intent="draft_email",
                task_type="communication",
                tool_name="draft_email",
                arguments=email_request,
                summary=self._summarize_email_request(email_request, send=False),
            )

        whatsapp_request = self._extract_whatsapp_request(normalized)
        if whatsapp_request is not None and self._is_send_whatsapp_request(normalized):
            return RouteResult(
                intent="send_whatsapp_message",
                task_type="communication",
                tool_name="send_whatsapp_message",
                arguments=whatsapp_request,
                summary=self._summarize_whatsapp_request(whatsapp_request, send=True),
            )

        if whatsapp_request is not None and ("whatsapp" in lowered or "message" in lowered):
            return RouteResult(
                intent="draft_whatsapp_message",
                task_type="communication",
                tool_name="draft_whatsapp_message",
                arguments=whatsapp_request,
                summary=self._summarize_whatsapp_request(whatsapp_request, send=False),
            )

        return RouteResult(
            intent="general_chat",
            task_type="conversation",
            tool_name=None,
            arguments={},
            summary="Respond conversationally without taking action.",
        )

    def _extract_search_query(self, user_text: str) -> str:
        for prefix in ("search for", "search", "look up", "research", "find on web"):
            if user_text.lower().startswith(prefix):
                query = user_text[len(prefix) :].strip(" :")
                if query:
                    return query
        return user_text.strip()

    def _is_clipboard_read_request(self, user_text: str) -> bool:
        lowered = user_text.lower().strip()
        prefixes = (
            "read clipboard",
            "read my clipboard",
            "show clipboard",
            "show my clipboard",
            "check clipboard",
            "check my clipboard",
            "what is on my clipboard",
            "what's on my clipboard",
            "what is in my clipboard",
            "what's in my clipboard",
        )
        return any(lowered.startswith(prefix) for prefix in prefixes)

    def _extract_clipboard_write_request(self, user_text: str) -> dict[str, Any] | None:
        patterns = (
            r"^(?:copy|put|save)\s+(.+?)\s+(?:to|into|on)\s+clipboard$",
            r"^(?:copy|put|save)\s+(.+?)\s+(?:to|into|on)\s+my\s+clipboard$",
            r"^(?:copy|put|save)\s+clipboard\s+(?:with\s+|:\s*)(.+)$",
            r"^(?:set|update)\s+clipboard\s+(?:to\s+|with\s+|:\s*)(.+)$",
        )
        for pattern in patterns:
            match = re.match(pattern, user_text.strip(), flags=re.IGNORECASE | re.DOTALL)
            if match is None:
                continue
            text = match.group(1).strip()
            if text:
                return {"text": text}
        if re.match(r"^(?:clear|empty)\s+(?:my\s+)?clipboard$", user_text.strip(), flags=re.IGNORECASE):
            return {"text": ""}
        return None

    def _extract_url(self, user_text: str) -> str:
        match = re.search(r"(https?://[^\s]+|[a-zA-Z0-9-]+\.[a-zA-Z]{2,})", user_text)
        if match:
            return match.group(1)

        tokens = [token for token in re.split(r"\s+", user_text) if token.isalpha()]
        if tokens:
            return f"{tokens[-1].lower()}.com"
        return "example.com"

    def _extract_note_title(self, user_text: str) -> str:
        trimmed = user_text.strip()
        if len(trimmed) <= 40:
            return trimmed
        return trimmed[:37].rstrip() + "..."

    def _extract_note_search_query(self, user_text: str) -> str | None:
        lowered = user_text.lower()
        prefixes = (
            "search notes for ",
            "search my notes for ",
            "find notes for ",
            "find notes about ",
            "find note ",
            "look in notes for ",
            "search notes ",
        )
        for prefix in prefixes:
            if lowered.startswith(prefix):
                query = user_text[len(prefix) :].strip(" .")
                return query or None
        return None

    def _extract_note_update_request(self, user_text: str) -> dict[str, Any] | None:
        patterns = (
            (r"^(append to|add to|update)\s+note\s+(.+?)(?:\s+with\s+|:\s*)(.+)$", "append"),
            (r"^(replace|rewrite)\s+note\s+(.+?)(?:\s+with\s+|:\s*)(.+)$", "replace"),
        )
        for pattern, mode in patterns:
            match = re.match(pattern, user_text.strip(), flags=re.IGNORECASE | re.DOTALL)
            if match is None:
                continue
            query = match.group(2).strip(" .")
            content = match.group(3).strip()
            if query and content:
                return {"query": query, "content": content, "mode": mode}
        return None

    def _extract_note_read_query(self, user_text: str) -> str | None:
        lowered = user_text.lower()
        prefixes = (
            "read note ",
            "read my note ",
            "open note ",
            "show note ",
            "view note ",
            "open my note ",
        )
        for prefix in prefixes:
            if lowered.startswith(prefix):
                query = user_text[len(prefix) :].strip(" .")
                return query or None
        return None

    def _extract_research_summary_query(self, user_text: str) -> str | None:
        lowered = user_text.lower()
        prefixes = (
            "research summary for ",
            "summarize research for ",
            "build a research brief for ",
            "build research brief for ",
            "research brief for ",
        )
        for prefix in prefixes:
            if lowered.startswith(prefix):
                query = user_text[len(prefix) :].strip(" .")
                return query or None
        return None

    def _extract_content_package_request(self, user_text: str) -> dict[str, Any] | None:
        lowered = user_text.lower()
        prefixes = (
            "youtube ideas for ",
            "youtube titles for ",
            "seo ideas for ",
            "seo titles for ",
            "youtube seo package for ",
            "content package for ",
        )
        for prefix in prefixes:
            if lowered.startswith(prefix):
                topic = user_text[len(prefix) :].strip(" .")
                if topic:
                    return {"topic": topic}
        return None

    def _extract_document_search_query(self, user_text: str) -> str | None:
        lowered = user_text.lower()
        prefixes = (
            "search documents for ",
            "search docs for ",
            "find documents about ",
            "find docs about ",
            "look in documents for ",
            "look in docs for ",
        )
        for prefix in prefixes:
            if lowered.startswith(prefix):
                query = user_text[len(prefix) :].strip(" .")
                return query or None
        return None

    def _extract_file_search_query(self, user_text: str) -> str | None:
        lowered = user_text.lower()
        prefixes = (
            "search files for ",
            "find files about ",
            "find files named ",
            "look in files for ",
        )
        for prefix in prefixes:
            if lowered.startswith(prefix):
                query = user_text[len(prefix) :].strip(" .")
                return query or None
        return None

    def _extract_folder_browse_query(self, user_text: str) -> str | None:
        lowered = user_text.lower().strip()
        if lowered in {"browse approved roots", "show approved roots", "list approved roots"}:
            return ""

        prefixes = (
            "browse folder ",
            "show folder ",
            "list files in ",
            "show files in ",
            "browse files in ",
        )
        for prefix in prefixes:
            if lowered.startswith(prefix):
                query = user_text[len(prefix) :].strip(" .").replace("\\", "/").strip("/")
                return query or None
        return None

    def _extract_document_read_query(self, user_text: str) -> str | None:
        lowered = user_text.lower()
        prefixes = (
            "read document ",
            "read doc ",
            "open document ",
            "open doc ",
            "show document ",
            "show doc ",
            "read file ",
            "open file ",
        )
        for prefix in prefixes:
            if lowered.startswith(prefix):
                query = user_text[len(prefix) :].strip(" .")
                return query or None
        return None

    def _extract_document_summary_query(self, user_text: str) -> str | None:
        lowered = user_text.lower()
        prefixes = (
            "summarize document ",
            "summarise document ",
            "summarize doc ",
            "summarise doc ",
            "summarize file ",
            "summarise file ",
        )
        for prefix in prefixes:
            if lowered.startswith(prefix):
                query = user_text[len(prefix) :].strip(" .")
                return query or None
        return None

    def _extract_webpage_summary_url(self, user_text: str) -> str | None:
        lowered = user_text.lower()
        prefixes = (
            "summarize website ",
            "summarise website ",
            "summarize webpage ",
            "summarise webpage ",
            "summarize web page ",
            "summarise web page ",
            "summarize page ",
            "summarise page ",
            "summarize url ",
            "summarise url ",
        )
        for prefix in prefixes:
            if lowered.startswith(prefix):
                value = user_text[len(prefix) :].strip(" .")
                return self._extract_url(value) if value else None
        return None

    def _extract_document_analysis_request(self, user_text: str) -> dict[str, Any] | None:
        stripped = user_text.strip()
        prefix_match = re.match(
            r"^(?:analy[sz]e\s+(?:document|doc|file)|review\s+data\s+for|summari[sz]e\s+data\s+for|summarize\s+data\s+for)\s+(.+)$",
            stripped,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if prefix_match is None:
            return None

        remainder = prefix_match.group(1).strip()
        schema_path = ""
        path_match = re.search(
            r"\s+(?:at\s+path|path)\s+([A-Za-z0-9_.\[\]-]+)\s*$",
            remainder,
            flags=re.IGNORECASE,
        )
        if path_match is not None:
            schema_path = path_match.group(1).strip()
            remainder = remainder[: path_match.start()].strip()

        filter_text = ""
        filter_match = re.search(r"\s+for\s+(.+)$", remainder, flags=re.IGNORECASE | re.DOTALL)
        if filter_match is not None:
            filter_text = filter_match.group(1).strip()
            remainder = remainder[: filter_match.start()].strip()

        query = remainder.strip(" .")
        if not query:
            return None

        payload: dict[str, Any] = {"query": query}
        if filter_text:
            payload["filter"] = filter_text
        if schema_path:
            payload["schema_path"] = schema_path
        return payload

    def _extract_webpage_read_url(self, user_text: str) -> str | None:
        lowered = user_text.lower()
        prefixes = (
            "read website ",
            "read webpage ",
            "read web page ",
            "read page ",
            "read url ",
            "show website ",
            "show webpage ",
            "show page ",
        )
        for prefix in prefixes:
            if lowered.startswith(prefix):
                value = user_text[len(prefix) :].strip(" .")
                return self._extract_url(value) if value else None
        return None

    def _summarize_document_analysis(self, payload: dict[str, Any]) -> str:
        query = payload.get("query", "document")
        summary = f"Analyze the data in '{query}'."
        if payload.get("filter"):
            summary = f"{summary} Filter: {payload['filter']}."
        if payload.get("schema_path"):
            summary = f"{summary} Path: {payload['schema_path']}."
        return summary

    def _extract_document_inspection_request(self, user_text: str) -> dict[str, Any] | None:
        stripped = user_text.strip()
        prefix_match = re.match(
            r"^(?:inspect\s+(?:document|doc|file)|show\s+structure\s+for|analy[sz]e\s+document|filter\s+document)\s+(.+)$",
            stripped,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if prefix_match is None:
            return None

        remainder = prefix_match.group(1).strip()
        depth_match = re.search(r"\s+depth\s+([1-4])\s*$", remainder, flags=re.IGNORECASE)
        schema_depth = None
        if depth_match is not None:
            schema_depth = int(depth_match.group(1))
            remainder = remainder[: depth_match.start()].strip()

        schema_path = ""
        path_match = re.search(
            r"\s+(?:at\s+path|path)\s+([A-Za-z0-9_.\[\]-]+)\s*$",
            remainder,
            flags=re.IGNORECASE,
        )
        if path_match is not None:
            schema_path = path_match.group(1).strip()
            remainder = remainder[: path_match.start()].strip()

        filter_text = ""
        filter_match = re.search(r"\s+for\s+(.+)$", remainder, flags=re.IGNORECASE | re.DOTALL)
        if filter_match is not None:
            filter_text = filter_match.group(1).strip()
            remainder = remainder[: filter_match.start()].strip()

        query = remainder.strip(" .")
        if not query:
            return None

        payload: dict[str, Any] = {"query": query}
        if filter_text:
            payload["filter"] = filter_text
        if schema_depth is not None:
            payload["schema_depth"] = schema_depth
        if schema_path:
            payload["schema_path"] = schema_path
        return payload

    def _extract_recipient(self, user_text: str) -> str:
        match = re.search(r"to\s+([A-Za-z0-9_.+-]+@[A-Za-z0-9_.-]+\.[A-Za-z]{2,})", user_text)
        if match:
            return match.group(1)
        return "recipient@example.com"

    def _is_send_email_request(self, user_text: str) -> bool:
        lowered = user_text.lower().strip()
        return any(
            lowered.startswith(prefix)
            for prefix in (
                "send email ",
                "send an email ",
                "send the email ",
                "email ",
            )
        )

    def _extract_email_request(self, user_text: str) -> dict[str, Any] | None:
        lowered = user_text.lower()
        if "email" not in lowered and re.search(r"[A-Za-z0-9_.+-]+@[A-Za-z0-9_.-]+\.[A-Za-z]{2,}", user_text) is None:
            return None

        recipient = self._extract_recipient(user_text)
        subject = self._extract_email_subject(user_text)
        body = self._extract_email_body(user_text)
        return {
            "to": recipient,
            "subject": subject,
            "body": body,
            "source": "assistant",
        }

    def _extract_email_body(self, user_text: str) -> str:
        match = re.search(r"(?:body|message)\s+(.+)$", user_text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""

    def _summarize_email_request(self, payload: dict[str, Any], *, send: bool) -> str:
        subject = str(payload.get("subject", "Draft from Zivra"))
        recipient = str(payload.get("to", "recipient@example.com"))
        if send:
            return f"Send an email to {recipient} with subject '{subject}'."
        return f"Draft an email to {recipient} with subject '{subject}'."

    def _extract_email_subject(self, user_text: str) -> str:
        match = re.search(
            r"subject\s+(.+?)(?:\s+(?:body|message)\s+.+)?$",
            user_text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if match:
            return match.group(1).strip()
        trimmed = user_text.strip()
        if len(trimmed) <= 50:
            return trimmed
        return trimmed[:47].rstrip() + "..."

    def _is_send_whatsapp_request(self, user_text: str) -> bool:
        lowered = user_text.lower().strip()
        return any(
            lowered.startswith(prefix)
            for prefix in (
                "send whatsapp ",
                "send a whatsapp ",
                "send whatsapp message ",
                "send a whatsapp message ",
            )
        )

    def _extract_whatsapp_request(self, user_text: str) -> dict[str, Any] | None:
        lowered = user_text.lower()
        if "whatsapp" not in lowered:
            return None

        pattern = re.compile(
            r"^(?:send|draft|save)\s+(?:a\s+)?whatsapp(?:\s+message)?\s+to\s+(.+?)(?:\s+(?:body|message)\s+(.+))?$",
            flags=re.IGNORECASE | re.DOTALL,
        )
        match = pattern.match(user_text.strip())
        if match is None:
            return None

        recipient = match.group(1).strip()
        body = (match.group(2) or "").strip()
        if not recipient:
            return None

        return {
            "to": recipient,
            "body": body,
            "source": "assistant",
        }

    def _summarize_whatsapp_request(self, payload: dict[str, Any], *, send: bool) -> str:
        recipient = str(payload.get("to", "recipient"))
        if send:
            return f"Open a WhatsApp handoff for {recipient}."
        return f"Draft a WhatsApp message for {recipient}."

    def _extract_application_name(self, user_text: str) -> str | None:
        lowered = user_text.lower()
        for alias in (
            "file explorer",
            "text editor",
            "notepad",
            "calculator",
            "calc",
            "explorer",
            "files",
        ):
            if alias in lowered:
                return normalize_app_name(alias)
        return None

    def _extract_workspace_name(self, user_text: str) -> str | None:
        lowered = user_text.lower()
        for alias in (
            "focus workspace",
            "research workspace",
            "planning workspace",
            "focus mode",
            "research mode",
            "planning mode",
        ):
            if alias in lowered:
                return normalize_workspace_name(alias)
        return None

    def _extract_reminder_request(self, user_text: str) -> dict[str, Any] | None:
        lowered = user_text.lower()
        trigger = None
        for prefix in (
            "remind me to ",
            "remind me ",
            "set a reminder to ",
            "set reminder to ",
            "set a reminder ",
            "set reminder ",
            "create a reminder to ",
            "create reminder to ",
            "add a reminder to ",
            "add reminder to ",
        ):
            if lowered.startswith(prefix):
                trigger = prefix
                break

        if trigger is None:
            return None

        content = user_text[len(trigger) :].strip(" .")
        if not content:
            return {
                "title": "Untitled reminder",
                "details": user_text.strip(),
            }

        parsed = self._parse_schedule(content)
        reminder_request = {
            "title": parsed.title or "Untitled reminder",
            "details": user_text.strip(),
            "due_at": parsed.due_at,
            "schedule_hint": parsed.schedule_hint,
        }
        if parsed.recurrence_rule:
            reminder_request["recurrence_rule"] = parsed.recurrence_rule
        if parsed.recurrence_label:
            reminder_request["recurrence_label"] = parsed.recurrence_label
        return reminder_request

    def _parse_schedule(self, content: str) -> ParsedReminderSchedule:
        reference = self._now_provider()
        parsers = (
            self._parse_recurrence,
            self._parse_relative_duration,
            self._parse_day_keyword,
            self._parse_weekday,
            self._parse_explicit_date,
        )

        for parser in parsers:
            parsed = parser(content, reference)
            if parsed is not None:
                return parsed

        return ParsedReminderSchedule(
            title=self._clean_reminder_title(content),
            due_at=None,
            schedule_hint=None,
        )

    def _parse_recurrence(self, content: str, reference: datetime) -> ParsedReminderSchedule | None:
        weekday_match = re.search(
            r"\bevery\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)"
            r"(?:\s+at\s+([0-9]{1,2}(?::[0-9]{2})?\s*(?:am|pm)?))?",
            content,
            flags=re.IGNORECASE,
        )
        if weekday_match is not None:
            weekday_lookup = {
                "monday": 0,
                "tuesday": 1,
                "wednesday": 2,
                "thursday": 3,
                "friday": 4,
                "saturday": 5,
                "sunday": 6,
            }
            target_weekday = weekday_lookup[weekday_match.group(1).lower()]
            hour, minute = self._parse_time_text(weekday_match.group(2))
            if hour is None or minute is None:
                hour, minute = 9, 0

            due_time = reference.replace(hour=hour, minute=minute, second=0, microsecond=0)
            days_ahead = (target_weekday - reference.weekday()) % 7
            due_time = due_time + timedelta(days=days_ahead)
            if due_time <= reference:
                due_time = due_time + timedelta(days=7)

            title = self._remove_matched_text(content, weekday_match.span())
            label = weekday_match.group(0).strip()
            return ParsedReminderSchedule(
                title=title,
                due_at=due_time.isoformat(),
                schedule_hint=label,
                recurrence_rule="weekly",
                recurrence_label=label,
            )

        match = re.search(
            r"\bevery\s+(weekday|day|week)(?:\s+at\s+([0-9]{1,2}(?::[0-9]{2})?\s*(?:am|pm)?))?",
            content,
            flags=re.IGNORECASE,
        )
        if match is None:
            return None

        hour, minute = self._parse_time_text(match.group(2))
        if hour is None or minute is None:
            hour, minute = 9, 0

        recurrence_token = match.group(1).lower()
        due_time = reference.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if recurrence_token == "weekday":
            if due_time <= reference:
                due_time = due_time + timedelta(days=1)
            while due_time.weekday() >= 5:
                due_time = due_time + timedelta(days=1)
            recurrence_rule = "weekdays"
        elif recurrence_token == "week":
            if due_time <= reference:
                due_time = due_time + timedelta(days=7)
            recurrence_rule = "weekly"
        else:
            if due_time <= reference:
                due_time = due_time + timedelta(days=1)
            recurrence_rule = "daily"

        title = self._remove_matched_text(content, match.span())
        label = match.group(0).strip()
        return ParsedReminderSchedule(
            title=title,
            due_at=due_time.isoformat(),
            schedule_hint=label,
            recurrence_rule=recurrence_rule,
            recurrence_label=label,
        )

    def _parse_relative_duration(self, content: str, reference: datetime) -> ParsedReminderSchedule | None:
        match = re.search(r"\bin\s+(\d+)\s+(minute|minutes|hour|hours|day|days)\b", content, flags=re.IGNORECASE)
        if match is None:
            return None

        amount = int(match.group(1))
        unit = match.group(2).lower()
        if "minute" in unit:
            due_time = reference + timedelta(minutes=amount)
        elif "hour" in unit:
            due_time = reference + timedelta(hours=amount)
        else:
            due_time = reference + timedelta(days=amount)

        title = self._remove_matched_text(content, match.span())
        return ParsedReminderSchedule(
            title=title,
            due_at=due_time.isoformat(),
            schedule_hint=match.group(0).strip(),
        )

    def _parse_day_keyword(self, content: str, reference: datetime) -> ParsedReminderSchedule | None:
        match = re.search(
            r"\b(today|tomorrow)\b(?:\s+at\s+([0-9]{1,2}(?::[0-9]{2})?\s*(?:am|pm)?))?",
            content,
            flags=re.IGNORECASE,
        )
        if match is None:
            return None

        hour, minute = self._parse_time_text(match.group(2))
        if hour is None or minute is None:
            hour, minute = 9, 0

        day_offset = 0 if match.group(1).lower() == "today" else 1
        due_time = (reference + timedelta(days=day_offset)).replace(
            hour=hour,
            minute=minute,
            second=0,
            microsecond=0,
        )
        if match.group(1).lower() == "today" and due_time <= reference:
            due_time = due_time + timedelta(days=1)

        title = self._remove_matched_text(content, match.span())
        return ParsedReminderSchedule(
            title=title,
            due_at=due_time.isoformat(),
            schedule_hint=match.group(0).strip(),
        )

    def _parse_weekday(self, content: str, reference: datetime) -> ParsedReminderSchedule | None:
        match = re.search(
            r"\b(?:on\s+)?(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b"
            r"(?:\s+at\s+([0-9]{1,2}(?::[0-9]{2})?\s*(?:am|pm)?))?",
            content,
            flags=re.IGNORECASE,
        )
        if match is None:
            return None

        weekday_lookup = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }
        target_weekday = weekday_lookup[match.group(1).lower()]
        hour, minute = self._parse_time_text(match.group(2))
        if hour is None or minute is None:
            hour, minute = 9, 0

        days_ahead = (target_weekday - reference.weekday()) % 7
        due_time = (reference + timedelta(days=days_ahead)).replace(
            hour=hour,
            minute=minute,
            second=0,
            microsecond=0,
        )
        if due_time <= reference:
            due_time = due_time + timedelta(days=7)

        title = self._remove_matched_text(content, match.span())
        return ParsedReminderSchedule(
            title=title,
            due_at=due_time.isoformat(),
            schedule_hint=match.group(0).strip(),
        )

    def _parse_explicit_date(self, content: str, reference: datetime) -> ParsedReminderSchedule | None:
        match = re.search(
            r"\b(?:on\s+)?(\d{4}-\d{2}-\d{2})\b(?:\s+at\s+([0-9]{1,2}(?::[0-9]{2})?\s*(?:am|pm)?))?",
            content,
            flags=re.IGNORECASE,
        )
        if match is None:
            return None

        try:
            due_time = datetime.fromisoformat(match.group(1)).replace(tzinfo=reference.tzinfo)
        except ValueError:
            return None

        hour, minute = self._parse_time_text(match.group(2))
        if hour is None or minute is None:
            hour, minute = 9, 0
        due_time = due_time.replace(hour=hour, minute=minute, second=0, microsecond=0)

        title = self._remove_matched_text(content, match.span())
        return ParsedReminderSchedule(
            title=title,
            due_at=due_time.isoformat(),
            schedule_hint=match.group(0).strip(),
        )

    def _parse_time_text(self, value: str | None) -> tuple[int | None, int | None]:
        if not value:
            return None, None

        normalized = value.strip().lower().replace(" ", "")
        meridiem_match = re.fullmatch(r"(\d{1,2})(?::(\d{2}))?(am|pm)", normalized)
        if meridiem_match:
            hour = int(meridiem_match.group(1))
            minute = int(meridiem_match.group(2) or "0")
            if hour < 1 or hour > 12 or minute > 59:
                return None, None
            if meridiem_match.group(3) == "pm" and hour != 12:
                hour += 12
            if meridiem_match.group(3) == "am" and hour == 12:
                hour = 0
            return hour, minute

        simple_match = re.fullmatch(r"(\d{1,2})(?::(\d{2}))?", normalized)
        if simple_match:
            hour = int(simple_match.group(1))
            minute = int(simple_match.group(2) or "0")
            if hour > 23 or minute > 59:
                return None, None
            return hour, minute

        return None, None

    def _remove_matched_text(self, content: str, span: tuple[int, int]) -> str:
        start, end = span
        cleaned = f"{content[:start]} {content[end:]}".strip()
        return self._clean_reminder_title(cleaned)

    def _clean_reminder_title(self, value: str) -> str:
        cleaned = re.sub(r"\s+", " ", value).strip(" .,:;-")
        return cleaned or "Untitled reminder"

    def _summarize_reminder(self, reminder_request: dict[str, Any]) -> str:
        title = str(reminder_request.get("title", "Untitled reminder"))
        recurrence_label = reminder_request.get("recurrence_label")
        if recurrence_label:
            return f"Create a recurring reminder titled '{title}' for {recurrence_label}."
        schedule_hint = reminder_request.get("schedule_hint")
        if schedule_hint:
            return f"Create a reminder titled '{title}' for {schedule_hint}."
        return f"Create a reminder titled '{title}'."

    def _summarize_note_update(self, note_update_request: dict[str, Any]) -> str:
        query = str(note_update_request.get("query", "note"))
        mode = str(note_update_request.get("mode", "append"))
        if mode == "replace":
            return f"Replace the contents of the note '{query}'."
        return f"Append to the note '{query}'."

    def _summarize_document_inspection(self, document_inspection_request: dict[str, Any]) -> str:
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


class AssistantOrchestrator:
    def __init__(
        self,
        *,
        registry: ToolRegistry,
        policy: PolicyEngine,
        audit: AuditLogger,
        memory: ConversationMemoryStore,
        planner: AssistantPlanner | None = None,
        router: IntentRouter | None = None,
    ) -> None:
        self.registry = registry
        self.policy = policy
        self.audit = audit
        self.memory = memory
        self.router = router or IntentRouter()
        self.planner = planner or RuleBasedPlanner(self.router)
        self._pending_actions: dict[str, ProposedAction] = {}

    @property
    def pending_count(self) -> int:
        return len(self._pending_actions)

    def list_pending_actions(self) -> list[dict[str, Any]]:
        return [
            action.to_dict()
            for action in sorted(
                self._pending_actions.values(),
                key=lambda action: (
                    action.group_id or action.action_id,
                    action.sequence_index,
                    action.action_id,
                ),
            )
        ]

    def recent_history(self, *, session_id: str, limit: int = 12) -> list[dict[str, Any]]:
        history = self.memory.recent_turns(session_id=session_id, limit=limit)
        return list(reversed(history))

    @property
    def planner_info(self) -> dict[str, Any]:
        return self.planner.to_dict()

    def _record_audit(
        self,
        *,
        action: ProposedAction,
        status: ActionStatus,
        decision: PolicyDecision,
        result: Any | None = None,
        error: str | None = None,
        prerequisite_action: ProposedAction | None = None,
        prerequisite_status: ActionStatus | None = None,
    ) -> dict[str, Any]:
        return self.audit.record(
            action=action,
            status=status,
            decision=decision,
            result=result,
            error=error,
            trace=self._build_audit_trace(
                action,
                prerequisite_action=prerequisite_action,
                prerequisite_status=prerequisite_status,
                error=error,
            ),
        )

    def _build_audit_trace(
        self,
        action: ProposedAction,
        *,
        prerequisite_action: ProposedAction | None = None,
        prerequisite_status: ActionStatus | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        trace: dict[str, Any] = {
            "step_number": action.sequence_index + 1,
        }
        if action.group_id:
            trace["group_id"] = action.group_id
        if action.group_summary:
            trace["group_summary"] = action.group_summary

        prerequisite_action_id = action.depends_on_action_id
        if prerequisite_action is not None:
            prerequisite_action_id = prerequisite_action.action_id
            trace["prerequisite_step_number"] = prerequisite_action.sequence_index + 1
            trace["prerequisite_summary"] = prerequisite_action.summary

        if prerequisite_action_id:
            trace["prerequisite_action_id"] = prerequisite_action_id

        if prerequisite_status is not None:
            trace["prerequisite_status"] = prerequisite_status.value

        if error and prerequisite_action_id:
            trace["dependency_reason"] = error

        return trace

    def handle_message(self, user_text: str, *, session_id: str = "default") -> OrchestratorResponse:
        self.memory.save_turn(session_id=session_id, role="user", content=user_text)

        planning = self.planner.plan(
            user_text,
            tools=self.registry.list_tools(),
            history=self.recent_history(session_id=session_id, limit=6),
        )
        warnings: list[str] = list(planning.warnings)
        actions: list[ProposedAction] = []
        outcomes: list[ActionOutcome] = []
        routes = list(planning.routes)
        actionable_routes = [route for route in routes if route.tool_name is not None]
        response_intent, response_task_type = self._resolve_response_identity(routes)
        group_id = str(uuid4()) if len(actionable_routes) > 1 else None
        group_summary = planning.summary or "Multi-step request"

        if not actionable_routes:
            assistant_text = (
                "I can help with system info, local note editing, approved document search, reading, summaries, and structure inspection, web search handoff, approved app launches, workspace launchers, websites, reminders, local email drafts, approval-gated email sending, WhatsApp drafts, and approval-gated WhatsApp handoff."
            )
            response = OrchestratorResponse(
                assistant_text=assistant_text,
                intent=response_intent,
                task_type=response_task_type,
                warnings=self._dedupe_warnings(warnings),
                memory_enabled=self.memory.enabled,
            )
            self.memory.save_turn(session_id=session_id, role="assistant", content=assistant_text)
            return response

        blocked_messages: list[str] = []
        pending_dependency_action_id: str | None = None
        queued_warning_added = False
        created_actions_by_index: list[ProposedAction] = []

        for index, route in enumerate(actionable_routes):
            definition = self.registry.get_definition(route.tool_name)
            action = ProposedAction(
                action_id=str(uuid4()),
                session_id=session_id,
                tool_name=definition.name,
                category=definition.category,
                permission_level=definition.permission_level,
                approval_mode=ApprovalMode.NONE,
                summary=route.summary,
                group_id=group_id,
                group_summary=group_summary if group_id else None,
                sequence_index=index,
                arguments=route.arguments,
            )
            created_actions_by_index.append(action)
            decision = self.policy.evaluate(action)
            action.approval_mode = decision.approval_mode
            actions.append(action)

            dependency_action: ProposedAction | None = None
            if planning.dependencies_explicit and route.depends_on_route_index is not None:
                dependency_action = created_actions_by_index[route.depends_on_route_index]
            elif not planning.dependencies_explicit and pending_dependency_action_id is not None and decision.requires_confirmation:
                dependency_action = next(
                    (
                        prior_action
                        for prior_action in actions
                        if prior_action.action_id == pending_dependency_action_id
                    ),
                    None,
                )

            if not decision.allowed:
                action.status = ActionStatus.BLOCKED
                blocked_messages.append(decision.reason)
                warnings.append(decision.reason)
                self._record_audit(action=action, status=ActionStatus.BLOCKED, decision=decision, error=decision.reason)
                continue

            if dependency_action is not None:
                if dependency_action.status in {ActionStatus.BLOCKED, ActionStatus.FAILED, ActionStatus.REJECTED}:
                    reason = f"Prerequisite step '{dependency_action.summary}' did not complete."
                    action.status = ActionStatus.BLOCKED
                    blocked_messages.append(reason)
                    warnings.append(reason)
                    self._record_audit(
                        action=action,
                        status=ActionStatus.BLOCKED,
                        decision=decision,
                        error=reason,
                        prerequisite_action=dependency_action,
                        prerequisite_status=dependency_action.status,
                    )
                    continue

                if dependency_action.status in {ActionStatus.PROPOSED, ActionStatus.QUEUED}:
                    action.depends_on_action_id = dependency_action.action_id
                    action.status = ActionStatus.QUEUED
                    if not queued_warning_added:
                        warnings.append("Later approval steps are staged until earlier ones are confirmed.")
                        queued_warning_added = True
                    self._pending_actions[action.action_id] = action
                    self._record_audit(
                        action=action,
                        status=ActionStatus.QUEUED,
                        decision=decision,
                        prerequisite_action=dependency_action,
                        prerequisite_status=dependency_action.status,
                    )
                    if not planning.dependencies_explicit and decision.requires_confirmation:
                        pending_dependency_action_id = action.action_id
                    continue

            if decision.requires_confirmation:
                action.status = ActionStatus.PROPOSED
                warnings.append(decision.reason)
                self._pending_actions[action.action_id] = action
                self._record_audit(action=action, status=ActionStatus.PROPOSED, decision=decision)
                pending_dependency_action_id = action.action_id
                continue

            outcome = self._execute_action(action=action, decision=decision)
            outcomes.append(outcome)

        assistant_text = self._build_execution_response_text(
            routes=actionable_routes,
            actions=actions,
            outcomes=outcomes,
            blocked_messages=blocked_messages,
            planning_summary=planning.summary,
        )

        response = OrchestratorResponse(
            assistant_text=assistant_text,
            intent=response_intent,
            task_type=response_task_type,
            actions=actions,
            outcomes=outcomes,
            warnings=self._dedupe_warnings(warnings),
            memory_enabled=self.memory.enabled,
        )
        self.memory.save_turn(session_id=session_id, role="assistant", content=assistant_text)
        return response

    def _resolve_response_identity(self, routes: list[PlanningRoute]) -> tuple[str, str]:
        actionable_routes = [route for route in routes if route.tool_name is not None]
        if len(actionable_routes) > 1:
            return "multi_action", "compound"
        if actionable_routes:
            return actionable_routes[0].intent, actionable_routes[0].task_type
        if routes:
            return routes[0].intent, routes[0].task_type
        return "general_chat", "conversation"

    def _build_execution_response_text(
        self,
        *,
        routes: list[PlanningRoute],
        actions: list[ProposedAction],
        outcomes: list[ActionOutcome],
        blocked_messages: list[str],
        planning_summary: str | None,
    ) -> str:
        proposed_actions = [action for action in actions if action.status == ActionStatus.PROPOSED]
        queued_actions = [action for action in actions if action.status == ActionStatus.QUEUED]
        blocked_actions = [action for action in actions if action.status == ActionStatus.BLOCKED]

        if len(routes) == 1:
            if blocked_messages:
                return blocked_messages[0]
            if proposed_actions:
                return f"{routes[0].summary} This needs approval before I run it."
            if outcomes:
                return outcomes[0].message

        parts: list[str] = []
        if planning_summary:
            parts.append(planning_summary.rstrip(".") + ".")
        if outcomes:
            parts.append(
                self._build_count_sentence(
                    count=len(outcomes),
                    singular="action ran",
                    plural="actions ran",
                    details=[action.summary for action in actions if action.status == ActionStatus.EXECUTED],
                )
            )
        if proposed_actions:
            parts.append(
                self._build_count_sentence(
                    count=len(proposed_actions),
                    singular="action needs approval",
                    plural="actions need approval",
                    details=[action.summary for action in proposed_actions],
                )
            )
        if queued_actions:
            parts.append(
                self._build_count_sentence(
                    count=len(queued_actions),
                    singular="action is queued behind earlier approval",
                    plural="actions are queued behind earlier approval",
                    details=[action.summary for action in queued_actions],
                )
            )
        dependency_summary = self._build_dependency_branch_summary(actions)
        if dependency_summary:
            parts.append(dependency_summary)
        if blocked_actions:
            parts.append(
                self._build_count_sentence(
                    count=len(blocked_actions),
                    singular="action was blocked by policy",
                    plural="actions were blocked by policy",
                    details=[action.summary for action in blocked_actions],
                    include_details=False,
                )
            )

        cleaned_parts = [part.strip() for part in parts if part and part.strip()]
        if cleaned_parts:
            return " ".join(cleaned_parts)
        return "I reviewed that request but did not run any actions."

    def _build_count_sentence(
        self,
        *,
        count: int,
        singular: str,
        plural: str,
        details: list[str],
        include_details: bool = True,
    ) -> str:
        if count <= 0:
            return ""
        prefix = f"{count} {singular if count == 1 else plural}."
        if not include_details:
            return prefix
        fragments = [self._summary_fragment(detail) for detail in details if detail]
        if not fragments:
            return prefix
        detail_copy = self._format_phrase_list(fragments[:2])
        if count > 2:
            detail_copy = f"{detail_copy}, and more"
        return f"{prefix[:-1]}: {detail_copy}."

    def _summary_fragment(self, summary: str) -> str:
        return summary.strip().rstrip(".")

    def _format_phrase_list(self, fragments: list[str]) -> str:
        if not fragments:
            return ""
        if len(fragments) == 1:
            return fragments[0]
        if len(fragments) == 2:
            return f"{fragments[0]} and {fragments[1]}"
        return f"{', '.join(fragments[:-1])}, and {fragments[-1]}"

    def _build_dependency_branch_summary(self, actions: list[ProposedAction]) -> str:
        if len(actions) < 2:
            return ""

        actions_by_id = {action.action_id: action for action in actions}
        grouped_dependents: dict[str, list[ProposedAction]] = {}
        for action in actions:
            if not action.depends_on_action_id:
                continue
            grouped_dependents.setdefault(action.depends_on_action_id, []).append(action)

        if not grouped_dependents:
            return ""

        fragments: list[str] = []
        sorted_groups = sorted(
            grouped_dependents.items(),
            key=lambda item: actions_by_id.get(item[0]).sequence_index if actions_by_id.get(item[0]) is not None else 999,
        )
        for dependency_action_id, dependents in sorted_groups:
            dependency_action = actions_by_id.get(dependency_action_id)
            if dependency_action is None:
                continue

            prerequisite_step = f"step {dependency_action.sequence_index + 1}"
            dependent_steps = self._format_phrase_list(
                [
                    f"step {dependent.sequence_index + 1}"
                    for dependent in sorted(dependents, key=lambda action: action.sequence_index)
                ]
            )
            verb = "depends" if len(dependents) == 1 else "depend"
            fragments.append(f"{dependent_steps} {verb} on {prerequisite_step}")

        if not fragments:
            return ""
        return f"Dependency branches: {'; '.join(fragments)}."

    def _dedupe_warnings(self, warnings: list[str]) -> list[str]:
        deduped: list[str] = []
        seen: set[str] = set()
        for warning in warnings:
            if warning in seen:
                continue
            seen.add(warning)
            deduped.append(warning)
        return deduped

    def _group_pending_actions(self, group_id: str) -> list[ProposedAction]:
        return sorted(
            [
                action
                for action in self._pending_actions.values()
                if action.group_id == group_id
            ],
            key=lambda action: (action.sequence_index, action.action_id),
        )

    def _build_group_resolution_message(
        self,
        *,
        actions: list[ProposedAction],
        outcomes: list[ActionOutcome],
        rejection: bool,
        fallback_message: str | None = None,
    ) -> str:
        if len(actions) == 1:
            if rejection:
                return fallback_message or "Action rejected. No changes were made."
            if outcomes:
                return outcomes[0].message

        group_summary = actions[0].group_summary or "Multi-step request"
        if rejection:
            return (
                f"{group_summary.rstrip('.')} was rejected. "
                f"Removed {len(actions)} pending action{'s' if len(actions) != 1 else ''}."
            )

        executed_actions = [
            action.summary
            for action, outcome in zip(actions, outcomes, strict=False)
            if outcome.status == ActionStatus.EXECUTED
        ]
        failed_count = len([outcome for outcome in outcomes if outcome.status == ActionStatus.FAILED])
        blocked_count = len([outcome for outcome in outcomes if outcome.status == ActionStatus.BLOCKED])
        parts = [f"{group_summary.rstrip('.')} approved."]
        if executed_actions:
            parts.append(
                self._build_count_sentence(
                    count=len(executed_actions),
                    singular="action ran",
                    plural="actions ran",
                    details=executed_actions,
                )
            )
        if failed_count:
            parts.append(
                self._build_count_sentence(
                    count=failed_count,
                    singular="action failed",
                    plural="actions failed",
                    details=[],
                    include_details=False,
                )
            )
        if blocked_count:
            parts.append(
                self._build_count_sentence(
                    count=blocked_count,
                    singular="dependent action was blocked",
                    plural="dependent actions were blocked",
                    details=[],
                    include_details=False,
                )
            )
        dependency_summary = self._build_dependency_branch_summary(actions)
        if dependency_summary:
            parts.append(dependency_summary)
        return " ".join(part for part in parts if part)

    def confirm_action(self, action_id: str, *, confirmation: str | None = None) -> OrchestratorResponse:
        action = self._pending_actions.get(action_id)
        if action is None:
            return OrchestratorResponse(
                assistant_text="I could not find that pending action.",
                intent="action_confirmation",
                task_type="approval",
                warnings=["The action may have already run or expired."],
                memory_enabled=self.memory.enabled,
            )

        if action.status == ActionStatus.QUEUED:
            return OrchestratorResponse(
                assistant_text="This action is waiting on an earlier approval step. Approve that step first.",
                intent="action_confirmation",
                task_type="approval",
                actions=[action],
                warnings=["Dependent step is still queued."],
                memory_enabled=self.memory.enabled,
            )

        decision = self.policy.evaluate(action)
        if decision.approval_mode == ApprovalMode.STRONG_CONFIRMATION and confirmation != "CONFIRM":
            return OrchestratorResponse(
                assistant_text="Strong confirmation is required. Reply with CONFIRM to continue.",
                intent="action_confirmation",
                task_type="approval",
                actions=[action],
                warnings=["Strong confirmation required."],
                memory_enabled=self.memory.enabled,
            )

        outcome = self._execute_action(action=action, decision=decision)
        self._pending_actions.pop(action_id, None)
        activated_actions, released_outcomes, removed_actions = (
            self._activate_dependent_actions(action)
            if outcome.status == ActionStatus.EXECUTED
            else ([], [], self._reject_dependent_actions(action, reason=outcome.message))
        )
        message = outcome.message
        if activated_actions:
            message = f"{message} {self._build_activation_message(activated_actions)}"
        if released_outcomes:
            message = f"{message} {self._build_release_outcome_message(released_outcomes)}"
        if removed_actions:
            message = f"{message} {len(removed_actions)} dependent step{'s were' if len(removed_actions) != 1 else ' was'} removed."
        response = OrchestratorResponse(
            assistant_text=message,
            intent="action_confirmation",
            task_type="approval",
            actions=[action, *activated_actions, *removed_actions],
            outcomes=[outcome, *released_outcomes],
            memory_enabled=self.memory.enabled,
        )
        self.memory.save_turn(session_id=action.session_id, role="assistant", content=message)
        return response

    def confirm_action_group(self, group_id: str, *, confirmation: str | None = None) -> OrchestratorResponse:
        actions = self._group_pending_actions(group_id)
        if not actions:
            return OrchestratorResponse(
                assistant_text="I could not find that pending action group.",
                intent="action_confirmation",
                task_type="approval",
                warnings=["The group may have already run or expired."],
                memory_enabled=self.memory.enabled,
            )

        decisions = [self.policy.evaluate(action) for action in actions]
        if any(decision.approval_mode == ApprovalMode.STRONG_CONFIRMATION for decision in decisions):
            if confirmation != "CONFIRM":
                return OrchestratorResponse(
                    assistant_text="Strong confirmation is required. Reply with CONFIRM to continue.",
                    intent="action_confirmation",
                    task_type="approval",
                    actions=actions,
                    warnings=["Strong confirmation required for this action group."],
                    memory_enabled=self.memory.enabled,
                )

        outcomes: list[ActionOutcome] = []
        outcome_by_action_id: dict[str, ActionOutcome] = {}
        action_by_id = {action.action_id: action for action in actions}
        for action, decision in zip(actions, decisions, strict=False):
            dependency_action_id = action.depends_on_action_id
            dependency_action: ProposedAction | None = None
            dependency_outcome: ActionOutcome | None = None
            if dependency_action_id:
                dependency_outcome = outcome_by_action_id.get(dependency_action_id)
                dependency_action = action_by_id.get(dependency_action_id)
                if dependency_outcome is None or dependency_outcome.status != ActionStatus.EXECUTED:
                    dependency_summary = dependency_action.summary if dependency_action is not None else "an earlier step"
                    outcome = self._block_action(
                        action,
                        decision=decision,
                        reason=f"Prerequisite step '{dependency_summary}' did not complete.",
                        prerequisite_action=dependency_action,
                        prerequisite_status=dependency_outcome.status if dependency_outcome is not None else None,
                    )
                    outcomes.append(outcome)
                    outcome_by_action_id[action.action_id] = outcome
                    continue

            outcome = self._execute_action(
                action=action,
                decision=decision,
                prerequisite_action=dependency_action,
                prerequisite_status=dependency_outcome.status if dependency_action_id else None,
            )
            outcomes.append(outcome)
            outcome_by_action_id[action.action_id] = outcome
            self._pending_actions.pop(action.action_id, None)

        message = self._build_group_resolution_message(
            actions=actions,
            outcomes=outcomes,
            rejection=False,
        )
        response = OrchestratorResponse(
            assistant_text=message,
            intent="action_confirmation",
            task_type="approval",
            actions=actions,
            outcomes=outcomes,
            memory_enabled=self.memory.enabled,
        )
        self.memory.save_turn(session_id=actions[0].session_id, role="assistant", content=message)
        return response

    def reject_action(self, action_id: str, *, reason: str | None = None) -> OrchestratorResponse:
        action = self._pending_actions.pop(action_id, None)
        if action is None:
            return OrchestratorResponse(
                assistant_text="I could not find that pending action.",
                intent="action_rejection",
                task_type="approval",
                warnings=["The action may have already been resolved."],
                memory_enabled=self.memory.enabled,
            )

        action.status = ActionStatus.REJECTED
        decision = self.policy.evaluate(action)
        message = reason or "Action rejected. No changes were made."
        self._record_audit(action=action, status=ActionStatus.REJECTED, decision=decision, error=message)
        rejected_dependents = self._reject_dependent_actions(action, reason=message)
        response_message = message
        if rejected_dependents:
            response_message = (
                f"{message} "
                f"{len(rejected_dependents)} dependent step{'s were' if len(rejected_dependents) != 1 else ' was'} also removed."
            )
        self.memory.save_turn(session_id=action.session_id, role="assistant", content=response_message)
        return OrchestratorResponse(
            assistant_text=response_message,
            intent="action_rejection",
            task_type="approval",
            actions=[action, *rejected_dependents],
            warnings=["Pending action removed."],
            memory_enabled=self.memory.enabled,
        )

    def reject_action_group(self, group_id: str, *, reason: str | None = None) -> OrchestratorResponse:
        actions = self._group_pending_actions(group_id)
        if not actions:
            return OrchestratorResponse(
                assistant_text="I could not find that pending action group.",
                intent="action_rejection",
                task_type="approval",
                warnings=["The group may have already been resolved."],
                memory_enabled=self.memory.enabled,
            )

        decisions = [self.policy.evaluate(action) for action in actions]
        message = reason or "Action group rejected. No changes were made."
        for action, decision in zip(actions, decisions, strict=False):
            self._pending_actions.pop(action.action_id, None)
            action.status = ActionStatus.REJECTED
            prerequisite_action = None
            prerequisite_status = None
            if action.depends_on_action_id:
                prerequisite_action = next(
                    (candidate for candidate in actions if candidate.action_id == action.depends_on_action_id),
                    None,
                )
                prerequisite_status = prerequisite_action.status if prerequisite_action is not None else None
            self._record_audit(
                action=action,
                status=ActionStatus.REJECTED,
                decision=decision,
                error=message,
                prerequisite_action=prerequisite_action,
                prerequisite_status=prerequisite_status,
            )

        response_message = self._build_group_resolution_message(
            actions=actions,
            outcomes=[],
            rejection=True,
            fallback_message=message,
        )
        self.memory.save_turn(session_id=actions[0].session_id, role="assistant", content=response_message)
        return OrchestratorResponse(
            assistant_text=response_message,
            intent="action_rejection",
            task_type="approval",
            actions=actions,
            warnings=["Pending action group removed."],
            memory_enabled=self.memory.enabled,
        )

    def _block_action(
        self,
        action: ProposedAction,
        *,
        decision: PolicyDecision,
        reason: str,
        prerequisite_action: ProposedAction | None = None,
        prerequisite_status: ActionStatus | None = None,
    ) -> ActionOutcome:
        action.status = ActionStatus.BLOCKED
        self._pending_actions.pop(action.action_id, None)
        self._record_audit(
            action=action,
            status=ActionStatus.BLOCKED,
            decision=decision,
            error=reason,
            prerequisite_action=prerequisite_action,
            prerequisite_status=prerequisite_status,
        )
        return ActionOutcome(
            action_id=action.action_id,
            status=ActionStatus.BLOCKED,
            message=reason,
            result={},
        )

    def _activate_dependent_actions(
        self,
        action: ProposedAction,
    ) -> tuple[list[ProposedAction], list[ActionOutcome], list[ProposedAction]]:
        activated: list[ProposedAction] = []
        outcomes: list[ActionOutcome] = []
        removed: list[ProposedAction] = []
        for pending_action in sorted(
            self._pending_actions.values(),
            key=lambda candidate: (candidate.sequence_index, candidate.action_id),
        ):
            if pending_action.depends_on_action_id != action.action_id:
                continue
            if pending_action.status != ActionStatus.QUEUED:
                continue

            decision = self.policy.evaluate(pending_action)
            pending_action.approval_mode = decision.approval_mode
            pending_action.depends_on_action_id = None
            if not decision.allowed:
                pending_action.status = ActionStatus.BLOCKED
                self._block_action(
                    pending_action,
                    decision=decision,
                    reason=decision.reason,
                    prerequisite_action=action,
                    prerequisite_status=action.status,
                )
                removed.append(pending_action)
                removed.extend(self._reject_dependent_actions(pending_action, reason=decision.reason))
                continue

            if decision.requires_confirmation:
                pending_action.status = ActionStatus.PROPOSED
                self._record_audit(
                    action=pending_action,
                    status=ActionStatus.PROPOSED,
                    decision=decision,
                    prerequisite_action=action,
                    prerequisite_status=action.status,
                )
                activated.append(pending_action)
                continue

            outcome = self._execute_action(
                action=pending_action,
                decision=decision,
                prerequisite_action=action,
                prerequisite_status=action.status,
            )
            self._pending_actions.pop(pending_action.action_id, None)
            outcomes.append(outcome)
            next_activated, next_outcomes, next_removed = self._activate_dependent_actions(pending_action)
            activated.extend(next_activated)
            outcomes.extend(next_outcomes)
            removed.extend(next_removed)
        return activated, outcomes, removed

    def _build_activation_message(self, actions: list[ProposedAction]) -> str:
        return self._build_count_sentence(
            count=len(actions),
            singular="next action is ready for approval",
            plural="next actions are ready for approval",
            details=[action.summary for action in actions],
        )

    def _build_release_outcome_message(self, outcomes: list[ActionOutcome]) -> str:
        return self._build_count_sentence(
            count=len(outcomes),
            singular="dependent action ran automatically",
            plural="dependent actions ran automatically",
            details=[outcome.message for outcome in outcomes],
        )

    def _reject_dependent_actions(self, action: ProposedAction, *, reason: str) -> list[ProposedAction]:
        rejected: list[ProposedAction] = []
        queue = [action.action_id]
        known_actions_by_id = {action.action_id: action}

        while queue:
            dependency_action_id = queue.pop(0)
            dependents = sorted(
                [
                    pending_action
                    for pending_action in self._pending_actions.values()
                    if pending_action.depends_on_action_id == dependency_action_id
                ],
                key=lambda candidate: (candidate.sequence_index, candidate.action_id),
            )
            for dependent in dependents:
                queue.append(dependent.action_id)
                self._pending_actions.pop(dependent.action_id, None)
                dependent.status = ActionStatus.REJECTED
                decision = self.policy.evaluate(dependent)
                prerequisite_action = known_actions_by_id.get(dependency_action_id)
                self._record_audit(
                    action=dependent,
                    status=ActionStatus.REJECTED,
                    decision=decision,
                    error=reason,
                    prerequisite_action=prerequisite_action,
                    prerequisite_status=prerequisite_action.status if prerequisite_action is not None else None,
                )
                known_actions_by_id[dependent.action_id] = dependent
                rejected.append(dependent)

        return rejected

    def _execute_action(
        self,
        *,
        action: ProposedAction,
        decision: PolicyDecision,
        prerequisite_action: ProposedAction | None = None,
        prerequisite_status: ActionStatus | None = None,
    ) -> ActionOutcome:
        action.status = ActionStatus.APPROVED
        result = self.registry.execute(action)

        if result.success:
            action.status = ActionStatus.EXECUTED
            self._record_audit(
                action=action,
                status=ActionStatus.EXECUTED,
                decision=decision,
                result=result,
                prerequisite_action=prerequisite_action,
                prerequisite_status=prerequisite_status,
            )
            return ActionOutcome(
                action_id=action.action_id,
                status=ActionStatus.EXECUTED,
                message=result.message,
                result=result.to_dict(),
            )

        action.status = ActionStatus.FAILED
        self._record_audit(
            action=action,
            status=ActionStatus.FAILED,
            decision=decision,
            result=result,
            error=result.message,
            prerequisite_action=prerequisite_action,
            prerequisite_status=prerequisite_status,
        )
        return ActionOutcome(
            action_id=action.action_id,
            status=ActionStatus.FAILED,
            message=result.message,
            result=result.to_dict(),
        )

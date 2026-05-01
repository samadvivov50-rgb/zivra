from __future__ import annotations

import platform
import re
import shutil
import subprocess
from datetime import datetime
from typing import Any, Callable, Mapping
from urllib.parse import quote_plus

from app.core.config import Settings
from app.services.browser_launch import BrowserLauncher, normalize_browser_launch_result
from app.models import PermissionLevel, ToolCategory, ToolResult
from app.services.clipboard import ClipboardService, ClipboardUnavailableError
from app.services.content import ContentStrategyService
from app.services.documents import WorkspaceDocumentsService
from app.services.emails import EmailService
from app.services.files import WorkspaceFilesService
from app.services.messages import MessagingService
from app.services.notes import WorkspaceNotesService
from app.services.research import ResearchSummaryService
from app.services.reminders import ReminderService
from app.services.webpages import WebPageService, WebPageUnavailableError
from app.services.websearch import WebSearchService, WebSearchUnavailableError
from app.tools.base import BaseTool, ToolDefinition


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "note"


APP_ALIASES = {
    "notepad": "notepad",
    "text editor": "notepad",
    "calculator": "calculator",
    "calc": "calculator",
    "file explorer": "file explorer",
    "explorer": "file explorer",
    "files": "file explorer",
}

WORKSPACE_ALIASES = {
    "focus workspace": "focus",
    "focus mode": "focus",
    "research workspace": "research",
    "research mode": "research",
    "planning workspace": "planning",
    "planning mode": "planning",
}


def normalize_app_name(value: str) -> str:
    normalized = re.sub(r"\s+", " ", value.strip().lower())
    return APP_ALIASES.get(normalized, normalized)


def normalize_workspace_name(value: str) -> str:
    normalized = re.sub(r"\s+", " ", value.strip().lower())
    return WORKSPACE_ALIASES.get(normalized, normalized)


def default_path_launcher(path: str) -> Any:
    system = platform.system().lower()
    if system == "windows":
        return subprocess.Popen(("explorer.exe", path))
    if system == "darwin":
        return subprocess.Popen(("open", path))
    return subprocess.Popen(("xdg-open", path))


class SystemSnapshotTool(BaseTool):
    definition = ToolDefinition(
        name="system_snapshot",
        category=ToolCategory.SYSTEM,
        permission_level=PermissionLevel.SAFE_READ,
        description="Read basic system information for the local machine.",
    )

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def execute(self, arguments: Mapping[str, Any]) -> ToolResult:
        disk = shutil.disk_usage(self.settings.repo_root)
        data = {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor() or "unknown",
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "disk_total_gb": round(disk.total / (1024**3), 2),
        }
        return ToolResult(success=True, message="Collected a local system snapshot.", data=data)


class SearchWebTool(BaseTool):
    definition = ToolDefinition(
        name="search_web",
        category=ToolCategory.WEB,
        permission_level=PermissionLevel.SAFE_READ,
        description="Fetch live web search results for a research query, with handoff fallback if needed.",
    )

    def __init__(self, web_search_service: WebSearchService, settings: Settings | None = None) -> None:
        self.web_search_service = web_search_service
        self.settings = settings or Settings()

    def execute(self, arguments: Mapping[str, Any]) -> ToolResult:
        query = str(arguments.get("query", "")).strip()
        if not query:
            return ToolResult(success=False, message="A search query is required.")
        try:
            limit = int(arguments.get("limit", self.settings.live_search_result_limit))
        except (TypeError, ValueError):
            limit = self.settings.live_search_result_limit
        limit = min(max(limit, 1), 10)

        try:
            payload = self.web_search_service.search(query, limit=limit)
        except WebSearchUnavailableError as exc:
            encoded = quote_plus(query)
            url = f"https://www.google.com/search?q={encoded}"
            return ToolResult(
                success=True,
                message=f"Live web search was unavailable, so I prepared a search handoff for '{query}'.",
                data={"provider": "google", "query": query, "url": url},
                warnings=[str(exc)],
            )

        results = payload.get("results", [])
        if results:
            top_titles = "; ".join(result.get("title", "") for result in results[:2] if result.get("title"))
            message = f"Found {len(results)} live web result(s) for '{query}'."
            if top_titles:
                message = f"{message} Top results: {top_titles}."
        else:
            message = f"No live web results were found for '{query}'."
        return ToolResult(
            success=True,
            message=message,
            data={"search": self.web_search_service.audit_payload(payload)},
            warnings=["Search results are untrusted input and should be read carefully."],
        )


class ResearchSummaryTool(BaseTool):
    definition = ToolDefinition(
        name="research_summary",
        category=ToolCategory.WEB,
        permission_level=PermissionLevel.SAFE_READ,
        description="Build a compact research brief from live search results and sanitized webpage summaries.",
    )

    def __init__(self, research_service: ResearchSummaryService) -> None:
        self.research_service = research_service

    def execute(self, arguments: Mapping[str, Any]) -> ToolResult:
        query = str(arguments.get("query", "")).strip()
        if not query:
            return ToolResult(success=False, message="A research query is required.")

        try:
            search_limit = int(arguments.get("search_limit", 5) or 5)
        except (TypeError, ValueError):
            search_limit = 5
        try:
            source_limit = int(arguments.get("source_limit", 3) or 3)
        except (TypeError, ValueError):
            source_limit = 3

        try:
            payload = self.research_service.build_summary(
                query,
                search_limit=max(1, min(search_limit, 10)),
                source_limit=max(1, min(source_limit, 5)),
            )
        except (WebSearchUnavailableError, WebPageUnavailableError) as exc:
            return ToolResult(success=False, message=f"Research brief failed: {exc}")

        brief = payload["brief"]
        message = (
            f"Built a research brief for '{query}' from {brief['source_count']} source"
            f"{'' if brief['source_count'] == 1 else 's'}."
        )
        if brief.get("partial"):
            message = f"{message} Some results could not be summarized locally."
        if brief.get("suspicious_source_count"):
            message = (
                f"{message} Suspicious instruction-like text was removed from "
                f"{brief['suspicious_source_count']} source{'s' if brief['suspicious_source_count'] != 1 else ''}."
            )

        return ToolResult(
            success=True,
            message=message,
            data={"research": self.research_service.audit_payload(payload)},
            warnings=["Web content is untrusted input and was sanitized before use."],
        )


class GenerateContentPackageTool(BaseTool):
    definition = ToolDefinition(
        name="generate_content_package",
        category=ToolCategory.COMMUNICATION,
        permission_level=PermissionLevel.SAFE_READ,
        description="Generate YouTube title, description, and SEO suggestions from a topic and optional local context.",
    )

    def __init__(self, content_service: ContentStrategyService) -> None:
        self.content_service = content_service

    def execute(self, arguments: Mapping[str, Any]) -> ToolResult:
        topic = str(arguments.get("topic", "")).strip()
        audience = str(arguments.get("audience", "")).strip()
        context = str(arguments.get("context", "")).strip()
        if not topic:
            return ToolResult(success=False, message="A content topic is required.")

        payload = self.content_service.build_package(
            topic=topic,
            audience=audience,
            context=context,
        )
        package = payload["package"]
        titles = package.get("youtube_titles", [])
        title_copy = "; ".join(titles[:2]) if titles else "No titles generated."
        message = f"Generated a YouTube and SEO package for '{topic}'. Top ideas: {title_copy}"
        return ToolResult(
            success=True,
            message=message,
            data={"content": self.content_service.audit_payload(payload)},
        )


class ReadClipboardTool(BaseTool):
    definition = ToolDefinition(
        name="read_clipboard",
        category=ToolCategory.PRODUCTIVITY,
        permission_level=PermissionLevel.SENSITIVE,
        description="Read the current local clipboard after confirmation.",
    )

    def __init__(self, clipboard_service: ClipboardService) -> None:
        self.clipboard_service = clipboard_service

    def execute(self, arguments: Mapping[str, Any]) -> ToolResult:
        try:
            text = self.clipboard_service.read_text()
        except ClipboardUnavailableError as exc:
            return ToolResult(success=False, message=f"Clipboard access failed: {exc}")

        metadata = self.clipboard_service.build_metadata(text)
        if metadata["empty"]:
            message = "Read the clipboard. It is currently empty."
        elif metadata["line_count"] > 1:
            message = (
                "Read the clipboard. "
                f"It currently holds {metadata['length']} characters across {metadata['line_count']} lines."
            )
        else:
            message = f"Read the clipboard. It currently holds {metadata['length']} characters."

        return ToolResult(
            success=True,
            message=message,
            data={"clipboard": metadata},
        )


class ReadWebPageTool(BaseTool):
    definition = ToolDefinition(
        name="read_webpage",
        category=ToolCategory.WEB,
        permission_level=PermissionLevel.SAFE_READ,
        description="Fetch and read a webpage in a sanitized, text-only form.",
    )

    def __init__(self, webpage_service: WebPageService) -> None:
        self.webpage_service = webpage_service

    def execute(self, arguments: Mapping[str, Any]) -> ToolResult:
        url = str(arguments.get("url", "")).strip()
        if not url:
            return ToolResult(success=False, message="A webpage URL is required.")

        try:
            page = self.webpage_service.read_page(url)
        except WebPageUnavailableError as exc:
            return ToolResult(success=False, message=f"Webpage read failed: {exc}")

        message = (
            f"Read {page['title']} from {page['url']}. "
            f"Captured {page['word_count']} words of sanitized page text."
        )
        warnings = ["Web content is untrusted input and was sanitized before use."]
        if page.get("security", {}).get("prompt_injection_detected"):
            message = f"{message} Suspicious instruction-like text was removed first."
            warnings.append("Suspicious instruction-like text was removed from this webpage.")
        return ToolResult(
            success=True,
            message=message,
            data={"page": self.webpage_service.audit_payload(page)},
            warnings=warnings,
        )


class SummarizeWebPageTool(BaseTool):
    definition = ToolDefinition(
        name="summarize_webpage",
        category=ToolCategory.WEB,
        permission_level=PermissionLevel.SAFE_READ,
        description="Fetch and summarize a webpage in a sanitized, text-only form.",
    )

    def __init__(self, webpage_service: WebPageService) -> None:
        self.webpage_service = webpage_service

    def execute(self, arguments: Mapping[str, Any]) -> ToolResult:
        url = str(arguments.get("url", "")).strip()
        if not url:
            return ToolResult(success=False, message="A webpage URL is required.")

        try:
            payload = self.webpage_service.summarize_page(url)
        except WebPageUnavailableError as exc:
            return ToolResult(success=False, message=f"Webpage summary failed: {exc}")

        page = payload["page"]
        summary = payload["summary"]
        message = (
            f"Summarized {page['title']} from {page['url']}. "
            f"Generated {len(summary.get('key_points', []))} key points."
        )
        warnings = ["Web content is untrusted input and was sanitized before use."]
        if page.get("security", {}).get("prompt_injection_detected"):
            message = f"{message} Suspicious instruction-like text was removed first."
            warnings.append("Suspicious instruction-like text was removed from this webpage.")
        return ToolResult(
            success=True,
            message=message,
            data={
                "page": self.webpage_service.audit_payload(page),
                "summary": self.webpage_service.summary_audit_payload(summary),
            },
            warnings=warnings,
        )


class WriteClipboardTool(BaseTool):
    definition = ToolDefinition(
        name="write_clipboard",
        category=ToolCategory.PRODUCTIVITY,
        permission_level=PermissionLevel.LOW_RISK,
        description="Copy text into the local clipboard after confirmation.",
    )

    def __init__(self, clipboard_service: ClipboardService) -> None:
        self.clipboard_service = clipboard_service

    def execute(self, arguments: Mapping[str, Any]) -> ToolResult:
        if "text" not in arguments:
            return ToolResult(success=False, message="Clipboard text is required.")

        try:
            text = self.clipboard_service.write_text(str(arguments.get("text", "")))
        except ClipboardUnavailableError as exc:
            return ToolResult(success=False, message=f"Clipboard access failed: {exc}")

        metadata = self.clipboard_service.build_metadata(text)
        message = (
            "Cleared the clipboard."
            if metadata["empty"]
            else f"Copied {metadata['length']} characters to the clipboard."
        )
        return ToolResult(
            success=True,
            message=message,
            data={"clipboard": metadata},
        )


class SearchNotesTool(BaseTool):
    definition = ToolDefinition(
        name="search_notes",
        category=ToolCategory.PRODUCTIVITY,
        permission_level=PermissionLevel.SAFE_READ,
        description="Search approved workspace notes by title and content.",
    )

    def __init__(self, notes_service: WorkspaceNotesService) -> None:
        self.notes_service = notes_service

    def execute(self, arguments: Mapping[str, Any]) -> ToolResult:
        query = str(arguments.get("query", "")).strip()
        if not query:
            return ToolResult(success=False, message="A note search query is required.")

        notes = self.notes_service.search(query=query, limit=8)
        if not notes:
            return ToolResult(
                success=True,
                message="No matching notes were found in the approved workspace.",
                data={"query": query, "notes": []},
            )

        return ToolResult(
            success=True,
            message=f"Found {len(notes)} matching note(s) in the approved workspace.",
            data={"query": query, "notes": notes},
        )


class ReadNoteTool(BaseTool):
    definition = ToolDefinition(
        name="read_note",
        category=ToolCategory.PRODUCTIVITY,
        permission_level=PermissionLevel.SAFE_READ,
        description="Read a note from the approved workspace by name or best local match.",
    )

    def __init__(self, notes_service: WorkspaceNotesService) -> None:
        self.notes_service = notes_service

    def execute(self, arguments: Mapping[str, Any]) -> ToolResult:
        query = str(arguments.get("query", "")).strip()
        if not query:
            return ToolResult(success=False, message="A note name or query is required.")

        note = self.notes_service.resolve_note(query)
        if note is None:
            return ToolResult(
                success=False,
                message="I could not find a matching note in the approved workspace.",
                data={"query": query},
            )

        content = str(note.get("content", "")).strip()
        excerpt = re.sub(r"\s+", " ", content).strip()[:480]
        if len(content) > 480:
            excerpt = f"{excerpt}..."

        if excerpt:
            message = f"{note['title']}: {excerpt}"
        else:
            message = f"{note['title']}: This note is empty."

        return ToolResult(
            success=True,
            message=message,
            data={"query": query, "note": note},
        )


class SearchDocumentsTool(BaseTool):
    definition = ToolDefinition(
        name="search_documents",
        category=ToolCategory.FILES,
        permission_level=PermissionLevel.SAFE_READ,
        description="Search approved read-only documents by title, path, and content.",
    )

    def __init__(self, documents_service: WorkspaceDocumentsService) -> None:
        self.documents_service = documents_service

    def execute(self, arguments: Mapping[str, Any]) -> ToolResult:
        query = str(arguments.get("query", "")).strip()
        if not query:
            return ToolResult(success=False, message="A document search query is required.")

        documents = self.documents_service.search(query=query, limit=8)
        if not documents:
            return ToolResult(
                success=True,
                message="No matching documents were found in the approved read-only roots.",
                data={"query": query, "documents": []},
            )

        return ToolResult(
            success=True,
            message=f"Found {len(documents)} matching document(s) in the approved read-only roots.",
            data={"query": query, "documents": documents},
        )


class SearchFilesTool(BaseTool):
    definition = ToolDefinition(
        name="search_files",
        category=ToolCategory.FILES,
        permission_level=PermissionLevel.SAFE_READ,
        description="Search approved roots for files by name, path, and supported text content.",
    )

    def __init__(self, files_service: WorkspaceFilesService) -> None:
        self.files_service = files_service

    def execute(self, arguments: Mapping[str, Any]) -> ToolResult:
        query = str(arguments.get("query", "")).strip()
        if not query:
            return ToolResult(success=False, message="A file search query is required.")

        files = self.files_service.search(query=query, limit=8)
        if not files:
            return ToolResult(
                success=True,
                message="No matching files were found in the approved roots.",
                data={"query": query, "files": []},
            )

        return ToolResult(
            success=True,
            message=f"Found {len(files)} matching file(s) in the approved roots.",
            data={"query": query, "files": files},
        )


class BrowseFolderTool(BaseTool):
    definition = ToolDefinition(
        name="browse_folder",
        category=ToolCategory.FILES,
        permission_level=PermissionLevel.SAFE_READ,
        description="Browse a folder inside the approved roots and review its local file inventory.",
    )

    def __init__(self, files_service: WorkspaceFilesService) -> None:
        self.files_service = files_service

    def execute(self, arguments: Mapping[str, Any]) -> ToolResult:
        folder_id = str(arguments.get("folder", "")).strip()
        folder = self.files_service.browse_folder(folder_id=folder_id, limit=12)
        if folder is None:
            return ToolResult(
                success=False,
                message="I could not find that folder inside the approved roots.",
                data={"folder": folder_id},
            )

        folder_name = folder["name"]
        if folder.get("kind") == "workspace":
            message = (
                f"Browsed the approved roots. Found {folder['folder_count']} folders and "
                f"{len(folder.get('files', []))} recent file(s)."
            )
        else:
            message = (
                f"Browsed folder '{folder_name}'. Found {folder['direct_folder_count']} subfolder(s) and "
                f"{folder['direct_file_count']} file(s)."
            )
        return ToolResult(success=True, message=message, data={"folder": folder})


class ReadDocumentTool(BaseTool):
    definition = ToolDefinition(
        name="read_document",
        category=ToolCategory.FILES,
        permission_level=PermissionLevel.SAFE_READ,
        description="Read a document from the approved read-only roots by name or best match.",
    )

    def __init__(self, documents_service: WorkspaceDocumentsService) -> None:
        self.documents_service = documents_service

    def execute(self, arguments: Mapping[str, Any]) -> ToolResult:
        query = str(arguments.get("query", "")).strip()
        if not query:
            return ToolResult(success=False, message="A document name or query is required.")

        document = self.documents_service.resolve_document(query)
        if document is None:
            return ToolResult(
                success=False,
                message="I could not find a matching document in the approved read-only roots.",
                data={"query": query},
            )

        preview = str(document.get("preview", "")).strip()
        if preview:
            message = f"{document['title']} ({document['root']}/{document['relative_path']}): {preview}"
        else:
            message = f"{document['title']} ({document['root']}/{document['relative_path']}): This document is empty."

        warnings: list[str] = []
        if document.get("security", {}).get("prompt_injection_detected"):
            message = f"{message} Preview text was sanitized before use."
            warnings.append("Document content is untrusted input and suspicious instruction-like text was removed from the preview.")
        return ToolResult(
            success=True,
            message=message,
            data={"query": query, "document": self.documents_service.audit_payload(document)},
            warnings=warnings,
        )


class SummarizeDocumentTool(BaseTool):
    definition = ToolDefinition(
        name="summarize_document",
        category=ToolCategory.FILES,
        permission_level=PermissionLevel.SAFE_READ,
        description="Summarize a document from the approved read-only roots.",
    )

    def __init__(self, documents_service: WorkspaceDocumentsService) -> None:
        self.documents_service = documents_service

    def execute(self, arguments: Mapping[str, Any]) -> ToolResult:
        query = str(arguments.get("query", "")).strip()
        if not query:
            return ToolResult(success=False, message="A document name or query is required.")

        payload = self.documents_service.summarize_document(query=query)
        if payload is None:
            return ToolResult(
                success=False,
                message="I could not find a matching document to summarize in the approved read-only roots.",
                data={"query": query},
            )

        document = payload["document"]
        summary = payload["summary"]
        key_points = summary.get("key_points", [])
        key_point_copy = "; ".join(str(point) for point in key_points[:2]) if key_points else "No key points extracted."
        message = f"Summary for {document['title']}: {summary['overview']}"
        if key_point_copy:
            message = f"{message} Key points: {key_point_copy}"

        warnings: list[str] = []
        if summary.get("security", {}).get("prompt_injection_detected"):
            message = f"{message} Suspicious instruction-like text was removed before summarization."
            warnings.append("Document summaries exclude suspicious instruction-like text from untrusted content.")
        return ToolResult(
            success=True,
            message=message,
            data={
                "query": query,
                "document": self.documents_service.audit_payload(document),
                "summary": summary,
            },
            warnings=warnings,
        )


class AnalyzeDocumentTool(BaseTool):
    definition = ToolDefinition(
        name="analyze_document",
        category=ToolCategory.FILES,
        permission_level=PermissionLevel.SAFE_READ,
        description="Run lightweight table analysis for a document in the approved read-only roots.",
    )

    def __init__(self, documents_service: WorkspaceDocumentsService) -> None:
        self.documents_service = documents_service

    def execute(self, arguments: Mapping[str, Any]) -> ToolResult:
        query = str(arguments.get("query", "")).strip()
        filter_text = str(arguments.get("filter", "")).strip() or None
        schema_path = str(arguments.get("schema_path", "")).strip() or None
        if not query:
            return ToolResult(success=False, message="A document name or query is required.")

        payload = self.documents_service.analyze_document(
            query=query,
            filter_text=filter_text,
            schema_path=schema_path,
        )
        if payload is None:
            return ToolResult(
                success=False,
                message="I could not find a matching document to analyze in the approved read-only roots.",
                data={"query": query},
            )
        if payload.get("analysis") is None:
            return ToolResult(
                success=False,
                message="No lightweight table analysis is available for that document view.",
                data={"query": query},
            )

        document = payload["document"]
        analysis = payload["analysis"]
        message = (
            f"Analyzed {document['title']}: {analysis['row_count']} row(s), {analysis['column_count']} column(s), "
            f"{analysis['numeric_column_count']} numeric column(s)."
        )
        if filter_text:
            message = f"{message} Filter '{filter_text}' applied."
        if schema_path:
            message = f"{message} Focused path: {schema_path}."

        warnings: list[str] = []
        if document.get("security", {}).get("prompt_injection_detected"):
            warnings.append("Analysis used an untrusted document. Suspicious instruction-like text was excluded from previews and summaries.")

        return ToolResult(
            success=True,
            message=message,
            data={
                "query": query,
                "document": self.documents_service.audit_payload(document),
                "analysis": analysis,
            },
            warnings=warnings,
        )


class InspectDocumentTool(BaseTool):
    definition = ToolDefinition(
        name="inspect_document",
        category=ToolCategory.FILES,
        permission_level=PermissionLevel.SAFE_READ,
        description="Inspect structure for a document in the approved read-only roots.",
    )

    def __init__(self, documents_service: WorkspaceDocumentsService) -> None:
        self.documents_service = documents_service

    def execute(self, arguments: Mapping[str, Any]) -> ToolResult:
        query = str(arguments.get("query", "")).strip()
        filter_text = str(arguments.get("filter", "")).strip() or None
        limit = int(arguments.get("limit", 8) or 8)
        schema_depth = int(arguments.get("schema_depth", 2) or 2)
        schema_path = str(arguments.get("schema_path", "")).strip() or None
        if not query:
            return ToolResult(success=False, message="A document name or query is required.")

        payload = self.documents_service.inspect_document(
            query=query,
            filter_text=filter_text,
            limit=max(1, min(limit, 25)),
            schema_depth=max(1, min(schema_depth, 4)),
            schema_path=schema_path,
        )
        if payload is None:
            return ToolResult(
                success=False,
                message="I could not find a matching document to inspect in the approved read-only roots.",
                data={"query": query},
            )

        document = payload["document"]
        inspection = payload["inspection"]
        label = inspection.get("label", "Document structure")
        message = f"{label} for {document['title']} is ready."
        if inspection.get("row_count") is not None:
            message = f"{message} Rows: {inspection['row_count']}."
        elif inspection.get("field_count") is not None:
            message = f"{message} Fields: {inspection['field_count']}."
        elif inspection.get("item_count") is not None:
            message = f"{message} Items: {inspection['item_count']}."
        message = f"{message} Schema depth: {inspection.get('schema_depth', schema_depth)}."
        if schema_path:
            focus = inspection.get("focus", {})
            if focus.get("found"):
                message = f"{message} Focused path: {schema_path}."
            else:
                message = f"{message} Path '{schema_path}' was not found."
        if filter_text:
            filtered_count = inspection.get("filtered_row_count", inspection.get("filtered_item_count"))
            if filtered_count is not None:
                message = f"{message} Filter '{filter_text}' matched {filtered_count} row(s)."

        warnings: list[str] = []
        if document.get("security", {}).get("prompt_injection_detected"):
            warnings.append("Inspection used an untrusted document. Suspicious instruction-like text was excluded from previews and summaries.")

        return ToolResult(
            success=True,
            message=message,
            data={
                "query": query,
                "document": self.documents_service.audit_payload(document),
                "inspection": inspection,
            },
            warnings=warnings,
        )


class UpdateNoteTool(BaseTool):
    definition = ToolDefinition(
        name="update_note",
        category=ToolCategory.FILES,
        permission_level=PermissionLevel.SENSITIVE,
        description="Append to or replace a note inside the approved workspace.",
    )

    def __init__(self, notes_service: WorkspaceNotesService) -> None:
        self.notes_service = notes_service

    def execute(self, arguments: Mapping[str, Any]) -> ToolResult:
        query = str(arguments.get("query", "")).strip()
        content = str(arguments.get("content", "")).strip()
        mode = str(arguments.get("mode", "append")).strip().lower()
        if not query:
            return ToolResult(success=False, message="A note name or query is required.")
        if not content:
            return ToolResult(success=False, message="Updated note content is required.")
        if mode not in {"append", "replace"}:
            return ToolResult(success=False, message="Unsupported note update mode.")

        note = self.notes_service.resolve_note(query)
        if note is None:
            return ToolResult(
                success=False,
                message="I could not find a matching note in the approved workspace.",
                data={"query": query},
            )

        updated_content = self._build_updated_content(
            note=note,
            content=content,
            mode=mode,
        )
        updated_note = self.notes_service.update_note(note["name"], content=updated_content)
        if updated_note is None:
            return ToolResult(
                success=False,
                message="The note could not be updated.",
                data={"query": query, "mode": mode},
            )

        message = (
            f"Appended to '{updated_note['title']}'."
            if mode == "append"
            else f"Replaced the contents of '{updated_note['title']}'."
        )
        return ToolResult(
            success=True,
            message=message,
            data={"query": query, "mode": mode, "note": updated_note},
        )

    def _build_updated_content(self, *, note: Mapping[str, Any], content: str, mode: str) -> str:
        cleaned = content.strip()
        if mode == "replace":
            if not cleaned.startswith("#"):
                cleaned = f"# {note['title']}\n\n{cleaned}"
            return f"{cleaned.rstrip()}\n"

        existing = str(note.get("content", "")).rstrip()
        if not existing:
            return f"{cleaned}\n"
        return f"{existing}\n\n{cleaned}\n"


class OpenWebsiteTool(BaseTool):
    definition = ToolDefinition(
        name="open_website",
        category=ToolCategory.WEB,
        permission_level=PermissionLevel.LOW_RISK,
        description="Open a website in the default browser after user confirmation.",
    )

    def __init__(self, opener: Callable[[str], Any] | None = None) -> None:
        self.browser_launcher = BrowserLauncher() if opener is None else None
        self.opener = opener or self.browser_launcher.open

    def execute(self, arguments: Mapping[str, Any]) -> ToolResult:
        raw_url = str(arguments.get("url", "")).strip()
        if not raw_url:
            return ToolResult(success=False, message="A URL is required to open a website.")

        if "://" not in raw_url:
            raw_url = f"https://{raw_url}"

        try:
            launch = normalize_browser_launch_result(self.opener(raw_url), raw_url)
        except Exception as exc:
            return ToolResult(
                success=False,
                message=f"Failed to open the website: {exc}",
                data={"url": raw_url},
            )

        if not launch["success"]:
            return ToolResult(
                success=False,
                message=launch["error"] or "The browser did not report a successful launch.",
                data={"url": raw_url, "launch": launch},
            )

        if launch["isolated_used"]:
            message = f"Opened {raw_url} in an isolated {launch['browser']} window."
            warnings: list[str] = []
        elif launch["used_fallback"]:
            message = f"Opened {raw_url} in the default browser because isolated launch was unavailable."
            warnings = ["No supported private-window browser launcher was found, so the default browser was used."]
        else:
            message = f"Opened {raw_url} in the default browser."
            warnings = []

        return ToolResult(
            success=True,
            message=message,
            data={"url": raw_url, "launch": launch},
            warnings=warnings,
        )


class OpenApplicationTool(BaseTool):
    definition = ToolDefinition(
        name="open_application",
        category=ToolCategory.SYSTEM,
        permission_level=PermissionLevel.LOW_RISK,
        description="Open an approved local application after user confirmation.",
    )

    def __init__(self, settings: Settings, launcher: Callable[[tuple[str, ...]], Any] | None = None) -> None:
        self.settings = settings
        self.launcher = launcher or subprocess.Popen

    def execute(self, arguments: Mapping[str, Any]) -> ToolResult:
        raw_name = str(arguments.get("application", "")).strip()
        if not raw_name:
            return ToolResult(success=False, message="An application name is required.")

        canonical_name = normalize_app_name(raw_name)
        command = self.settings.approved_apps.get(canonical_name)
        if not command:
            return ToolResult(
                success=False,
                message=f"'{raw_name}' is not in the approved app list.",
                data={"approved_apps": sorted(self.settings.approved_apps)},
            )

        try:
            self.launcher(command)
        except Exception as exc:
            return ToolResult(
                success=False,
                message=f"Failed to open {canonical_name}: {exc}",
                data={"application": canonical_name, "command": list(command)},
            )

        return ToolResult(
            success=True,
            message=f"Opened {canonical_name}.",
            data={"application": canonical_name, "command": list(command)},
        )


class LaunchWorkspaceTool(BaseTool):
    definition = ToolDefinition(
        name="launch_workspace",
        category=ToolCategory.PRODUCTIVITY,
        permission_level=PermissionLevel.LOW_RISK,
        description="Launch an approved workspace profile containing apps, folders, and websites.",
    )

    def __init__(
        self,
        settings: Settings,
        *,
        command_launcher: Callable[[tuple[str, ...]], Any] | None = None,
        url_opener: Callable[[str], Any] | None = None,
        path_launcher: Callable[[str], Any] | None = None,
    ) -> None:
        self.settings = settings
        self.command_launcher = command_launcher or subprocess.Popen
        self.browser_launcher = BrowserLauncher() if url_opener is None else None
        self.url_opener = url_opener or self.browser_launcher.open
        self.path_launcher = path_launcher or default_path_launcher

    def execute(self, arguments: Mapping[str, Any]) -> ToolResult:
        raw_name = str(arguments.get("workspace", "")).strip()
        if not raw_name:
            return ToolResult(success=False, message="A workspace profile name is required.")

        workspace_name = normalize_workspace_name(raw_name)
        profile = self.settings.workspace_profiles.get(workspace_name)
        if profile is None:
            return ToolResult(
                success=False,
                message=f"'{raw_name}' is not an approved workspace profile.",
                data={"workspace_profiles": sorted(self.settings.workspace_profiles)},
            )

        launched_apps: list[str] = []
        opened_urls: list[str] = []
        browser_launches: list[dict[str, Any]] = []
        opened_paths: list[str] = []

        try:
            for app_name in profile.get("apps", ()):
                command = self.settings.approved_apps.get(str(app_name))
                if not command:
                    return ToolResult(
                        success=False,
                        message=f"The workspace profile references an unapproved app: {app_name}",
                        data={"workspace": workspace_name},
                    )
                self.command_launcher(command)
                launched_apps.append(str(app_name))

            for relative_path in profile.get("paths", ()):
                resolved_path = self._resolve_workspace_path(str(relative_path))
                self.path_launcher(str(resolved_path))
                opened_paths.append(str(resolved_path))

            for url in profile.get("urls", ()):
                launch = normalize_browser_launch_result(self.url_opener(str(url)), str(url))
                if not launch["success"]:
                    return ToolResult(
                        success=False,
                        message=launch["error"] or f"The browser did not report a successful launch for {url}.",
                        data={"workspace": workspace_name},
                    )
                opened_urls.append(str(url))
                browser_launches.append(launch)
        except Exception as exc:
            return ToolResult(
                success=False,
                message=f"Failed to launch the {workspace_name} workspace: {exc}",
                data={"workspace": workspace_name},
            )

        isolated_launches = [launch for launch in browser_launches if launch.get("isolated_used")]
        fallback_launches = [launch for launch in browser_launches if launch.get("used_fallback")]
        warnings: list[str] = []
        message = f"Launched the {workspace_name} workspace."
        if isolated_launches:
            message = (
                f"{message} Opened {len(isolated_launches)} web handoff"
                f"{'' if len(isolated_launches) == 1 else 's'} in isolated browser windows."
            )
        if fallback_launches:
            warnings.append("Some workspace URLs used the default browser because isolated launch was unavailable.")

        return ToolResult(
            success=True,
            message=message,
            data={
                "workspace": workspace_name,
                "launched_apps": launched_apps,
                "opened_urls": opened_urls,
                "browser_launches": browser_launches,
                "opened_paths": opened_paths,
            },
            warnings=warnings,
        )

    def _resolve_workspace_path(self, path_key: str) -> Any:
        if path_key == "notes":
            return self.settings.notes_dir.resolve()
        return (self.settings.repo_root / path_key).resolve()


class CreateNoteTool(BaseTool):
    definition = ToolDefinition(
        name="create_note",
        category=ToolCategory.PRODUCTIVITY,
        permission_level=PermissionLevel.SENSITIVE,
        description="Create a local note inside the approved notes workspace.",
    )

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def execute(self, arguments: Mapping[str, Any]) -> ToolResult:
        title = str(arguments.get("title", "Quick note")).strip() or "Quick note"
        content = str(arguments.get("content", "")).strip()

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{timestamp}-{_slugify(title)}.md"
        note_path = self.settings.notes_dir / filename
        note_path.parent.mkdir(parents=True, exist_ok=True)

        note_body = f"# {title}\n\n{content}\n"
        note_path.write_text(note_body, encoding="utf-8")

        return ToolResult(
            success=True,
            message="Created a note in the approved notes workspace.",
            data={"path": str(note_path), "title": title},
        )


class CreateReminderTool(BaseTool):
    definition = ToolDefinition(
        name="create_reminder",
        category=ToolCategory.PRODUCTIVITY,
        permission_level=PermissionLevel.LOW_RISK,
        description="Create a local reminder item for follow-up work.",
    )

    def __init__(self, reminder_service: ReminderService) -> None:
        self.reminder_service = reminder_service

    def execute(self, arguments: Mapping[str, Any]) -> ToolResult:
        title = str(arguments.get("title", "")).strip() or "Untitled reminder"
        details = str(arguments.get("details", "")).strip()
        schedule_hint = str(arguments.get("schedule_hint", "")).strip() or None
        due_at = str(arguments.get("due_at", "")).strip() or None
        recurrence_rule = str(arguments.get("recurrence_rule", "")).strip() or None
        recurrence_label = str(arguments.get("recurrence_label", "")).strip() or None

        try:
            reminder = self.reminder_service.create_reminder(
                title=title,
                details=details,
                schedule_hint=schedule_hint,
                due_at=due_at,
                recurrence_rule=recurrence_rule,
                recurrence_label=recurrence_label,
            )
        except ValueError as exc:
            return ToolResult(success=False, message=str(exc))

        if reminder["due_at"] and reminder.get("recurrence_label"):
            message = f"Created a recurring reminder for {reminder['due_display']} ({reminder['recurrence_label']})."
        elif reminder["due_at"]:
            message = f"Created a reminder for {reminder['due_display']}."
        elif reminder["schedule_hint"]:
            message = f"Created a reminder with the schedule hint '{reminder['schedule_hint']}'."
        else:
            message = "Created an unscheduled reminder."

        return ToolResult(
            success=True,
            message=message,
            data=reminder,
        )


class DraftEmailTool(BaseTool):
    definition = ToolDefinition(
        name="draft_email",
        category=ToolCategory.COMMUNICATION,
        permission_level=PermissionLevel.LOW_RISK,
        description="Save a structured email draft into the local outbox without sending it.",
    )

    def __init__(self, email_service: EmailService) -> None:
        self.email_service = email_service

    def execute(self, arguments: Mapping[str, Any]) -> ToolResult:
        recipient = str(arguments.get("to", "")).strip() or "recipient@example.com"
        subject = str(arguments.get("subject", "Draft from Zivra")).strip()
        body = str(arguments.get("body", "")).strip()
        source = str(arguments.get("source", "assistant")).strip() or "assistant"
        email = self.email_service.create_draft(
            to_address=recipient,
            subject=subject,
            body=body,
            source=source,
        )

        return ToolResult(
            success=True,
            message=f"Saved a local email draft for {recipient}.",
            data={
                "email": self.email_service.audit_payload(email),
                "delivery": self.email_service.delivery_status(),
            },
        )


class SendEmailTool(BaseTool):
    definition = ToolDefinition(
        name="send_email",
        category=ToolCategory.COMMUNICATION,
        permission_level=PermissionLevel.SENSITIVE,
        description="Send an email through configured SMTP after explicit confirmation.",
    )

    def __init__(self, email_service: EmailService) -> None:
        self.email_service = email_service

    def execute(self, arguments: Mapping[str, Any]) -> ToolResult:
        recipient = str(arguments.get("to", "")).strip() or "recipient@example.com"
        subject = str(arguments.get("subject", "Draft from Zivra")).strip()
        body = str(arguments.get("body", "")).strip()
        source = str(arguments.get("source", "assistant")).strip() or "assistant"

        try:
            email = self.email_service.create_and_send(
                to_address=recipient,
                subject=subject,
                body=body,
                source=source,
            )
        except ValueError as exc:
            return ToolResult(
                success=False,
                message=str(exc),
                data={"to": recipient, "subject": subject},
            )

        if email["status"] == "failed":
            return ToolResult(
                success=False,
                message=f"Email delivery failed: {email['error'] or 'Unknown delivery error.'}",
                data={
                    "email": self.email_service.audit_payload(email),
                    "delivery": self.email_service.delivery_status(),
                },
            )

        return ToolResult(
            success=True,
            message=f"Sent the email to {recipient}.",
            data={
                "email": self.email_service.audit_payload(email),
                "delivery": self.email_service.delivery_status(),
            },
        )


class DraftWhatsAppMessageTool(BaseTool):
    definition = ToolDefinition(
        name="draft_whatsapp_message",
        category=ToolCategory.COMMUNICATION,
        permission_level=PermissionLevel.LOW_RISK,
        description="Save a WhatsApp message draft into the local messaging outbox without opening it.",
    )

    def __init__(self, messaging_service: MessagingService) -> None:
        self.messaging_service = messaging_service

    def execute(self, arguments: Mapping[str, Any]) -> ToolResult:
        recipient = str(arguments.get("to", "")).strip()
        body = str(arguments.get("body", "")).strip()
        source = str(arguments.get("source", "assistant")).strip() or "assistant"
        try:
            outbox_message = self.messaging_service.create_whatsapp_draft(
                to_number=recipient,
                body=body,
                source=source,
            )
        except ValueError as exc:
            return ToolResult(success=False, message=str(exc), data={"to": recipient})

        return ToolResult(
            success=True,
            message=f"Saved a local WhatsApp draft for {outbox_message['to']}.",
            data={
                "message": self.messaging_service.audit_payload(outbox_message),
                "delivery": self.messaging_service.delivery_status(),
            },
        )


class SendWhatsAppMessageTool(BaseTool):
    definition = ToolDefinition(
        name="send_whatsapp_message",
        category=ToolCategory.COMMUNICATION,
        permission_level=PermissionLevel.SENSITIVE,
        description="Send through WhatsApp Cloud API when configured, otherwise open a WhatsApp browser handoff after confirmation.",
    )

    def __init__(self, messaging_service: MessagingService) -> None:
        self.messaging_service = messaging_service

    def execute(self, arguments: Mapping[str, Any]) -> ToolResult:
        recipient = str(arguments.get("to", "")).strip()
        body = str(arguments.get("body", "")).strip()
        source = str(arguments.get("source", "assistant")).strip() or "assistant"

        try:
            outbox_message = self.messaging_service.create_whatsapp_draft(
                to_number=recipient,
                body=body,
                source=source,
            )
        except ValueError as exc:
            return ToolResult(success=False, message=str(exc), data={"to": recipient})

        handed_off_message = self.messaging_service.send_whatsapp_draft(int(outbox_message["id"]))
        if handed_off_message is None:
            return ToolResult(
                success=False,
                message="The WhatsApp handoff could not be reloaded after opening it.",
                data={"to": recipient},
            )

        if handed_off_message["status"] == "failed":
            return ToolResult(
                success=False,
                message=self.messaging_service.format_dispatch_message(handed_off_message),
                data={
                    "message": self.messaging_service.audit_payload(handed_off_message),
                    "delivery": self.messaging_service.delivery_status(),
                },
            )

        message = self.messaging_service.format_dispatch_message(handed_off_message)
        launch = handed_off_message.get("launch", {})
        warnings = (
            ["No supported private-window browser launcher was found, so the default browser was used."]
            if launch.get("used_fallback")
            else []
        )

        return ToolResult(
            success=True,
            message=message,
            data={
                "message": self.messaging_service.audit_payload(handed_off_message),
                "delivery": self.messaging_service.delivery_status(),
            },
            warnings=warnings,
        )

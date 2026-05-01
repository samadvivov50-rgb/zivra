from __future__ import annotations

from typing import Iterable

from app.core.config import Settings
from app.models import ProposedAction, ToolResult
from app.services.clipboard import ClipboardService
from app.services.content import ContentStrategyService
from app.services.documents import WorkspaceDocumentsService
from app.services.emails import EmailService
from app.services.files import WorkspaceFilesService
from app.services.messages import MessagingService
from app.services.notes import WorkspaceNotesService
from app.services.research import ResearchSummaryService
from app.services.reminders import ReminderService
from app.services.webpages import WebPageService
from app.services.websearch import WebSearchService
from app.tools.base import BaseTool, ToolDefinition
from app.tools.safe import (
    AnalyzeDocumentTool,
    CreateNoteTool,
    CreateReminderTool,
    DraftEmailTool,
    DraftWhatsAppMessageTool,
    BrowseFolderTool,
    GenerateContentPackageTool,
    InspectDocumentTool,
    LaunchWorkspaceTool,
    OpenApplicationTool,
    ReadDocumentTool,
    ReadClipboardTool,
    ReadWebPageTool,
    ResearchSummaryTool,
    OpenWebsiteTool,
    ReadNoteTool,
    SearchFilesTool,
    SearchDocumentsTool,
    SearchNotesTool,
    SearchWebTool,
    SendEmailTool,
    SendWhatsAppMessageTool,
    SummarizeWebPageTool,
    SummarizeDocumentTool,
    SystemSnapshotTool,
    UpdateNoteTool,
    WriteClipboardTool,
)


class ToolRegistry:
    def __init__(self, tools: Iterable[BaseTool]) -> None:
        self._tools = {tool.definition.name: tool for tool in tools}

    def list_tools(self) -> list[ToolDefinition]:
        return [tool.definition for tool in self._tools.values()]

    def get_definition(self, tool_name: str) -> ToolDefinition:
        return self._tools[tool_name].definition

    def execute(self, action: ProposedAction) -> ToolResult:
        return self._tools[action.tool_name].execute(action.arguments)


def build_default_registry(
    settings: Settings,
    *,
    notes_service: WorkspaceNotesService,
    documents_service: WorkspaceDocumentsService,
    files_service: WorkspaceFilesService | None = None,
    reminder_service: ReminderService,
    email_service: EmailService | None = None,
    messaging_service: MessagingService | None = None,
    content_service: ContentStrategyService | None = None,
    research_service: ResearchSummaryService | None = None,
    clipboard_service: ClipboardService | None = None,
    webpage_service: WebPageService | None = None,
    web_search_service: WebSearchService | None = None,
    website_opener=None,
    app_launcher=None,
    path_launcher=None,
) -> ToolRegistry:
    resolved_clipboard_service = clipboard_service or ClipboardService()
    resolved_webpage_service = webpage_service or WebPageService()
    resolved_web_search_service = web_search_service or WebSearchService()
    resolved_content_service = content_service or ContentStrategyService()
    resolved_research_service = research_service or ResearchSummaryService(
        resolved_web_search_service,
        resolved_webpage_service,
    )
    resolved_email_service = email_service or EmailService(settings.emails_db_path, settings=settings)
    resolved_messaging_service = messaging_service or MessagingService(settings.messages_db_path)
    resolved_files_service = files_service or WorkspaceFilesService(
        settings.approved_document_roots,
        write_roots=settings.approved_write_roots,
    )
    return ToolRegistry(
        [
            SystemSnapshotTool(settings),
            SearchWebTool(resolved_web_search_service, settings),
            ResearchSummaryTool(resolved_research_service),
            GenerateContentPackageTool(resolved_content_service),
            ReadClipboardTool(resolved_clipboard_service),
            WriteClipboardTool(resolved_clipboard_service),
            ReadWebPageTool(resolved_webpage_service),
            SummarizeWebPageTool(resolved_webpage_service),
            SearchNotesTool(notes_service),
            ReadNoteTool(notes_service),
            SearchFilesTool(resolved_files_service),
            BrowseFolderTool(resolved_files_service),
            SearchDocumentsTool(documents_service),
            ReadDocumentTool(documents_service),
            SummarizeDocumentTool(documents_service),
            AnalyzeDocumentTool(documents_service),
            InspectDocumentTool(documents_service),
            UpdateNoteTool(notes_service),
            OpenWebsiteTool(website_opener),
            OpenApplicationTool(settings, app_launcher),
            LaunchWorkspaceTool(
                settings,
                command_launcher=app_launcher,
                url_opener=website_opener,
                path_launcher=path_launcher,
            ),
            CreateNoteTool(settings),
            CreateReminderTool(reminder_service),
            DraftEmailTool(resolved_email_service),
            SendEmailTool(resolved_email_service),
            DraftWhatsAppMessageTool(resolved_messaging_service),
            SendWhatsAppMessageTool(resolved_messaging_service),
        ]
    )

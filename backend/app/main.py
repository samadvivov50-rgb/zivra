from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import assistant, clipboard, content, dashboard, documents, emails, files, health, messages, notes, reminders, research, runtime, settings as settings_routes, sync, vision, web, workflows
from app.core.config import Settings
from app.services.audit import AuditLogger
from app.services.clipboard import ClipboardService
from app.services.content import ContentStrategyService
from app.services.documents import WorkspaceDocumentsService
from app.services.emails import EmailService
from app.services.files import WorkspaceFilesService
from app.services.messages import MessagingService
from app.services.memory import ConversationMemoryStore
from app.services.notes import WorkspaceNotesService
from app.services.orchestrator import AssistantOrchestrator, IntentRouter
from app.services.planning import build_planner
from app.services.policy import PolicyEngine
from app.services.preferences import PreferencesService
from app.services.research import ResearchSummaryService
from app.services.reminders import ReminderService
from app.services.secrets import SecretsService
from app.services.sync import CompanionSyncService
from app.services.vision import VisionService
from app.services.webpages import WebPageService
from app.services.websearch import WebSearchService
from app.services.workflows import WorkflowService
from app.tools.registry import build_default_registry


def create_app() -> FastAPI:
    settings = Settings()
    settings.ensure_runtime_dirs()
    preferences_service = PreferencesService(
        settings.preferences_path,
        defaults={
            "assistant_name": settings.assistant_name,
            "safe_mode": settings.safe_mode,
            "memory_enabled": settings.memory_enabled,
            "voice_auto_speak": settings.voice_auto_speak,
            "voice_auto_send": settings.voice_auto_send,
            "voice_wake_phrase_enabled": settings.voice_wake_phrase_enabled,
            "voice_wake_phrase": settings.voice_wake_phrase,
            "workflow_supervisor_enabled": settings.workflow_supervisor_enabled,
            "workflow_supervisor_max_tasks_per_cycle": settings.workflow_supervisor_max_tasks_per_cycle,
            "workflow_supervisor_max_pending_approvals": settings.workflow_supervisor_max_pending_approvals,
            "workflow_supervisor_pause_on_failure": settings.workflow_supervisor_pause_on_failure,
            "live_search_result_limit": settings.live_search_result_limit,
            "dashboard_refresh_seconds": settings.dashboard_refresh_seconds,
            "whatsapp_api_version": settings.whatsapp_api_version,
            "whatsapp_phone_number_id": settings.whatsapp_phone_number_id,
            "whatsapp_verify_token": settings.whatsapp_verify_token,
        },
    )
    preferences_service.apply_to_settings(settings)
    secrets_service = SecretsService(settings.secrets_path)
    secrets_service.apply_to_settings(settings)

    reminders_service = ReminderService(settings.reminders_db_path)
    workflow_service = WorkflowService(settings.workflows_db_path)
    clipboard_service = ClipboardService()
    vision_service = VisionService(settings)
    webpage_service = WebPageService()
    web_search_service = WebSearchService()
    content_service = ContentStrategyService()
    notes_service = WorkspaceNotesService(settings.notes_dir)
    documents_service = WorkspaceDocumentsService(settings.approved_document_roots)
    email_service = EmailService(settings.emails_db_path, settings=settings)
    messaging_service = MessagingService(settings.messages_db_path, settings=settings)
    research_service = ResearchSummaryService(web_search_service, webpage_service)
    files_service = WorkspaceFilesService(
        settings.approved_document_roots,
        write_roots=settings.approved_write_roots,
    )
    registry = build_default_registry(
        settings,
        notes_service=notes_service,
        documents_service=documents_service,
        files_service=files_service,
        reminder_service=reminders_service,
        email_service=email_service,
        messaging_service=messaging_service,
        content_service=content_service,
        research_service=research_service,
        clipboard_service=clipboard_service,
        webpage_service=webpage_service,
        web_search_service=web_search_service,
    )
    policy = PolicyEngine(safe_mode=settings.safe_mode, approved_roots=settings.approved_roots)
    audit_logger = AuditLogger(settings.audit_log_path)
    memory = ConversationMemoryStore(settings.memory_db_path, enabled=settings.memory_enabled)
    router = IntentRouter()
    planner = build_planner(settings, fallback_router=router)
    orchestrator = AssistantOrchestrator(
        registry=registry,
        policy=policy,
        audit=audit_logger,
        memory=memory,
        planner=planner,
        router=router,
    )
    sync_service = CompanionSyncService(
        settings=settings,
        orchestrator=orchestrator,
        audit_logger=audit_logger,
        reminders_service=reminders_service,
        workflow_service=workflow_service,
        notes_service=notes_service,
        email_service=email_service,
        messaging_service=messaging_service,
        memory_store=memory,
    )

    app = FastAPI(
        title="Zivra Assistant",
        version="0.1.0",
        description="Local-first AI assistant starter with policy-gated actions.",
    )
    app.state.settings = settings
    app.state.preferences_service = preferences_service
    app.state.secrets_service = secrets_service
    app.state.audit_logger = audit_logger
    app.state.orchestrator = orchestrator
    app.state.policy_engine = policy
    app.state.registry = registry
    app.state.memory_store = memory
    app.state.clipboard_service = clipboard_service
    app.state.vision_service = vision_service
    app.state.webpage_service = webpage_service
    app.state.web_search_service = web_search_service
    app.state.content_service = content_service
    app.state.notes_service = notes_service
    app.state.documents_service = documents_service
    app.state.email_service = email_service
    app.state.messaging_service = messaging_service
    app.state.research_service = research_service
    app.state.files_service = files_service
    app.state.reminders_service = reminders_service
    app.state.workflow_service = workflow_service
    app.state.sync_service = sync_service

    app.include_router(health.router)
    app.include_router(assistant.router)
    app.include_router(clipboard.router)
    app.include_router(content.router)
    app.include_router(dashboard.router)
    app.include_router(documents.router)
    app.include_router(emails.router)
    app.include_router(files.router)
    app.include_router(messages.router)
    app.include_router(notes.router)
    app.include_router(reminders.router)
    app.include_router(research.router)
    app.include_router(runtime.router)
    app.include_router(settings_routes.router)
    app.include_router(sync.router)
    app.include_router(vision.router)
    app.include_router(web.router)
    app.include_router(workflows.router)

    static_dir = Path(__file__).resolve().parents[2] / "dashboard"
    if static_dir.exists():
        app.mount("/ui", StaticFiles(directory=str(static_dir), html=True), name="ui")

    @app.get("/", include_in_schema=False)
    def root(request: Request) -> RedirectResponse:
        target = "/ui/"
        if request.url.query:
            target = f"{target}?{request.url.query}"
        return RedirectResponse(url=target)

    @app.get("/mobile", include_in_schema=False)
    def mobile(request: Request) -> RedirectResponse:
        target = "/ui/mobile.html"
        if request.url.query:
            target = f"{target}?{request.url.query}"
        return RedirectResponse(url=target)

    return app


app = create_app()

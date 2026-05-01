from __future__ import annotations

import os
import platform
from dataclasses import dataclass, field
from pathlib import Path


def _env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _optional_env_path(name: str) -> Path | None:
    value = os.getenv(name, "").strip()
    if not value:
        return None
    return Path(value).expanduser()


@dataclass(slots=True)
class Settings:
    repo_root: Path = field(default_factory=_default_repo_root)
    data_dir_override: Path | None = field(default_factory=lambda: _optional_env_path("ZIVRA_DATA_DIR"))
    assistant_name: str = "Zivra"
    environment: str = "development"
    safe_mode: bool = False
    memory_enabled: bool = True
    voice_auto_speak: bool = False
    voice_auto_send: bool = False
    voice_wake_phrase_enabled: bool = False
    voice_wake_phrase: str = "hey zivra"
    workflow_supervisor_enabled: bool = False
    workflow_supervisor_max_tasks_per_cycle: int = 1
    workflow_supervisor_max_pending_approvals: int = 1
    workflow_supervisor_pause_on_failure: bool = True
    live_search_result_limit: int = 6
    dashboard_refresh_seconds: int = 60
    planner_mode: str = field(default_factory=lambda: os.getenv("ZIVRA_PLANNER_MODE", "auto"))
    llm_base_url: str = field(default_factory=lambda: os.getenv("ZIVRA_LLM_BASE_URL", "https://api.openai.com/v1"))
    llm_api_key: str = field(
        default_factory=lambda: os.getenv("ZIVRA_LLM_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    )
    llm_model: str = field(default_factory=lambda: os.getenv("ZIVRA_LLM_MODEL", ""))
    vision_model: str = field(
        default_factory=lambda: os.getenv("ZIVRA_VISION_MODEL", os.getenv("ZIVRA_LLM_MODEL", ""))
    )
    llm_timeout_seconds: float = field(
        default_factory=lambda: float(os.getenv("ZIVRA_LLM_TIMEOUT_SECONDS", "20"))
    )
    smtp_host: str = field(default_factory=lambda: os.getenv("ZIVRA_SMTP_HOST", ""))
    smtp_port: int = field(default_factory=lambda: int(os.getenv("ZIVRA_SMTP_PORT", "587")))
    smtp_username: str = field(default_factory=lambda: os.getenv("ZIVRA_SMTP_USERNAME", ""))
    smtp_password: str = field(default_factory=lambda: os.getenv("ZIVRA_SMTP_PASSWORD", ""))
    smtp_use_tls: bool = field(default_factory=lambda: _env_flag("ZIVRA_SMTP_USE_TLS", True))
    smtp_use_ssl: bool = field(default_factory=lambda: _env_flag("ZIVRA_SMTP_USE_SSL", False))
    email_from_address: str = field(
        default_factory=lambda: os.getenv("ZIVRA_EMAIL_FROM", os.getenv("ZIVRA_SMTP_USERNAME", ""))
    )
    email_from_name: str = field(default_factory=lambda: os.getenv("ZIVRA_EMAIL_FROM_NAME", ""))
    whatsapp_api_version: str = field(default_factory=lambda: os.getenv("ZIVRA_WHATSAPP_API_VERSION", "v23.0"))
    whatsapp_phone_number_id: str = field(default_factory=lambda: os.getenv("ZIVRA_WHATSAPP_PHONE_NUMBER_ID", ""))
    whatsapp_verify_token: str = field(default_factory=lambda: os.getenv("ZIVRA_WHATSAPP_VERIFY_TOKEN", ""))
    whatsapp_access_token: str = field(default_factory=lambda: os.getenv("ZIVRA_WHATSAPP_ACCESS_TOKEN", ""))
    whatsapp_app_secret: str = field(default_factory=lambda: os.getenv("ZIVRA_WHATSAPP_APP_SECRET", ""))

    def __post_init__(self) -> None:
        self.repo_root = Path(self.repo_root)
        if self.data_dir_override is not None:
            self.data_dir_override = Path(self.data_dir_override)
        self.assistant_name = (self.assistant_name or "Zivra").strip() or "Zivra"
        self.voice_wake_phrase = (self.voice_wake_phrase or "hey zivra").strip()[:48] or "hey zivra"
        self.workflow_supervisor_max_tasks_per_cycle = min(max(int(self.workflow_supervisor_max_tasks_per_cycle), 1), 5)
        self.workflow_supervisor_max_pending_approvals = min(
            max(int(self.workflow_supervisor_max_pending_approvals), 1),
            10,
        )
        self.live_search_result_limit = min(max(int(self.live_search_result_limit), 1), 10)
        self.dashboard_refresh_seconds = min(max(int(self.dashboard_refresh_seconds), 15), 300)
        self.refresh_integration_settings_from_environment()

    @property
    def backend_dir(self) -> Path:
        return self.repo_root / "backend"

    @property
    def data_dir(self) -> Path:
        if self.data_dir_override is not None:
            return self.data_dir_override.resolve()
        return self.backend_dir / "data"

    @property
    def audit_log_path(self) -> Path:
        return self.data_dir / "audit" / "actions.jsonl"

    @property
    def memory_db_path(self) -> Path:
        return self.data_dir / "memory" / "conversations.sqlite3"

    @property
    def reminders_db_path(self) -> Path:
        return self.data_dir / "reminders" / "reminders.sqlite3"

    @property
    def workflows_db_path(self) -> Path:
        return self.data_dir / "workflows" / "workflows.sqlite3"

    @property
    def emails_db_path(self) -> Path:
        return self.data_dir / "emails" / "outbox.sqlite3"

    @property
    def messages_db_path(self) -> Path:
        return self.data_dir / "messages" / "outbox.sqlite3"

    @property
    def preferences_path(self) -> Path:
        return self.data_dir / "settings" / "preferences.json"

    @property
    def secrets_path(self) -> Path:
        return self.data_dir / "settings" / "secrets.json"

    @property
    def notes_dir(self) -> Path:
        return self.repo_root / "notes"

    @property
    def docs_dir(self) -> Path:
        return self.repo_root / "docs"

    @property
    def approved_document_roots(self) -> dict[str, Path]:
        return {
            "notes": self.notes_dir.resolve(),
            "docs": self.docs_dir.resolve(),
        }

    @property
    def approved_read_roots(self) -> tuple[Path, ...]:
        return tuple(self.approved_document_roots.values())

    @property
    def approved_write_roots(self) -> tuple[Path, ...]:
        return (self.notes_dir.resolve(),)

    @property
    def approved_roots(self) -> tuple[Path, ...]:
        return self.approved_read_roots

    @property
    def approved_apps(self) -> dict[str, tuple[str, ...]]:
        system = platform.system().lower()
        if system == "windows":
            return {
                "notepad": ("notepad.exe",),
                "calculator": ("calc.exe",),
                "file explorer": ("explorer.exe",),
            }
        return {}

    @property
    def workspace_profiles(self) -> dict[str, dict[str, object]]:
        return {
            "focus": {
                "description": "Open a lightweight writing setup centered on notes.",
                "apps": ("notepad",),
                "urls": (),
                "paths": ("notes",),
            },
            "research": {
                "description": "Open note-taking plus a browser search surface for research work.",
                "apps": ("notepad",),
                "urls": ("https://www.google.com",),
                "paths": ("notes",),
            },
            "planning": {
                "description": "Open planning tools with notes and calculator together.",
                "apps": ("notepad", "calculator"),
                "urls": (),
                "paths": ("notes",),
            },
        }

    def ensure_runtime_dirs(self) -> None:
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        self.memory_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.reminders_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.workflows_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.emails_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.messages_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.preferences_path.parent.mkdir(parents=True, exist_ok=True)
        self.secrets_path.parent.mkdir(parents=True, exist_ok=True)
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        self.docs_dir.mkdir(parents=True, exist_ok=True)

    def refresh_integration_settings_from_environment(self) -> None:
        self.planner_mode = os.getenv("ZIVRA_PLANNER_MODE", self.planner_mode or "auto").strip().lower() or "auto"
        self.llm_base_url = (
            os.getenv("ZIVRA_LLM_BASE_URL", self.llm_base_url or "https://api.openai.com/v1").strip()
            or "https://api.openai.com/v1"
        )
        self.llm_model = os.getenv("ZIVRA_LLM_MODEL", self.llm_model or "").strip()
        self.vision_model = os.getenv("ZIVRA_VISION_MODEL", self.vision_model or self.llm_model or "").strip()
        self.llm_api_key = os.getenv("ZIVRA_LLM_API_KEY", os.getenv("OPENAI_API_KEY", "")).strip()
        try:
            self.llm_timeout_seconds = float(os.getenv("ZIVRA_LLM_TIMEOUT_SECONDS", str(self.llm_timeout_seconds or 20)))
        except ValueError:
            self.llm_timeout_seconds = 20.0
        if self.llm_timeout_seconds <= 0:
            self.llm_timeout_seconds = 20.0

        self.smtp_host = os.getenv("ZIVRA_SMTP_HOST", self.smtp_host or "").strip()
        try:
            self.smtp_port = int(os.getenv("ZIVRA_SMTP_PORT", str(self.smtp_port or 587)))
        except ValueError:
            self.smtp_port = 587
        if self.smtp_port <= 0:
            self.smtp_port = 587
        self.smtp_username = os.getenv("ZIVRA_SMTP_USERNAME", "").strip()
        self.smtp_password = os.getenv("ZIVRA_SMTP_PASSWORD", "").strip()
        self.smtp_use_tls = _env_flag("ZIVRA_SMTP_USE_TLS", self.smtp_use_tls)
        self.smtp_use_ssl = _env_flag("ZIVRA_SMTP_USE_SSL", self.smtp_use_ssl)
        self.email_from_address = os.getenv("ZIVRA_EMAIL_FROM", self.smtp_username).strip()
        self.email_from_name = (
            os.getenv("ZIVRA_EMAIL_FROM_NAME", self.email_from_name or self.assistant_name).strip()
            or self.assistant_name
        )
        self.whatsapp_api_version = (
            os.getenv("ZIVRA_WHATSAPP_API_VERSION", self.whatsapp_api_version or "v23.0").strip() or "v23.0"
        )
        self.whatsapp_phone_number_id = os.getenv(
            "ZIVRA_WHATSAPP_PHONE_NUMBER_ID",
            self.whatsapp_phone_number_id or "",
        ).strip()
        self.whatsapp_verify_token = os.getenv(
            "ZIVRA_WHATSAPP_VERIFY_TOKEN",
            self.whatsapp_verify_token or "",
        ).strip()
        self.whatsapp_access_token = os.getenv("ZIVRA_WHATSAPP_ACCESS_TOKEN", "").strip()
        self.whatsapp_app_secret = os.getenv("ZIVRA_WHATSAPP_APP_SECRET", "").strip()


settings = Settings()

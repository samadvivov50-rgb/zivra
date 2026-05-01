from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class PermissionLevel(StrEnum):
    SAFE_READ = "safe_read"
    LOW_RISK = "low_risk"
    SENSITIVE = "sensitive"
    HIGH_RISK = "high_risk"


class ApprovalMode(StrEnum):
    NONE = "none"
    USER_CONFIRMATION = "user_confirmation"
    STRONG_CONFIRMATION = "strong_confirmation"


class ActionStatus(StrEnum):
    QUEUED = "queued"
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    BLOCKED = "blocked"
    EXECUTED = "executed"
    FAILED = "failed"


class ToolCategory(StrEnum):
    SYSTEM = "system"
    WEB = "web"
    FILES = "files"
    COMMUNICATION = "communication"
    PRODUCTIVITY = "productivity"


def _serialize(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    return value


@dataclass(slots=True)
class ToolResult:
    success: bool
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return _serialize(asdict(self))


@dataclass(slots=True)
class ProposedAction:
    action_id: str
    session_id: str
    tool_name: str
    category: ToolCategory
    permission_level: PermissionLevel
    approval_mode: ApprovalMode
    summary: str
    group_id: str | None = None
    group_summary: str | None = None
    sequence_index: int = 0
    depends_on_action_id: str | None = None
    arguments: dict[str, Any] = field(default_factory=dict)
    status: ActionStatus = ActionStatus.PROPOSED

    def to_dict(self) -> dict[str, Any]:
        return _serialize(asdict(self))


@dataclass(slots=True)
class ActionOutcome:
    action_id: str
    status: ActionStatus
    message: str
    result: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _serialize(asdict(self))


@dataclass(slots=True)
class OrchestratorResponse:
    assistant_text: str
    intent: str
    task_type: str
    actions: list[ProposedAction] = field(default_factory=list)
    outcomes: list[ActionOutcome] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    memory_enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["actions"] = [action.to_dict() for action in self.actions]
        payload["outcomes"] = [outcome.to_dict() for outcome in self.outcomes]
        return _serialize(payload)

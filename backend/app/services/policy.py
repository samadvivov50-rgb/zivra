from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.models import ApprovalMode, PermissionLevel, ProposedAction


@dataclass(slots=True)
class PolicyDecision:
    allowed: bool
    requires_confirmation: bool
    approval_mode: ApprovalMode
    reason: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["approval_mode"] = self.approval_mode.value
        return payload


class PolicyEngine:
    def __init__(self, *, safe_mode: bool = False, approved_roots: tuple[Path, ...] = ()) -> None:
        self.safe_mode = safe_mode
        self.approved_roots = tuple(root.resolve() for root in approved_roots)

    def evaluate(self, action: ProposedAction) -> PolicyDecision:
        if self.safe_mode and action.permission_level == PermissionLevel.HIGH_RISK:
            return PolicyDecision(
                allowed=False,
                requires_confirmation=False,
                approval_mode=ApprovalMode.STRONG_CONFIRMATION,
                reason="High-risk actions are blocked while safe mode is enabled.",
            )

        if action.permission_level == PermissionLevel.SAFE_READ:
            return PolicyDecision(
                allowed=True,
                requires_confirmation=False,
                approval_mode=ApprovalMode.NONE,
                reason="Safe read actions can execute immediately.",
            )

        if action.permission_level in (PermissionLevel.LOW_RISK, PermissionLevel.SENSITIVE):
            return PolicyDecision(
                allowed=True,
                requires_confirmation=True,
                approval_mode=ApprovalMode.USER_CONFIRMATION,
                reason="This action changes state or affects another app and needs user confirmation.",
            )

        return PolicyDecision(
            allowed=True,
            requires_confirmation=True,
            approval_mode=ApprovalMode.STRONG_CONFIRMATION,
            reason="High-risk actions require strong confirmation.",
        )

    def is_path_approved(self, target: Path) -> bool:
        resolved = target.resolve()
        for approved_root in self.approved_roots:
            try:
                resolved.relative_to(approved_root)
                return True
            except ValueError:
                continue
        return False

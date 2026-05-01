from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.core.config import Settings
from app.models import ApprovalMode, PermissionLevel, ProposedAction, ToolCategory
from app.services.policy import PolicyEngine


class PolicyEngineTests(unittest.TestCase):
    def test_safe_reads_execute_immediately(self) -> None:
        engine = PolicyEngine()
        action = ProposedAction(
            action_id="1",
            session_id="test-session",
            tool_name="system_snapshot",
            category=ToolCategory.SYSTEM,
            permission_level=PermissionLevel.SAFE_READ,
            approval_mode=ApprovalMode.NONE,
            summary="Collect system info.",
        )

        decision = engine.evaluate(action)

        self.assertTrue(decision.allowed)
        self.assertFalse(decision.requires_confirmation)
        self.assertEqual(decision.approval_mode, ApprovalMode.NONE)

    def test_high_risk_actions_are_blocked_in_safe_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(repo_root=Path(temp_dir), safe_mode=True)
            engine = PolicyEngine(safe_mode=settings.safe_mode, approved_roots=settings.approved_roots)
            action = ProposedAction(
                action_id="2",
                session_id="test-session",
                tool_name="shutdown_machine",
                category=ToolCategory.SYSTEM,
                permission_level=PermissionLevel.HIGH_RISK,
                approval_mode=ApprovalMode.NONE,
                summary="Shut down the machine.",
            )

            decision = engine.evaluate(action)

        self.assertFalse(decision.allowed)
        self.assertIn("blocked", decision.reason.lower())


if __name__ == "__main__":
    unittest.main()

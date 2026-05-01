from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.models import (
    ActionStatus,
    ApprovalMode,
    PermissionLevel,
    ProposedAction,
    ToolCategory,
    ToolResult,
)
from app.services.audit import AuditLogger
from app.services.policy import PolicyDecision


class AuditLoggerTests(unittest.TestCase):
    def test_query_paginates_newest_events(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = AuditLogger(Path(temp_dir) / "audit.jsonl")
            decision = self._decision()

            for index in range(3):
                action = self._action(
                    action_id=f"action-{index}",
                    summary=f"Action {index}",
                    sequence_index=index,
                )
                logger.record(
                    action=action,
                    status=ActionStatus.EXECUTED,
                    decision=decision,
                    result=ToolResult(success=True, message=f"Ran {index}"),
                )

            page = logger.query(limit=1, offset=1)

            self.assertEqual(page["total"], 3)
            self.assertEqual(page["offset"], 1)
            self.assertEqual(page["limit"], 1)
            self.assertTrue(page["has_more"])
            self.assertEqual(len(page["items"]), 1)
            self.assertEqual(page["items"][0]["action"]["summary"], "Action 1")

    def test_query_searches_across_event_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = AuditLogger(Path(temp_dir) / "audit.jsonl")
            decision = self._decision()

            logger.record(
                action=self._action(
                    action_id="launch-step",
                    summary="Open calculator",
                    group_summary="Launch morning tools",
                ),
                status=ActionStatus.EXECUTED,
                decision=decision,
                result=ToolResult(success=True, message="Calculator opened"),
            )
            logger.record(
                action=self._action(
                    action_id="followup-step",
                    summary="Open example.com",
                    sequence_index=1,
                    depends_on_action_id="launch-step",
                ),
                status=ActionStatus.BLOCKED,
                decision=decision,
                error="Prerequisite step 'Open calculator' did not complete.",
                trace={
                    "prerequisite_summary": "Open calculator",
                    "prerequisite_status": "failed",
                    "dependency_reason": "Prerequisite step 'Open calculator' did not complete.",
                },
            )

            query = logger.query(limit=10, search_query="morning tools")
            self.assertEqual(query["total"], 1)
            self.assertEqual(query["items"][0]["action"]["summary"], "Open calculator")

            prerequisite_query = logger.query(limit=10, search_query="did not complete")
            self.assertEqual(prerequisite_query["total"], 1)
            self.assertEqual(prerequisite_query["items"][0]["status"], "blocked")
            self.assertEqual(prerequisite_query["items"][0]["trace"]["prerequisite_summary"], "Open calculator")

    def test_query_filters_by_status_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = AuditLogger(Path(temp_dir) / "audit.jsonl")
            decision = self._decision()

            logger.record(
                action=self._action(action_id="approval-step", summary="Open calculator"),
                status=ActionStatus.PROPOSED,
                decision=decision,
            )
            logger.record(
                action=self._action(action_id="blocked-step", summary="Open example.com"),
                status=ActionStatus.BLOCKED,
                decision=decision,
                error="Blocked",
            )
            logger.record(
                action=self._action(action_id="success-step", summary="Read architecture"),
                status=ActionStatus.EXECUTED,
                decision=decision,
                result=ToolResult(success=True, message="Read architecture"),
            )

            attention = logger.query(limit=10, status_scope="attention")
            self.assertEqual(attention["total"], 1)
            self.assertEqual(attention["items"][0]["status"], "blocked")

            approval = logger.query(limit=10, status_scope="approval")
            self.assertEqual(approval["total"], 1)
            self.assertEqual(approval["items"][0]["status"], "proposed")

    def test_query_filters_by_time_range(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "audit.jsonl"
            logger = AuditLogger(log_path)
            decision = self._decision()

            logger.record(
                action=self._action(action_id="old-step", summary="Old action"),
                status=ActionStatus.EXECUTED,
                decision=decision,
                result=ToolResult(success=True, message="Old action ran"),
            )
            logger.record(
                action=self._action(action_id="new-step", summary="New action"),
                status=ActionStatus.EXECUTED,
                decision=decision,
                result=ToolResult(success=True, message="New action ran"),
            )

            lines = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            lines[0]["timestamp"] = "2026-03-19T08:00:00+00:00"
            lines[1]["timestamp"] = "2026-03-21T18:30:00+00:00"
            log_path.write_text("\n".join(json.dumps(line) for line in lines) + "\n", encoding="utf-8")

            filtered = logger.query(
                limit=10,
                started_after="2026-03-20T00:00:00+00:00",
                ended_before="2026-03-21T23:59:59+00:00",
            )

            self.assertEqual(filtered["total"], 1)
            self.assertEqual(filtered["items"][0]["action"]["summary"], "New action")

    def test_export_reports_truncation_when_limit_is_smaller_than_match_count(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = AuditLogger(Path(temp_dir) / "audit.jsonl")
            decision = self._decision()

            for index in range(3):
                logger.record(
                    action=self._action(action_id=f"export-{index}", summary=f"Export action {index}"),
                    status=ActionStatus.EXECUTED,
                    decision=decision,
                    result=ToolResult(success=True, message=f"Export action {index} ran"),
                )

            exported = logger.export(limit=2)

            self.assertEqual(exported["total"], 3)
            self.assertEqual(exported["exported_count"], 2)
            self.assertTrue(exported["truncated"])

    def test_query_groups_pages_by_flow_instead_of_raw_events(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = AuditLogger(Path(temp_dir) / "audit.jsonl")
            decision = self._decision()

            logger.record(
                action=self._action(action_id="solo-step", summary="Single action"),
                status=ActionStatus.EXECUTED,
                decision=decision,
                result=ToolResult(success=True, message="Single action ran"),
            )
            logger.record(
                action=self._action(
                    action_id="flow-step-1",
                    summary="Grouped step 1",
                    group_summary="Morning flow",
                    sequence_index=0,
                ),
                status=ActionStatus.PROPOSED,
                decision=decision,
            )
            logger.record(
                action=self._action(
                    action_id="flow-step-2",
                    summary="Grouped step 2",
                    group_summary="Morning flow",
                    sequence_index=1,
                    depends_on_action_id="flow-step-1",
                ),
                status=ActionStatus.QUEUED,
                decision=decision,
                trace={
                    "group_id": "group-1",
                    "group_summary": "Morning flow",
                    "prerequisite_action_id": "flow-step-1",
                },
            )

            first_page = logger.query_groups(limit=1)
            self.assertEqual(first_page["total_groups"], 2)
            self.assertEqual(first_page["total_events"], 3)
            self.assertTrue(first_page["has_more"])
            self.assertEqual(len(first_page["groups"]), 1)
            self.assertEqual(first_page["groups"][0]["title"], "Morning flow")
            self.assertEqual(first_page["groups"][0]["event_count"], 2)

            second_page = logger.query_groups(limit=1, offset=1)
            self.assertEqual(len(second_page["groups"]), 1)
            self.assertEqual(second_page["groups"][0]["title"], "Single action")

    def _action(
        self,
        *,
        action_id: str,
        summary: str,
        sequence_index: int = 0,
        group_summary: str | None = None,
        depends_on_action_id: str | None = None,
    ) -> ProposedAction:
        return ProposedAction(
            action_id=action_id,
            session_id="test-session",
            tool_name="open_application",
            category=ToolCategory.SYSTEM,
            permission_level=PermissionLevel.LOW_RISK,
            approval_mode=ApprovalMode.USER_CONFIRMATION,
            summary=summary,
            group_id="group-1" if group_summary else None,
            group_summary=group_summary,
            sequence_index=sequence_index,
            depends_on_action_id=depends_on_action_id,
            arguments={"application": "calculator"},
        )

    def _decision(self) -> PolicyDecision:
        return PolicyDecision(
            allowed=True,
            requires_confirmation=True,
            approval_mode=ApprovalMode.USER_CONFIRMATION,
            reason="Needs approval.",
        )


if __name__ == "__main__":
    unittest.main()

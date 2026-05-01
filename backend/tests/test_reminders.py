from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from app.api.routes.reminders import _normalize_due_at
from app.services.orchestrator import IntentRouter
from app.services.reminders import ReminderService
from app.tools.safe import CreateReminderTool


class ReminderTests(unittest.TestCase):
    def test_reminder_service_creates_and_lists_pending_items(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ReminderService(Path(temp_dir) / "reminders.sqlite3")

            created = service.create_reminder(
                title="Review roadmap",
                details="Check phase sequencing",
                schedule_hint="tomorrow at 9am",
                due_at="2026-03-21T09:00:00+00:00",
            )
            reminders = service.list_upcoming(limit=5)

            self.assertEqual(service.count_pending(), 1)
            self.assertEqual(created["title"], "Review roadmap")
            self.assertEqual(reminders[0]["title"], "Review roadmap")
            self.assertEqual(reminders[0]["schedule_hint"], "tomorrow at 9am")

    def test_create_reminder_tool_uses_service(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ReminderService(Path(temp_dir) / "reminders.sqlite3")
            tool = CreateReminderTool(service)

            result = tool.execute(
                {
                    "title": "Ship the demo",
                    "details": "Reminder created from chat",
                    "schedule_hint": "in 2 hours",
                    "due_at": "2026-03-20T14:00:00+00:00",
                }
            )

            self.assertTrue(result.success)
            self.assertEqual(result.data["title"], "Ship the demo")
            self.assertEqual(service.count_pending(), 1)

    def test_create_reminder_tool_supports_recurrence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ReminderService(Path(temp_dir) / "reminders.sqlite3")
            tool = CreateReminderTool(service)

            result = tool.execute(
                {
                    "title": "Review metrics",
                    "details": "Recurring check-in",
                    "schedule_hint": "every weekday at 9am",
                    "due_at": "2030-04-02T09:00:00+00:00",
                    "recurrence_rule": "weekdays",
                    "recurrence_label": "every weekday at 9am",
                }
            )

            self.assertTrue(result.success)
            self.assertEqual(result.data["recurrence_rule"], "weekdays")
            self.assertEqual(result.data["recurrence_label"], "every weekday at 9am")

    def test_service_can_complete_and_reopen_reminders(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ReminderService(Path(temp_dir) / "reminders.sqlite3")
            created = service.create_reminder(title="Finish QA pass")

            completed = service.complete_reminder(created["id"])

            self.assertIsNotNone(completed)
            self.assertEqual(completed["status"], "completed")
            self.assertIsNotNone(completed["completed_at"])
            self.assertEqual(service.count_pending(), 0)

            reopened = service.reopen_reminder(created["id"])

            self.assertIsNotNone(reopened)
            self.assertEqual(reopened["status"], "pending")
            self.assertIsNone(reopened["completed_at"])
            self.assertEqual(service.count_pending(), 1)

    def test_service_can_reschedule_reminders(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ReminderService(Path(temp_dir) / "reminders.sqlite3")
            created = service.create_reminder(title="Rework the landing page")

            updated = service.reschedule_reminder(
                created["id"],
                due_at="2030-04-02T09:00:00+00:00",
                schedule_hint="tomorrow at 9am",
            )

            self.assertIsNotNone(updated)
            self.assertEqual(updated["status"], "pending")
            self.assertEqual(updated["due_at"], "2030-04-02T09:00:00+00:00")
            self.assertEqual(updated["schedule_hint"], "tomorrow at 9am")

    def test_service_can_set_and_clear_recurrence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ReminderService(Path(temp_dir) / "reminders.sqlite3")
            created = service.create_reminder(
                title="Review analytics",
                due_at="2030-04-02T09:00:00+00:00",
            )

            recurring = service.set_recurrence(
                created["id"],
                recurrence_rule="daily",
                recurrence_label="every day",
            )

            self.assertIsNotNone(recurring)
            self.assertEqual(recurring["recurrence_rule"], "daily")
            self.assertEqual(recurring["recurrence_label"], "every day")

            cleared = service.clear_recurrence(created["id"])

            self.assertIsNotNone(cleared)
            self.assertIsNone(cleared["recurrence_rule"])
            self.assertIsNone(cleared["recurrence_label"])

    def test_completing_recurring_reminder_creates_next_occurrence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ReminderService(Path(temp_dir) / "reminders.sqlite3")
            created = service.create_reminder(
                title="Review analytics",
                due_at="2999-01-01T09:00:00+00:00",
                recurrence_rule="daily",
                recurrence_label="every day",
            )

            completed = service.complete_reminder(created["id"])
            reminders = service.list_upcoming(limit=10, include_completed=True)

            self.assertIsNotNone(completed)
            self.assertEqual(completed["status"], "completed")
            self.assertIn("next_occurrence", completed)
            self.assertEqual(completed["next_occurrence"]["due_at"], "2999-01-02T09:00:00+00:00")
            self.assertEqual(completed["next_occurrence"]["recurrence_rule"], "daily")
            self.assertEqual(service.count_pending(), 1)
            self.assertEqual(len([item for item in reminders if item["status"] == "pending"]), 1)

    def test_weekday_recurrence_skips_weekends(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ReminderService(Path(temp_dir) / "reminders.sqlite3")
            friday_due = datetime(2030, 3, 1, 9, 0, tzinfo=timezone.utc)
            self.assertEqual(friday_due.weekday(), 4)
            created = service.create_reminder(
                title="Weekday standup",
                due_at=friday_due.isoformat(),
                recurrence_rule="weekdays",
                recurrence_label="every weekday",
            )

            completed = service.complete_reminder(created["id"])

            self.assertIsNotNone(completed)
            self.assertEqual(completed["next_occurrence"]["due_at"], "2030-03-04T09:00:00+00:00")

    def test_custom_schedule_normalization_keeps_offset_aware_values(self) -> None:
        self.assertEqual(_normalize_due_at("2030-04-02T09:00:00+00:00"), "2030-04-02T09:00:00+00:00")

    def test_list_upcoming_can_include_completed_items(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ReminderService(Path(temp_dir) / "reminders.sqlite3")
            created = service.create_reminder(title="Wrap release notes")
            service.complete_reminder(created["id"])

            pending_only = service.list_upcoming(limit=5)
            with_completed = service.list_upcoming(limit=5, include_completed=True)

            self.assertEqual(pending_only, [])
            self.assertEqual(len(with_completed), 1)
            self.assertEqual(with_completed[0]["status"], "completed")
            self.assertIsNotNone(with_completed[0]["completed_display"])

    def test_list_upcoming_can_include_archived_items(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ReminderService(Path(temp_dir) / "reminders.sqlite3")
            service.create_reminder(title="Keep active")
            archived = service.create_reminder(title="Archive me")
            service.archive_reminder(archived["id"])

            default_list = service.list_upcoming(limit=5, include_completed=True)
            with_archived = service.list_upcoming(limit=5, include_completed=True, include_archived=True)

            self.assertTrue(all(item["status"] != "archived" for item in default_list))
            archived_item = next(item for item in with_archived if item["id"] == archived["id"])
            self.assertEqual(archived_item["status"], "archived")
            self.assertIsNotNone(archived_item["archived_display"])

    def test_summary_reports_pending_overdue_unscheduled_and_completed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ReminderService(Path(temp_dir) / "reminders.sqlite3")
            service.create_reminder(title="Past due", due_at="2000-01-01T09:00:00+00:00")
            service.create_reminder(title="Future item", due_at="2999-01-01T09:00:00+00:00")
            service.create_reminder(title="No date")
            done = service.create_reminder(title="Completed item", due_at="2026-03-20T09:00:00+00:00")
            archived = service.create_reminder(title="Archived item")
            service.complete_reminder(done["id"])
            service.archive_reminder(archived["id"])

            summary = service.summary()

            self.assertEqual(summary["pending"], 3)
            self.assertEqual(summary["overdue"], 1)
            self.assertEqual(summary["unscheduled"], 1)
            self.assertEqual(summary["completed"], 1)
            self.assertEqual(summary["archived"], 1)

    def test_service_can_archive_and_restore_reminders(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ReminderService(Path(temp_dir) / "reminders.sqlite3")
            created = service.create_reminder(title="Tidy reminder history")

            archived = service.archive_reminder(created["id"])

            self.assertIsNotNone(archived)
            self.assertEqual(archived["status"], "archived")
            self.assertIsNotNone(archived["archived_at"])
            self.assertEqual(service.count_pending(), 0)

            restored = service.restore_reminder(created["id"])

            self.assertIsNotNone(restored)
            self.assertEqual(restored["status"], "pending")
            self.assertIsNone(restored["archived_at"])
            self.assertEqual(service.count_pending(), 1)

    def test_service_can_archive_completed_reminders_in_bulk(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ReminderService(Path(temp_dir) / "reminders.sqlite3")
            first = service.create_reminder(title="Completed one")
            second = service.create_reminder(title="Completed two")
            service.create_reminder(title="Keep pending")
            service.complete_reminder(first["id"])
            service.complete_reminder(second["id"])

            archived_count = service.archive_completed_reminders()
            reminders = service.list_upcoming(limit=10, include_archived=True)

            self.assertEqual(archived_count, 2)
            archived_ids = {item["id"] for item in reminders if item["status"] == "archived"}
            self.assertEqual(archived_ids, {first["id"], second["id"]})

    def test_service_can_restore_archived_reminders_in_bulk(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ReminderService(Path(temp_dir) / "reminders.sqlite3")
            first = service.create_reminder(title="Archived one")
            second = service.create_reminder(title="Archived two")
            service.archive_reminder(first["id"])
            service.archive_reminder(second["id"])

            restored_count = service.restore_archived_reminders()
            reminders = service.list_upcoming(limit=10)

            self.assertEqual(restored_count, 2)
            restored_ids = {item["id"] for item in reminders if item["status"] == "pending"}
            self.assertEqual(restored_ids, {first["id"], second["id"]})

    def test_service_can_delete_archived_reminder(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ReminderService(Path(temp_dir) / "reminders.sqlite3")
            archived = service.create_reminder(title="Delete me")
            pending = service.create_reminder(title="Keep me")
            service.archive_reminder(archived["id"])

            deleted = service.delete_archived_reminder(archived["id"])
            reminders = service.list_upcoming(limit=10, include_archived=True)

            self.assertTrue(deleted)
            self.assertNotIn(archived["id"], {item["id"] for item in reminders})
            self.assertIn(pending["id"], {item["id"] for item in reminders})

    def test_service_can_purge_archived_reminders(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ReminderService(Path(temp_dir) / "reminders.sqlite3")
            first = service.create_reminder(title="Archived one")
            second = service.create_reminder(title="Archived two")
            pending = service.create_reminder(title="Keep pending")
            service.archive_reminder(first["id"])
            service.archive_reminder(second["id"])

            deleted_count = service.purge_archived_reminders()
            reminders = service.list_upcoming(limit=10, include_archived=True)

            self.assertEqual(deleted_count, 2)
            self.assertEqual({item["id"] for item in reminders}, {pending["id"]})

    def test_router_routes_relative_reminder_requests(self) -> None:
        router = IntentRouter(now_provider=lambda: datetime(2026, 3, 20, 10, 0, tzinfo=timezone.utc))

        route = router.route("Remind me to review roadmap tomorrow at 9am")

        self.assertEqual(route.tool_name, "create_reminder")
        self.assertEqual(route.arguments["title"], "review roadmap")
        self.assertEqual(route.arguments["schedule_hint"], "tomorrow at 9am")
        self.assertEqual(route.arguments["due_at"], "2026-03-21T09:00:00+00:00")

    def test_router_routes_duration_reminders_before_search(self) -> None:
        router = IntentRouter(now_provider=lambda: datetime(2026, 3, 20, 10, 0, tzinfo=timezone.utc))

        route = router.route("Remind me to research launch plans in 2 hours")

        self.assertEqual(route.tool_name, "create_reminder")
        self.assertEqual(route.arguments["title"], "research launch plans")
        self.assertEqual(route.arguments["schedule_hint"], "in 2 hours")
        self.assertEqual(route.arguments["due_at"], "2026-03-20T12:00:00+00:00")

    def test_router_routes_weekday_recurrence_requests(self) -> None:
        router = IntentRouter(now_provider=lambda: datetime(2026, 3, 20, 10, 0, tzinfo=timezone.utc))

        route = router.route("Remind me to review the roadmap every weekday at 9am")

        self.assertEqual(route.tool_name, "create_reminder")
        self.assertEqual(route.arguments["title"], "review the roadmap")
        self.assertEqual(route.arguments["recurrence_rule"], "weekdays")
        self.assertEqual(route.arguments["recurrence_label"], "every weekday at 9am")
        self.assertEqual(route.arguments["due_at"], "2026-03-23T09:00:00+00:00")

    def test_router_routes_weekly_named_day_recurrence_requests(self) -> None:
        router = IntentRouter(now_provider=lambda: datetime(2026, 3, 20, 10, 0, tzinfo=timezone.utc))

        route = router.route("Remind me to publish the report every monday at 8am")

        self.assertEqual(route.tool_name, "create_reminder")
        self.assertEqual(route.arguments["title"], "publish the report")
        self.assertEqual(route.arguments["recurrence_rule"], "weekly")
        self.assertEqual(route.arguments["recurrence_label"], "every monday at 8am")
        self.assertEqual(route.arguments["due_at"], "2026-03-23T08:00:00+00:00")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Mapping


WorkflowRunner = Callable[[str, str], Mapping[str, Any]]


class WorkflowService:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS workflows (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    schedule_type TEXT NOT NULL DEFAULT 'manual',
                    interval_hours INTEGER,
                    run_hour INTEGER,
                    run_minute INTEGER,
                    run_weekday INTEGER,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_queued_at TEXT,
                    last_run_at TEXT,
                    last_task_status TEXT,
                    next_run_at TEXT
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id INTEGER NOT NULL,
                    prompt TEXT NOT NULL,
                    queued_for TEXT NOT NULL,
                    source TEXT NOT NULL DEFAULT 'schedule',
                    status TEXT NOT NULL DEFAULT 'queued',
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    finished_at TEXT,
                    assistant_text TEXT,
                    error TEXT,
                    pending_action_count INTEGER NOT NULL DEFAULT 0,
                    outcome_count INTEGER NOT NULL DEFAULT 0,
                    UNIQUE(workflow_id, queued_for, source),
                    FOREIGN KEY (workflow_id) REFERENCES workflows(id)
                )
                """
            )
            connection.commit()

    def create_workflow(
        self,
        *,
        name: str,
        prompt: str,
        schedule_type: str,
        interval_hours: int | None = None,
        run_hour: int | None = None,
        run_minute: int | None = None,
        run_weekday: int | None = None,
        active: bool = True,
    ) -> dict[str, Any]:
        schedule = self._normalize_schedule(
            schedule_type=schedule_type,
            interval_hours=interval_hours,
            run_hour=run_hour,
            run_minute=run_minute,
            run_weekday=run_weekday,
        )
        now = self._now()
        next_run_at = self._compute_next_run(schedule, reference=now) if active else None

        with closing(self._connect()) as connection:
            cursor = connection.execute(
                """
                INSERT INTO workflows (
                    name,
                    prompt,
                    schedule_type,
                    interval_hours,
                    run_hour,
                    run_minute,
                    run_weekday,
                    active,
                    created_at,
                    updated_at,
                    next_run_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self._clean_name(name),
                    self._clean_prompt(prompt),
                    schedule["schedule_type"],
                    schedule["interval_hours"],
                    schedule["run_hour"],
                    schedule["run_minute"],
                    schedule["run_weekday"],
                    1 if active else 0,
                    now.isoformat(),
                    now.isoformat(),
                    next_run_at,
                ),
            )
            connection.commit()
            workflow_id = int(cursor.lastrowid)

        workflow = self.get_workflow(workflow_id)
        if workflow is None:
            raise RuntimeError("Workflow creation completed but could not be reloaded.")
        return workflow

    def list_workflows(self, *, limit: int = 20) -> list[dict[str, Any]]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    name,
                    prompt,
                    schedule_type,
                    interval_hours,
                    run_hour,
                    run_minute,
                    run_weekday,
                    active,
                    created_at,
                    updated_at,
                    last_queued_at,
                    last_run_at,
                    last_task_status,
                    next_run_at
                FROM workflows
                ORDER BY active DESC, CASE WHEN next_run_at IS NULL THEN 1 ELSE 0 END, next_run_at ASC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._serialize_workflow_row(row) for row in rows]

    def get_workflow(self, workflow_id: int) -> dict[str, Any] | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    name,
                    prompt,
                    schedule_type,
                    interval_hours,
                    run_hour,
                    run_minute,
                    run_weekday,
                    active,
                    created_at,
                    updated_at,
                    last_queued_at,
                    last_run_at,
                    last_task_status,
                    next_run_at
                FROM workflows
                WHERE id = ?
                """,
                (workflow_id,),
            ).fetchone()
        if row is None:
            return None
        return self._serialize_workflow_row(row)

    def set_workflow_active(self, workflow_id: int, *, active: bool) -> dict[str, Any] | None:
        workflow = self.get_workflow(workflow_id)
        if workflow is None:
            return None
        schedule = self._schedule_from_workflow(workflow)
        next_run_at = self._compute_next_run(schedule, reference=self._now()) if active else None
        with closing(self._connect()) as connection:
            connection.execute(
                """
                UPDATE workflows
                SET active = ?, next_run_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (1 if active else 0, next_run_at, self._now().isoformat(), workflow_id),
            )
            connection.commit()
        return self.get_workflow(workflow_id)

    def queue_workflow_now(self, workflow_id: int, *, source: str = "manual") -> dict[str, Any] | None:
        workflow = self.get_workflow(workflow_id)
        if workflow is None:
            return None
        queued_for = self._now().isoformat()
        with closing(self._connect()) as connection:
            cursor = connection.execute(
                """
                INSERT INTO workflow_tasks (
                    workflow_id,
                    prompt,
                    queued_for,
                    source,
                    status,
                    created_at
                )
                VALUES (?, ?, ?, ?, 'queued', ?)
                """,
                (
                    workflow_id,
                    str(workflow["prompt"]),
                    queued_for,
                    source,
                    self._now().isoformat(),
                ),
            )
            connection.execute(
                """
                UPDATE workflows
                SET last_queued_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (queued_for, self._now().isoformat(), workflow_id),
            )
            connection.commit()
            task_id = int(cursor.lastrowid)
        return self.get_task(task_id)

    def dispatch_due(self, *, reference: datetime | None = None) -> list[dict[str, Any]]:
        due_reference = (reference or self._now()).astimezone()
        created: list[dict[str, Any]] = []
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    name,
                    prompt,
                    schedule_type,
                    interval_hours,
                    run_hour,
                    run_minute,
                    run_weekday,
                    active,
                    created_at,
                    updated_at,
                    last_queued_at,
                    last_run_at,
                    last_task_status,
                    next_run_at
                FROM workflows
                WHERE active = 1 AND next_run_at IS NOT NULL
                ORDER BY next_run_at ASC, id ASC
                """
            ).fetchall()

            for row in rows:
                workflow = self._serialize_workflow_row(row)
                next_run_at = self._parse_timestamp(workflow.get("next_run_at"))
                if next_run_at is None or next_run_at > due_reference:
                    continue

                queued_for = next_run_at.isoformat()
                cursor = connection.execute(
                    """
                    INSERT OR IGNORE INTO workflow_tasks (
                        workflow_id,
                        prompt,
                        queued_for,
                        source,
                        status,
                        created_at
                    )
                    VALUES (?, ?, ?, 'schedule', 'queued', ?)
                    """,
                    (
                        workflow["id"],
                        workflow["prompt"],
                        queued_for,
                        self._now().isoformat(),
                    ),
                )
                next_due = self._advance_next_run(workflow, from_run=next_run_at)
                connection.execute(
                    """
                    UPDATE workflows
                    SET last_queued_at = ?, next_run_at = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        queued_for,
                        next_due,
                        self._now().isoformat(),
                        workflow["id"],
                    ),
                )
                if int(cursor.rowcount or 0):
                    task_id = int(cursor.lastrowid)
                    task = self._get_task_from_connection(connection, task_id)
                    if task is not None:
                        created.append(task)
            connection.commit()
        return created

    def list_tasks(self, *, limit: int = 20, status: str | None = None) -> list[dict[str, Any]]:
        query = """
            SELECT
                t.id,
                t.workflow_id,
                t.prompt,
                t.queued_for,
                t.source,
                t.status,
                t.created_at,
                t.started_at,
                t.finished_at,
                t.assistant_text,
                t.error,
                t.pending_action_count,
                t.outcome_count,
                w.name AS workflow_name
            FROM workflow_tasks t
            JOIN workflows w ON w.id = t.workflow_id
        """
        parameters: list[Any] = []
        if status:
            query += " WHERE t.status = ?"
            parameters.append(status)
        query += """
            ORDER BY
                CASE t.status
                    WHEN 'queued' THEN 0
                    WHEN 'running' THEN 1
                    WHEN 'approval_pending' THEN 2
                    ELSE 3
                END,
                t.queued_for ASC,
                t.id DESC
            LIMIT ?
        """
        parameters.append(limit)
        with closing(self._connect()) as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [self._serialize_task_row(row) for row in rows]

    def get_task(self, task_id: int) -> dict[str, Any] | None:
        with closing(self._connect()) as connection:
            return self._get_task_from_connection(connection, task_id)

    def run_task(self, task_id: int, *, runner: WorkflowRunner) -> dict[str, Any] | None:
        task = self.get_task(task_id)
        if task is None:
            return None
        if task["status"] != "queued":
            raise ValueError("Only queued tasks can be run.")

        started_at = self._now().isoformat()
        with closing(self._connect()) as connection:
            connection.execute(
                """
                UPDATE workflow_tasks
                SET status = 'running', started_at = ?, error = NULL
                WHERE id = ?
                """,
                (started_at, task_id),
            )
            connection.commit()

        try:
            response = dict(
                runner(
                    str(task["prompt"]),
                    f"workflow-{task['workflow_id']}-task-{task_id}",
                )
            )
        except Exception as exc:
            error_text = str(exc) or exc.__class__.__name__
            with closing(self._connect()) as connection:
                finished_at = self._now().isoformat()
                connection.execute(
                    """
                    UPDATE workflow_tasks
                    SET status = 'failed', finished_at = ?, error = ?
                    WHERE id = ?
                    """,
                    (finished_at, error_text, task_id),
                )
                connection.execute(
                    """
                    UPDATE workflows
                    SET last_run_at = ?, last_task_status = 'failed', updated_at = ?
                    WHERE id = ?
                    """,
                    (finished_at, finished_at, task["workflow_id"]),
                )
                connection.commit()
            updated = self.get_task(task_id)
            if updated is None:
                raise RuntimeError("Task failed but could not be reloaded.") from exc
            return {"task": updated, "response": None}

        pending_actions = [
            action
            for action in response.get("actions", [])
            if str(action.get("status", "")).lower() in {"proposed", "queued"}
        ]
        outcome_statuses = {
            str(outcome.get("status", "")).lower()
            for outcome in response.get("outcomes", [])
        }
        task_status = "completed"
        error_text: str | None = None
        if pending_actions:
            task_status = "approval_pending"
        elif outcome_statuses & {"failed", "blocked", "rejected"}:
            task_status = "failed"
            error_text = "One or more workflow actions did not complete successfully."

        finished_at = self._now().isoformat()
        with closing(self._connect()) as connection:
            connection.execute(
                """
                UPDATE workflow_tasks
                SET
                    status = ?,
                    finished_at = ?,
                    assistant_text = ?,
                    error = ?,
                    pending_action_count = ?,
                    outcome_count = ?
                WHERE id = ?
                """,
                (
                    task_status,
                    finished_at,
                    str(response.get("assistant_text", "")).strip(),
                    error_text,
                    len(pending_actions),
                    len(response.get("outcomes", [])),
                    task_id,
                ),
            )
            connection.execute(
                """
                UPDATE workflows
                SET last_run_at = ?, last_task_status = ?, updated_at = ?
                WHERE id = ?
                """,
                (finished_at, task_status, finished_at, task["workflow_id"]),
            )
            connection.commit()
        updated = self.get_task(task_id)
        if updated is None:
            raise RuntimeError("Task run completed but could not be reloaded.")
        return {"task": updated, "response": response}

    def cancel_task(self, task_id: int) -> dict[str, Any] | None:
        task = self.get_task(task_id)
        if task is None:
            return None
        if task["status"] != "queued":
            raise ValueError("Only queued tasks can be canceled.")

        finished_at = self._now().isoformat()
        with closing(self._connect()) as connection:
            connection.execute(
                """
                UPDATE workflow_tasks
                SET status = 'canceled', finished_at = ?, error = ?
                WHERE id = ?
                """,
                (finished_at, "Canceled before execution.", task_id),
            )
            connection.commit()

        updated = self.get_task(task_id)
        if updated is None:
            raise RuntimeError("Task cancellation completed but could not be reloaded.")
        return updated

    def retry_task(self, task_id: int) -> dict[str, Any] | None:
        task = self.get_task(task_id)
        if task is None:
            return None
        if task["status"] not in {"failed", "canceled"}:
            raise ValueError("Only failed or canceled tasks can be retried.")
        return self.queue_workflow_now(int(task["workflow_id"]), source="retry")

    def supervisor_cycle(
        self,
        *,
        runner: WorkflowRunner,
        enabled: bool,
        max_tasks: int,
        max_pending_approvals: int,
        pause_workflows_on_failure: bool,
    ) -> dict[str, Any]:
        dispatched_tasks = self.dispatch_due()
        cycle = {
            "enabled": bool(enabled),
            "dispatched_count": len(dispatched_tasks),
            "run_count": 0,
            "stopped_reason": "disabled" if not enabled else "",
            "dispatched_tasks": dispatched_tasks,
            "executed_tasks": [],
            "paused_workflows": [],
        }
        if not enabled:
            return cycle

        task_limit = min(max(int(max_tasks or 1), 1), 5)
        approval_limit = min(max(int(max_pending_approvals or 1), 1), 10)
        summary = self.summary()
        if summary["approval_pending_tasks"] >= approval_limit:
            cycle["stopped_reason"] = "approval_limit_reached"
            return cycle

        queued_tasks = self.list_tasks(limit=max(task_limit * 3, task_limit), status="queued")
        for task in queued_tasks:
            if cycle["run_count"] >= task_limit:
                cycle["stopped_reason"] = "cycle_limit_reached"
                break

            summary = self.summary()
            if summary["approval_pending_tasks"] >= approval_limit:
                cycle["stopped_reason"] = "approval_limit_reached"
                break

            task_result = self.run_task(int(task["id"]), runner=runner)
            if task_result is None:
                continue

            updated_task = task_result["task"]
            cycle["run_count"] += 1
            cycle["executed_tasks"].append(updated_task)

            if updated_task["status"] == "failed" and pause_workflows_on_failure:
                paused_workflow = self.set_workflow_active(int(updated_task["workflow_id"]), active=False)
                if paused_workflow is not None:
                    cycle["paused_workflows"].append(paused_workflow)
                cycle["stopped_reason"] = "workflow_failed"
                break

            if updated_task["status"] == "approval_pending":
                summary = self.summary()
                if summary["approval_pending_tasks"] >= approval_limit:
                    cycle["stopped_reason"] = "approval_limit_reached"
                    break

        if not cycle["stopped_reason"]:
            cycle["stopped_reason"] = "idle" if cycle["run_count"] == 0 else "completed"
        return cycle

    def summary(self) -> dict[str, int]:
        with closing(self._connect()) as connection:
            workflow_rows = connection.execute("SELECT active, schedule_type FROM workflows").fetchall()
            task_rows = connection.execute("SELECT status FROM workflow_tasks").fetchall()

        summary = {
            "active_workflows": 0,
            "paused_workflows": 0,
            "manual_workflows": 0,
            "queued_tasks": 0,
            "running_tasks": 0,
            "approval_pending_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "canceled_tasks": 0,
        }
        for row in workflow_rows:
            if int(row["active"] or 0):
                summary["active_workflows"] += 1
            else:
                summary["paused_workflows"] += 1
            if str(row["schedule_type"] or "manual") == "manual":
                summary["manual_workflows"] += 1

        for row in task_rows:
            status = str(row["status"] or "queued")
            if status == "queued":
                summary["queued_tasks"] += 1
            elif status == "running":
                summary["running_tasks"] += 1
            elif status == "approval_pending":
                summary["approval_pending_tasks"] += 1
            elif status == "completed":
                summary["completed_tasks"] += 1
            elif status == "failed":
                summary["failed_tasks"] += 1
            elif status == "canceled":
                summary["canceled_tasks"] += 1
        return summary

    def audit_workflow_payload(self, workflow: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "id": workflow["id"],
            "name": workflow["name"],
            "schedule_type": workflow["schedule_type"],
            "schedule_label": workflow["schedule_label"],
            "active": workflow["active"],
            "next_run_at": workflow["next_run_at"],
            "last_run_at": workflow["last_run_at"],
            "last_task_status": workflow["last_task_status"],
        }

    def audit_task_payload(self, task: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "id": task["id"],
            "workflow_id": task["workflow_id"],
            "workflow_name": task["workflow_name"],
            "queued_for": task["queued_for"],
            "source": task["source"],
            "status": task["status"],
            "pending_action_count": task["pending_action_count"],
            "outcome_count": task["outcome_count"],
            "assistant_text_length": len(str(task.get("assistant_text") or "")),
            "error": task["error"],
        }

    def _get_task_from_connection(self, connection: sqlite3.Connection, task_id: int) -> dict[str, Any] | None:
        row = connection.execute(
            """
            SELECT
                t.id,
                t.workflow_id,
                t.prompt,
                t.queued_for,
                t.source,
                t.status,
                t.created_at,
                t.started_at,
                t.finished_at,
                t.assistant_text,
                t.error,
                t.pending_action_count,
                t.outcome_count,
                w.name AS workflow_name
            FROM workflow_tasks t
            JOIN workflows w ON w.id = t.workflow_id
            WHERE t.id = ?
            """,
            (task_id,),
        ).fetchone()
        if row is None:
            return None
        return self._serialize_task_row(row)

    def _serialize_workflow_row(self, row: sqlite3.Row | Mapping[str, Any]) -> dict[str, Any]:
        schedule_type = str(row["schedule_type"] or "manual")
        interval_hours = row["interval_hours"]
        run_hour = row["run_hour"]
        run_minute = row["run_minute"]
        run_weekday = row["run_weekday"]
        schedule = {
            "schedule_type": schedule_type,
            "interval_hours": int(interval_hours) if interval_hours is not None else None,
            "run_hour": int(run_hour) if run_hour is not None else None,
            "run_minute": int(run_minute) if run_minute is not None else None,
            "run_weekday": int(run_weekday) if run_weekday is not None else None,
        }
        next_run_at = row["next_run_at"]
        last_run_at = row["last_run_at"]
        last_queued_at = row["last_queued_at"]
        return {
            "id": int(row["id"]),
            "name": str(row["name"] or ""),
            "prompt": str(row["prompt"] or ""),
            "schedule_type": schedule_type,
            "interval_hours": schedule["interval_hours"],
            "run_hour": schedule["run_hour"],
            "run_minute": schedule["run_minute"],
            "run_weekday": schedule["run_weekday"],
            "schedule_label": self._schedule_label(schedule),
            "active": bool(int(row["active"] or 0)),
            "created_at": str(row["created_at"] or ""),
            "updated_at": str(row["updated_at"] or ""),
            "next_run_at": next_run_at,
            "next_run_display": self._display_timestamp(next_run_at),
            "last_queued_at": last_queued_at,
            "last_queued_display": self._display_timestamp(last_queued_at),
            "last_run_at": last_run_at,
            "last_run_display": self._display_timestamp(last_run_at),
            "last_task_status": str(row["last_task_status"] or ""),
        }

    def _serialize_task_row(self, row: sqlite3.Row | Mapping[str, Any]) -> dict[str, Any]:
        return {
            "id": int(row["id"]),
            "workflow_id": int(row["workflow_id"]),
            "workflow_name": str(row["workflow_name"] or ""),
            "prompt": str(row["prompt"] or ""),
            "queued_for": str(row["queued_for"] or ""),
            "queued_for_display": self._display_timestamp(row["queued_for"]),
            "source": str(row["source"] or "schedule"),
            "status": str(row["status"] or "queued"),
            "created_at": str(row["created_at"] or ""),
            "started_at": str(row["started_at"] or ""),
            "finished_at": str(row["finished_at"] or ""),
            "finished_display": self._display_timestamp(row["finished_at"]),
            "assistant_text": str(row["assistant_text"] or ""),
            "error": str(row["error"] or ""),
            "pending_action_count": int(row["pending_action_count"] or 0),
            "outcome_count": int(row["outcome_count"] or 0),
        }

    def _schedule_from_workflow(self, workflow: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "schedule_type": workflow["schedule_type"],
            "interval_hours": workflow.get("interval_hours"),
            "run_hour": workflow.get("run_hour"),
            "run_minute": workflow.get("run_minute"),
            "run_weekday": workflow.get("run_weekday"),
        }

    def _normalize_schedule(
        self,
        *,
        schedule_type: str,
        interval_hours: int | None,
        run_hour: int | None,
        run_minute: int | None,
        run_weekday: int | None,
    ) -> dict[str, Any]:
        normalized_type = str(schedule_type or "manual").strip().lower()
        if normalized_type not in {"manual", "hourly", "daily", "weekly"}:
            raise ValueError("Unsupported workflow schedule type.")

        schedule = {
            "schedule_type": normalized_type,
            "interval_hours": None,
            "run_hour": None,
            "run_minute": None,
            "run_weekday": None,
        }
        if normalized_type == "hourly":
            if interval_hours is None:
                raise ValueError("Hourly workflows need an interval in hours.")
            schedule["interval_hours"] = min(max(int(interval_hours), 1), 24)
        elif normalized_type == "daily":
            if run_hour is None or run_minute is None:
                raise ValueError("Daily workflows need a run hour and minute.")
            schedule["run_hour"] = min(max(int(run_hour), 0), 23)
            schedule["run_minute"] = min(max(int(run_minute), 0), 59)
        elif normalized_type == "weekly":
            if run_weekday is None or run_hour is None or run_minute is None:
                raise ValueError("Weekly workflows need a weekday plus run hour and minute.")
            schedule["run_weekday"] = min(max(int(run_weekday), 0), 6)
            schedule["run_hour"] = min(max(int(run_hour), 0), 23)
            schedule["run_minute"] = min(max(int(run_minute), 0), 59)
        return schedule

    def _compute_next_run(self, schedule: Mapping[str, Any], *, reference: datetime) -> str | None:
        schedule_type = str(schedule["schedule_type"])
        local_reference = reference.astimezone()
        if schedule_type == "manual":
            return None
        if schedule_type == "hourly":
            return (local_reference + timedelta(hours=int(schedule["interval_hours"] or 1))).isoformat()
        if schedule_type == "daily":
            candidate = local_reference.replace(
                hour=int(schedule["run_hour"] or 0),
                minute=int(schedule["run_minute"] or 0),
                second=0,
                microsecond=0,
            )
            if candidate <= local_reference:
                candidate += timedelta(days=1)
            return candidate.isoformat()
        candidate = local_reference.replace(
            hour=int(schedule["run_hour"] or 0),
            minute=int(schedule["run_minute"] or 0),
            second=0,
            microsecond=0,
        )
        delta_days = (int(schedule["run_weekday"] or 0) - candidate.weekday()) % 7
        candidate += timedelta(days=delta_days)
        if candidate <= local_reference:
            candidate += timedelta(days=7)
        return candidate.isoformat()

    def _advance_next_run(self, workflow: Mapping[str, Any], *, from_run: datetime) -> str | None:
        schedule = self._schedule_from_workflow(workflow)
        schedule_type = str(schedule["schedule_type"])
        local_run = from_run.astimezone()
        if schedule_type == "manual":
            return None
        if schedule_type == "hourly":
            return (local_run + timedelta(hours=int(schedule["interval_hours"] or 1))).isoformat()
        if schedule_type == "daily":
            return (local_run + timedelta(days=1)).replace(second=0, microsecond=0).isoformat()
        if schedule_type == "weekly":
            return (local_run + timedelta(days=7)).replace(second=0, microsecond=0).isoformat()
        return None

    def _schedule_label(self, schedule: Mapping[str, Any]) -> str:
        schedule_type = str(schedule["schedule_type"])
        if schedule_type == "manual":
            return "Manual run only"
        if schedule_type == "hourly":
            interval = int(schedule["interval_hours"] or 1)
            return f"Every {interval} hour{'s' if interval != 1 else ''}"
        if schedule_type == "daily":
            return f"Daily at {self._format_clock(schedule['run_hour'], schedule['run_minute'])}"
        weekday = self._weekday_label(int(schedule["run_weekday"] or 0))
        return f"{weekday} at {self._format_clock(schedule['run_hour'], schedule['run_minute'])}"

    def _weekday_label(self, weekday: int) -> str:
        labels = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        return labels[min(max(int(weekday), 0), 6)]

    def _format_clock(self, hour: Any, minute: Any) -> str:
        return f"{int(hour or 0):02d}:{int(minute or 0):02d}"

    def _display_timestamp(self, value: Any) -> str | None:
        parsed = self._parse_timestamp(value)
        if parsed is None:
            return None
        return parsed.astimezone().strftime("%b %d, %Y %I:%M %p")

    def _parse_timestamp(self, value: Any) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value))
        except ValueError:
            return None

    def _clean_name(self, value: str) -> str:
        cleaned = str(value or "").strip()
        return cleaned[:80] or "Untitled workflow"

    def _clean_prompt(self, value: str) -> str:
        cleaned = str(value or "").strip()
        return cleaned[:600] or "Review the current workspace."

    def _now(self) -> datetime:
        return datetime.now().astimezone()

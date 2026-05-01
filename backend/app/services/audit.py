from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.models import ActionStatus, ProposedAction, ToolResult
from app.services.policy import PolicyDecision

REDACTED_ARGUMENT_FIELDS_BY_TOOL = {
    "draft_email": {"body"},
    "send_email": {"body"},
    "draft_whatsapp_message": {"body"},
    "send_whatsapp_message": {"body"},
    "generate_content_package": {"context"},
}


class AuditLogger:
    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def record(
        self,
        *,
        action: ProposedAction,
        status: ActionStatus,
        decision: PolicyDecision,
        result: ToolResult | None = None,
        error: str | None = None,
        trace: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        serialized_action = self._sanitize_action(action.to_dict())
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": serialized_action,
            "status": status.value,
            "decision": decision.to_dict(),
            "result": result.to_dict() if result else None,
            "error": error,
        }
        normalized_trace = self._normalize_trace(event["action"], trace)
        if normalized_trace:
            event["trace"] = normalized_trace
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event) + "\n")
        return event

    def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.query(limit=limit)["items"]

    def query(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        search_query: str | None = None,
        status_scope: str | None = None,
        started_after: str | None = None,
        ended_before: str | None = None,
    ) -> dict[str, Any]:
        if not self.log_path.exists():
            return {
                "items": [],
                "total": 0,
                "offset": max(offset, 0),
                "limit": max(limit, 1),
                "has_more": False,
                "query": (search_query or "").strip(),
                "status_scope": self._normalize_status_scope(status_scope),
                "started_after": (started_after or "").strip(),
                "ended_before": (ended_before or "").strip(),
            }

        normalized_limit = max(1, limit)
        normalized_offset = max(0, offset)
        normalized_query = (search_query or "").strip()
        normalized_status_scope = self._normalize_status_scope(status_scope)

        events = self._filter_events(
            search_query=search_query,
            status_scope=status_scope,
            started_after=started_after,
            ended_before=ended_before,
        )

        total = len(events)
        window = events[normalized_offset : normalized_offset + normalized_limit]
        return {
            "items": window,
            "total": total,
            "offset": normalized_offset,
            "limit": normalized_limit,
            "has_more": normalized_offset + normalized_limit < total,
            "query": normalized_query,
            "status_scope": normalized_status_scope,
            "started_after": started_after,
            "ended_before": ended_before,
        }

    def export(
        self,
        *,
        limit: int = 500,
        search_query: str | None = None,
        status_scope: str | None = None,
        started_after: str | None = None,
        ended_before: str | None = None,
    ) -> dict[str, Any]:
        payload = self.query(
            limit=max(1, limit),
            offset=0,
            search_query=search_query,
            status_scope=status_scope,
            started_after=started_after,
            ended_before=ended_before,
        )
        payload["exported_count"] = len(payload["items"])
        payload["truncated"] = payload["has_more"]
        return payload

    def query_groups(
        self,
        *,
        limit: int = 10,
        offset: int = 0,
        search_query: str | None = None,
        status_scope: str | None = None,
        started_after: str | None = None,
        ended_before: str | None = None,
    ) -> dict[str, Any]:
        normalized_limit = max(1, limit)
        normalized_offset = max(0, offset)
        normalized_query = (search_query or "").strip()
        normalized_status_scope = self._normalize_status_scope(status_scope)

        filtered_events = self._filter_events(
            search_query=search_query,
            status_scope=status_scope,
            started_after=started_after,
            ended_before=ended_before,
        )
        groups = self._group_events(filtered_events)
        window = groups[normalized_offset : normalized_offset + normalized_limit]
        return {
            "groups": window,
            "total_groups": len(groups),
            "total_events": len(filtered_events),
            "offset": normalized_offset,
            "limit": normalized_limit,
            "has_more": normalized_offset + normalized_limit < len(groups),
            "query": normalized_query,
            "status_scope": normalized_status_scope,
            "started_after": started_after,
            "ended_before": ended_before,
        }

    def _load_events(self) -> list[dict[str, Any]]:
        if not self.log_path.exists():
            return []

        with self.log_path.open("r", encoding="utf-8") as handle:
            lines = [line.strip() for line in handle if line.strip()]

        events = [json.loads(line) for line in reversed(lines)]
        for event in events:
            normalized_trace = self._normalize_trace(
                event.get("action", {}),
                event.get("trace"),
            )
            if normalized_trace:
                event["trace"] = normalized_trace
        return events

    def _matches_query(self, event: dict[str, Any], needle: str) -> bool:
        haystack = json.dumps(event, ensure_ascii=False, sort_keys=True).casefold()
        return needle in haystack

    def _filter_events(
        self,
        *,
        search_query: str | None = None,
        status_scope: str | None = None,
        started_after: str | None = None,
        ended_before: str | None = None,
    ) -> list[dict[str, Any]]:
        normalized_query = (search_query or "").strip()
        normalized_status_scope = self._normalize_status_scope(status_scope)
        normalized_started_after = self._parse_datetime(started_after)
        normalized_ended_before = self._parse_datetime(ended_before)

        events = self._load_events()
        if normalized_query:
            needle = normalized_query.casefold()
            events = [event for event in events if self._matches_query(event, needle)]
        if normalized_status_scope:
            events = [event for event in events if self._matches_status_scope(event, normalized_status_scope)]
        if normalized_started_after or normalized_ended_before:
            events = [
                event
                for event in events
                if self._matches_time_range(
                    event,
                    started_after=normalized_started_after,
                    ended_before=normalized_ended_before,
                )
            ]
        return events

    def _group_events(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[str, dict[str, Any]] = {}
        for event in events:
            key = self._group_key_for_event(event)
            if key not in grouped:
                trace = event.get("trace") or {}
                action = event.get("action") or {}
                grouped[key] = {
                    "group_key": key,
                    "group_id": trace.get("group_id") or action.get("group_id"),
                    "title": trace.get("group_summary") or action.get("group_summary") or action.get("summary") or "Activity",
                    "entries": [],
                }
            grouped[key]["entries"].append(event)

        groups: list[dict[str, Any]] = []
        for group in grouped.values():
            entries = sorted(group["entries"], key=self._event_timestamp_value)
            latest_entry = max(entries, key=self._event_timestamp_value)
            unique_steps = {
                entry.get("trace", {}).get("step_number")
                for entry in entries
                if isinstance(entry.get("trace", {}).get("step_number"), int)
            }
            groups.append(
                {
                    **group,
                    "entries": entries,
                    "latest_timestamp": latest_entry.get("timestamp"),
                    "event_count": len(entries),
                    "step_count": len(unique_steps),
                    "has_linked_flow": any(bool((entry.get("trace") or {}).get("group_id")) for entry in entries),
                }
            )

        groups.sort(key=lambda group: self._parse_datetime(group.get("latest_timestamp")) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        return groups

    def _sanitize_action(self, action: dict[str, Any]) -> dict[str, Any]:
        tool_name = str(action.get("tool_name") or "")
        redacted_fields = REDACTED_ARGUMENT_FIELDS_BY_TOOL.get(tool_name)
        if not redacted_fields:
            return action

        arguments = dict(action.get("arguments") or {})
        for field_name in redacted_fields:
            value = str(arguments.get(field_name) or "")
            if not value:
                continue
            arguments[f"{field_name}_length"] = len(value)
            arguments[f"has_{field_name}"] = True
            arguments[field_name] = "[redacted]"
        action["arguments"] = arguments
        return action

    def _group_key_for_event(self, event: dict[str, Any]) -> str:
        trace = event.get("trace") or {}
        action = event.get("action") or {}
        return (
            trace.get("group_id")
            or action.get("group_id")
            or action.get("action_id")
            or f"{event.get('timestamp', '')}:{action.get('summary', 'activity')}"
        )

    def _event_timestamp_value(self, event: dict[str, Any]) -> datetime:
        return self._parse_datetime(event.get("timestamp")) or datetime.min.replace(tzinfo=timezone.utc)

    def _normalize_status_scope(self, status_scope: str | None) -> str:
        normalized = (status_scope or "all").strip().casefold()
        valid_values = {status.value for status in ActionStatus}
        valid_scopes = {"all", "attention", "approval"} | valid_values
        if normalized in valid_scopes:
            return normalized
        return "all"

    def _matches_status_scope(self, event: dict[str, Any], status_scope: str) -> bool:
        status = str(event.get("status") or "").casefold()
        if status_scope == "all":
            return True
        if status_scope == "attention":
            return status in {"failed", "blocked", "rejected"}
        if status_scope == "approval":
            return status in {"proposed", "queued"}
        return status == status_scope

    def _matches_time_range(
        self,
        event: dict[str, Any],
        *,
        started_after: datetime | None,
        ended_before: datetime | None,
    ) -> bool:
        timestamp = self._parse_datetime(event.get("timestamp"))
        if timestamp is None:
            return False
        if started_after is not None and timestamp < started_after:
            return False
        if ended_before is not None and timestamp > ended_before:
            return False
        return True

    def _parse_datetime(self, value: Any) -> datetime | None:
        if value is None:
            return None
        normalized = str(value).strip()
        if not normalized:
            return None
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _normalize_trace(
        self,
        action: dict[str, Any],
        trace: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        normalized: dict[str, Any] = {}
        if trace:
            normalized.update(trace)

        sequence_index = action.get("sequence_index")
        if isinstance(sequence_index, int):
            normalized.setdefault("step_number", sequence_index + 1)

        group_id = action.get("group_id")
        if group_id:
            normalized.setdefault("group_id", group_id)

        group_summary = action.get("group_summary")
        if group_summary:
            normalized.setdefault("group_summary", group_summary)

        prerequisite_action_id = action.get("depends_on_action_id")
        if prerequisite_action_id:
            normalized.setdefault("prerequisite_action_id", prerequisite_action_id)

        if not normalized:
            return None
        return normalized

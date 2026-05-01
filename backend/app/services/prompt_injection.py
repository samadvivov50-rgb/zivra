from __future__ import annotations

import re
from typing import Any, Iterable


class PromptInjectionDefense:
    RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
        (
            "Prompt override attempt",
            re.compile(
                r"^\s*(ignore|disregard|forget)\b.{0,60}\b(previous|prior|above|earlier)\b.{0,30}\b(instructions?|prompts?|messages?|rules?)\b",
                flags=re.IGNORECASE,
            ),
        ),
        (
            "Role override attempt",
            re.compile(r"^\s*(you are now|act as|pretend to be)\b", flags=re.IGNORECASE),
        ),
        (
            "Tool execution request",
            re.compile(
                r"^\s*(use|invoke|call|run|execute)\b.{0,30}\b(tools?|functions?|commands?)\b",
                flags=re.IGNORECASE,
            ),
        ),
        (
            "External action request",
            re.compile(
                r"^\s*(send|open|launch|delete|shutdown|restart|copy|browse|visit|click|submit)\b.{0,60}\b(emails?|messages?|websites?|apps?|applications?|files?|clipboard|forms?|links?)\b",
                flags=re.IGNORECASE,
            ),
        ),
        (
            "Secret exfiltration request",
            re.compile(
                r"^\s*(reveal|show|print|expose)\b.{0,60}\b(system prompts?|developer messages?|secrets?|passwords?|api keys?|credentials?)\b",
                flags=re.IGNORECASE,
            ),
        ),
        (
            "Response override attempt",
            re.compile(r"^\s*(reply with|respond with|output only|instead do)\b", flags=re.IGNORECASE),
        ),
    )

    def sanitize_text(self, text: str) -> dict[str, Any]:
        normalized = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
        labels: list[str] = []
        safe_lines: list[str] = []
        removed_line_count = 0

        for line in normalized.split("\n"):
            stripped = line.strip()
            if not stripped:
                safe_lines.append("")
                continue

            label = self._match_label(stripped)
            if label is not None:
                removed_line_count += 1
                labels.append(label)
                continue
            safe_lines.append(line)

        sanitized_text = "\n".join(safe_lines)
        sanitized_text = re.sub(r"\n\s*\n\s*\n+", "\n\n", sanitized_text).strip()
        return {
            "sanitized_text": sanitized_text,
            **self._metadata(labels=labels, removed_line_count=removed_line_count),
        }

    def filter_items(self, items: Iterable[str]) -> dict[str, Any]:
        labels: list[str] = []
        kept_items: list[str] = []
        removed_line_count = 0

        for item in items:
            text = str(item or "").strip()
            if not text:
                continue

            label = self._match_label(text)
            if label is not None:
                removed_line_count += 1
                labels.append(label)
                continue
            kept_items.append(text)

        return {
            "items": kept_items,
            **self._metadata(labels=labels, removed_line_count=removed_line_count),
        }

    def merge_metadata(self, *parts: dict[str, Any]) -> dict[str, Any]:
        labels: list[str] = []
        removed_line_count = 0
        for part in parts:
            removed_line_count += int(part.get("removed_line_count", 0) or 0)
            for label in part.get("flag_labels", []) or []:
                normalized = str(label or "").strip()
                if normalized and normalized not in labels:
                    labels.append(normalized)
        return self._metadata(labels=labels, removed_line_count=removed_line_count)

    def to_metadata(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "prompt_injection_detected": bool(payload.get("prompt_injection_detected")),
            "flag_count": int(payload.get("flag_count", 0) or 0),
            "removed_line_count": int(payload.get("removed_line_count", 0) or 0),
            "flag_labels": list(payload.get("flag_labels", []) or []),
            "notice": str(payload.get("notice", "") or ""),
        }

    def _match_label(self, text: str) -> str | None:
        for label, pattern in self.RULES:
            if pattern.search(text):
                return label
        return None

    def _metadata(self, *, labels: list[str], removed_line_count: int) -> dict[str, Any]:
        unique_labels: list[str] = []
        for label in labels:
            if label not in unique_labels:
                unique_labels.append(label)
        detected = removed_line_count > 0
        return {
            "prompt_injection_detected": detected,
            "flag_count": removed_line_count,
            "removed_line_count": removed_line_count,
            "flag_labels": unique_labels,
            "notice": (
                "Suspicious instruction-like text was removed from this untrusted source before summarization."
                if detected
                else ""
            ),
        }

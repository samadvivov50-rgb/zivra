from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "with",
    "your",
}


class ContentStrategyService:
    def build_package(
        self,
        *,
        topic: str,
        audience: str | None = None,
        context: str | None = None,
    ) -> dict[str, Any]:
        cleaned_topic = self._clean_text(topic) or "Untitled topic"
        cleaned_audience = self._clean_text(audience or "")
        cleaned_context = self._clean_text(context or "")

        highlights = self._extract_highlights(cleaned_context)
        terms = self._extract_terms(" ".join(part for part in (cleaned_topic, cleaned_audience, cleaned_context) if part))
        titles = self._build_titles(cleaned_topic, cleaned_audience, terms)
        seo_title = titles[0]
        meta_description = self._build_meta_description(cleaned_topic, cleaned_audience, highlights, terms)
        youtube_description = self._build_youtube_description(
            cleaned_topic,
            cleaned_audience,
            highlights,
            terms,
        )
        tags = self._build_tags(cleaned_topic, terms)
        chapters = self._build_chapters(cleaned_topic, highlights, terms)

        return {
            "topic": cleaned_topic,
            "audience": cleaned_audience,
            "context_length": len(cleaned_context),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "package": {
                "angle": self._build_angle(cleaned_topic, cleaned_audience, highlights),
                "youtube_titles": titles,
                "seo_title": seo_title,
                "meta_description": meta_description,
                "youtube_description": youtube_description,
                "tags": tags,
                "chapters": chapters,
                "highlights": highlights,
            },
        }

    def audit_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        package = payload.get("package", {})
        return {
            "topic": payload.get("topic", ""),
            "audience": payload.get("audience", ""),
            "generated_at": payload.get("generated_at", ""),
            "context_length": payload.get("context_length", 0),
            "package": {
                "angle": package.get("angle", ""),
                "title_count": len(package.get("youtube_titles", [])),
                "tag_count": len(package.get("tags", [])),
                "chapter_count": len(package.get("chapters", [])),
                "highlight_count": len(package.get("highlights", [])),
            },
        }

    def _build_titles(self, topic: str, audience: str, terms: list[str]) -> list[str]:
        audience_label = audience or "builders"
        term_label = terms[0] if terms else "results"
        templates = [
            f"{topic}: the practical playbook",
            f"What most people miss about {topic}",
            f"{topic} explained for {audience_label}",
            f"{topic}: mistakes that slow teams down",
            f"{topic}: a smarter way to focus on {term_label}",
        ]

        seen: set[str] = set()
        titles: list[str] = []
        for item in templates:
            normalized = self._trim_title(item)
            lowered = normalized.casefold()
            if lowered in seen:
                continue
            seen.add(lowered)
            titles.append(normalized)
        return titles[:5]

    def _build_meta_description(
        self,
        topic: str,
        audience: str,
        highlights: list[str],
        terms: list[str],
    ) -> str:
        audience_label = audience or "practical teams"
        detail = highlights[0] if highlights else f"key ideas around {', '.join(terms[:2])}" if terms else "the practical details"
        text = f"Learn {topic} for {audience_label}. This guide covers {detail.lower()} and gives you a clearer plan for what to do next."
        return self._trim_copy(text, 158)

    def _build_youtube_description(
        self,
        topic: str,
        audience: str,
        highlights: list[str],
        terms: list[str],
    ) -> str:
        audience_label = audience or "teams building practical workflows"
        bullets = highlights[:3] or [f"Why {topic} matters right now", f"What to focus on first with {topic}"]
        value_line = ", ".join(terms[:4]) if terms else topic
        lines = [
            f"In this video, we break down {topic} for {audience_label}.",
            "",
            "You will learn:",
            *[f"- {item}" for item in bullets],
            "",
            f"This episode is shaped around practical signals like {value_line}.",
            "Subscribe for more local-first productivity and workflow ideas.",
        ]
        return "\n".join(lines).strip()

    def _build_tags(self, topic: str, terms: list[str]) -> list[str]:
        candidates = [topic, *terms, f"{topic} tutorial", f"{topic} tips"]
        tags: list[str] = []
        seen: set[str] = set()
        for candidate in candidates:
            cleaned = self._clean_text(candidate)
            if not cleaned:
                continue
            lowered = cleaned.casefold()
            if lowered in seen:
                continue
            seen.add(lowered)
            tags.append(cleaned)
        return tags[:8]

    def _build_chapters(self, topic: str, highlights: list[str], terms: list[str]) -> list[str]:
        chapters = [
            f"Why {topic} matters",
            highlights[0] if highlights else f"The current state of {topic}",
            highlights[1] if len(highlights) > 1 else f"What to fix first in {topic}",
            f"Next steps using {terms[0]}" if terms else f"Next steps for {topic}",
        ]
        return [self._trim_copy(item, 72) for item in chapters[:4]]

    def _build_angle(self, topic: str, audience: str, highlights: list[str]) -> str:
        audience_label = audience or "practical builders"
        if highlights:
            return self._trim_copy(
                f"A pragmatic take on {topic} for {audience_label}, grounded in {highlights[0].lower()}.",
                180,
            )
        return self._trim_copy(
            f"A pragmatic take on {topic} for {audience_label}, focused on clear next steps instead of buzzwords.",
            180,
        )

    def _extract_highlights(self, context: str) -> list[str]:
        if not context:
            return []

        lines = [self._clean_text(line) for line in context.splitlines()]
        candidates = [line for line in lines if len(line) >= 18]
        if not candidates:
            candidates = [segment.strip() for segment in re.split(r"(?<=[.!?])\s+", context) if len(segment.strip()) >= 18]

        highlights: list[str] = []
        seen: set[str] = set()
        for item in candidates:
            lowered = item.casefold()
            if lowered in seen:
                continue
            seen.add(lowered)
            highlights.append(self._trim_copy(item, 96))
            if len(highlights) >= 4:
                break
        return highlights

    def _extract_terms(self, text: str) -> list[str]:
        words = [word.casefold() for word in re.findall(r"[A-Za-z0-9][A-Za-z0-9+-]*", text)]
        filtered = [word for word in words if word not in STOPWORDS and len(word) > 2]
        counts = Counter(filtered)
        return [word for word, _ in counts.most_common(8)]

    def _clean_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", str(value or "")).strip()

    def _trim_copy(self, value: str, limit: int) -> str:
        cleaned = self._clean_text(value)
        if len(cleaned) <= limit:
            return cleaned
        return cleaned[: limit - 3].rstrip(" ,.;:-") + "..."

    def _trim_title(self, title: str) -> str:
        return self._trim_copy(title, 68)

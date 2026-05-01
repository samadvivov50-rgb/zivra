from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class WorkspaceNotesService:
    def __init__(self, notes_dir: Path) -> None:
        self.notes_dir = notes_dir
        self.notes_dir.mkdir(parents=True, exist_ok=True)

    def list_recent(self, *, limit: int = 10) -> list[dict[str, Any]]:
        notes = self._list_note_files()
        notes.sort(key=lambda path: path.stat().st_mtime, reverse=True)
        return [self._serialize_note(path) for path in notes[:limit]]

    def search(self, *, query: str, limit: int = 10) -> list[dict[str, Any]]:
        normalized_query = query.strip().lower()
        if not normalized_query:
            return self.list_recent(limit=limit)

        tokens = [token for token in normalized_query.split() if token]
        matches: list[tuple[int, float, dict[str, Any]]] = []

        for path in self._list_note_files():
            raw = path.read_text(encoding="utf-8", errors="ignore")
            title = self._extract_title(path, raw)
            title_lower = title.lower()
            raw_lower = raw.lower()
            haystack = f"{title_lower}\n{raw_lower}"
            if not all(token in haystack for token in tokens):
                continue

            score = 0
            if normalized_query in title_lower:
                score += 5
            if normalized_query in raw_lower:
                score += 3
            score += sum(haystack.count(token) for token in tokens)

            payload = self._serialize_note(path, raw=raw)
            payload["match_preview"] = self._extract_match_preview(raw=raw, query=normalized_query, title=title)
            payload["match_score"] = score
            matches.append((score, path.stat().st_mtime, payload))

        matches.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return [payload for _, _, payload in matches[:limit]]

    def resolve_note(self, query: str) -> dict[str, Any] | None:
        normalized_query = query.strip()
        if not normalized_query:
            return None

        direct_name = Path(normalized_query).name
        exact_by_name = self.read_note(direct_name)
        if exact_by_name is not None:
            return exact_by_name

        lowered_query = normalized_query.lower()
        for path in self._list_note_files():
            raw = path.read_text(encoding="utf-8", errors="ignore")
            title = self._extract_title(path, raw).lower()
            if path.stem.lower() == lowered_query or title == lowered_query:
                payload = self._serialize_note(path, raw=raw)
                payload["content"] = raw
                return payload

        matches = self.search(query=normalized_query, limit=1)
        if not matches:
            return None
        return self.read_note(matches[0]["name"])

    def read_note(self, name: str) -> dict[str, Any] | None:
        note_path = self._resolve_note_path(name)
        if note_path is None:
            return None
        if not note_path.exists() or not note_path.is_file():
            return None

        payload = self._serialize_note(note_path)
        payload["content"] = note_path.read_text(encoding="utf-8", errors="ignore")
        return payload

    def update_note(self, name: str, *, content: str) -> dict[str, Any] | None:
        note_path = self._resolve_note_path(name)
        if note_path is None:
            return None
        if not note_path.exists() or not note_path.is_file():
            return None

        note_path.write_text(content, encoding="utf-8")
        updated = self.read_note(note_path.name)
        if updated is None:
            return None
        return updated

    def _list_note_files(self) -> list[Path]:
        return [
            path
            for path in self.notes_dir.iterdir()
            if path.is_file() and path.suffix.lower() in {".md", ".txt"}
        ]

    def _resolve_note_path(self, name: str) -> Path | None:
        note_path = (self.notes_dir / Path(name).name).resolve()
        try:
            note_path.relative_to(self.notes_dir.resolve())
        except ValueError:
            return None
        return note_path

    def _serialize_note(self, path: Path, *, raw: str | None = None) -> dict[str, Any]:
        raw = raw if raw is not None else path.read_text(encoding="utf-8", errors="ignore")
        stat = path.stat()
        return {
            "name": path.name,
            "path": str(path),
            "title": self._extract_title(path, raw),
            "preview": self._extract_preview(raw),
            "size_bytes": stat.st_size,
            "updated_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        }

    def _extract_title(self, path: Path, content: str) -> str:
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                return stripped.lstrip("#").strip() or path.stem
            if stripped:
                return stripped[:80]
        return path.stem

    def _extract_preview(self, content: str) -> str:
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        for line in lines:
            if not line.startswith("#"):
                return line[:180]
        return "No preview available."

    def _extract_match_preview(self, *, raw: str, query: str, title: str) -> str:
        raw_lower = raw.lower()
        position = raw_lower.find(query)
        if position == -1:
            return title[:180]

        start = max(0, position - 48)
        end = min(len(raw), position + len(query) + 96)
        snippet = " ".join(raw[start:end].split())
        if start > 0:
            snippet = f"...{snippet}"
        if end < len(raw):
            snippet = f"{snippet}..."
        return snippet[:180]

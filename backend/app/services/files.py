from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


class WorkspaceFilesService:
    TEXT_SUFFIXES = {".md", ".txt", ".rst", ".json", ".csv", ".yaml", ".yml", ".log"}
    PREVIEW_SUFFIXES = TEXT_SUFFIXES
    MAX_TEXT_SEARCH_BYTES = 400_000

    def __init__(self, roots: Mapping[str, Path], *, write_roots: Iterable[Path] = ()) -> None:
        self.roots = {label: Path(root).resolve() for label, root in roots.items()}
        self.write_roots = tuple(Path(root).resolve() for root in write_roots)
        for root in self.roots.values():
            root.mkdir(parents=True, exist_ok=True)

    def list_recent(self, *, limit: int = 12) -> list[dict[str, Any]]:
        files = self._list_files()
        files.sort(key=lambda item: item[1].stat().st_mtime, reverse=True)
        return [self._serialize_file(label, path) for label, path in files[:limit]]

    def list_roots(self) -> list[dict[str, Any]]:
        roots = [self._serialize_folder(label, root, label, include_children=False) for label, root in self.roots.items()]
        roots.sort(key=lambda item: item["name"].lower())
        return roots

    def search(self, *, query: str, limit: int = 12) -> list[dict[str, Any]]:
        normalized_query = query.strip().lower()
        if not normalized_query:
            return self.list_recent(limit=limit)

        tokens = [token for token in normalized_query.split() if token]
        matches: list[tuple[int, float, dict[str, Any]]] = []
        for label, path in self._list_files():
            relative_path = path.relative_to(self.roots[label]).as_posix()
            name_lower = path.name.lower()
            relative_lower = relative_path.lower()
            haystack_segments = [label.lower(), name_lower, relative_lower]
            raw = ""
            raw_lower = ""
            if self._is_text_file(path):
                raw = self._read_text(path)
                raw_lower = raw.lower()
                haystack_segments.append(raw_lower)

            haystack = "\n".join(haystack_segments)
            if not all(token in haystack for token in tokens):
                continue

            score = 0
            if normalized_query in name_lower:
                score += 5
            if normalized_query in relative_lower:
                score += 4
            if raw_lower and normalized_query in raw_lower:
                score += 3
            score += 2 * sum(name_lower.count(token) for token in tokens)
            score += 2 * sum(relative_lower.count(token) for token in tokens)
            if raw_lower:
                score += sum(raw_lower.count(token) for token in tokens)

            payload = self._serialize_file(label, path, raw=raw or None)
            payload["match_score"] = score
            payload["match_preview"] = self._extract_match_preview(
                raw=raw,
                query=normalized_query,
                fallback=relative_path,
            )
            matches.append((score, path.stat().st_mtime, payload))

        matches.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return [payload for _, _, payload in matches[:limit]]

    def browse_folder(self, folder_id: str | None = None, *, limit: int = 16) -> dict[str, Any] | None:
        normalized_folder_id = str(folder_id or "").strip().replace("\\", "/").strip("/")
        if not normalized_folder_id:
            roots = self.list_roots()
            recent_files = self.list_recent(limit=limit)
            return {
                "id": "",
                "name": "Approved roots",
                "root": "",
                "relative_path": "",
                "path": "",
                "writable": False,
                "kind": "workspace",
                "breadcrumbs": [{"id": "", "label": "Approved roots"}],
                "folders": roots,
                "files": recent_files,
                "folder_count": len(roots),
                "direct_folder_count": len(roots),
                "file_count": sum(root["file_count"] for root in roots),
                "direct_file_count": len(recent_files),
                "total_size_bytes": sum(root["total_size_bytes"] for root in roots),
            }

        resolved = self._resolve_folder_path(normalized_folder_id)
        if resolved is None:
            return None

        label, folder_path = resolved
        if not folder_path.exists() or not folder_path.is_dir():
            return None

        subfolders = [
            self._serialize_folder(label, child, label)
            for child in folder_path.iterdir()
            if child.is_dir()
        ]
        subfolders.sort(key=lambda item: item["name"].lower())

        files = [
            self._serialize_file(label, child)
            for child in folder_path.iterdir()
            if child.is_file()
        ]
        files.sort(key=lambda item: item["updated_at"], reverse=True)

        relative_path = folder_path.relative_to(self.roots[label]).as_posix() if folder_path != self.roots[label] else ""
        stats = self._folder_stats(folder_path)
        return {
            "id": normalized_folder_id,
            "name": folder_path.name if relative_path else label,
            "root": label,
            "relative_path": relative_path,
            "path": str(folder_path),
            "writable": self._is_writable_path(folder_path),
            "kind": "folder",
            "breadcrumbs": self._build_breadcrumbs(label, relative_path),
            "folders": subfolders,
            "files": files[:limit],
            "folder_count": stats["folder_count"],
            "direct_folder_count": len(subfolders),
            "file_count": stats["file_count"],
            "direct_file_count": len(files),
            "total_size_bytes": stats["total_size_bytes"],
            "updated_at": stats["updated_at"],
            "remaining_file_count": max(0, len(files) - limit),
        }

    def _list_files(self) -> list[tuple[str, Path]]:
        files: list[tuple[str, Path]] = []
        for label, root in self.roots.items():
            for path in root.rglob("*"):
                if path.is_file():
                    files.append((label, path))
        return files

    def _resolve_folder_path(self, folder_id: str) -> tuple[str, Path] | None:
        normalized = folder_id.strip().replace("\\", "/").strip("/")
        if not normalized:
            return None

        if "/" not in normalized:
            root = self.roots.get(normalized)
            if root is None:
                return None
            return normalized, root

        label, relative_path = normalized.split("/", 1)
        root = self.roots.get(label)
        if root is None:
            return None

        folder_path = (root / relative_path).resolve()
        try:
            folder_path.relative_to(root)
        except ValueError:
            return None
        return label, folder_path

    def _serialize_folder(
        self,
        label: str,
        path: Path,
        root_label: str,
        *,
        include_children: bool = True,
    ) -> dict[str, Any]:
        relative_path = path.relative_to(self.roots[root_label]).as_posix() if path != self.roots[root_label] else ""
        folder_id = f"{root_label}/{relative_path}" if relative_path else root_label
        stats = self._folder_stats(path)
        payload = {
            "id": folder_id,
            "name": path.name if relative_path else root_label,
            "root": root_label,
            "relative_path": relative_path,
            "path": str(path),
            "writable": self._is_writable_path(path),
            "folder_count": stats["folder_count"],
            "file_count": stats["file_count"],
            "total_size_bytes": stats["total_size_bytes"],
            "updated_at": stats["updated_at"],
        }
        if include_children:
            payload["direct_folder_count"] = sum(1 for child in path.iterdir() if child.is_dir())
            payload["direct_file_count"] = sum(1 for child in path.iterdir() if child.is_file())
        return payload

    def _serialize_file(self, label: str, path: Path, *, raw: str | None = None) -> dict[str, Any]:
        stat = path.stat()
        relative_path = path.relative_to(self.roots[label]).as_posix()
        document_id = f"{label}/{relative_path}"
        text = raw if raw is not None else (self._read_text(path) if self._is_previewable(path) else "")
        return {
            "id": document_id,
            "name": path.name,
            "root": label,
            "relative_path": relative_path,
            "path": str(path),
            "extension": path.suffix.lower(),
            "size_bytes": stat.st_size,
            "updated_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            "writable": self._is_writable_path(path),
            "readable_document_id": document_id if self._is_text_file(path) else "",
            "preview": self._extract_preview(text, fallback=path.name),
        }

    def _folder_stats(self, path: Path) -> dict[str, Any]:
        file_count = 0
        folder_count = 0
        total_size_bytes = 0
        latest_mtime = path.stat().st_mtime if path.exists() else 0.0
        for child in path.rglob("*"):
            if child.is_dir():
                folder_count += 1
                latest_mtime = max(latest_mtime, child.stat().st_mtime)
                continue
            if child.is_file():
                file_count += 1
                stat = child.stat()
                total_size_bytes += stat.st_size
                latest_mtime = max(latest_mtime, stat.st_mtime)
        return {
            "file_count": file_count,
            "folder_count": folder_count,
            "total_size_bytes": total_size_bytes,
            "updated_at": datetime.fromtimestamp(latest_mtime, tz=timezone.utc).isoformat(),
        }

    def _build_breadcrumbs(self, label: str, relative_path: str) -> list[dict[str, str]]:
        breadcrumbs = [{"id": "", "label": "Approved roots"}, {"id": label, "label": label}]
        current = label
        for segment in [part for part in relative_path.split("/") if part]:
            current = f"{current}/{segment}"
            breadcrumbs.append({"id": current, "label": segment})
        return breadcrumbs

    def _is_writable_path(self, path: Path) -> bool:
        resolved = path.resolve()
        for root in self.write_roots:
            try:
                resolved.relative_to(root)
                return True
            except ValueError:
                continue
        return False

    def _is_text_file(self, path: Path) -> bool:
        return path.suffix.lower() in self.TEXT_SUFFIXES

    def _is_previewable(self, path: Path) -> bool:
        return self._is_text_file(path) and path.stat().st_size <= self.MAX_TEXT_SEARCH_BYTES

    def _read_text(self, path: Path) -> str:
        if path.stat().st_size > self.MAX_TEXT_SEARCH_BYTES:
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")

    def _extract_preview(self, content: str, *, fallback: str) -> str:
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        if not lines:
            return fallback
        for line in lines:
            if not line.startswith("#"):
                return line[:180]
        return lines[0][:180]

    def _extract_match_preview(self, *, raw: str, query: str, fallback: str) -> str:
        if not raw:
            return fallback[:180]
        raw_lower = raw.lower()
        position = raw_lower.find(query)
        if position == -1:
            return self._extract_preview(raw, fallback=fallback)
        start = max(0, position - 48)
        end = min(len(raw), position + len(query) + 96)
        snippet = " ".join(raw[start:end].split())
        if start > 0:
            snippet = f"...{snippet}"
        if end < len(raw):
            snippet = f"{snippet}..."
        return snippet[:180]

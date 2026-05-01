from __future__ import annotations

from collections import Counter
import csv
import json
import re
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any, Mapping

from app.services.prompt_injection import PromptInjectionDefense


class WorkspaceDocumentsService:
    ALLOWED_SUFFIXES = {".md", ".txt", ".rst", ".json", ".csv", ".yaml", ".yml"}

    def __init__(self, roots: Mapping[str, Path], *, prompt_injection_defense: PromptInjectionDefense | None = None) -> None:
        self.roots = {label: Path(root).resolve() for label, root in roots.items()}
        self.prompt_injection_defense = prompt_injection_defense or PromptInjectionDefense()
        for root in self.roots.values():
            root.mkdir(parents=True, exist_ok=True)

    def list_recent(self, *, limit: int = 10) -> list[dict[str, Any]]:
        documents = self._list_document_files()
        documents.sort(key=lambda item: item[1].stat().st_mtime, reverse=True)
        return [self._serialize_document(label, path) for label, path in documents[:limit]]

    def search(self, *, query: str, limit: int = 10) -> list[dict[str, Any]]:
        normalized_query = query.strip().lower()
        if not normalized_query:
            return self.list_recent(limit=limit)

        tokens = [token for token in normalized_query.split() if token]
        matches: list[tuple[int, float, dict[str, Any]]] = []

        for label, path in self._list_document_files():
            raw = path.read_text(encoding="utf-8", errors="ignore")
            title = self._extract_title(path, raw)
            relative_path = path.relative_to(self.roots[label]).as_posix()
            title_lower = title.lower()
            relative_lower = relative_path.lower()
            raw_lower = raw.lower()
            haystack = f"{label.lower()}\n{relative_lower}\n{title_lower}\n{raw_lower}"
            if not all(token in haystack for token in tokens):
                continue

            score = 0
            if normalized_query in title_lower:
                score += 5
            if normalized_query in relative_lower:
                score += 4
            if normalized_query in raw_lower:
                score += 3
            score += 3 * sum(title_lower.count(token) for token in tokens)
            score += 2 * sum(relative_lower.count(token) for token in tokens)
            score += sum(raw_lower.count(token) for token in tokens)

            payload = self._serialize_document(label, path, raw=raw)
            payload["match_preview"] = self._extract_match_preview(raw=raw, query=normalized_query, title=title)
            payload["match_score"] = score
            matches.append((score, path.stat().st_mtime, payload))

        matches.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return [payload for _, _, payload in matches[:limit]]

    def resolve_document(self, query: str) -> dict[str, Any] | None:
        normalized_query = query.strip()
        if not normalized_query:
            return None

        exact_document = self.read_document(normalized_query.replace("\\", "/").lstrip("/"))
        if exact_document is not None:
            return exact_document

        lowered_query = normalized_query.lower()
        for label, path in self._list_document_files():
            raw = path.read_text(encoding="utf-8", errors="ignore")
            relative_path = path.relative_to(self.roots[label]).as_posix().lower()
            title = self._extract_title(path, raw).lower()
            if (
                path.name.lower() == lowered_query
                or path.stem.lower() == lowered_query
                or relative_path == lowered_query
                or f"{label}/{relative_path}" == lowered_query
                or title == lowered_query
            ):
                payload = self._serialize_document(label, path, raw=raw)
                payload["content"] = raw
                return payload

        matches = self.search(query=normalized_query, limit=1)
        if not matches:
            return None
        return self.read_document(str(matches[0]["id"]))

    def read_document(self, document_id: str) -> dict[str, Any] | None:
        resolved = self._resolve_document_path(document_id)
        if resolved is None:
            return None

        label, document_path = resolved
        if not document_path.exists() or not document_path.is_file():
            return None

        payload = self._serialize_document(label, document_path)
        payload["content"] = document_path.read_text(encoding="utf-8", errors="ignore")
        return payload

    def audit_payload(self, document: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "id": str(document.get("id", "") or ""),
            "name": str(document.get("name", "") or ""),
            "root": str(document.get("root", "") or ""),
            "relative_path": str(document.get("relative_path", "") or ""),
            "title": str(document.get("title", "") or ""),
            "preview": str(document.get("preview", "") or ""),
            "size_bytes": int(document.get("size_bytes", 0) or 0),
            "updated_at": str(document.get("updated_at", "") or ""),
            "security": self.prompt_injection_defense.to_metadata(document.get("security", {})),
        }

    def summarize_document(self, *, document_id: str | None = None, query: str | None = None) -> dict[str, Any] | None:
        document = None
        if document_id:
            document = self.read_document(document_id)
        elif query:
            document = self.resolve_document(query)

        if document is None:
            return None

        summary = self._build_summary(document)
        return {"document": document, "summary": summary}

    def inspect_document(
        self,
        *,
        document_id: str | None = None,
        query: str | None = None,
        filter_text: str | None = None,
        limit: int = 5,
        schema_depth: int = 2,
        schema_path: str | None = None,
    ) -> dict[str, Any] | None:
        document = None
        if document_id:
            document = self.read_document(document_id)
        elif query:
            document = self.resolve_document(query)

        if document is None:
            return None

        inspection = self._build_inspection(
            document,
            filter_text=filter_text,
            limit=limit,
            schema_depth=max(1, min(schema_depth, 4)),
            schema_path=(schema_path or "").strip() or None,
        )
        return {"document": document, "inspection": inspection}

    def export_document_table(
        self,
        *,
        document_id: str | None = None,
        query: str | None = None,
        filter_text: str | None = None,
        schema_path: str | None = None,
    ) -> dict[str, Any] | None:
        document = None
        if document_id:
            document = self.read_document(document_id)
        elif query:
            document = self.resolve_document(query)

        if document is None:
            return None

        table = self._build_table_export(
            document,
            filter_text=filter_text,
            schema_path=(schema_path or "").strip() or None,
        )
        return {"document": document, "table": table}

    def analyze_document(
        self,
        *,
        document_id: str | None = None,
        query: str | None = None,
        filter_text: str | None = None,
        schema_path: str | None = None,
    ) -> dict[str, Any] | None:
        document = None
        if document_id:
            document = self.read_document(document_id)
        elif query:
            document = self.resolve_document(query)

        if document is None:
            return None

        table = self._build_table_export(
            document,
            filter_text=filter_text,
            schema_path=(schema_path or "").strip() or None,
        )
        if table is None:
            return {"document": document, "analysis": None}

        analysis = self._build_table_analysis(
            table,
            filter_text=filter_text,
            schema_path=(schema_path or "").strip() or None,
        )
        return {"document": document, "analysis": analysis}

    def _list_document_files(self) -> list[tuple[str, Path]]:
        documents: list[tuple[str, Path]] = []
        for label, root in self.roots.items():
            for path in root.rglob("*"):
                if not path.is_file():
                    continue
                if path.suffix.lower() not in self.ALLOWED_SUFFIXES:
                    continue
                documents.append((label, path))
        return documents

    def _resolve_document_path(self, document_id: str) -> tuple[str, Path] | None:
        normalized = document_id.strip().replace("\\", "/").lstrip("/")
        if "/" not in normalized:
            return None

        label, relative_path = normalized.split("/", 1)
        root = self.roots.get(label)
        if root is None or not relative_path:
            return None

        document_path = (root / relative_path).resolve()
        try:
            document_path.relative_to(root)
        except ValueError:
            return None

        if document_path.suffix.lower() not in self.ALLOWED_SUFFIXES:
            return None
        return label, document_path

    def _serialize_document(self, label: str, path: Path, *, raw: str | None = None) -> dict[str, Any]:
        raw = raw if raw is not None else path.read_text(encoding="utf-8", errors="ignore")
        stat = path.stat()
        relative_path = path.relative_to(self.roots[label]).as_posix()
        security_signal = self.prompt_injection_defense.sanitize_text(raw)
        safe_preview_source = security_signal.get("sanitized_text") or raw
        return {
            "id": f"{label}/{relative_path}",
            "name": path.name,
            "path": str(path),
            "root": label,
            "relative_path": relative_path,
            "title": self._extract_title(path, safe_preview_source or raw),
            "preview": self._extract_preview(safe_preview_source or raw),
            "size_bytes": stat.st_size,
            "updated_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            "security": self.prompt_injection_defense.to_metadata(security_signal),
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

    def _build_summary(self, document: Mapping[str, Any]) -> dict[str, Any]:
        content = str(document.get("content", ""))
        security_signal = self.prompt_injection_defense.sanitize_text(content)
        summary_source = security_signal.get("sanitized_text") or content
        headings = self._extract_headings(summary_source)[:5]
        overview = self._extract_overview(summary_source, fallback=str(document.get("preview", "")))
        key_points = self._extract_key_points(summary_source, overview=overview)[:4]
        format_hint = self._extract_format_hint(
            name=str(document.get("name", "")),
            content=content,
        )
        word_count = len(re.findall(r"\b\w+\b", summary_source))
        read_time_minutes = max(1, round(word_count / 200)) if word_count else 1
        security = self.prompt_injection_defense.merge_metadata(
            document.get("security", {}),
            security_signal,
        )

        return {
            "overview": overview or "No summary available.",
            "key_points": key_points,
            "headings": headings,
            "format_hint": format_hint,
            "word_count": word_count,
            "estimated_read_time_minutes": read_time_minutes,
            "security": self.prompt_injection_defense.to_metadata(security),
        }

    def _build_inspection(
        self,
        document: Mapping[str, Any],
        *,
        filter_text: str | None,
        limit: int,
        schema_depth: int,
        schema_path: str | None,
    ) -> dict[str, Any]:
        name = str(document.get("name", ""))
        content = str(document.get("content", ""))
        suffix = Path(name).suffix.lower()

        if suffix == ".json":
            return self._inspect_json(
                content,
                filter_text=filter_text,
                limit=limit,
                schema_depth=schema_depth,
                schema_path=schema_path,
            )
        if suffix == ".csv":
            return self._inspect_csv(
                content,
                filter_text=filter_text,
                limit=limit,
                schema_depth=schema_depth,
                schema_path=schema_path,
            )
        if suffix in {".yaml", ".yml"}:
            return self._inspect_yaml(content, limit=limit, schema_depth=schema_depth, schema_path=schema_path)
        return self._inspect_text(content, limit=limit)

    def _extract_headings(self, content: str) -> list[str]:
        headings: list[str] = []
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                heading = stripped.lstrip("#").strip()
                if heading:
                    headings.append(heading)
        return headings

    def _extract_overview(self, content: str, *, fallback: str) -> str:
        sentences = self._collect_sentences(content)
        for sentence in sentences:
            cleaned = sentence.strip()
            if len(cleaned) >= 40:
                return cleaned[:240]
        return fallback[:240]

    def _extract_key_points(self, content: str, *, overview: str) -> list[str]:
        points: list[str] = []
        seen: set[str] = set()

        for line in content.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            normalized = stripped.lstrip("-*0123456789. )").strip()
            if stripped.startswith(("-", "*")) or re.match(r"^\d+[.)]\s+", stripped):
                if len(normalized) < 12:
                    continue
                candidate = normalized[:180]
                lowered = candidate.lower()
                if lowered not in seen:
                    seen.add(lowered)
                    points.append(candidate)
            if len(points) >= 4:
                return points

        for sentence in self._collect_sentences(content):
            cleaned = sentence.strip()
            if len(cleaned) < 18:
                continue
            if cleaned == overview:
                continue
            lowered = cleaned.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            points.append(cleaned[:180])
            if len(points) >= 4:
                break
        return points

    def _collect_sentences(self, content: str) -> list[str]:
        paragraphs: list[str] = []
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.startswith(("-", "*")) or re.match(r"^\d+[.)]\s+", stripped):
                stripped = stripped.lstrip("-*0123456789. )").strip()
            paragraphs.append(stripped)

        joined = " ".join(paragraphs)
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", joined) if part.strip()]
        return sentences or paragraphs

    def _extract_format_hint(self, *, name: str, content: str) -> str | None:
        suffix = Path(name).suffix.lower()
        if suffix == ".json":
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                return "JSON document with invalid syntax."

            if isinstance(parsed, dict):
                keys = list(parsed.keys())
                preview = ", ".join(str(key) for key in keys[:6]) or "no keys"
                return f"JSON object with {len(keys)} top-level keys: {preview}."
            if isinstance(parsed, list):
                return f"JSON array with {len(parsed)} top-level item(s)."
            return f"JSON scalar value of type {type(parsed).__name__}."

        if suffix == ".csv":
            reader = csv.reader(StringIO(content))
            rows = [row for row in reader if row]
            if not rows:
                return "CSV document with no rows."
            headers = ", ".join(rows[0][:6]) or "no headers"
            data_rows = max(0, len(rows) - 1)
            return f"CSV table with {len(rows[0])} column(s) and {data_rows} data row(s). Headers: {headers}."

        if suffix in {".yaml", ".yml"}:
            keys: list[str] = []
            for line in content.splitlines():
                if line.startswith((" ", "\t", "-", "#")):
                    continue
                match = re.match(r"^([A-Za-z0-9_.-]+):", line)
                if match:
                    keys.append(match.group(1))
            if keys:
                preview = ", ".join(keys[:6])
                return f"YAML document with top-level fields such as {preview}."
            return "YAML document with no simple top-level fields detected."

        return None

    def _inspect_json(
        self,
        content: str,
        *,
        filter_text: str | None,
        limit: int,
        schema_depth: int,
        schema_path: str | None,
    ) -> dict[str, Any]:
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            return {
                "kind": "json_invalid",
                "label": "Invalid JSON",
                "error": f"JSON parse error near line {exc.lineno}, column {exc.colno}.",
                "sample_lines": self._sample_lines(content, limit=limit),
            }

        focus_source = parsed
        if isinstance(parsed, dict):
            items = list(parsed.items())
            inspection = {
                "kind": "json_object",
                "label": "JSON object",
                "field_count": len(items),
                "top_level_keys": [str(key) for key, _ in items[:12]],
                "schema_depth": schema_depth,
                "schema_fields": self._collect_json_schema_fields(parsed, max_depth=schema_depth),
                "sample_fields": [
                    {
                        "key": str(key),
                        "type": self._infer_value_type(value),
                        "preview": self._stringify_preview(value),
                    }
                    for key, value in items[:8]
                ],
            }
            if schema_path:
                inspection["focus"] = self._build_json_focus(
                    focus_source,
                    schema_path=schema_path,
                    limit=limit,
                    schema_depth=schema_depth,
                )
            return inspection

        if isinstance(parsed, list):
            item_type = self._infer_common_type(item for item in parsed[: min(len(parsed), 50)])
            inspection: dict[str, Any] = {
                "kind": "json_array",
                "label": "JSON array",
                "item_count": len(parsed),
                "item_type": item_type,
                "filterable": False,
                "schema_depth": schema_depth,
                "sample_items": [self._build_preview_item(item) for item in parsed[:limit]],
            }
            if parsed and all(isinstance(item, dict) for item in parsed):
                keys: list[str] = []
                for item in parsed:
                    for key in item.keys():
                        key_text = str(key)
                        if key_text not in keys:
                            keys.append(key_text)
                filtered_rows = self._filter_mapping_rows(parsed, filter_text=filter_text)
                focus_source = filtered_rows if filter_text else parsed
                inspection["top_level_keys"] = keys[:12]
                inspection["filterable"] = True
                inspection["filter_applied"] = filter_text or ""
                inspection["filtered_item_count"] = len(filtered_rows)
                inspection["schema_fields"] = self._collect_json_array_schema_fields(parsed, max_depth=schema_depth)
                inspection["sample_rows"] = [
                    {key: self._stringify_preview(item.get(key)) for key in keys[:8]}
                    for item in filtered_rows[:limit]
                ]
            elif filter_text:
                filtered_items = [
                    item for item in parsed if self._value_matches_filter(item, filter_text)
                ]
                focus_source = filtered_items
                inspection["filter_applied"] = filter_text
                inspection["filtered_item_count"] = len(filtered_items)
                inspection["sample_items"] = [self._build_preview_item(item) for item in filtered_items[:limit]]
            if schema_path:
                inspection["focus"] = self._build_json_focus(
                    focus_source,
                    schema_path=schema_path,
                    limit=limit,
                    schema_depth=schema_depth,
                )
            return inspection

        inspection = {
            "kind": "json_scalar",
            "label": "JSON value",
            "sample_items": [self._build_preview_item(parsed)],
        }
        if schema_path:
            inspection["focus"] = self._build_json_focus(
                focus_source,
                schema_path=schema_path,
                limit=limit,
                schema_depth=schema_depth,
            )
        return inspection

    def _inspect_csv(
        self,
        content: str,
        *,
        filter_text: str | None,
        limit: int,
        schema_depth: int,
        schema_path: str | None,
    ) -> dict[str, Any]:
        reader = csv.reader(StringIO(content))
        rows = [row for row in reader if row]
        if not rows:
            inspection = {
                "kind": "csv",
                "label": "CSV table",
                "headers": [],
                "schema_fields": [],
                "schema_depth": schema_depth,
                "row_count": 0,
                "filtered_row_count": 0,
                "filterable": True,
                "filter_applied": filter_text or "",
                "sample_rows": [],
            }
            if schema_path:
                inspection["focus"] = {"path": schema_path, "found": False}
            return inspection

        headers = [str(cell) for cell in rows[0]]
        data_rows: list[dict[str, str]] = []
        for row in rows[1:]:
            data_rows.append(
                {
                    headers[index] if index < len(headers) else f"column_{index + 1}": row[index] if index < len(row) else ""
                    for index in range(len(headers))
                }
            )
        filtered_rows = self._filter_mapping_rows(data_rows, filter_text=filter_text)
        schema_fields = [
            {
                "name": header,
                "type": self._infer_common_type(row.get(header, "") for row in data_rows[: min(len(data_rows), 50)]),
            }
            for header in headers[:12]
        ]

        inspection = {
            "kind": "csv",
            "label": "CSV table",
            "headers": headers[:12],
            "schema_fields": schema_fields,
            "schema_depth": schema_depth,
            "row_count": len(data_rows),
            "filtered_row_count": len(filtered_rows),
            "filterable": True,
            "filter_applied": filter_text or "",
            "sample_rows": filtered_rows[:limit],
        }
        if schema_path:
            inspection["focus"] = self._build_csv_focus(
                filtered_rows if filter_text else data_rows,
                headers=headers,
                schema_fields=schema_fields,
                schema_path=schema_path,
                limit=limit,
            )
        return inspection

    def _inspect_yaml(
        self,
        content: str,
        *,
        limit: int,
        schema_depth: int,
        schema_path: str | None,
    ) -> dict[str, Any]:
        schema_fields = self._collect_yaml_schema_fields(content, max_depth=schema_depth)
        inspection = {
            "kind": "yaml",
            "label": "YAML document",
            "top_level_keys": [field["name"] for field in schema_fields if field.get("depth") == 1][:12],
            "schema_fields": schema_fields,
            "schema_depth": schema_depth,
            "sample_lines": self._sample_lines(content, limit=limit),
        }
        if schema_path:
            inspection["focus"] = self._build_yaml_focus(
                content,
                schema_path=schema_path,
                limit=limit,
                schema_depth=schema_depth,
            )
        return inspection

    def _inspect_text(self, content: str, *, limit: int) -> dict[str, Any]:
        lines = self._sample_lines(content, limit=limit)
        return {
            "kind": "text",
            "label": "Text document",
            "sample_lines": lines,
        }

    def _sample_lines(self, content: str, *, limit: int = 6) -> list[str]:
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        return lines[:limit]

    def _stringify_preview(self, value: Any) -> str:
        if isinstance(value, (dict, list)):
            serialized = json.dumps(value, ensure_ascii=True)
            return serialized[:140] + ("..." if len(serialized) > 140 else "")
        preview = str(value)
        return preview[:140] + ("..." if len(preview) > 140 else "")

    def _build_preview_item(self, value: Any) -> dict[str, str]:
        return {
            "type": self._infer_value_type(value),
            "preview": self._stringify_preview(value),
        }

    def _stringify_export_value(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=True)
        return str(value)

    def _build_table_export(
        self,
        document: Mapping[str, Any],
        *,
        filter_text: str | None,
        schema_path: str | None,
    ) -> dict[str, Any] | None:
        name = str(document.get("name", ""))
        content = str(document.get("content", ""))
        suffix = Path(name).suffix.lower()

        if suffix == ".csv":
            return self._export_csv_table(content, filter_text=filter_text, schema_path=schema_path)
        if suffix == ".json":
            return self._export_json_table(content, filter_text=filter_text, schema_path=schema_path)
        return None

    def _export_csv_table(
        self,
        content: str,
        *,
        filter_text: str | None,
        schema_path: str | None,
    ) -> dict[str, Any] | None:
        headers, data_rows = self._parse_csv_rows(content)
        if not headers and not data_rows:
            return None

        filtered_rows = self._filter_mapping_rows(data_rows, filter_text=filter_text)
        if schema_path:
            normalized_path = schema_path.strip()
            if normalized_path not in headers:
                return None
            return {
                "headers": [normalized_path],
                "rows": [
                    {normalized_path: self._stringify_export_value(row.get(normalized_path, ""))}
                    for row in filtered_rows
                ],
                "row_count": len(filtered_rows),
            }

        return self._build_mapping_table_export(filtered_rows, headers=headers)

    def _parse_csv_rows(self, content: str) -> tuple[list[str], list[dict[str, str]]]:
        reader = csv.reader(StringIO(content))
        rows = [row for row in reader if row]
        if not rows:
            return [], []

        headers = [str(cell) for cell in rows[0]]
        data_rows: list[dict[str, str]] = []
        for row in rows[1:]:
            data_rows.append(
                {
                    headers[index] if index < len(headers) else f"column_{index + 1}": row[index] if index < len(row) else ""
                    for index in range(len(headers))
                }
            )
        return headers, data_rows

    def _export_json_table(
        self,
        content: str,
        *,
        filter_text: str | None,
        schema_path: str | None,
    ) -> dict[str, Any] | None:
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return None

        source = parsed
        root_headers: list[str] | None = None
        if isinstance(parsed, list) and all(isinstance(item, Mapping) for item in parsed):
            root_headers = self._collect_mapping_headers(parsed)
            source = self._filter_mapping_rows(parsed, filter_text=filter_text)
        elif isinstance(parsed, list) and filter_text:
            source = [item for item in parsed if self._value_matches_filter(item, filter_text)]

        if schema_path:
            matches = self._extract_json_path_matches(source, schema_path.strip())
            return self._build_json_table_export_from_matches(matches)

        if isinstance(source, list) and all(isinstance(item, Mapping) for item in source):
            return self._build_mapping_table_export(source, headers=root_headers)

        return None

    def _build_json_table_export_from_matches(self, matches: list[Any]) -> dict[str, Any] | None:
        if not matches:
            return None

        if len(matches) == 1:
            only_match = matches[0]
            if isinstance(only_match, Mapping):
                return self._build_mapping_table_export([only_match])
            if isinstance(only_match, list):
                if only_match and all(isinstance(item, Mapping) for item in only_match):
                    return self._build_mapping_table_export(only_match)
                return self._build_scalar_table_export(only_match)
            return self._build_scalar_table_export([only_match])

        if all(isinstance(match, Mapping) for match in matches):
            return self._build_mapping_table_export(matches)

        if all(isinstance(match, list) for match in matches):
            flattened: list[Any] = []
            for match in matches:
                flattened.extend(match)
            if flattened and all(isinstance(item, Mapping) for item in flattened):
                return self._build_mapping_table_export(flattened)
            return self._build_scalar_table_export(flattened)

        return self._build_scalar_table_export(matches)

    def _build_mapping_table_export(
        self,
        rows: list[Mapping[str, Any]],
        *,
        headers: list[str] | None = None,
    ) -> dict[str, Any] | None:
        if headers is None:
            headers = self._collect_mapping_headers(rows)
        if not headers:
            return None

        return {
            "headers": headers,
            "rows": [
                {header: self._stringify_export_value(row.get(header)) for header in headers}
                for row in rows
            ],
            "row_count": len(rows),
        }

    def _build_scalar_table_export(self, values: list[Any]) -> dict[str, Any] | None:
        if not values:
            return None
        return {
            "headers": ["value"],
            "rows": [{"value": self._stringify_export_value(value)} for value in values],
            "row_count": len(values),
        }

    def _build_table_analysis(
        self,
        table: Mapping[str, Any],
        *,
        filter_text: str | None,
        schema_path: str | None,
    ) -> dict[str, Any]:
        headers = [str(header) for header in (table.get("headers") or [])]
        rows = [row for row in (table.get("rows") or []) if isinstance(row, Mapping)]
        row_count = len(rows)
        numeric_columns: list[dict[str, Any]] = []
        categorical_columns: list[dict[str, Any]] = []
        empty_columns: list[str] = []

        for header in headers:
            values = [self._normalize_analysis_value(row.get(header, "")) for row in rows]
            non_empty_values = [value for value in values if value != ""]
            if not non_empty_values:
                empty_columns.append(header)
                continue

            parsed_numbers = [number for number in (self._parse_analysis_number(value) for value in non_empty_values) if number is not None]
            if parsed_numbers and len(parsed_numbers) == len(non_empty_values):
                total = sum(parsed_numbers)
                numeric_columns.append(
                    {
                        "name": header,
                        "count": len(parsed_numbers),
                        "missing_count": row_count - len(non_empty_values),
                        "min": self._format_analysis_number(min(parsed_numbers)),
                        "max": self._format_analysis_number(max(parsed_numbers)),
                        "sum": self._format_analysis_number(total),
                        "mean": self._format_analysis_number(total / len(parsed_numbers)),
                    }
                )
                continue

            counts = Counter(non_empty_values)
            categorical_columns.append(
                {
                    "name": header,
                    "count": len(non_empty_values),
                    "missing_count": row_count - len(non_empty_values),
                    "unique_count": len(counts),
                    "top_values": [
                        {"value": value, "count": count}
                        for value, count in counts.most_common(3)
                    ],
                }
            )

        overview = (
            f"Analyzed {row_count} row(s) across {len(headers)} column(s). "
            f"Found {len(numeric_columns)} numeric column(s) and {len(categorical_columns)} categorical column(s)."
        )
        if empty_columns:
            overview = f"{overview} Empty columns: {', '.join(empty_columns[:3])}."
        return {
            "label": "Table analysis",
            "overview": overview,
            "row_count": row_count,
            "column_count": len(headers),
            "numeric_column_count": len(numeric_columns),
            "categorical_column_count": len(categorical_columns),
            "empty_columns": empty_columns,
            "filter_applied": filter_text or "",
            "schema_path": schema_path or "",
            "numeric_columns": numeric_columns,
            "categorical_columns": categorical_columns,
        }

    def _collect_mapping_headers(self, rows: list[Mapping[str, Any]]) -> list[str]:
        headers: list[str] = []
        for row in rows:
            for key in row.keys():
                key_text = str(key)
                if key_text not in headers:
                    headers.append(key_text)
        return headers

    def _normalize_analysis_value(self, value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    def _parse_analysis_number(self, value: str) -> float | None:
        normalized = value.strip().replace(",", "")
        if not normalized:
            return None
        if not re.fullmatch(r"-?\d+(?:\.\d+)?", normalized):
            return None
        try:
            return float(normalized)
        except ValueError:
            return None

    def _format_analysis_number(self, value: float) -> int | float:
        rounded = round(value, 3)
        if float(rounded).is_integer():
            return int(rounded)
        return rounded

    def _build_csv_focus(
        self,
        rows: list[Mapping[str, Any]],
        *,
        headers: list[str],
        schema_fields: list[dict[str, Any]],
        schema_path: str,
        limit: int,
    ) -> dict[str, Any]:
        normalized_path = schema_path.strip()
        if not normalized_path or normalized_path not in headers:
            return {"path": normalized_path, "found": False}

        field_type = next(
            (field.get("type", "text") for field in schema_fields if field.get("name") == normalized_path),
            "text",
        )
        return {
            "path": normalized_path,
            "found": True,
            "type": field_type,
            "match_count": len(rows),
            "sample_rows": [{normalized_path: self._stringify_preview(row.get(normalized_path, ""))} for row in rows[:limit]],
            "headers": [normalized_path],
        }

    def _build_json_focus(
        self,
        value: Any,
        *,
        schema_path: str,
        limit: int,
        schema_depth: int,
    ) -> dict[str, Any]:
        normalized_path = schema_path.strip()
        if not normalized_path:
            return {"path": normalized_path, "found": False}

        path_represents_array = normalized_path.endswith("[]")
        matches = self._extract_json_path_matches(value, normalized_path)
        if not matches:
            return {"path": normalized_path, "found": False}

        if len(matches) == 1:
            return self._describe_json_focus_value(
                matches[0],
                path=normalized_path,
                limit=limit,
                schema_depth=schema_depth,
                match_count=1,
                path_represents_array=path_represents_array,
            )

        if all(isinstance(match, Mapping) for match in matches):
            return self._describe_json_focus_rows(
                matches,
                path=normalized_path,
                limit=limit,
                schema_depth=schema_depth,
                container_type="array" if path_represents_array else "object",
                item_count=len(matches) if path_represents_array else None,
            )

        if all(isinstance(match, list) for match in matches):
            flattened: list[Any] = []
            for match in matches:
                flattened.extend(match)
            return self._describe_json_focus_value(
                flattened,
                path=normalized_path,
                limit=limit,
                schema_depth=schema_depth,
                match_count=len(matches),
                path_represents_array=path_represents_array,
            )

        focus = {
            "path": normalized_path,
            "found": True,
            "type": "array" if path_represents_array else self._infer_common_type(matches),
            "match_count": len(matches),
            "sample_items": [self._build_preview_item(match) for match in matches[:limit]],
        }
        if path_represents_array:
            focus["item_count"] = len(matches)
        return focus

    def _describe_json_focus_value(
        self,
        value: Any,
        *,
        path: str,
        limit: int,
        schema_depth: int,
        match_count: int,
        path_represents_array: bool = False,
    ) -> dict[str, Any]:
        if isinstance(value, Mapping):
            return self._describe_json_focus_rows(
                [value],
                path=path,
                limit=limit,
                schema_depth=schema_depth,
                container_type="array" if path_represents_array else "object",
                item_count=1 if path_represents_array else None,
            )

        if isinstance(value, list):
            focus: dict[str, Any] = {
                "path": path,
                "found": True,
                "type": "array",
                "match_count": match_count,
                "item_count": len(value),
            }
            if value and all(isinstance(item, Mapping) for item in value):
                mapping_focus = self._describe_json_focus_rows(
                    value,
                    path=path,
                    limit=limit,
                    schema_depth=schema_depth,
                    container_type="array",
                    item_count=len(value),
                )
                mapping_focus["type"] = "array"
                mapping_focus["item_count"] = len(value)
                return mapping_focus

            focus["sample_items"] = [self._build_preview_item(item) for item in value[:limit]]
            if any(isinstance(item, (dict, list)) for item in value[: min(len(value), 10)]):
                focus["schema_fields"] = self._collect_json_schema_fields(value, max_depth=schema_depth)
            return focus

        if path_represents_array:
            return {
                "path": path,
                "found": True,
                "type": "array",
                "match_count": match_count,
                "item_count": 1,
                "sample_items": [self._build_preview_item(value)],
            }

        return {
            "path": path,
            "found": True,
            "type": self._infer_value_type(value),
            "match_count": match_count,
            "sample_items": [self._build_preview_item(value)],
        }

    def _describe_json_focus_rows(
        self,
        rows: list[Mapping[str, Any]],
        *,
        path: str,
        limit: int,
        schema_depth: int,
        container_type: str = "object",
        item_count: int | None = None,
    ) -> dict[str, Any]:
        headers: list[str] = []
        for row in rows[: min(len(rows), 25)]:
            for key in row.keys():
                key_text = str(key)
                if key_text not in headers:
                    headers.append(key_text)

        focus = {
            "path": path,
            "found": True,
            "type": container_type,
            "match_count": len(rows),
            "field_count": len(headers),
            "headers": headers[:8],
            "sample_rows": [
                {key: self._stringify_preview(row.get(key)) for key in headers[:8]}
                for row in rows[:limit]
            ],
            "schema_fields": self._collect_json_array_schema_fields(rows, max_depth=schema_depth),
        }
        if item_count is not None:
            focus["item_count"] = item_count
        return focus

    def _extract_json_path_matches(self, value: Any, schema_path: str) -> list[Any]:
        segments = [segment.strip() for segment in schema_path.split(".") if segment.strip()]
        if not segments:
            return [value]

        matches: list[Any] = [value]
        for segment in segments:
            next_matches: list[Any] = []
            if segment == "[]":
                for match in matches:
                    if isinstance(match, list):
                        next_matches.extend(match)
                matches = next_matches
                continue

            is_array_segment = segment.endswith("[]")
            key = segment[:-2] if is_array_segment else segment
            for match in matches:
                child: Any | None = None
                if key:
                    if isinstance(match, Mapping) and key in match:
                        child = match[key]
                    else:
                        continue
                else:
                    child = match

                if is_array_segment:
                    if isinstance(child, list):
                        next_matches.extend(child)
                    continue

                next_matches.append(child)

            matches = next_matches
            if not matches:
                break

        return matches

    def _filter_mapping_rows(
        self,
        rows: list[Mapping[str, Any]],
        *,
        filter_text: str | None,
    ) -> list[Mapping[str, Any]]:
        normalized_filter = (filter_text or "").strip().lower()
        if not normalized_filter:
            return list(rows)
        return [row for row in rows if self._row_matches_filter(row, normalized_filter)]

    def _row_matches_filter(self, row: Mapping[str, Any], filter_text: str) -> bool:
        for key, value in row.items():
            haystack = f"{key} {value}".lower()
            if filter_text in haystack:
                return True
        return False

    def _value_matches_filter(self, value: Any, filter_text: str) -> bool:
        preview = self._stringify_preview(value).lower()
        return filter_text.lower() in preview

    def _infer_common_type(self, values: Any) -> str:
        inferred = {
            inferred_type
            for inferred_type in (self._infer_value_type(value) for value in values)
            if inferred_type != "empty"
        }
        if not inferred:
            return "empty"
        if len(inferred) == 1:
            return next(iter(inferred))
        return "mixed"

    def _infer_value_type(self, value: Any) -> str:
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, int) and not isinstance(value, bool):
            return "integer"
        if isinstance(value, float):
            return "number"
        if isinstance(value, dict):
            return "object"
        if isinstance(value, list):
            return "array"

        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return "empty"
            if stripped.lower() in {"true", "false"}:
                return "boolean"
            if re.fullmatch(r"-?\d+", stripped):
                return "integer"
            if re.fullmatch(r"-?\d+\.\d+", stripped):
                return "number"
            if stripped.startswith("{") and stripped.endswith("}"):
                return "object"
            if stripped.startswith("[") and stripped.endswith("]"):
                return "array"
            return "text"

        return type(value).__name__.lower()

    def _collect_json_schema_fields(
        self,
        value: Any,
        *,
        max_depth: int,
        path: str = "",
        current_depth: int = 1,
    ) -> list[dict[str, Any]]:
        if current_depth > max_depth:
            return []

        fields: list[dict[str, Any]] = []
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}" if path else str(key)
                child_type = self._infer_value_type(child)
                fields.append({"name": child_path, "type": child_type, "depth": current_depth})
                if child_type in {"object", "array"} and current_depth < max_depth:
                    fields.extend(
                        self._collect_json_schema_fields(
                            child,
                            max_depth=max_depth,
                            path=child_path,
                            current_depth=current_depth + 1,
                        )
                    )
        elif isinstance(value, list):
            if not value:
                fields.append({"name": f"{path}[]" if path else "[]", "type": "empty", "depth": current_depth})
                return fields

            list_path = f"{path}[]" if path else "[]"
            item_type = self._infer_common_type(item for item in value[: min(len(value), 50)])
            fields.append({"name": list_path, "type": item_type, "depth": current_depth})

            if current_depth >= max_depth:
                return fields

            if all(isinstance(item, dict) for item in value[: min(len(value), 10)]):
                merged_keys: list[str] = []
                for item in value[: min(len(value), 10)]:
                    for key in item.keys():
                        key_text = str(key)
                        if key_text not in merged_keys:
                            merged_keys.append(key_text)
                for key in merged_keys:
                    child_values = [item.get(key) for item in value[: min(len(value), 50)] if isinstance(item, dict)]
                    child_type = self._infer_common_type(child_values)
                    child_path = f"{list_path}.{key}"
                    fields.append({"name": child_path, "type": child_type, "depth": current_depth + 1})
                    sample_child = next((item.get(key) for item in value if isinstance(item, dict) and key in item), None)
                    if child_type in {"object", "array"} and current_depth + 1 < max_depth:
                        fields.extend(
                            self._collect_json_schema_fields(
                                sample_child,
                                max_depth=max_depth,
                                path=child_path,
                                current_depth=current_depth + 2,
                            )
                        )
            elif any(isinstance(item, (dict, list)) for item in value[: min(len(value), 10)]):
                sample_item = next((item for item in value if isinstance(item, (dict, list))), None)
                if sample_item is not None:
                    fields.extend(
                        self._collect_json_schema_fields(
                            sample_item,
                            max_depth=max_depth,
                            path=list_path,
                            current_depth=current_depth + 1,
                        )
                    )
        return fields

    def _collect_json_array_schema_fields(self, rows: list[Mapping[str, Any]], *, max_depth: int) -> list[dict[str, Any]]:
        merged: dict[str, dict[str, Any]] = {}
        for row in rows[: min(len(rows), 25)]:
            for field in self._collect_json_schema_fields(row, max_depth=max_depth):
                existing = merged.get(field["name"])
                if existing is None:
                    merged[field["name"]] = dict(field)
                    continue
                if existing["type"] != field["type"]:
                    existing["type"] = "mixed"
        return list(merged.values())

    def _collect_yaml_schema_fields(self, content: str, *, max_depth: int) -> list[dict[str, Any]]:
        nodes = self._collect_yaml_schema_nodes(content, max_depth=max_depth)
        return [
            {"name": node["name"], "type": node["type"], "depth": node["depth"]}
            for node in nodes[:40]
        ]

    def _collect_yaml_schema_nodes(self, content: str, *, max_depth: int) -> list[dict[str, Any]]:
        nodes: list[dict[str, Any]] = []
        stack: list[tuple[int, str]] = []

        for line_index, raw_line in enumerate(content.splitlines()):
            if not raw_line.strip() or raw_line.lstrip().startswith("#"):
                continue

            normalized = raw_line.replace("\t", "  ")
            indent = len(normalized) - len(normalized.lstrip(" "))
            stripped = normalized.strip()

            if stripped.startswith("- "):
                item_value = stripped[2:].strip()
                if not stack:
                    continue
                while stack and stack[-1][0] > indent:
                    stack.pop()
                parent_path = stack[-1][1]
                nodes = self._merge_schema_node(
                    nodes,
                    {
                        "name": parent_path,
                        "type": "array",
                        "depth": self._path_depth(parent_path),
                        "line_index": line_index,
                        "indent": max(indent - 2, 0),
                    },
                )
                list_path = f"{parent_path}[]"
                depth = self._path_depth(list_path)
                if depth <= max_depth:
                    item_type = "object" if re.match(r"^([A-Za-z0-9_.-]+):\s*(.*)$", item_value) else self._infer_yaml_inline_type(item_value)
                    nodes = self._merge_schema_node(
                        nodes,
                        {
                            "name": list_path,
                            "type": item_type,
                            "depth": depth,
                            "line_index": line_index,
                            "indent": indent,
                        },
                    )

                key_match = re.match(r"^([A-Za-z0-9_.-]+):\s*(.*)$", item_value)
                if key_match and depth < max_depth:
                    child_key = key_match.group(1)
                    child_value = key_match.group(2)
                    child_path = f"{list_path}.{child_key}"
                    child_depth = self._path_depth(child_path)
                    child_type = self._infer_yaml_inline_type(child_value)
                    nodes = self._merge_schema_node(
                        nodes,
                        {
                            "name": child_path,
                            "type": child_type,
                            "depth": child_depth,
                            "line_index": line_index,
                            "indent": indent + 2,
                        },
                    )
                    if child_type in {"object", "array"}:
                        stack.append((indent + 2, child_path))
                continue

            key_match = re.match(r"^([A-Za-z0-9_.-]+):\s*(.*)$", stripped)
            if key_match is None:
                continue

            key = key_match.group(1)
            raw_value = key_match.group(2)
            while stack and stack[-1][0] >= indent:
                stack.pop()

            parent_path = stack[-1][1] if stack else ""
            path = f"{parent_path}.{key}" if parent_path else key
            depth = self._path_depth(path)
            field_type = self._infer_yaml_inline_type(raw_value)
            if depth <= max_depth:
                nodes = self._merge_schema_node(
                    nodes,
                    {
                        "name": path,
                        "type": field_type,
                        "depth": depth,
                        "line_index": line_index,
                        "indent": indent,
                    },
                )

            if field_type in {"object", "array"} or raw_value == "":
                stack.append((indent, path))

        return nodes[:80]

    def _merge_schema_field(self, fields: list[dict[str, Any]], field: dict[str, Any]) -> list[dict[str, Any]]:
        for existing in fields:
            if existing["name"] != field["name"]:
                continue
            if existing["type"] == "object" and field["type"] == "array":
                existing["type"] = "array"
                return fields
            if existing["type"] == "array" and field["type"] == "object":
                return fields
            if existing["type"] != field["type"]:
                existing["type"] = "mixed"
            return fields
        fields.append(field)
        return fields

    def _merge_schema_node(self, nodes: list[dict[str, Any]], node: dict[str, Any]) -> list[dict[str, Any]]:
        for existing in nodes:
            if existing["name"] != node["name"]:
                continue
            if existing["type"] == "object" and node["type"] == "array":
                existing["type"] = "array"
            elif existing["type"] != node["type"] and not (
                existing["type"] == "array" and node["type"] == "object"
            ):
                existing["type"] = "mixed"

            if node["line_index"] < existing["line_index"]:
                existing["line_index"] = node["line_index"]
                existing["indent"] = node["indent"]
            return nodes

        nodes.append(node)
        return nodes

    def _build_yaml_focus(
        self,
        content: str,
        *,
        schema_path: str,
        limit: int,
        schema_depth: int,
    ) -> dict[str, Any]:
        normalized_path = schema_path.strip()
        if not normalized_path:
            return {"path": normalized_path, "found": False}

        lookup_depth = max(4, self._path_depth(normalized_path) + schema_depth)
        nodes = self._collect_yaml_schema_nodes(content, max_depth=lookup_depth)
        exact_node = next((node for node in nodes if node["name"] == normalized_path), None)
        if exact_node is None:
            return {"path": normalized_path, "found": False}

        base_depth = self._path_depth(normalized_path)
        descendants: list[dict[str, Any]] = []
        line_actions: list[dict[str, Any]] = []
        for node in nodes:
            if node["name"] == normalized_path:
                continue
            if not (
                node["name"].startswith(f"{normalized_path}.")
                or node["name"].startswith(f"{normalized_path}[].")
                or node["name"].startswith(f"{normalized_path}[]")
            ):
                continue
            relative_depth = max(1, node["depth"] - base_depth)
            if relative_depth > schema_depth:
                continue
            relative_name = self._relative_schema_name(node["name"], normalized_path)
            descendants.append(
                {
                    "name": relative_name,
                    "type": node["type"],
                    "depth": relative_depth,
                }
            )
            if relative_depth == 1:
                line_actions.append(
                    {
                        "name": relative_name,
                        "path": node["name"],
                        "type": node["type"],
                        "preview": self._extract_yaml_line_preview(content, line_index=node["line_index"]),
                    }
                )

        focus = {
            "path": normalized_path,
            "found": True,
            "type": exact_node["type"],
            "schema_fields": descendants[:24],
            "sample_lines": self._extract_yaml_block_lines(
                content,
                start_line=exact_node["line_index"],
                base_indent=exact_node["indent"],
                limit=limit,
            ),
        }
        if line_actions:
            focus["line_actions"] = line_actions[:12]
        return focus

    def _extract_yaml_block_lines(
        self,
        content: str,
        *,
        start_line: int,
        base_indent: int,
        limit: int,
    ) -> list[str]:
        lines = content.splitlines()
        block: list[str] = []
        for index in range(start_line, len(lines)):
            raw_line = lines[index]
            if not raw_line.strip():
                continue
            normalized = raw_line.replace("\t", "  ")
            indent = len(normalized) - len(normalized.lstrip(" "))
            if index > start_line and indent <= base_indent:
                break
            block.append(normalized.strip())
            if len(block) >= limit:
                break
        return block

    def _extract_yaml_line_preview(self, content: str, *, line_index: int) -> str:
        lines = content.splitlines()
        if line_index < 0 or line_index >= len(lines):
            return ""
        return lines[line_index].replace("\t", "  ").strip()

    def _relative_schema_name(self, name: str, base_path: str) -> str:
        if name == base_path:
            return name
        if name.startswith(f"{base_path}."):
            return name[len(base_path) + 1 :]
        if name.startswith(f"{base_path}[]"):
            relative = name[len(base_path) :]
            return relative.lstrip(".")
        return name

    def _infer_yaml_inline_type(self, raw_value: str) -> str:
        stripped = raw_value.strip()
        if stripped == "":
            return "object"
        if stripped == "[]":
            return "array"
        if stripped == "{}":
            return "object"
        return self._infer_value_type(stripped)

    def _path_depth(self, path: str) -> int:
        if not path:
            return 0
        return path.count(".") + path.count("[]") + 1

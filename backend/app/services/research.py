from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from app.services.webpages import WebPageService, WebPageUnavailableError
from app.services.websearch import WebSearchService


class ResearchSummaryService:
    def __init__(
        self,
        web_search_service: WebSearchService,
        webpage_service: WebPageService,
    ) -> None:
        self.web_search_service = web_search_service
        self.webpage_service = webpage_service

    def build_summary(
        self,
        query: str,
        *,
        search_limit: int = 5,
        source_limit: int = 3,
    ) -> dict[str, Any]:
        search_payload = self.web_search_service.search(query, limit=max(1, min(search_limit, 10)))
        sources: list[dict[str, Any]] = []
        fetch_errors: list[dict[str, str]] = []

        for result in (search_payload.get("results") or [])[: max(1, min(source_limit, 5))]:
            url = str(result.get("url", "")).strip()
            if not url:
                continue
            try:
                payload = self.webpage_service.summarize_page(url)
            except WebPageUnavailableError as exc:
                fetch_errors.append({"url": url, "error": str(exc)})
                continue

            page = payload["page"]
            summary = payload["summary"]
            sources.append(
                {
                    "rank": result.get("rank", len(sources) + 1),
                    "title": page.get("title", result.get("title", url)),
                    "url": page.get("url", url),
                    "domain": self._extract_domain(page.get("url", url)),
                    "search_title": result.get("title", ""),
                    "search_snippet": result.get("snippet", ""),
                    "overview": summary.get("overview", ""),
                    "key_points": summary.get("key_points", [])[:4],
                    "headings": summary.get("headings", [])[:5],
                    "estimated_read_time_minutes": summary.get("estimated_read_time_minutes", 1),
                    "security": page.get("security", {}),
                }
            )

        brief = self._build_brief(query=query, sources=sources, fetch_errors=fetch_errors)
        return {
            "query": str(query).strip(),
            "search": search_payload,
            "brief": brief,
            "sources": sources,
            "fetch_errors": fetch_errors,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def audit_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        brief = payload.get("brief", {})
        source_count = int(brief.get("source_count", 0) or 0)
        return {
            "query": payload.get("query", ""),
            "generated_at": payload.get("generated_at", ""),
            "search": self.web_search_service.audit_payload(payload.get("search", {})),
            "brief": {
                "overview": (
                    f"Research brief generated for '{payload.get('query', '')}' using {source_count} source"
                    f"{'' if source_count == 1 else 's'}."
                ),
                "key_finding_count": len(brief.get("key_findings", [])),
                "source_count": source_count,
                "partial": bool(brief.get("partial")),
                "suspicious_source_count": int(brief.get("suspicious_source_count", 0) or 0),
            },
            "sources": [
                {
                    "title": source.get("title", ""),
                    "url": source.get("url", ""),
                    "domain": source.get("domain", ""),
                    "rank": source.get("rank", 0),
                    "security": {
                        "prompt_injection_detected": bool(source.get("security", {}).get("prompt_injection_detected")),
                        "flag_count": int(source.get("security", {}).get("flag_count", 0) or 0),
                    },
                }
                for source in (payload.get("sources") or [])[:5]
            ],
            "fetch_error_count": len(payload.get("fetch_errors") or []),
        }

    def _build_brief(
        self,
        *,
        query: str,
        sources: list[dict[str, Any]],
        fetch_errors: list[dict[str, str]],
    ) -> dict[str, Any]:
        key_findings: list[str] = []
        seen: set[str] = set()

        for source in sources:
            for item in source.get("key_points", []):
                normalized = str(item).strip()
                lowered = normalized.casefold()
                if not normalized or lowered in seen:
                    continue
                seen.add(lowered)
                key_findings.append(normalized)
                if len(key_findings) >= 6:
                    break
            if len(key_findings) >= 6:
                break

        source_domains = [source.get("domain", "") for source in sources if source.get("domain")]
        suspicious_source_count = sum(
            1 for source in sources if bool(source.get("security", {}).get("prompt_injection_detected"))
        )
        domain_copy = ", ".join(source_domains[:3])
        if sources:
            overview = (
                f"Research brief for '{query}': reviewed {len(sources)} sanitized source"
                f"{'' if len(sources) == 1 else 's'}"
            )
            if domain_copy:
                overview = f"{overview} from {domain_copy}"
            leading = sources[0].get("overview", "")
            if leading:
                overview = f"{overview}. {leading}"
        else:
            overview = f"Research brief for '{query}': no readable sources were summarized yet."

        if fetch_errors and sources:
            overview = f"{overview} Some sources could not be summarized locally."
        if suspicious_source_count:
            overview = f"{overview} Suspicious instruction-like text was removed from {suspicious_source_count} source(s)."

        return {
            "overview": overview,
            "key_findings": key_findings,
            "source_count": len(sources),
            "partial": bool(fetch_errors),
            "source_domains": source_domains,
            "suspicious_source_count": suspicious_source_count,
        }

    def _extract_domain(self, url: str) -> str:
        parsed = urlparse(url)
        return parsed.netloc or url

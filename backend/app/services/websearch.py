from __future__ import annotations

import re
from datetime import datetime, timezone
from html import unescape
from typing import Any, Callable
from urllib.parse import parse_qs, quote_plus, unquote, urlparse
from urllib.request import Request, urlopen


class WebSearchUnavailableError(RuntimeError):
    """Raised when live web search cannot be completed."""


class WebSearchService:
    USER_AGENT = "Zivra/0.1 (+https://local.zivra)"

    def __init__(
        self,
        *,
        fetcher: Callable[[str], str] | None = None,
        timeout_seconds: float = 12.0,
        max_bytes: int = 500_000,
    ) -> None:
        self._fetcher = fetcher or self._default_fetch
        self.timeout_seconds = timeout_seconds
        self.max_bytes = max_bytes

    def search(self, query: str, *, limit: int = 5) -> dict[str, Any]:
        normalized_query = str(query or "").strip()
        if not normalized_query:
            raise WebSearchUnavailableError("A search query is required.")

        html = self._fetcher(normalized_query)
        results = self._parse_results(html, limit=max(1, min(limit, 10)))
        return {
            "provider": "duckduckgo",
            "query": normalized_query,
            "handoff_url": f"https://duckduckgo.com/?q={quote_plus(normalized_query)}",
            "result_count": len(results),
            "results": results,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    def audit_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "provider": payload.get("provider", "duckduckgo"),
            "query": payload.get("query", ""),
            "handoff_url": payload.get("handoff_url", ""),
            "result_count": payload.get("result_count", 0),
            "results": [
                {
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "rank": result.get("rank", 0),
                }
                for result in (payload.get("results") or [])[:5]
            ],
            "fetched_at": payload.get("fetched_at", ""),
        }

    def _default_fetch(self, query: str) -> str:
        request = Request(
            f"https://html.duckduckgo.com/html/?q={quote_plus(query)}",
            headers={
                "User-Agent": self.USER_AGENT,
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read(self.max_bytes + 1)
        except Exception as exc:  # pragma: no cover - network normalization
            raise WebSearchUnavailableError(str(exc)) from exc

        if len(raw) > self.max_bytes:
            raw = raw[: self.max_bytes]
        return raw.decode("utf-8", errors="ignore")

    def _parse_results(self, html: str, *, limit: int) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        anchor_pattern = re.compile(
            r'<a[^>]+class="[^"]*(?:result__a|result-link)[^"]*"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
            flags=re.IGNORECASE | re.DOTALL,
        )

        for index, match in enumerate(anchor_pattern.finditer(html), start=1):
            if len(results) >= limit:
                break
            href = self._normalize_result_url(match.group(1))
            title = self._strip_html(match.group(2))
            if not href or not title:
                continue

            snippet_window = html[match.end() : match.end() + 1200]
            snippet_match = re.search(
                r'<(?:a|div)[^>]+class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</(?:a|div)>',
                snippet_window,
                flags=re.IGNORECASE | re.DOTALL,
            )
            snippet = self._strip_html(snippet_match.group(1)) if snippet_match else ""
            results.append(
                {
                    "rank": index,
                    "title": title,
                    "url": href,
                    "snippet": snippet[:280],
                }
            )

        return results

    def _normalize_result_url(self, href: str) -> str:
        cleaned = unescape(href or "").strip()
        if not cleaned:
            return ""
        parsed = urlparse(cleaned)
        if parsed.netloc.endswith("duckduckgo.com") and parsed.path.startswith("/l/"):
            params = parse_qs(parsed.query)
            if "uddg" in params and params["uddg"]:
                return unquote(params["uddg"][0])
        return cleaned

    def _strip_html(self, value: str) -> str:
        cleaned = re.sub(r"<[^>]+>", " ", unescape(value or ""))
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

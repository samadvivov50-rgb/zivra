from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.api.routes.web import search_web
from app.core.config import Settings
from app.services.audit import AuditLogger
from app.services.websearch import WebSearchService
from app.tools.safe import SearchWebTool


class WebSearchServiceTests(unittest.TestCase):
    def test_search_parses_duckduckgo_style_results(self) -> None:
        html = """
        <html>
          <body>
            <a class="result__a" href="https://duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fguide">Example Guide</a>
            <div class="result__snippet">A useful guide for testing live web search results.</div>
            <a class="result__a" href="https://example.org/post">Example Post</a>
            <div class="result__snippet">Another result with a compact snippet.</div>
          </body>
        </html>
        """
        service = WebSearchService(fetcher=lambda query: html)

        payload = service.search("desktop assistant", limit=5)

        self.assertEqual(payload["provider"], "duckduckgo")
        self.assertEqual(payload["result_count"], 2)
        self.assertEqual(payload["results"][0]["title"], "Example Guide")
        self.assertEqual(payload["results"][0]["url"], "https://example.com/guide")
        self.assertIn("live web search", payload["results"][0]["snippet"].lower())

    def test_audit_payload_keeps_titles_and_urls_but_not_snippets(self) -> None:
        service = WebSearchService(fetcher=lambda query: "")
        payload = {
            "provider": "duckduckgo",
            "query": "desktop assistant",
            "handoff_url": "https://duckduckgo.com/?q=desktop+assistant",
            "result_count": 1,
            "results": [
                {
                    "rank": 1,
                    "title": "Example Guide",
                    "url": "https://example.com/guide",
                    "snippet": "This snippet should not land in the audit payload.",
                }
            ],
            "fetched_at": "2026-03-21T00:00:00+00:00",
        }

        audit_payload = service.audit_payload(payload)

        self.assertEqual(audit_payload["results"][0]["title"], "Example Guide")
        self.assertNotIn("snippet", audit_payload["results"][0])


class SearchWebToolTests(unittest.TestCase):
    def test_search_web_tool_returns_live_result_metadata(self) -> None:
        service = WebSearchService(
            fetcher=lambda query: """
            <a class="result__a" href="https://example.com/guide">Example Guide</a>
            <div class="result__snippet">Useful snippet text that should stay out of the audit payload.</div>
            """
        )
        tool = SearchWebTool(service)

        result = tool.execute({"query": "desktop assistant"})

        self.assertTrue(result.success)
        self.assertIn("Found 1 live web result", result.message)
        self.assertIn("search", result.data)
        self.assertNotIn("Useful snippet text", json.dumps(result.data))

    def test_search_web_tool_uses_configured_default_limit(self) -> None:
        service = WebSearchService(
            fetcher=lambda query: """
            <a class="result__a" href="https://example.com/guide-1">Guide 1</a>
            <div class="result__snippet">Snippet 1</div>
            <a class="result__a" href="https://example.com/guide-2">Guide 2</a>
            <div class="result__snippet">Snippet 2</div>
            <a class="result__a" href="https://example.com/guide-3">Guide 3</a>
            <div class="result__snippet">Snippet 3</div>
            """
        )
        settings = Settings(repo_root=Path(tempfile.gettempdir()), live_search_result_limit=2)
        tool = SearchWebTool(service, settings)

        result = tool.execute({"query": "desktop assistant"})

        self.assertTrue(result.success)
        self.assertEqual(result.data["search"]["result_count"], 2)


class WebSearchRouteTests(unittest.TestCase):
    def test_search_route_returns_results_and_audit_log_uses_metadata_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            request = self._build_request(
                temp_dir,
                WebSearchService(
                    fetcher=lambda query: """
                    <a class="result__a" href="https://example.com/guide">Example Guide</a>
                    <div class="result__snippet">Useful snippet text that should not be written to the audit log.</div>
                    """
                ),
            )

            response = search_web(request, q="desktop assistant", limit=5)

            self.assertEqual(response["result_count"], 1)
            self.assertEqual(response["results"][0]["title"], "Example Guide")
            events = request.app.state.audit_logger.recent(limit=5)
            self.assertEqual(len(events), 1)
            self.assertNotIn("Useful snippet text", json.dumps(events[0]))
            self.assertEqual(events[0]["result"]["data"]["search"]["results"][0]["title"], "Example Guide")

    def test_search_route_uses_saved_limit_when_limit_is_omitted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            request = self._build_request(
                temp_dir,
                WebSearchService(
                    fetcher=lambda query: """
                    <a class="result__a" href="https://example.com/guide-1">Guide 1</a>
                    <div class="result__snippet">Snippet 1</div>
                    <a class="result__a" href="https://example.com/guide-2">Guide 2</a>
                    <div class="result__snippet">Snippet 2</div>
                    <a class="result__a" href="https://example.com/guide-3">Guide 3</a>
                    <div class="result__snippet">Snippet 3</div>
                    """
                ),
                settings=SimpleNamespace(live_search_result_limit=2),
            )

            response = search_web(request, q="desktop assistant")

            self.assertEqual(response["result_count"], 2)

    def _build_request(self, temp_dir: str, web_search_service: WebSearchService, settings=None):
        state = SimpleNamespace(
            web_search_service=web_search_service,
            audit_logger=AuditLogger(Path(temp_dir) / "audit" / "actions.jsonl"),
            settings=settings or SimpleNamespace(live_search_result_limit=5),
        )
        return SimpleNamespace(app=SimpleNamespace(state=state))


if __name__ == "__main__":
    unittest.main()

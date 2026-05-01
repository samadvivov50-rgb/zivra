from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from starlette.requests import Request

from app.core.config import Settings
from app.main import create_app


class AppRedirectTests(unittest.TestCase):
    def test_mobile_redirect_preserves_query_string(self) -> None:
        with tempfile.TemporaryDirectory() as temp_repo:
            with patch("app.main.Settings", side_effect=lambda: Settings(repo_root=Path(temp_repo))):
                app = create_app()

            mobile_endpoint = next(
                route.endpoint
                for route in app.router.routes
                if getattr(route, "path", None) == "/mobile"
            )
            request = Request(
                {
                    "type": "http",
                    "method": "GET",
                    "path": "/mobile",
                    "query_string": b"session_id=smoke-session",
                    "headers": [],
                }
            )
            response = mobile_endpoint(request)

            self.assertEqual(response.status_code, 307)
            self.assertEqual(response.headers["location"], "/ui/mobile.html?session_id=smoke-session")


if __name__ == "__main__":
    unittest.main()

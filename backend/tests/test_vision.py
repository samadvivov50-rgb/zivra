from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.api.routes.vision import VisionAnalyzeRequest, analyze_image, read_vision_status
from app.core.config import Settings
from app.services.vision import VisionService

SAMPLE_PNG_DATA_URL = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO2pJ4kAAAAASUVORK5CYII="
)


class VisionServiceTests(unittest.TestCase):
    def test_service_analyzes_png_metadata_locally(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(repo_root=Path(temp_dir))
            service = VisionService(settings)

            payload = service.analyze_data_url(
                SAMPLE_PNG_DATA_URL,
                filename="screen.png",
                prompt="Check the dialog title",
            )

            self.assertEqual(payload["image"]["format"], "png")
            self.assertEqual(payload["image"]["width"], 1)
            self.assertEqual(payload["image"]["height"], 1)
            self.assertEqual(payload["summary"]["provider"], "local")
            self.assertIn("metadata", payload["summary"]["overview"].lower())
            self.assertIn("Check the dialog title", " ".join(payload["summary"]["key_points"]))

    def test_service_uses_multimodal_executor_when_configured(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(repo_root=Path(temp_dir))
            settings.llm_api_key = "test-key"
            settings.vision_model = "gpt-4.1-mini"
            service = VisionService(
                settings,
                request_executor=lambda payload: {
                    "choices": [
                        {
                            "message": {
                                "content": (
                                    '{"overview":"A small status badge is visible.",'
                                    '"key_points":["Single indicator on screen"],'
                                    '"visible_text":["OK"],'
                                    '"suggested_actions":["Confirm the status source"],'
                                    '"contains_sensitive_content":false}'
                                )
                            }
                        }
                    ]
                },
            )

            payload = service.analyze_data_url(SAMPLE_PNG_DATA_URL, filename="badge.png")

            self.assertEqual(payload["summary"]["provider"], "openai_compatible")
            self.assertEqual(payload["summary"]["visible_text"], ["OK"])
            self.assertEqual(payload["model"]["mode"], "multimodal")


class VisionRouteTests(unittest.TestCase):
    def test_status_route_reports_local_only_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            request = self._build_request(temp_dir)

            response = read_vision_status(request)

            self.assertFalse(response["status"]["ready"])
            self.assertEqual(response["status"]["mode"], "metadata_only")

    def test_analyze_route_returns_metadata_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            request = self._build_request(temp_dir)

            response = analyze_image(
                VisionAnalyzeRequest(
                    data_url=SAMPLE_PNG_DATA_URL,
                    filename="screen.png",
                    prompt="Summarize the screenshot",
                ),
                request,
            )

            self.assertIsNotNone(response["analysis"])
            self.assertEqual(response["analysis"]["image"]["filename"], "screen.png")
            self.assertIn("locally", response["message"].lower())

    def test_analyze_route_reports_invalid_payload_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            request = self._build_request(temp_dir)

            response = analyze_image(
                VisionAnalyzeRequest(
                    data_url="data:text/plain;base64,SGVsbG8=",
                    filename="bad.txt",
                ),
                request,
            )

            self.assertIsNone(response["analysis"])
            self.assertIn("image", response["message"].lower())

    def _build_request(self, temp_dir: str):
        settings = Settings(repo_root=Path(temp_dir))
        state = SimpleNamespace(
            vision_service=VisionService(settings),
        )
        return SimpleNamespace(app=SimpleNamespace(state=state))


if __name__ == "__main__":
    unittest.main()

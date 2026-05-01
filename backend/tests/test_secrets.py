from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.api.routes.settings import clear_secret_settings, read_secret_settings, update_secret_settings, UpdateSecretsRequest
from app.core.config import Settings
from app.services.orchestrator import IntentRouter
from app.services.planning import build_planner
from app.services.secrets import BaseSecretProtector, SecretsService


class FakeSecretProtector(BaseSecretProtector):
    provider = "fake"
    label = "Fake encrypted vault"
    available = True

    def protect(self, plaintext: str) -> str:
        return f"enc::{str(plaintext)[::-1]}"

    def unprotect(self, ciphertext: str) -> str:
        prefix = "enc::"
        if not str(ciphertext).startswith(prefix):
            raise ValueError("Bad test ciphertext.")
        return str(ciphertext)[len(prefix) :][::-1]


class SecretsServiceTests(unittest.TestCase):
    def test_update_encrypts_values_and_applies_runtime_settings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(repo_root=Path(temp_dir), llm_model="gpt-test", smtp_host="smtp.example.com")
            service = SecretsService(settings.secrets_path, protector=FakeSecretProtector())

            snapshot = service.update(
                settings,
                {
                    "llm_api_key": "sk-test-secret-1234",
                    "smtp_username": "mailer@example.com",
                    "smtp_password": "very-secret-password",
                    "whatsapp_access_token": "wa-test-token",
                    "whatsapp_app_secret": "wa-app-secret",
                },
            )

            self.assertEqual(settings.llm_api_key, "sk-test-secret-1234")
            self.assertEqual(settings.smtp_username, "mailer@example.com")
            self.assertEqual(settings.smtp_password, "very-secret-password")
            self.assertEqual(settings.email_from_address, "mailer@example.com")
            self.assertEqual(settings.whatsapp_access_token, "wa-test-token")
            self.assertEqual(settings.whatsapp_app_secret, "wa-app-secret")
            self.assertEqual(snapshot["fields"]["llm_api_key"]["source"], "vault")
            self.assertTrue(snapshot["runtime"]["planner_ready"])
            self.assertTrue(snapshot["runtime"]["smtp_ready"])
            self.assertFalse(snapshot["runtime"]["whatsapp_ready"])

            raw_payload = settings.secrets_path.read_text(encoding="utf-8")
            self.assertNotIn("sk-test-secret-1234", raw_payload)
            self.assertNotIn("mailer@example.com", raw_payload)
            self.assertNotIn("very-secret-password", raw_payload)
            self.assertNotIn("wa-test-token", raw_payload)
            self.assertNotIn("wa-app-secret", raw_payload)

    def test_clear_restores_environment_backed_secret_values(self) -> None:
        original_env = {
            "ZIVRA_LLM_API_KEY": os.getenv("ZIVRA_LLM_API_KEY"),
            "ZIVRA_SMTP_USERNAME": os.getenv("ZIVRA_SMTP_USERNAME"),
            "ZIVRA_SMTP_PASSWORD": os.getenv("ZIVRA_SMTP_PASSWORD"),
            "ZIVRA_EMAIL_FROM": os.getenv("ZIVRA_EMAIL_FROM"),
            "ZIVRA_WHATSAPP_ACCESS_TOKEN": os.getenv("ZIVRA_WHATSAPP_ACCESS_TOKEN"),
            "ZIVRA_WHATSAPP_APP_SECRET": os.getenv("ZIVRA_WHATSAPP_APP_SECRET"),
        }
        try:
            os.environ["ZIVRA_LLM_API_KEY"] = "env-llm-key"
            os.environ["ZIVRA_SMTP_USERNAME"] = "env-user@example.com"
            os.environ["ZIVRA_SMTP_PASSWORD"] = "env-password"
            os.environ.pop("ZIVRA_EMAIL_FROM", None)
            os.environ["ZIVRA_WHATSAPP_ACCESS_TOKEN"] = "env-wa-token"
            os.environ["ZIVRA_WHATSAPP_APP_SECRET"] = "env-wa-secret"

            with tempfile.TemporaryDirectory() as temp_dir:
                settings = Settings(repo_root=Path(temp_dir), llm_model="gpt-test", whatsapp_phone_number_id="12345")
                service = SecretsService(settings.secrets_path, protector=FakeSecretProtector())
                service.update(
                    settings,
                    {
                        "llm_api_key": "vault-llm-key",
                        "smtp_username": "vault-user@example.com",
                        "smtp_password": "vault-password",
                        "whatsapp_access_token": "vault-wa-token",
                        "whatsapp_app_secret": "vault-wa-secret",
                    },
                )

                snapshot = service.clear(settings)

                self.assertEqual(settings.llm_api_key, "env-llm-key")
                self.assertEqual(settings.smtp_username, "env-user@example.com")
                self.assertEqual(settings.smtp_password, "env-password")
                self.assertEqual(settings.email_from_address, "env-user@example.com")
                self.assertEqual(settings.whatsapp_access_token, "env-wa-token")
                self.assertEqual(settings.whatsapp_app_secret, "env-wa-secret")
                self.assertEqual(snapshot["fields"]["llm_api_key"]["source"], "environment")
                self.assertEqual(snapshot["fields"]["whatsapp_access_token"]["source"], "environment")
                self.assertFalse(settings.secrets_path.exists())
        finally:
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


class SecretRouteTests(unittest.TestCase):
    def test_secret_routes_refresh_runtime_planner(self) -> None:
        original_env = {
            "ZIVRA_LLM_API_KEY": os.getenv("ZIVRA_LLM_API_KEY"),
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        }
        try:
            os.environ.pop("ZIVRA_LLM_API_KEY", None)
            os.environ.pop("OPENAI_API_KEY", None)

            with tempfile.TemporaryDirectory() as temp_dir:
                request = self._build_request(temp_dir)

                before = read_secret_settings(request)
                self.assertFalse(before["fields"]["llm_api_key"]["configured"])
                self.assertEqual(request.app.state.orchestrator.planner.mode, "rule")

                response = update_secret_settings(
                    UpdateSecretsRequest(llm_api_key="sk-live-secret"),
                    request,
                )

                self.assertEqual(response["fields"]["llm_api_key"]["source"], "vault")
                self.assertEqual(request.app.state.orchestrator.planner.mode, "llm")

                cleared = clear_secret_settings(request)

                self.assertFalse(cleared["fields"]["llm_api_key"]["stored_in_vault"])
                self.assertEqual(request.app.state.orchestrator.planner.mode, "rule")
        finally:
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def _build_request(self, temp_dir: str):
        settings = Settings(repo_root=Path(temp_dir), planner_mode="llm", llm_model="gpt-test")
        settings.ensure_runtime_dirs()
        router = IntentRouter()
        state = SimpleNamespace(
            settings=settings,
            secrets_service=SecretsService(settings.secrets_path, protector=FakeSecretProtector()),
            orchestrator=SimpleNamespace(
                router=router,
                planner=build_planner(settings, fallback_router=router),
            ),
        )
        return SimpleNamespace(app=SimpleNamespace(state=state))


if __name__ == "__main__":
    unittest.main()

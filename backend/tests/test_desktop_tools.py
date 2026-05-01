from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.services.emails import EmailService
from app.services.orchestrator import IntentRouter
from app.tools.safe import DraftEmailTool, LaunchWorkspaceTool, OpenApplicationTool, OpenWebsiteTool


class _FakeSettings:
    approved_apps = {
        "notepad": ("notepad.exe",),
        "calculator": ("calc.exe",),
        "file explorer": ("explorer.exe",),
    }

    def __init__(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._temp_dir.name)
        self.notes_dir = self.repo_root / "notes"
        self.emails_db_path = self.repo_root / "emails.sqlite3"
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        self.smtp_host = ""
        self.smtp_port = 587
        self.smtp_username = ""
        self.smtp_password = ""
        self.smtp_use_tls = True
        self.smtp_use_ssl = False
        self.email_from_address = "zivra@example.com"
        self.email_from_name = "Zivra"
        self.workspace_profiles = {
            "research": {
                "description": "Research setup",
                "apps": ("notepad",),
                "urls": ("https://www.google.com",),
                "paths": ("notes",),
            }
        }

    def cleanup(self) -> None:
        self._temp_dir.cleanup()


class DesktopToolsTests(unittest.TestCase):
    def test_open_website_tool_uses_browser_opener(self) -> None:
        opened_urls: list[str] = []
        tool = OpenWebsiteTool(opener=lambda url: opened_urls.append(url) or True)

        result = tool.execute({"url": "example.com"})

        self.assertTrue(result.success)
        self.assertEqual(opened_urls, ["https://example.com"])
        self.assertEqual(result.data["url"], "https://example.com")

    def test_open_application_tool_uses_approved_command(self) -> None:
        launched_commands: list[tuple[str, ...]] = []
        settings = _FakeSettings()
        self.addCleanup(settings.cleanup)
        tool = OpenApplicationTool(settings, launcher=lambda command: launched_commands.append(command))

        result = tool.execute({"application": "calc"})

        self.assertTrue(result.success)
        self.assertEqual(launched_commands, [("calc.exe",)])
        self.assertEqual(result.data["application"], "calculator")

    def test_draft_email_tool_saves_local_outbox_draft(self) -> None:
        settings = _FakeSettings()
        self.addCleanup(settings.cleanup)
        service = EmailService(settings.emails_db_path, settings=settings)
        tool = DraftEmailTool(service)

        result = tool.execute({"to": "team@example.com", "subject": "Weekly sync", "body": "Status attached"})

        self.assertTrue(result.success)
        drafts = service.list_emails(limit=5)
        self.assertEqual(len(drafts), 1)
        self.assertEqual(drafts[0]["to"], "team@example.com")
        self.assertEqual(drafts[0]["status"], "draft")

    def test_launch_workspace_tool_opens_apps_urls_and_paths(self) -> None:
        launched_commands: list[tuple[str, ...]] = []
        opened_urls: list[str] = []
        opened_paths: list[str] = []
        settings = _FakeSettings()
        self.addCleanup(settings.cleanup)
        tool = LaunchWorkspaceTool(
            settings,
            command_launcher=lambda command: launched_commands.append(command),
            url_opener=lambda url: opened_urls.append(url) or True,
            path_launcher=lambda path: opened_paths.append(path),
        )

        result = tool.execute({"workspace": "research"})

        self.assertTrue(result.success)
        self.assertEqual(launched_commands, [("notepad.exe",)])
        self.assertEqual(opened_urls, ["https://www.google.com"])
        self.assertEqual(opened_paths, [str(settings.notes_dir.resolve())])

    def test_router_routes_known_apps_before_websites(self) -> None:
        router = IntentRouter()

        route = router.route("Open notepad")

        self.assertEqual(route.tool_name, "open_application")
        self.assertEqual(route.arguments["application"], "notepad")

    def test_router_still_routes_urls_to_websites(self) -> None:
        router = IntentRouter()

        route = router.route("Open example.com")

        self.assertEqual(route.tool_name, "open_website")
        self.assertEqual(route.arguments["url"], "example.com")

    def test_router_routes_known_workspaces(self) -> None:
        router = IntentRouter()

        route = router.route("Launch research workspace")

        self.assertEqual(route.tool_name, "launch_workspace")
        self.assertEqual(route.arguments["workspace"], "research")

    def test_router_routes_workspace_modes(self) -> None:
        router = IntentRouter()

        route = router.route("Start planning mode")

        self.assertEqual(route.tool_name, "launch_workspace")
        self.assertEqual(route.arguments["workspace"], "planning")


if __name__ == "__main__":
    unittest.main()

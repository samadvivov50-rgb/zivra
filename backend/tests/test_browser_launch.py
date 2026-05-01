from __future__ import annotations

import unittest

from app.services.browser_launch import BrowserLauncher


class BrowserLauncherTests(unittest.TestCase):
    def test_open_prefers_isolated_edge_window_when_available(self) -> None:
        launched_commands: list[tuple[str, ...]] = []
        launcher = BrowserLauncher(
            which=lambda name: "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" if name == "msedge.exe" else None,
            popen=lambda command: launched_commands.append(command),
            fallback_opener=lambda url: True,
            system_name="windows",
        )

        result = launcher.open("https://example.com")

        self.assertTrue(result["success"])
        self.assertTrue(result["isolated_used"])
        self.assertEqual(result["browser"], "Microsoft Edge")
        self.assertEqual(result["mode"], "inprivate")
        self.assertEqual(
            launched_commands,
            [("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe", "--inprivate", "https://example.com")],
        )

    def test_open_falls_back_to_default_browser_when_private_window_launcher_is_unavailable(self) -> None:
        opened_urls: list[str] = []
        launcher = BrowserLauncher(
            which=lambda name: None,
            popen=lambda command: None,
            fallback_opener=lambda url: opened_urls.append(url) or True,
            system_name="linux",
        )

        result = launcher.open("https://example.com")

        self.assertTrue(result["success"])
        self.assertFalse(result["isolated_used"])
        self.assertTrue(result["used_fallback"])
        self.assertEqual(opened_urls, ["https://example.com"])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import webbrowser
from pathlib import Path
from typing import Any, Callable, Mapping


def normalize_browser_launch_result(result: Any, url: str) -> dict[str, Any]:
    if isinstance(result, Mapping):
        success = bool(result.get("success"))
        return {
            "success": success,
            "url": str(result.get("url", url) or url),
            "isolated_requested": bool(result.get("isolated_requested", False)),
            "isolated_used": bool(result.get("isolated_used", False)),
            "used_fallback": bool(result.get("used_fallback", False)),
            "browser": str(result.get("browser", "") or ""),
            "mode": str(result.get("mode", "default_browser") or "default_browser"),
            "status_label": str(result.get("status_label", "Browser handoff") or "Browser handoff"),
            "error": str(result.get("error", "") or ""),
            "command": list(result.get("command", []) or []),
        }

    opened = bool(result)
    return {
        "success": opened,
        "url": str(url or ""),
        "isolated_requested": False,
        "isolated_used": False,
        "used_fallback": False,
        "browser": "",
        "mode": "default_browser",
        "status_label": "Browser handoff",
        "error": "" if opened else "The browser did not report a successful launch.",
        "command": [],
    }


class BrowserLauncher:
    CANDIDATES = (
        {
            "browser": "Microsoft Edge",
            "executables": ("msedge.exe", "msedge"),
            "flags": ("--inprivate",),
            "mode": "inprivate",
            "windows_paths": (
                ("ProgramFiles(x86)", "Microsoft", "Edge", "Application", "msedge.exe"),
                ("ProgramFiles", "Microsoft", "Edge", "Application", "msedge.exe"),
            ),
        },
        {
            "browser": "Google Chrome",
            "executables": ("chrome.exe", "chrome"),
            "flags": ("--incognito",),
            "mode": "incognito",
            "windows_paths": (
                ("LocalAppData", "Google", "Chrome", "Application", "chrome.exe"),
                ("ProgramFiles(x86)", "Google", "Chrome", "Application", "chrome.exe"),
                ("ProgramFiles", "Google", "Chrome", "Application", "chrome.exe"),
            ),
        },
        {
            "browser": "Mozilla Firefox",
            "executables": ("firefox.exe", "firefox"),
            "flags": ("--private-window",),
            "mode": "private_window",
            "windows_paths": (
                ("ProgramFiles", "Mozilla Firefox", "firefox.exe"),
                ("ProgramFiles(x86)", "Mozilla Firefox", "firefox.exe"),
            ),
        },
    )

    def __init__(
        self,
        *,
        which: Callable[[str], str | None] | None = None,
        popen: Callable[[tuple[str, ...]], Any] | None = None,
        fallback_opener: Callable[[str], bool] | None = None,
        system_name: str | None = None,
    ) -> None:
        self.which = which or shutil.which
        self.popen = popen or subprocess.Popen
        self.fallback_opener = fallback_opener or (lambda url: webbrowser.open(url, new=2))
        self.system_name = (system_name or platform.system()).lower()

    def capabilities(self) -> dict[str, Any]:
        candidate = self._find_candidate()
        return {
            "isolated_available": candidate is not None,
            "browser": candidate["browser"] if candidate else "",
            "mode": candidate["mode"] if candidate else "default_browser",
            "status_label": "Isolated browser handoff" if candidate else "Browser handoff",
        }

    def open(self, url: str, *, isolated: bool = True) -> dict[str, Any]:
        normalized_url = str(url or "").strip()
        if not normalized_url:
            return {
                "success": False,
                "url": "",
                "isolated_requested": isolated,
                "isolated_used": False,
                "used_fallback": False,
                "browser": "",
                "mode": "default_browser",
                "status_label": "Browser handoff",
                "error": "A URL is required.",
                "command": [],
            }

        candidate = self._find_candidate() if isolated else None
        if candidate is not None:
            command = (candidate["path"], *candidate["flags"], normalized_url)
            self.popen(command)
            return {
                "success": True,
                "url": normalized_url,
                "isolated_requested": True,
                "isolated_used": True,
                "used_fallback": False,
                "browser": candidate["browser"],
                "mode": candidate["mode"],
                "status_label": "Isolated browser handoff",
                "error": "",
                "command": list(command),
            }

        try:
            opened = bool(self.fallback_opener(normalized_url))
        except Exception as exc:
            return {
                "success": False,
                "url": normalized_url,
                "isolated_requested": isolated,
                "isolated_used": False,
                "used_fallback": isolated,
                "browser": "",
                "mode": "default_browser",
                "status_label": "Browser handoff",
                "error": str(exc),
                "command": [],
            }

        return {
            "success": opened,
            "url": normalized_url,
            "isolated_requested": isolated,
            "isolated_used": False,
            "used_fallback": isolated,
            "browser": "",
            "mode": "default_browser",
            "status_label": "Browser handoff",
            "error": "" if opened else "The browser did not report a successful launch.",
            "command": [],
        }

    def _find_candidate(self) -> dict[str, Any] | None:
        for candidate in self.CANDIDATES:
            executable_path = self._resolve_executable(candidate)
            if not executable_path:
                continue
            return {
                "browser": candidate["browser"],
                "mode": candidate["mode"],
                "flags": tuple(candidate["flags"]),
                "path": executable_path,
            }
        return None

    def _resolve_executable(self, candidate: Mapping[str, Any]) -> str | None:
        for executable in candidate.get("executables", ()) or ():
            resolved = self.which(str(executable))
            if resolved:
                return str(resolved)

        if self.system_name != "windows":
            return None

        for parts in candidate.get("windows_paths", ()) or ():
            if not parts:
                continue
            root_name = str(parts[0])
            root_value = os.getenv(root_name, "")
            if not root_value:
                continue
            candidate_path = Path(root_value).joinpath(*[str(part) for part in parts[1:]])
            if candidate_path.exists():
                return str(candidate_path)
        return None

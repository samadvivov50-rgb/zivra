from __future__ import annotations

import platform
import shutil
import subprocess
from typing import Callable


class ClipboardUnavailableError(RuntimeError):
    """Raised when the local clipboard is not available."""


class ClipboardService:
    def __init__(
        self,
        *,
        reader: Callable[[], str] | None = None,
        writer: Callable[[str], None] | None = None,
    ) -> None:
        self._reader = reader or self._default_read_text
        self._writer = writer or self._default_write_text

    def read_text(self) -> str:
        try:
            text = self._reader()
        except ClipboardUnavailableError:
            raise
        except Exception as exc:  # pragma: no cover - defensive normalization
            raise ClipboardUnavailableError(str(exc)) from exc
        return self._normalize_text(text)

    def write_text(self, text: str) -> str:
        normalized = self._normalize_text(text)
        try:
            self._writer(normalized)
        except ClipboardUnavailableError:
            raise
        except Exception as exc:  # pragma: no cover - defensive normalization
            raise ClipboardUnavailableError(str(exc)) from exc
        return normalized

    def build_metadata(self, text: str) -> dict[str, int | bool]:
        normalized = self._normalize_text(text)
        return {
            "length": len(normalized),
            "line_count": normalized.count("\n") + 1 if normalized else 0,
            "empty": not bool(normalized),
        }

    def _default_read_text(self) -> str:
        system = platform.system().lower()
        if system == "windows":
            return self._run_command(("powershell", "-NoProfile", "-Command", "Get-Clipboard -Raw"))
        if system == "darwin":
            return self._run_command(("pbpaste",))
        if shutil.which("wl-paste"):
            return self._run_command(("wl-paste", "--no-newline"))
        if shutil.which("xclip"):
            return self._run_command(("xclip", "-selection", "clipboard", "-o"))
        raise ClipboardUnavailableError("No supported clipboard reader was found on this machine.")

    def _default_write_text(self, text: str) -> None:
        system = platform.system().lower()
        if system == "windows":
            self._run_command(
                ("powershell", "-NoProfile", "-Command", "Set-Clipboard -Value ([Console]::In.ReadToEnd())"),
                input_text=text,
            )
            return
        if system == "darwin":
            self._run_command(("pbcopy",), input_text=text)
            return
        if shutil.which("wl-copy"):
            self._run_command(("wl-copy",), input_text=text)
            return
        if shutil.which("xclip"):
            self._run_command(("xclip", "-selection", "clipboard"), input_text=text)
            return
        raise ClipboardUnavailableError("No supported clipboard writer was found on this machine.")

    def _run_command(self, command: tuple[str, ...], *, input_text: str | None = None) -> str:
        completed = subprocess.run(
            command,
            input=input_text,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            stderr = (completed.stderr or "").strip()
            stdout = (completed.stdout or "").strip()
            detail = stderr or stdout or f"Clipboard command failed with exit code {completed.returncode}."
            raise ClipboardUnavailableError(detail)
        return completed.stdout

    def _normalize_text(self, text: str | None) -> str:
        return str(text or "").replace("\r\n", "\n")

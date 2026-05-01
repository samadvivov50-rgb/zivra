from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.core.config import Settings


class SettingsTests(unittest.TestCase):
    def test_data_dir_can_be_overridden_by_environment(self) -> None:
        with tempfile.TemporaryDirectory() as temp_repo, tempfile.TemporaryDirectory() as temp_data:
            with patch.dict(os.environ, {"ZIVRA_DATA_DIR": temp_data}, clear=False):
                settings = Settings(repo_root=Path(temp_repo))
                settings.ensure_runtime_dirs()

                self.assertEqual(settings.data_dir, Path(temp_data).resolve())
                self.assertEqual(settings.audit_log_path.parent, Path(temp_data).resolve() / "audit")
                self.assertEqual(settings.memory_db_path.parent, Path(temp_data).resolve() / "memory")
                self.assertTrue(settings.preferences_path.parent.exists())
                self.assertEqual(settings.notes_dir, Path(temp_repo) / "notes")


if __name__ == "__main__":
    unittest.main()

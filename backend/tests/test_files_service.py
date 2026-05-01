from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.api.routes.files import browse_folder, list_files, search_files
from app.services.files import WorkspaceFilesService
from app.services.orchestrator import IntentRouter
from app.tools.safe import BrowseFolderTool, SearchFilesTool


class WorkspaceFilesServiceTests(unittest.TestCase):
    def test_list_recent_includes_files_across_approved_roots(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            notes_dir = repo_root / "notes"
            docs_dir = repo_root / "docs"
            notes_dir.mkdir()
            docs_dir.mkdir()

            first = notes_dir / "draft.txt"
            second = docs_dir / "guide.md"
            first.write_text("draft", encoding="utf-8")
            second.write_text("# Guide\n\nship checklist", encoding="utf-8")

            service = WorkspaceFilesService({"notes": notes_dir, "docs": docs_dir}, write_roots=(notes_dir,))
            files = service.list_recent(limit=5)

            self.assertEqual(len(files), 2)
            self.assertEqual({item["root"] for item in files}, {"notes", "docs"})
            self.assertTrue(any(item["writable"] for item in files if item["root"] == "notes"))

    def test_search_matches_name_path_and_text_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            notes_dir = repo_root / "notes"
            docs_dir = repo_root / "docs"
            notes_dir.mkdir()
            docs_dir.mkdir()
            (docs_dir / "roadmap.md").write_text("# Roadmap\n\nphase two file explorer", encoding="utf-8")
            nested = docs_dir / "guides"
            nested.mkdir()
            (nested / "checklist.txt").write_text("launch checklist", encoding="utf-8")

            service = WorkspaceFilesService({"notes": notes_dir, "docs": docs_dir}, write_roots=(notes_dir,))
            files = service.search(query="checklist", limit=5)

            self.assertEqual(len(files), 1)
            self.assertEqual(files[0]["name"], "checklist.txt")
            self.assertIn("launch checklist", files[0]["match_preview"].lower())

    def test_browse_folder_returns_breadcrumbs_and_direct_children(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            notes_dir = repo_root / "notes"
            docs_dir = repo_root / "docs"
            notes_dir.mkdir()
            docs_dir.mkdir()
            guides_dir = docs_dir / "guides"
            guides_dir.mkdir()
            (guides_dir / "checklist.txt").write_text("launch checklist", encoding="utf-8")

            service = WorkspaceFilesService({"notes": notes_dir, "docs": docs_dir}, write_roots=(notes_dir,))
            folder = service.browse_folder("docs/guides")

            self.assertIsNotNone(folder)
            self.assertEqual(folder["root"], "docs")
            self.assertEqual(folder["direct_file_count"], 1)
            self.assertEqual(folder["breadcrumbs"][-1]["label"], "guides")
            self.assertEqual(folder["files"][0]["name"], "checklist.txt")

    def test_browse_folder_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            service = WorkspaceFilesService(
                {"notes": repo_root / "notes", "docs": repo_root / "docs"},
                write_roots=(repo_root / "notes",),
            )

            folder = service.browse_folder("docs/../../secret")

            self.assertIsNone(folder)


class FileToolTests(unittest.TestCase):
    def test_search_files_tool_returns_file_matches(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            notes_dir = repo_root / "notes"
            docs_dir = repo_root / "docs"
            notes_dir.mkdir()
            docs_dir.mkdir()
            (docs_dir / "roadmap.md").write_text("# Roadmap\n\nfile explorer", encoding="utf-8")

            service = WorkspaceFilesService({"notes": notes_dir, "docs": docs_dir}, write_roots=(notes_dir,))
            result = SearchFilesTool(service).execute({"query": "explorer"})

            self.assertTrue(result.success)
            self.assertEqual(result.data["files"][0]["name"], "roadmap.md")

    def test_browse_folder_tool_returns_folder_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            notes_dir = repo_root / "notes"
            docs_dir = repo_root / "docs"
            notes_dir.mkdir()
            docs_dir.mkdir()
            (docs_dir / "roadmap.md").write_text("# Roadmap\n\nfile explorer", encoding="utf-8")

            service = WorkspaceFilesService({"notes": notes_dir, "docs": docs_dir}, write_roots=(notes_dir,))
            result = BrowseFolderTool(service).execute({"folder": "docs"})

            self.assertTrue(result.success)
            self.assertIn("Browsed folder 'docs'", result.message)
            self.assertEqual(result.data["folder"]["direct_file_count"], 1)


class FileRouteTests(unittest.TestCase):
    def test_file_routes_return_search_and_folder_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            request = self._build_request(temp_dir)

            recent = list_files(request, limit=5)
            searched = search_files(request, q="checklist", limit=5)
            folder = browse_folder(request, folder_id="docs")

            self.assertEqual(len(recent["files"]), 2)
            self.assertEqual(searched["files"][0]["name"], "checklist.txt")
            self.assertEqual(folder["folder"]["root"], "docs")

    def _build_request(self, temp_dir: str):
        repo_root = Path(temp_dir)
        notes_dir = repo_root / "notes"
        docs_dir = repo_root / "docs"
        notes_dir.mkdir()
        docs_dir.mkdir()
        (notes_dir / "scratch.txt").write_text("notes scratchpad", encoding="utf-8")
        (docs_dir / "checklist.txt").write_text("launch checklist", encoding="utf-8")
        service = WorkspaceFilesService({"notes": notes_dir, "docs": docs_dir}, write_roots=(notes_dir,))
        state = SimpleNamespace(files_service=service)
        return SimpleNamespace(app=SimpleNamespace(state=state))


class FileRouterTests(unittest.TestCase):
    def test_router_routes_file_search_requests(self) -> None:
        router = IntentRouter()

        route = router.route("Search files for roadmap")

        self.assertEqual(route.tool_name, "search_files")
        self.assertEqual(route.arguments["query"], "roadmap")

    def test_router_routes_folder_browse_requests(self) -> None:
        router = IntentRouter()

        route = router.route("Browse folder docs/guides")

        self.assertEqual(route.tool_name, "browse_folder")
        self.assertEqual(route.arguments["folder"], "docs/guides")


if __name__ == "__main__":
    unittest.main()

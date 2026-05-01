from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

router = APIRouter(prefix="/files", tags=["files"])


@router.get("")
def list_files(request: Request, limit: int = Query(default=12, ge=1, le=50)) -> dict:
    files_service = request.app.state.files_service
    return {
        "files": files_service.list_recent(limit=limit),
        "roots": files_service.list_roots(),
    }


@router.get("/search")
def search_files(request: Request, q: str = "", limit: int = Query(default=12, ge=1, le=50)) -> dict:
    files_service = request.app.state.files_service
    return {
        "files": files_service.search(query=q, limit=limit),
        "roots": files_service.list_roots(),
    }


@router.get("/folder")
def browse_folder(request: Request, folder_id: str = "", limit: int = 16) -> dict:
    files_service = request.app.state.files_service
    folder = files_service.browse_folder(folder_id=folder_id, limit=min(max(int(limit), 1), 50))
    if folder is None:
        raise HTTPException(status_code=404, detail="Folder not found inside approved roots.")

    return {
        "folder": folder,
        "roots": files_service.list_roots(),
    }

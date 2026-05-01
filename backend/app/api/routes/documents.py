from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("")
def list_documents(request: Request, limit: int = Query(default=8, ge=1, le=50)) -> dict:
    documents_service = request.app.state.documents_service
    return {"documents": documents_service.list_recent(limit=limit)}


@router.get("/search")
def search_documents(request: Request, q: str = "", limit: int = Query(default=8, ge=1, le=50)) -> dict:
    documents_service = request.app.state.documents_service
    return {"documents": documents_service.search(query=q, limit=limit)}


@router.get("/read")
def read_document(
    request: Request,
    document_id: str | None = Query(default=None),
    query: str | None = Query(default=None),
) -> dict:
    documents_service = request.app.state.documents_service

    document = None
    if document_id:
        document = documents_service.read_document(document_id)
    elif query:
        document = documents_service.resolve_document(query)

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found inside approved roots.")

    return document


@router.get("/summary")
def summarize_document(
    request: Request,
    document_id: str | None = Query(default=None),
    query: str | None = Query(default=None),
) -> dict:
    documents_service = request.app.state.documents_service
    summary = documents_service.summarize_document(document_id=document_id, query=query)

    if summary is None:
        raise HTTPException(status_code=404, detail="Document not found inside approved roots.")

    return summary


@router.get("/analyze")
def analyze_document(
    request: Request,
    document_id: str | None = Query(default=None),
    query: str | None = Query(default=None),
    filter: str = "",
    schema_path: str = "",
) -> dict:
    documents_service = request.app.state.documents_service
    analysis = documents_service.analyze_document(
        document_id=document_id,
        query=query,
        filter_text=filter or None,
        schema_path=schema_path or None,
    )

    if analysis is None:
        raise HTTPException(status_code=404, detail="Document not found inside approved roots.")
    if analysis.get("analysis") is None:
        raise HTTPException(status_code=400, detail="No lightweight analysis is available for this document view.")

    return analysis


@router.get("/inspect")
def inspect_document(
    request: Request,
    document_id: str | None = Query(default=None),
    query: str | None = Query(default=None),
    filter: str = "",
    limit: int = Query(default=8, ge=1, le=25),
    schema_depth: int = Query(default=2, ge=1, le=4),
    schema_path: str = "",
) -> dict:
    documents_service = request.app.state.documents_service
    inspection = documents_service.inspect_document(
        document_id=document_id,
        query=query,
        filter_text=filter or None,
        limit=limit,
        schema_depth=schema_depth,
        schema_path=schema_path or None,
    )

    if inspection is None:
        raise HTTPException(status_code=404, detail="Document not found inside approved roots.")

    return inspection


@router.get("/export-table")
def export_document_table(
    request: Request,
    document_id: str | None = Query(default=None),
    query: str | None = Query(default=None),
    filter: str = "",
    schema_path: str = "",
) -> dict:
    documents_service = request.app.state.documents_service
    exported = documents_service.export_document_table(
        document_id=document_id,
        query=query,
        filter_text=filter or None,
        schema_path=schema_path or None,
    )

    if exported is None:
        raise HTTPException(status_code=404, detail="Document not found inside approved roots.")
    if exported.get("table") is None:
        raise HTTPException(status_code=400, detail="No tabular export is available for this document view.")

    return exported

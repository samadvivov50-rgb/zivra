from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.services.vision import VisionAnalysisError

router = APIRouter(prefix="/vision", tags=["vision"])


class VisionAnalyzeRequest(BaseModel):
    data_url: str
    filename: str | None = Field(default=None, max_length=256)
    prompt: str | None = Field(default=None, max_length=500)


@router.get("/status")
def read_vision_status(request: Request) -> dict:
    return {"status": request.app.state.vision_service.status()}


@router.post("/analyze")
def analyze_image(payload: VisionAnalyzeRequest, request: Request) -> dict:
    vision_service = request.app.state.vision_service
    try:
        analysis = vision_service.analyze_data_url(
            payload.data_url,
            filename=payload.filename or "",
            prompt=payload.prompt or "",
        )
    except VisionAnalysisError as exc:
        return {
            "message": str(exc),
            "analysis": None,
        }

    model = analysis.get("model", {})
    if model.get("ready") and analysis.get("summary", {}).get("provider") == "openai_compatible":
        message = "Analyzed the screenshot with local metadata plus a multimodal model."
    else:
        message = "Analyzed the screenshot locally from image metadata."
    return {
        "message": message,
        "analysis": analysis,
    }

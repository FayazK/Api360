from __future__ import annotations

from app.services.ai.video.types import VideoGenerationRequest

from .base import BaseGoogleVideoModel


class Veo2ModelService(BaseGoogleVideoModel):
    """Google Veo 2 video generation (silent videos)."""

    def __init__(self) -> None:
        super().__init__(model_id="veo-2.0-generate-001")

    def resolve_model_id(self, request: VideoGenerationRequest) -> str:
        model = (request.model or self.model_id).strip()
        return model or self.model_id


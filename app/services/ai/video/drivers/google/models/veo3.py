from __future__ import annotations

from typing import Optional

from app.services.ai.video.types import VideoGenerationRequest

from .base import BaseGoogleVideoModel


class Veo3ModelService(BaseGoogleVideoModel):
    """Google Veo 3 video generation with fast variation support."""

    fast_model_id = "veo-3.0-fast-generate-001"

    def __init__(self) -> None:
        super().__init__(model_id="veo-3.0-generate-001")

    def resolve_model_id(self, request: VideoGenerationRequest) -> str:
        explicit = (request.model or self.model_id).strip() or self.model_id
        if explicit == self.fast_model_id:
            return explicit

        variation = self._normalize_variation((request.extra or {}).get("variation"))
        if variation == "fast":
            return self.fast_model_id

        return explicit

    def _normalize_variation(self, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        normalized = str(value).lower().strip()
        if normalized in {"fast", "veo3-fast", "veo-3-fast", "fast-track"}:
            return "fast"
        if normalized in {"standard", "default", "veo3"}:
            return "standard"
        return normalized or None


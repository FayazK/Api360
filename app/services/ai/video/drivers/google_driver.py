from __future__ import annotations

from typing import Dict, Optional

try:
    from google import genai
except Exception:  # pragma: no cover - optional dependency
    genai = None  # type: ignore

from app.services.ai.video.types import VideoGenerationRequest, VideoGenerationResult
from .base_driver import BaseVideoDriver
from .google.registry import GoogleVideoModelRegistry


class GoogleVideoDriver(BaseVideoDriver):
    """Google Gemini/Veo video driver."""

    provider = "gemini"
    default_model = "veo-2.0-generate-001"

    def __init__(self, config: Optional[Dict[str, object]] = None) -> None:
        super().__init__(config=config)
        if genai is None:
            raise ImportError(
                "google-genai is not installed. Install with: pip install google-genai"
            )
        self._client = genai.Client()

    def generate(self, request: VideoGenerationRequest) -> VideoGenerationResult:
        model_id = (request.model or self.default_model or "").strip()
        if not model_id:
            raise ValueError("Gemini video driver requires a model to be specified")

        service = GoogleVideoModelRegistry.get_model_service(model_id)
        if not service:
            supported = ", ".join(GoogleVideoModelRegistry.supported_models().keys())
            raise ValueError(
                f"Model '{model_id}' is not supported by Gemini video driver. Supported: {supported}"
            )

        result = service.generate(self._client, request)
        self._store_metadata(model=result.model, provider=self.provider)
        return result


# Register driver with factory
from app.services.ai.video.factory import VideoDriverFactory

VideoDriverFactory.register(GoogleVideoDriver)

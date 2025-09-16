from __future__ import annotations

from typing import Dict, Optional

from app.services.ai.video.types import VideoGenerationRequest, VideoGenerationResult
from .base_driver import BaseVideoDriver
from .replicate.registry import ReplicateVideoModelRegistry


class ReplicateVideoDriver(BaseVideoDriver):
    provider = "replicate"
    default_model = "runwayml/gen2"

    def __init__(self, config: Optional[Dict[str, object]] = None) -> None:
        super().__init__(config=config)

    def generate(self, request: VideoGenerationRequest) -> VideoGenerationResult:
        model_id = request.model or self.default_model
        driver = ReplicateVideoModelRegistry.get_driver(model_id)
        if not driver:
            supported = ", ".join(ReplicateVideoModelRegistry.list_models().keys())
            raise ValueError(
                f"Model '{model_id}' not supported by Replicate video driver. Supported: {supported}"
            )

        result = driver.generate(request)
        self._store_metadata(model=result.model, provider=self.provider)
        return result


from app.services.ai.video.factory import VideoDriverFactory

VideoDriverFactory.register(ReplicateVideoDriver)

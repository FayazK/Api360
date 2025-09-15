from __future__ import annotations

from typing import Any, Dict, Optional

from app.services.ai.image.factory import ImageDriver, ImageDriverFactory
from app.services.ai.image.types import (
    ImageGenerationRequest,
    ImageGenerationResult,
)

from .replicate.registry import ReplicateModelRegistry


class ReplicateImageDriver(ImageDriver):
    """Model-specific Replicate image generation driver.

    This driver only supports models with dedicated implementations. Each model
    has precise parameter mapping and validation for reliable generation.

    Supported models:
      - bytedance/seedream-4: Advanced text-to-image and editing up to 4K
      - black-forest-labs/flux-krea-dev: Distinctive aesthetic style and realism

    Aliases supported:
      - seedream-4, seedream4 → bytedance/seedream-4
      - flux-krea-dev, flux-krea, krea-dev → black-forest-labs/flux-krea-dev
    """

    provider = "replicate"
    default_model = "bytedance/seedream-4"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self._model_drivers = {}

    def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        model_id = request.model or self.default_model
        
        # Get model-specific driver
        driver = self._get_model_driver(model_id)
        if not driver:
            supported_models = list(ReplicateModelRegistry.get_supported_models())
            raise ValueError(
                f"Model '{model_id}' is not supported. "
                f"Supported models: {', '.join(supported_models)}"
            )
        
        return driver.generate(request)
    
    def _get_model_driver(self, model_id: str) -> Optional[Any]:
        """Get cached model-specific driver for the given model ID."""
        # Cache drivers to avoid recreating them
        if model_id not in self._model_drivers:
            driver_class = ReplicateModelRegistry.get_driver_class(model_id)
            if driver_class:
                try:
                    self._model_drivers[model_id] = driver_class()
                except Exception as e:
                    raise RuntimeError(f"Failed to initialize driver for {model_id}: {e}")
            else:
                return None
        
        return self._model_drivers.get(model_id)
    
    def get_supported_models(self) -> Dict[str, str]:
        """Get list of all supported models and their driver information."""
        models = {}
        for model_id, info in ReplicateModelRegistry.list_models().items():
            models[model_id] = info['driver_class']
        return models
    
    def is_model_supported(self, model_id: str) -> bool:
        """Check if a model is supported."""
        return ReplicateModelRegistry.is_supported(model_id)


# Register driver on import
ImageDriverFactory.register(ReplicateImageDriver)

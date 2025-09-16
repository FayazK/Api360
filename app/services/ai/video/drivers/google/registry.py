from __future__ import annotations

from typing import Dict, Optional, Type

from .models.base import BaseGoogleVideoModel
from .models.veo2 import Veo2ModelService
from .models.veo3 import Veo3ModelService


class GoogleVideoModelRegistry:
    """Registry mapping Veo model identifiers to service classes."""

    _model_classes: Dict[str, Type[BaseGoogleVideoModel]] = {
        "veo-2.0-generate-001": Veo2ModelService,
        "veo-3.0-generate-001": Veo3ModelService,
        "veo-3.0-fast-generate-001": Veo3ModelService,
    }

    _aliases: Dict[str, str] = {
        "veo2": "veo-2.0-generate-001",
        "veo3": "veo-3.0-generate-001",
        "veo3-fast": "veo-3.0-fast-generate-001",
        "veo-3-fast": "veo-3.0-fast-generate-001",
    }

    @classmethod
    def get_model_service(cls, model_id: str) -> Optional[BaseGoogleVideoModel]:
        canonical = cls._aliases.get(model_id, model_id)
        service_cls = cls._model_classes.get(canonical)
        if not service_cls:
            return None
        return service_cls()

    @classmethod
    def supported_models(cls) -> Dict[str, Type[BaseGoogleVideoModel]]:
        return dict(cls._model_classes)


from __future__ import annotations

from typing import Dict, Optional, Type

from .base import BaseReplicateVideoDriver
from .models.gen2 import RunwayGen2Driver
from .models.seedance_1_pro import Seedance1ProDriver


class ReplicateVideoModelRegistry:
    """Registry for Replicate video models."""

    _model_classes: Dict[str, Type[BaseReplicateVideoDriver]] = {
        "runwayml/gen2": RunwayGen2Driver,
        "bytedance/seedance-1-pro": Seedance1ProDriver,
    }

    _aliases: Dict[str, str] = {
        "gen2": "runwayml/gen2",
        "runway-gen2": "runwayml/gen2",
        "seedance": "bytedance/seedance-1-pro",
        "seedance-1-pro": "bytedance/seedance-1-pro",
    }

    @classmethod
    def get_driver(cls, model_id: str) -> Optional[BaseReplicateVideoDriver]:
        canonical = cls._aliases.get(model_id, model_id)
        driver_cls = cls._model_classes.get(canonical)
        if not driver_cls:
            return None
        return driver_cls()

    @classmethod
    def list_models(cls) -> Dict[str, Type[BaseReplicateVideoDriver]]:
        return dict(cls._model_classes)

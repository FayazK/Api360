from __future__ import annotations

from typing import Any, Dict, Optional, Type

from app.config.video_models import get_video_models_config
from .types import VideoGenerationRequest


class VideoDriver:
    """Abstract base for video generation drivers."""

    provider: str = ""
    default_model: str = ""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:  # pragma: no cover - base
        self.config: Dict[str, Any] = config or {}
        yaml_default = self.config.get("default_model")
        if isinstance(yaml_default, str) and yaml_default.strip():
            self.default_model = yaml_default.strip()

    def generate(self, request: VideoGenerationRequest):  # pragma: no cover - interface
        raise NotImplementedError


class VideoDriverFactory:
    """Registry/factory for video drivers."""

    _registry: Dict[str, Type[VideoDriver]] = {}

    @classmethod
    def register(cls, driver_cls: Type[VideoDriver]) -> None:
        key = getattr(driver_cls, "provider", "").strip().lower()
        if not key:
            raise ValueError("Video driver must define non-empty `provider`.")
        cls._registry[key] = driver_cls

    @classmethod
    def has_provider(cls, provider: str) -> bool:
        return provider.lower() in cls._registry

    @classmethod
    def get(cls, provider: str) -> VideoDriver:
        key = provider.lower().strip()
        if key not in cls._registry:
            raise KeyError(f"No video driver registered for provider '{provider}'.")

        cfg = get_video_models_config()
        providers_cfg = (cfg or {}).get("providers", {}) or {}
        provider_cfg = providers_cfg.get(key) or {}
        return cls._registry[key](config=provider_cfg)

    @classmethod
    def providers(cls):
        return sorted(cls._registry.keys())


# Import drivers for side-effect registrations
try:  # pragma: no cover - import side effects only
    from . import drivers  # noqa: F401
except Exception:  # pragma: no cover - defensive
    pass


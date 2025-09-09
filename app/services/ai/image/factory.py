from __future__ import annotations

from typing import Dict, Optional, Type

from .types import ImageGenerationRequest


class ImageDriver:
    """Abstract base protocol for image drivers.

    Concrete drivers should subclass this and implement `generate`.
    """

    # Human-friendly provider name, e.g., "gemini", "imagen", "dalle".
    provider: str = ""
    # A sensible default model for this driver (driver-level default).
    default_model: str = ""

    def generate(self, request: ImageGenerationRequest):  # pragma: no cover - interface
        raise NotImplementedError


class ImageDriverFactory:
    """Factory/registry for image generation drivers.

    Drivers register themselves (or via module import side effects). The
    factory returns an instantiated driver by provider key.
    """

    _registry: Dict[str, Type[ImageDriver]] = {}

    @classmethod
    def register(cls, driver_cls: Type[ImageDriver]) -> None:
        key = getattr(driver_cls, "provider", "").strip().lower()
        if not key:
            raise ValueError("Image driver must define non-empty `provider`.")
        cls._registry[key] = driver_cls

    @classmethod
    def has_provider(cls, provider: str) -> bool:
        return provider.lower() in cls._registry

    @classmethod
    def get(cls, provider: str) -> ImageDriver:
        key = provider.lower().strip()
        if key not in cls._registry:
            raise KeyError(f"No image driver registered for provider '{provider}'.")
        return cls._registry[key]()

    @classmethod
    def providers(cls):
        return sorted(cls._registry.keys())


# Ensure `drivers` package is imported so any side-effect registrations happen.
try:  # pragma: no cover - import side-effect only
    from . import drivers  # noqa: F401
except Exception:
    # Import errors should not break the app at import time; drivers will be
    # resolved when actually requested.
    pass


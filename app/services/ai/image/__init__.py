"""
Image generation service scaffolding.

This package provides a provider-agnostic image generation engine with a
pluggable driver architecture. Routes and services should depend on the
engine or the unified request/response types defined here, not on specific
providers.
"""

from .base import ImageEngine, ImageGenerationError
from .types import (
    ImageGenerationRequest,
    ImageGenerationResult,
    GeneratedImage,
)

__all__ = [
    "ImageEngine",
    "ImageGenerationError",
    "ImageGenerationRequest",
    "ImageGenerationResult",
    "GeneratedImage",
]


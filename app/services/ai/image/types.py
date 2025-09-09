from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ImageGenerationRequest:
    """Unified request for image generation across providers.

    Required:
      - prompt: main text prompt

    Optional (forwarded only if explicitly set by caller):
      - provider: explicit provider key to use (e.g., "gemini", "imagen")
      - model: provider-specific model name
      - seed, width, height, ratio, num_images, steps, guidance_scale, quality
      - negative_prompt, stop, safety, user, template_variables
      - image_inputs: list of initial images (bytes) for img2img/inpainting
      - mask: optional mask image (bytes) for inpainting workflows
      - extra: arbitrary provider-specific params to pass through

    The service must never invent defaults for unset optionals; the selected
    driver and provider should apply their defaults.
    """

    prompt: str

    # Provider selection
    provider: Optional[str] = None
    model: Optional[str] = None

    # Common generation controls
    seed: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    ratio: Optional[str] = None  # e.g., "1:1", "16:9"
    num_images: Optional[int] = None
    steps: Optional[int] = None
    guidance_scale: Optional[float] = None  # CFG
    quality: Optional[str] = None  # e.g., "high", "draft"
    negative_prompt: Optional[str] = None
    stop: Optional[List[str]] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None

    # Image-to-image / inpainting
    image_inputs: Optional[List[bytes]] = None
    mask: Optional[bytes] = None

    # Misc
    system_prompt: Optional[str] = None
    safety: Optional[Dict[str, Any]] = None
    user: Optional[str] = None
    template_variables: Optional[Dict[str, Any]] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeneratedImage:
    """A single unified generated image representation.

    At least one of (b64_data, url, path) should be provided by a driver.
    The engine normalizes to ensure downstream consumers can rely on b64_data
    and mime_type when possible.
    """

    b64_data: Optional[str] = None
    mime_type: Optional[str] = None
    url: Optional[str] = None
    path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ImageGenerationResult:
    provider: str
    model: str
    images: List[GeneratedImage]
    metadata: Dict[str, Any] = field(default_factory=dict)

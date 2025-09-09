from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class ImageGenImage(BaseModel):
    b64_data: Optional[str] = Field(None, description="Base64-encoded image data")
    mime_type: Optional[str] = Field(None, description="MIME type of the image")
    url: Optional[str] = Field(None, description="URL to the stored image, if applicable")
    path: Optional[str] = Field(None, description="Filesystem path, if applicable")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Driver-provided metadata for this image")


class ImageGenerationAPIRequest(BaseModel):
    """API request for image generation or editing.

    Only `prompt` is required. Optional fields are passed through to the image
    engine and driver only if explicitly provided.
    """

    prompt: str = Field(..., min_length=1, description="Main text prompt")

    # Provider/model selection
    provider: Optional[str] = Field(None, description="Image provider key (e.g., 'gemini-nano-banana')")
    model: Optional[str] = Field(None, description="Model name to use; defaults to driver/provider default")

    # Generation controls
    ratio: Optional[str] = Field(None, description="Aspect ratio guidance (e.g., '1:1', '16:9', '4:5')")
    negative_prompt: Optional[str] = Field(None, description="What to avoid in the image")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Creativity/variation control")
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    stop_sequences: Optional[List[str]] = Field(None, description="Stop sequences for generation (if supported)")

    # Context & safety
    system_prompt: Optional[str] = Field(None, description="Global style/guardrails for the request")
    safety: Optional[Dict[str, Any]] = Field(None, description="Safety settings structure passed to provider")

    # Optional images as base64 strings for image→image or multi-image fusion
    images_b64: Optional[List[str]] = Field(None, description="Input images as base64 strings")

    # Provider-specific passthrough
    extra: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Arbitrary provider-specific parameters")


class ImageGenerationAPIResponse(BaseModel):
    provider: str
    model: str
    images: List[ImageGenImage]
    metadata: Dict[str, Any] = Field(default_factory=dict)


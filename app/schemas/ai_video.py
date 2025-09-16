from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class VideoGenVideo(BaseModel):
    url: Optional[str] = Field(None, description="Accessible URL for the generated video")
    path: Optional[str] = Field(None, description="Filesystem path for the stored video")
    mime_type: Optional[str] = Field(None, description="MIME type such as video/mp4")
    duration_seconds: Optional[float] = Field(None, description="Duration of the clip in seconds")
    width: Optional[int] = Field(None, description="Frame width in pixels")
    height: Optional[int] = Field(None, description="Frame height in pixels")
    size_bytes: Optional[int] = Field(None, description="Approximate size of the video in bytes")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Provider-supplied metadata")


class VideoGenerationAPIRequest(BaseModel):
    """Video generation API request. Only `prompt` is required."""

    prompt: str = Field(..., min_length=1, description="Primary text prompt")

    # Provider/model selection
    provider: Optional[str] = Field(None, description="Video provider key (e.g., 'gemini')")
    model: Optional[str] = Field(None, description="Provider model identifier")

    # Video tuning
    duration_seconds: Optional[float] = Field(None, gt=0, description="Requested clip length")
    fps: Optional[int] = Field(None, gt=0, description="Frames per second")
    aspect_ratio: Optional[str] = Field(None, description="Aspect ratio such as '16:9'")
    resolution: Optional[str] = Field(None, description="Requested resolution label (e.g., '1080p')")
    negative_prompt: Optional[str] = Field(None, description="Content to avoid in generation")
    seed: Optional[int] = Field(None, ge=0, description="Seed to encourage repeatability")

    # Audio controls
    audio: Optional[Dict[str, Any]] = Field(None, description="Audio generation controls (e.g., enable/disable)")

    # Optional template context & system prompt bridging to internal engines
    system_prompt: Optional[str] = Field(None, description="System-level guidance for provider")
    template_variables: Optional[Dict[str, Any]] = Field(None, description="Template variables expanded server-side")

    # Provider passthrough
    extra: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Arbitrary provider-specific parameters")

    # Optional base64 inputs for JSON requests
    images_b64: Optional[List[str]] = Field(None, description="Seed images encoded as base64 strings")
    videos_b64: Optional[List[str]] = Field(None, description="Seed videos encoded as base64 strings")


class VideoGenerationAPIResponse(BaseModel):
    provider: str
    model: str
    videos: List[VideoGenVideo]
    metadata: Dict[str, Any] = Field(default_factory=dict)

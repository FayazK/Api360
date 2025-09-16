from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class VideoGenerationRequest:
    """Unified request for video generation.

    Only `prompt` is required; other parameters are forwarded only when
    explicitly provided so drivers can rely on provider defaults.
    """

    prompt: str

    # Provider/model selection
    provider: Optional[str] = None
    model: Optional[str] = None

    # Common video controls
    duration_seconds: Optional[float] = None
    fps: Optional[int] = None
    aspect_ratio: Optional[str] = None
    resolution: Optional[str] = None
    negative_prompt: Optional[str] = None
    seed: Optional[int] = None

    # Audio controls (e.g., enable/disable native audio, voiceover prompts)
    audio: Optional[Dict[str, Any]] = None

    # Optional media inputs
    image_inputs: Optional[List[bytes]] = None
    video_inputs: Optional[List[bytes]] = None

    # Context
    template_variables: Optional[Dict[str, Any]] = None
    system_prompt: Optional[str] = None

    # Provider specific passthrough
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeneratedVideo:
    """Representation of a generated video asset."""

    url: Optional[str] = None
    path: Optional[str] = None
    mime_type: Optional[str] = None
    duration_seconds: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    size_bytes: Optional[int] = None
    b64_data: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VideoGenerationResult:
    provider: str
    model: str
    videos: List[GeneratedVideo]
    metadata: Dict[str, Any] = field(default_factory=dict)


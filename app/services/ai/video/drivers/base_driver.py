from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ..factory import VideoDriver
from ..types import VideoGenerationRequest, VideoGenerationResult


class BaseVideoDriver(VideoDriver, ABC):
    """Base class for all video generation drivers."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config=config)
        self._metadata: Dict[str, Any] = {}

    @abstractmethod
    def generate(self, request: VideoGenerationRequest) -> VideoGenerationResult:
        """Generate a video for the supplied request."""

    def _collect_metadata(self) -> Dict[str, Any]:
        """Return metadata about the last request, if recorded."""
        return dict(self._metadata)

    def _store_metadata(self, **details: Any) -> None:
        self._metadata = {k: v for k, v in details.items() if v is not None}


from __future__ import annotations

import base64
from typing import Any, Dict, List, Optional

from .factory import VideoDriverFactory
from .types import GeneratedVideo, VideoGenerationRequest, VideoGenerationResult


class VideoGenerationError(RuntimeError):
    """Raised when a video generation request cannot be fulfilled."""


class VideoEngine:
    """Provider-agnostic orchestration for video generation."""

    def __init__(self, default_provider: Optional[str] = None) -> None:
        self.default_provider = (default_provider or "").strip() or None

    def generate(self, request: VideoGenerationRequest) -> VideoGenerationResult:
        provider = (request.provider or self.default_provider or "").strip()
        if not provider:
            raise VideoGenerationError(
                "No provider specified. Pass `provider` or configure a default."
            )

        try:
            driver = VideoDriverFactory.get(provider)
        except KeyError as exc:
            raise VideoGenerationError(str(exc)) from exc

        raw_result = driver.generate(request)
        return self._normalize_result(
            raw=raw_result,
            provider=provider,
            request_model=request.model,
            driver_default_model=getattr(driver, "default_model", ""),
        )

    # --- helpers ---------------------------------------------------------

    def _normalize_result(
        self,
        raw: Any,
        provider: str,
        request_model: Optional[str],
        driver_default_model: str,
    ) -> VideoGenerationResult:
        if isinstance(raw, VideoGenerationResult):
            return raw

        if isinstance(raw, dict):
            videos_payload = raw.get("videos", [])
            videos = self._coerce_videos(videos_payload)
            model = raw.get("model") or request_model or driver_default_model or ""
            metadata: Dict[str, Any] = raw.get("metadata", {}) or {}
            return VideoGenerationResult(provider=provider, model=model, videos=videos, metadata=metadata)

        if isinstance(raw, list):
            videos = self._coerce_videos(raw)
            model = request_model or driver_default_model or ""
            return VideoGenerationResult(provider=provider, model=model, videos=videos, metadata={})

        model = request_model or driver_default_model or ""
        return VideoGenerationResult(
            provider=provider,
            model=model,
            videos=[],
            metadata={"raw": raw},
        )

    def _coerce_videos(self, payload: Any) -> List[GeneratedVideo]:
        videos: List[GeneratedVideo] = []
        for item in payload or []:
            if isinstance(item, GeneratedVideo):
                videos.append(item)
                continue
            if isinstance(item, dict):
                videos.append(
                    GeneratedVideo(
                        url=item.get("url"),
                        path=item.get("path"),
                        mime_type=item.get("mime_type"),
                        duration_seconds=item.get("duration_seconds"),
                        width=item.get("width"),
                        height=item.get("height"),
                        size_bytes=item.get("size_bytes"),
                        b64_data=item.get("b64_data"),
                        metadata=item.get("metadata", {}) or {},
                    )
                )
                continue
            if isinstance(item, (bytes, bytearray)):
                videos.append(
                    GeneratedVideo(
                        b64_data=base64.b64encode(item).decode("utf-8"),
                        mime_type="video/mp4",
                    )
                )
                continue
            videos.append(GeneratedVideo(metadata={"raw": item}))
        return videos


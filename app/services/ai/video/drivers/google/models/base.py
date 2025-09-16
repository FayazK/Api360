from __future__ import annotations

import base64
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Optional

try:
    from google import genai
    from google.genai import types as genai_types
except Exception:  # pragma: no cover - optional dependency
    genai = None  # type: ignore
    genai_types = None  # type: ignore

from app.services.ai.video.types import GeneratedVideo, VideoGenerationRequest, VideoGenerationResult


class BaseGoogleVideoModel(ABC):
    """Shared helpers for Google/Gemini Veo models."""

    poll_interval_seconds: float = 5.0
    max_poll_attempts: int = 60  # 5 minutes default

    def __init__(self, model_id: str) -> None:
        self.model_id = model_id

        if genai is None or genai_types is None:
            raise ImportError(
                "google-genai is required for Gemini video generation."
            )

    @abstractmethod
    def resolve_model_id(self, request: VideoGenerationRequest) -> str:
        """Return concrete model identifier to send to the API."""

    def generate(self, client: "genai.Client", request: VideoGenerationRequest) -> VideoGenerationResult:
        resolved_model = self.resolve_model_id(request)
        api_params = self._build_api_params(resolved_model, request)

        operation = client.models.generate_videos(**api_params)
        final_operation = self._wait_for_completion(client, operation)

        videos = self._extract_videos(client, final_operation)
        metadata = self._build_metadata(final_operation, api_params)

        return VideoGenerationResult(
            provider="gemini",
            model=resolved_model,
            videos=videos,
            metadata=metadata,
        )

    def _build_api_params(
        self,
        model: str,
        request: VideoGenerationRequest,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "model": model,
            "prompt": request.prompt,
        }

        config_kwargs: Dict[str, Any] = {}
        if request.negative_prompt:
            config_kwargs["negative_prompt"] = request.negative_prompt
        if request.aspect_ratio:
            config_kwargs["aspect_ratio"] = request.aspect_ratio
        if request.resolution:
            config_kwargs["resolution"] = request.resolution
        if request.duration_seconds is not None:
            config_kwargs["duration_seconds"] = request.duration_seconds
        if request.fps is not None:
            config_kwargs["fps"] = request.fps
        if request.seed is not None:
            config_kwargs["seed"] = request.seed
        if request.audio:
            config_kwargs["audio_config"] = request.audio

        # Allow callers to override config/dynamic params via `extra`
        extra = request.extra or {}
        if isinstance(extra.get("config"), dict):
            config_kwargs.update(extra["config"])
        if isinstance(extra.get("api_params"), dict):
            for key, value in extra["api_params"].items():
                if key not in params:
                    params[key] = value

        if config_kwargs:
            params["config"] = genai_types.GenerateVideosConfig(**config_kwargs)

        if request.system_prompt:
            params["system_instruction"] = request.system_prompt

        # Support first image/video inputs for img2img / video2video
        if request.image_inputs:
            params["image"] = genai_types.Part.from_bytes(
                data=request.image_inputs[0],
                mime_type="image/png",
            )
        if request.video_inputs:
            params["video"] = genai_types.Part.from_bytes(
                data=request.video_inputs[0],
                mime_type="video/mp4",
            )

        return params

    def _wait_for_completion(self, client: "genai.Client", operation: Any) -> Any:
        attempts = 0

        current = operation
        while not getattr(current, "done", False):
            attempts += 1
            if attempts > self.max_poll_attempts:
                raise TimeoutError("Video generation timed out waiting for completion")
            time.sleep(self.poll_interval_seconds)
            current = client.operations.get(current)

        return current

    def _extract_videos(self, client: "genai.Client", operation: Any) -> List[GeneratedVideo]:
        response = getattr(operation, "response", None)
        generated: Iterable[Any] = getattr(response, "generated_videos", []) if response else []
        videos: List[GeneratedVideo] = []

        for entry in generated:
            video_asset = getattr(entry, "video", None)
            url = None
            size_bytes = getattr(entry, "size_bytes", None)
            duration_sec = getattr(entry, "duration_seconds", None)
            width = getattr(entry, "width", None)
            height = getattr(entry, "height", None)
            metadata: Dict[str, Any] = {}

            if video_asset is not None:
                url = getattr(video_asset, "uri", None) or getattr(video_asset, "download_uri", None)
                metadata["video_name"] = getattr(video_asset, "name", None)
            else:
                metadata["raw_entry"] = entry

            b64_data: Optional[str] = None
            try:
                if video_asset is not None:
                    download = client.files.download(file=video_asset)
                    data = getattr(download, "content", None)
                    if data is None and hasattr(download, "read"):
                        data = download.read()
                    if data:
                        b64_data = base64.b64encode(data).decode("utf-8")
                        if size_bytes is None:
                            size_bytes = len(data)
            except Exception:
                # Download failures should not abort the request; fall back to provider link.
                pass

            videos.append(
                GeneratedVideo(
                    url=url,
                    mime_type="video/mp4",
                    duration_seconds=duration_sec,
                    width=width,
                    height=height,
                    size_bytes=size_bytes,
                    b64_data=b64_data,
                    metadata=metadata,
                )
            )

        return videos

    def _build_metadata(self, operation: Any, api_params: Dict[str, Any]) -> Dict[str, Any]:
        metadata: Dict[str, Any] = {
            "operation_name": getattr(operation, "name", None),
            "model": api_params.get("model"),
        }
        if "config" in api_params:
            config_obj = api_params["config"]
            try:
                metadata["parameters"] = {
                    key: getattr(config_obj, key)
                    for key in dir(config_obj)
                    if not key.startswith("_") and not callable(getattr(config_obj, key))
                }
            except Exception:
                metadata["parameters"] = {}
        else:
            metadata["parameters"] = {}
        return metadata


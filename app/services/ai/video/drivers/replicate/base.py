"""Base utilities for Replicate video drivers."""

from __future__ import annotations

import base64
import json
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings
from app.services.ai.video.types import (
    GeneratedVideo,
    VideoGenerationRequest,
    VideoGenerationResult,
)
from app.services.ai.video.factory import VideoDriver


class BaseReplicateVideoDriver(VideoDriver, ABC):
    provider = "replicate"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config=config)
        if not settings.REPLICATE_API_TOKEN:
            raise ValueError("REPLICATE_API_TOKEN environment variable is required")

        self._client = httpx.Client(
            base_url="https://api.replicate.com/v1",
            headers={
                "Authorization": f"Token {settings.REPLICATE_API_TOKEN}",
                "Content-Type": "application/json",
            },
            timeout=180.0,
        )

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Replicate model name (e.g., 'runwayml/gen2')."""

    @property
    def model_version(self) -> Optional[str]:
        return None

    @abstractmethod
    def map_parameters(self, request: VideoGenerationRequest) -> Dict[str, Any]:
        """Map unified request into model-specific parameters."""

    @abstractmethod
    def validate_parameters(self, params: Dict[str, Any]) -> None:
        """Validate mapped params against schema/constraints."""

    def generate(self, request: VideoGenerationRequest) -> VideoGenerationResult:
        mapped = self.map_parameters(request)
        self.validate_parameters(mapped)

        version_id = self.model_version or self._resolve_model_version()
        if not version_id:
            raise RuntimeError(f"Unable to resolve version for Replicate model '{self.model_id}'")

        prediction_payload = {
            "version": version_id,
            "input": mapped,
        }

        response = self._client.post("/predictions", json=prediction_payload)
        if response.status_code != 201:
            self._raise_api_error(response)

        prediction = response.json()
        prediction_id = prediction.get("id")

        result = self._poll_prediction(prediction_id)
        output = self._normalize_output(result.get("output"))

        metadata = {
            "prediction_id": prediction_id,
            "model": self.model_id,
            "parameters": {k: v for k, v in mapped.items() if not self._is_binary(v)},
        }

        return VideoGenerationResult(
            provider=self.provider,
            model=self.model_id,
            videos=output,
            metadata=metadata,
        )

    # --- internal helpers -------------------------------------------------

    def _resolve_model_version(self) -> Optional[str]:
        try:
            resp = self._client.get(f"/models/{self.model_id}")
            if resp.status_code == 200:
                data = resp.json() or {}
                latest = data.get("latest_version") or data.get("default_version") or {}
                if isinstance(latest, dict):
                    version = latest.get("id")
                    if version:
                        return version
        except Exception:
            pass

        try:
            resp = self._client.get(f"/models/{self.model_id}/versions")
            if resp.status_code == 200:
                data = resp.json() or {}
                versions = data.get("results") or data.get("versions") or []
                if versions:
                    candidate = versions[0]
                    if isinstance(candidate, dict):
                        version = candidate.get("id")
                        if version:
                            return version
        except Exception:
            pass

        return None

    def _poll_prediction(self, prediction_id: str) -> Dict[str, Any]:
        max_wait_seconds = 5 * 60
        interval = 3
        waited = 0

        while waited <= max_wait_seconds:
            response = self._client.get(f"/predictions/{prediction_id}")
            if response.status_code != 200:
                self._raise_api_error(response)
            payload = response.json() or {}
            status = payload.get("status")
            if status == "succeeded":
                return payload
            if status in {"failed", "canceled", "cancelled"}:
                raise RuntimeError(payload.get("error", "Replicate prediction failed"))

            time.sleep(interval)
            waited += interval

        raise TimeoutError("Replicate prediction timed out")

    def _normalize_output(self, output: Any) -> List[GeneratedVideo]:
        if not output:
            return []

        videos: List[GeneratedVideo] = []

        def to_video(item: Any) -> GeneratedVideo:
            if isinstance(item, dict):
                url = item.get("url") or item.get("uri")
                mime = item.get("mime_type") or "video/mp4"
                metadata = {k: v for k, v in item.items() if k not in {"url", "uri", "mime_type", "data"}}
                b64 = None
                data = item.get("data")
                if isinstance(data, (bytes, bytearray)):
                    b64 = base64.b64encode(data).decode("utf-8")
                elif isinstance(data, str) and data.startswith("data:"):
                    b64 = data.split(",", 1)[-1]
                return GeneratedVideo(url=url, mime_type=mime, b64_data=b64, metadata=metadata)
            if isinstance(item, str):
                return GeneratedVideo(url=item, mime_type="video/mp4", metadata={})
            if isinstance(item, (bytes, bytearray)):
                return GeneratedVideo(
                    mime_type="video/mp4",
                    b64_data=base64.b64encode(item).decode("utf-8"),
                )
            return GeneratedVideo(metadata={"raw": item})

        if isinstance(output, list):
            for entry in output:
                videos.append(to_video(entry))
        else:
            videos.append(to_video(output))

        return videos

    def _raise_api_error(self, response: httpx.Response) -> None:
        try:
            payload = response.json()
            message = payload.get("error") or payload
        except Exception:
            message = response.text
        raise RuntimeError(f"Replicate API error ({response.status_code}): {message}")

    def _is_binary(self, value: Any) -> bool:
        if isinstance(value, (bytes, bytearray)):
            return True
        if isinstance(value, str) and value.startswith("data:"):
            return True
        return False

    # Utility helper for converting bytes to data URL for API submission
    def bytes_to_data_uri(self, data: bytes, mime_type: str = "video/mp4") -> str:
        encoded = base64.b64encode(data).decode("utf-8")
        return f"data:{mime_type};base64,{encoded}"

    def load_schema(self, schema_path: str) -> Dict[str, Any]:
        with open(schema_path, "r", encoding="utf-8") as handle:
            return json.load(handle)

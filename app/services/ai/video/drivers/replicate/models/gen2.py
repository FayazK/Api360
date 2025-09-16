from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from app.services.ai.video.types import VideoGenerationRequest

from ..base import BaseReplicateVideoDriver


class RunwayGen2Driver(BaseReplicateVideoDriver):
    """Replicate driver for runwayml/gen2."""

    default_model = "runwayml/gen2"

    def __init__(self) -> None:
        super().__init__()
        schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "schemas", "runway_gen2.json")
        self._schema = self.load_schema(schema_path)

    @property
    def model_id(self) -> str:
        return self.default_model

    def map_parameters(self, request: VideoGenerationRequest) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "prompt": request.prompt,
        }

        if request.negative_prompt:
            params["negative_prompt"] = request.negative_prompt
        if request.aspect_ratio:
            params["aspect_ratio"] = request.aspect_ratio
        if request.duration_seconds is not None:
            params["duration"] = request.duration_seconds
        if request.seed is not None:
            params["seed"] = request.seed
        if request.audio:
            params["audio"] = request.audio

        image_inputs = self._prepare_image_inputs(request.image_inputs)
        if image_inputs:
            params["image"] = image_inputs[0]
        video_inputs = self._prepare_video_inputs(request.video_inputs)
        if video_inputs:
            params["input_video"] = video_inputs[0]

        # Allow caller extras to override or extend parameters
        for key, value in (request.extra or {}).items():
            if key not in params:
                params[key] = value

        return params

    def validate_parameters(self, params: Dict[str, Any]) -> None:
        properties = self._schema.get("properties", {})
        required = self._schema.get("required", [])

        for field in required:
            if field not in params:
                raise ValueError(f"'{field}' is required for runwayml/gen2")

        for key, value in params.items():
            schema = properties.get(key)
            if not schema:
                continue
            expected_type = schema.get("type")
            if expected_type == "string" and not isinstance(value, str):
                raise ValueError(f"Parameter '{key}' must be a string")
            if expected_type == "number" and not isinstance(value, (int, float)):
                raise ValueError(f"Parameter '{key}' must be numeric")
            if expected_type == "integer" and not isinstance(value, int):
                raise ValueError(f"Parameter '{key}' must be an integer")

            if "enum" in schema and value not in schema["enum"]:
                valid = ", ".join(schema["enum"])
                raise ValueError(f"Parameter '{key}' must be one of: {valid}")

    def _prepare_image_inputs(self, inputs: Optional[List[bytes]]) -> List[str]:
        results: List[str] = []
        if not inputs:
            return results
        for blob in inputs:
            if isinstance(blob, (bytes, bytearray)):
                results.append(self.bytes_to_data_uri(bytes(blob), mime_type="image/png"))
        return results

    def _prepare_video_inputs(self, inputs: Optional[List[bytes]]) -> List[str]:
        results: List[str] = []
        if not inputs:
            return results
        for blob in inputs:
            if isinstance(blob, (bytes, bytearray)):
                results.append(self.bytes_to_data_uri(bytes(blob), mime_type="video/mp4"))
        return results


from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from app.services.ai.video.types import VideoGenerationRequest

from ..base import BaseReplicateVideoDriver


class Seedance1ProDriver(BaseReplicateVideoDriver):
    """Replicate driver for bytedance/seedance-1-pro."""

    default_model = "bytedance/seedance-1-pro"

    def __init__(self) -> None:
        super().__init__()
        schema_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "schemas",
            "seedance_1_pro.json",
        )
        self._schema = self.load_schema(schema_path)

    @property
    def model_id(self) -> str:
        return self.default_model

    def map_parameters(self, request: VideoGenerationRequest) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "prompt": request.prompt,
        }

        if request.fps is not None:
            params["fps"] = request.fps
        if request.duration_seconds is not None:
            params["duration"] = int(round(request.duration_seconds))
        if request.resolution:
            params["resolution"] = request.resolution
        if request.aspect_ratio:
            params["aspect_ratio"] = request.aspect_ratio
        if request.seed is not None:
            params["seed"] = request.seed

        image_inputs = self._prepare_image_inputs(request.image_inputs)
        if image_inputs:
            params["image"] = image_inputs[0]

        extras = request.extra or {}
        if "camera_fixed" in extras and extras["camera_fixed"] is not None:
            params["camera_fixed"] = bool(extras["camera_fixed"])

        for key, value in extras.items():
            if key not in params and value is not None:
                params[key] = value

        return params

    def validate_parameters(self, params: Dict[str, Any]) -> None:
        properties = self._schema.get("properties", {})
        required = self._schema.get("required", [])

        for field in required:
            if field not in params:
                raise ValueError(f"'{field}' is required for bytedance/seedance-1-pro")

        for key, value in params.items():
            schema = properties.get(key)
            if not schema or value is None:
                continue

            expected_type = schema.get("type")
            if expected_type == "string" and not isinstance(value, str):
                raise ValueError(f"Parameter '{key}' must be a string")
            if expected_type == "integer" and not isinstance(value, int):
                raise ValueError(f"Parameter '{key}' must be an integer")
            if expected_type == "number" and not isinstance(value, (int, float)):
                raise ValueError(f"Parameter '{key}' must be numeric")
            if expected_type == "boolean" and not isinstance(value, bool):
                raise ValueError(f"Parameter '{key}' must be a boolean")

            if "enum" in schema and value not in schema["enum"]:
                valid = ", ".join(str(item) for item in schema["enum"])
                raise ValueError(f"Parameter '{key}' must be one of: {valid}")
            if "minimum" in schema and isinstance(value, (int, float)):
                if value < schema["minimum"]:
                    raise ValueError(f"Parameter '{key}' must be >= {schema['minimum']}")
            if "maximum" in schema and isinstance(value, (int, float)):
                if value > schema["maximum"]:
                    raise ValueError(f"Parameter '{key}' must be <= {schema['maximum']}")

    def _prepare_image_inputs(self, inputs: Optional[List[bytes]]) -> List[str]:
        results: List[str] = []
        if not inputs:
            return results
        for blob in inputs:
            if isinstance(blob, (bytes, bytearray)):
                results.append(self.bytes_to_data_uri(bytes(blob), mime_type="image/png"))
        return results

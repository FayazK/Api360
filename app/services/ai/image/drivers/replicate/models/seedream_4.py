"""
Replicate driver for ByteDance Seedream-4 model.

Handles parameter mapping and validation for the seedream-4 model,
supporting text-to-image generation and precise image editing.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from app.services.ai.image.types import ImageGenerationRequest
from ..base import BaseReplicateDriver


class Seedream4Driver(BaseReplicateDriver):
    """Driver for ByteDance Seedream-4 image generation model."""
    
    provider = "replicate"
    default_model = "bytedance/seedream-4"
    
    def __init__(self) -> None:
        super().__init__()
        
        # Load schema
        schema_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "schemas", 
            "seedream_4.json"
        )
        with open(schema_path, 'r') as f:
            self._schema = json.load(f)
    
    @property
    def model_id(self) -> str:
        return "bytedance/seedream-4"
    
    @property
    def model_version(self) -> Optional[str]:
        return None  # Use latest version
    
    def map_parameters(self, request: ImageGenerationRequest) -> Dict[str, Any]:
        """Map unified request parameters to Seedream-4 specific parameters."""
        params: Dict[str, Any] = {
            "prompt": request.prompt
        }
        
        # Handle image inputs - convert from bytes to data URIs or use URLs
        if request.image_inputs:
            image_uris = []
            for img_data in request.image_inputs:
                if isinstance(img_data, bytes):
                    # Convert bytes to data URI
                    data_uri = self._prepare_image_input(img_data)
                    image_uris.append(data_uri)
                elif isinstance(img_data, str):
                    # Assume it's already a URL
                    image_uris.append(img_data)
            
            if image_uris:
                params["image_input"] = image_uris
        
        # Handle size and dimensions
        if request.width is not None and request.height is not None:
            params["size"] = "custom"
            params["width"] = request.width
            params["height"] = request.height
        else:
            # Use predefined size
            if request.width and request.height:
                # Determine closest size
                total_pixels = request.width * request.height
                if total_pixels <= 1024 * 1024:
                    params["size"] = "1K"
                elif total_pixels <= 2048 * 2048:
                    params["size"] = "2K"
                else:
                    params["size"] = "4K"
            else:
                params["size"] = "2K"  # Default
        
        # Handle aspect ratio
        if request.ratio:
            ratio_map = self._schema.get("ratio_mapping", {})
            if request.ratio in ratio_map:
                params["aspect_ratio"] = ratio_map[request.ratio]
            else:
                params["aspect_ratio"] = request.ratio
        
        # Handle number of images
        if request.num_images is not None and request.num_images > 1:
            params["max_images"] = min(request.num_images, 15)
            params["sequential_image_generation"] = "auto"
        
        # Add extra parameters
        if request.extra:
            for key, value in request.extra.items():
                if key not in params:  # Don't override mapped parameters
                    params[key] = value
        
        return params
    
    def validate_parameters(self, params: Dict[str, Any]) -> None:
        """Validate parameters against Seedream-4 schema."""
        schema_props = self._schema.get("properties", {})
        
        # Check required parameters
        required = self._schema.get("required", [])
        for req_param in required:
            if req_param not in params:
                raise ValueError(f"Required parameter '{req_param}' is missing")
        
        # Validate individual parameters
        for param_name, param_value in params.items():
            if param_name not in schema_props:
                continue  # Allow extra parameters
            
            param_schema = schema_props[param_name]
            self._validate_parameter(param_name, param_value, param_schema)
    
    def _validate_parameter(self, name: str, value: Any, schema: Dict[str, Any]) -> None:
        """Validate a single parameter against its schema."""
        param_type = schema.get("type")
        
        if param_type == "string":
            if not isinstance(value, str):
                raise ValueError(f"Parameter '{name}' must be a string, got {type(value)}")
            
            # Check enum values
            if "enum" in schema and value not in schema["enum"]:
                valid_values = ", ".join(schema["enum"])
                raise ValueError(f"Parameter '{name}' must be one of: {valid_values}")
        
        elif param_type == "integer":
            if not isinstance(value, int):
                raise ValueError(f"Parameter '{name}' must be an integer, got {type(value)}")
            
            # Check min/max
            if "minimum" in schema and value < schema["minimum"]:
                raise ValueError(f"Parameter '{name}' must be >= {schema['minimum']}")
            if "maximum" in schema and value > schema["maximum"]:
                raise ValueError(f"Parameter '{name}' must be <= {schema['maximum']}")
        
        elif param_type == "array":
            if not isinstance(value, list):
                raise ValueError(f"Parameter '{name}' must be an array, got {type(value)}")
            
            # Validate array items if schema provided
            items_schema = schema.get("items")
            if items_schema:
                for i, item in enumerate(value):
                    if "type" in items_schema and items_schema["type"] == "string":
                        if not isinstance(item, str):
                            raise ValueError(f"Parameter '{name}[{i}]' must be a string")
                    if "format" in items_schema and items_schema["format"] == "uri":
                        if not (item.startswith("http") or item.startswith("data:")):
                            raise ValueError(f"Parameter '{name}[{i}]' must be a valid URI")
    
    def _get_resolution_for_size(self, size: str) -> tuple[int, int]:
        """Get width/height for predefined size."""
        size_map = {
            "1K": (1024, 1024),
            "2K": (2048, 2048),
            "4K": (4096, 4096),
        }
        return size_map.get(size, (2048, 2048))
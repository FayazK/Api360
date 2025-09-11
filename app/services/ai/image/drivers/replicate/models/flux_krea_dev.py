"""
Replicate driver for Black Forest Labs FLUX.1 Krea [dev] model.

Handles parameter mapping and validation for the flux-krea-dev model,
offering distinctive aesthetics and exceptional realism.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from app.services.ai.image.types import ImageGenerationRequest
from ..base import BaseReplicateDriver


class FluxKreaDevDriver(BaseReplicateDriver):
    """Driver for Black Forest Labs FLUX.1 Krea [dev] image generation model."""
    
    provider = "replicate"
    default_model = "black-forest-labs/flux-krea-dev"
    
    def __init__(self) -> None:
        super().__init__()
        
        # Load schema
        schema_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "schemas", 
            "flux_krea_dev.json"
        )
        with open(schema_path, 'r') as f:
            self._schema = json.load(f)
    
    @property
    def model_id(self) -> str:
        return "black-forest-labs/flux-krea-dev"
    
    @property
    def model_version(self) -> Optional[str]:
        return "ce472e62d34a1f4e5415eb704a032ecf118f067345ef4a9cc1913d01e369b7a3"
    
    def map_parameters(self, request: ImageGenerationRequest) -> Dict[str, Any]:
        """Map unified request parameters to FLUX Krea Dev specific parameters."""
        params: Dict[str, Any] = {
            "prompt": request.prompt
        }
        
        # Handle image input - FLUX only supports single image
        if request.image_inputs:
            first_image = request.image_inputs[0]
            if isinstance(first_image, bytes):
                # Convert bytes to data URI
                params["image"] = self._prepare_image_input(first_image)
            elif isinstance(first_image, str):
                # Assume it's already a URL
                params["image"] = first_image
        
        # Handle seed
        if request.seed is not None:
            params["seed"] = request.seed
        
        # Handle number of outputs
        if request.num_images is not None:
            params["num_outputs"] = min(request.num_images, 4)  # Max 4 for this model
        
        # Handle steps
        if request.steps is not None:
            params["num_inference_steps"] = max(1, min(request.steps, 50))
        
        # Handle guidance scale
        if request.guidance_scale is not None:
            params["guidance"] = max(0.0, min(request.guidance_scale, 10.0))
        
        # Handle aspect ratio
        if request.ratio:
            ratio_map = self._schema.get("ratio_mapping", {})
            if request.ratio in ratio_map:
                params["aspect_ratio"] = ratio_map[request.ratio]
            else:
                # Try to use the ratio directly if it's supported
                supported_ratios = self._schema.get("properties", {}).get("aspect_ratio", {}).get("enum", [])
                if request.ratio in supported_ratios:
                    params["aspect_ratio"] = request.ratio
        
        # Handle quality (maps to output_quality)
        if request.quality is not None:
            params["output_quality"] = max(0, min(int(request.quality * 100), 100))
        
        # Handle width/height through megapixels
        if request.width is not None and request.height is not None:
            total_pixels = request.width * request.height
            megapixels = total_pixels / (1024 * 1024)
            if megapixels <= 0.3:
                params["megapixels"] = "0.25"
            else:
                params["megapixels"] = "1"
        
        # Handle image-to-image specific parameters
        if "image" in params:
            # Set prompt strength if provided, otherwise use default
            if hasattr(request, 'prompt_strength') and request.prompt_strength is not None:
                params["prompt_strength"] = max(0.0, min(request.prompt_strength, 1.0))
        
        # Handle output format
        if hasattr(request, 'output_format') and request.output_format:
            if request.output_format in ["webp", "jpg", "png"]:
                params["output_format"] = request.output_format
        
        # Handle safety checker
        if hasattr(request, 'disable_safety_checker') and request.disable_safety_checker is not None:
            params["disable_safety_checker"] = request.disable_safety_checker
        
        # Handle go_fast optimization (default: true)
        params["go_fast"] = True
        if hasattr(request, 'go_fast') and request.go_fast is not None:
            params["go_fast"] = request.go_fast
        
        # Add extra parameters
        if request.extra:
            for key, value in request.extra.items():
                if key not in params:  # Don't override mapped parameters
                    params[key] = value
        
        return params
    
    def validate_parameters(self, params: Dict[str, Any]) -> None:
        """Validate parameters against FLUX Krea Dev schema."""
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
        
        elif param_type == "number":
            if not isinstance(value, (int, float)):
                raise ValueError(f"Parameter '{name}' must be a number, got {type(value)}")
            
            # Check min/max
            if "minimum" in schema and value < schema["minimum"]:
                raise ValueError(f"Parameter '{name}' must be >= {schema['minimum']}")
            if "maximum" in schema and value > schema["maximum"]:
                raise ValueError(f"Parameter '{name}' must be <= {schema['maximum']}")
        
        elif param_type == "boolean":
            if not isinstance(value, bool):
                raise ValueError(f"Parameter '{name}' must be a boolean, got {type(value)}")
    
    def _calculate_megapixels(self, width: int, height: int) -> str:
        """Calculate megapixels setting based on dimensions."""
        total_pixels = width * height
        megapixels = total_pixels / (1024 * 1024)
        
        # Round to nearest supported value
        if megapixels <= 0.3:
            return "0.25"
        else:
            return "1"
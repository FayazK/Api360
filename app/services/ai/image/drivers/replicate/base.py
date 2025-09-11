"""
Base class for Replicate model-specific drivers.

Provides common functionality for direct API calls, parameter validation,
and output normalization across different Replicate models.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from io import BytesIO
from typing import Any, Dict, List, Optional, Union
import base64

try:
    import httpx
except ImportError:
    raise ImportError("httpx is required for Replicate drivers. Install with: pip install httpx")

from app.core.config import settings
from app.services.ai.image.factory import ImageDriver
from app.services.ai.image.types import (
    GeneratedImage,
    ImageGenerationRequest,
    ImageGenerationResult,
)


class BaseReplicateDriver(ImageDriver, ABC):
    """Base class for Replicate model-specific drivers."""
    
    provider = "replicate"
    
    def __init__(self) -> None:
        if not settings.REPLICATE_API_TOKEN:
            raise ValueError("REPLICATE_API_TOKEN environment variable is required")
        
        self._client = httpx.Client(
            base_url="https://api.replicate.com/v1",
            headers={
                "Authorization": f"Token {settings.REPLICATE_API_TOKEN}",
                "Content-Type": "application/json",
            },
            timeout=120.0,
        )
    
    @property
    @abstractmethod
    def model_id(self) -> str:
        """Replicate model identifier (e.g., 'bytedance/seedream-4')."""
        pass
    
    @property
    @abstractmethod
    def model_version(self) -> Optional[str]:
        """Specific model version hash, if pinned."""
        pass
    
    @abstractmethod
    def map_parameters(self, request: ImageGenerationRequest) -> Dict[str, Any]:
        """Map unified request parameters to model-specific parameters."""
        pass
    
    @abstractmethod
    def validate_parameters(self, params: Dict[str, Any]) -> None:
        """Validate parameters against model schema."""
        pass
    
    def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        """Generate images using the Replicate API."""
        
        # Map and validate parameters
        mapped_params = self.map_parameters(request)
        self.validate_parameters(mapped_params)
        
        # Prepare API payload
        model_ref = self.model_id
        if self.model_version:
            model_ref = f"{self.model_id}:{self.model_version}"
        
        prediction_data = {
            "version": self.model_version or "latest",
            "input": mapped_params
        }
        
        # Create prediction
        response = self._client.post("/predictions", json=prediction_data)
        
        if response.status_code != 201:
            self._handle_api_error(response)
        
        prediction = response.json()
        prediction_id = prediction["id"]
        
        # Poll for completion
        result = self._wait_for_completion(prediction_id)
        
        # Normalize output
        images = self._normalize_output(result.get("output"))
        
        # Build metadata
        metadata = {
            "model": model_ref,
            "prediction_id": prediction_id,
            "parameters": {k: v for k, v in mapped_params.items() 
                         if not self._is_file_parameter(k, v)},
        }
        
        return ImageGenerationResult(
            provider=self.provider,
            model=model_ref,
            images=images,
            metadata=metadata,
        )
    
    def _wait_for_completion(self, prediction_id: str) -> Dict[str, Any]:
        """Poll prediction until completion."""
        import time
        
        max_wait = 300  # 5 minutes
        poll_interval = 2  # 2 seconds
        waited = 0
        
        while waited < max_wait:
            response = self._client.get(f"/predictions/{prediction_id}")
            
            if response.status_code != 200:
                self._handle_api_error(response)
            
            prediction = response.json()
            status = prediction.get("status")
            
            if status == "succeeded":
                return prediction
            elif status == "failed":
                error_msg = prediction.get("error", "Prediction failed")
                raise RuntimeError(f"Replicate prediction failed: {error_msg}")
            elif status in ["canceled", "cancelled"]:
                raise RuntimeError("Replicate prediction was canceled")
            
            time.sleep(poll_interval)
            waited += poll_interval
        
        raise TimeoutError(f"Prediction {prediction_id} did not complete within {max_wait} seconds")
    
    def _normalize_output(self, output: Any) -> List[GeneratedImage]:
        """Normalize various output formats to GeneratedImage objects."""
        images: List[GeneratedImage] = []
        
        if not output:
            return images
        
        def is_url(val: str) -> bool:
            return isinstance(val, str) and re.match(r"^https?://", val) is not None
        
        def add_url(url: str):
            images.append(GeneratedImage(url=url))
        
        def add_bytes(data: bytes, mime: Optional[str] = None):
            images.append(
                GeneratedImage(
                    b64_data=base64.b64encode(data).decode("utf-8"),
                    mime_type=mime or "image/png",
                )
            )
        
        def try_extract_url(obj: Any) -> Optional[str]:
            """Try to extract URL from various object types."""
            if hasattr(obj, "url") and is_url(getattr(obj, "url")):
                return getattr(obj, "url")
            
            try:
                str_repr = str(obj)
                if is_url(str_repr):
                    return str_repr
            except Exception:
                pass
            
            return None
        
        # Handle different output structures
        if isinstance(output, list):
            for item in output:
                if isinstance(item, str) and is_url(item):
                    add_url(item)
                elif isinstance(item, (bytes, bytearray)):
                    add_bytes(item)
                elif isinstance(item, dict):
                    # Common patterns: {"image": url}, {"images": [urls]}, {"url": url}
                    if "images" in item and isinstance(item["images"], list):
                        for u in item["images"]:
                            if is_url(u):
                                add_url(u)
                    elif "image" in item and is_url(item["image"]):
                        add_url(item["image"])
                    elif "url" in item and is_url(item["url"]):
                        add_url(item["url"])
                    else:
                        # Store unknown dict as metadata
                        images.append(GeneratedImage(
                            metadata={"raw": {k: str(v) for k, v in item.items()}}
                        ))
                else:
                    # Try to extract URL from object
                    url = try_extract_url(item)
                    if url:
                        add_url(url)
                    else:
                        images.append(GeneratedImage(
                            metadata={
                                "raw_type": type(item).__name__,
                                "raw_repr": repr(item)
                            }
                        ))
        
        elif isinstance(output, str) and is_url(output):
            add_url(output)
        elif isinstance(output, (bytes, bytearray)):
            add_bytes(output)
        elif isinstance(output, dict):
            if "images" in output and isinstance(output["images"], list):
                for u in output["images"]:
                    if is_url(u):
                        add_url(u)
            elif "image" in output and is_url(output["image"]):
                add_url(output["image"])
            elif "url" in output and is_url(output["url"]):
                add_url(output["url"])
            else:
                images.append(GeneratedImage(
                    metadata={"raw": {k: str(v) for k, v in output.items()}}
                ))
        else:
            # Try to extract URL from single object
            url = try_extract_url(output)
            if url:
                add_url(url)
            else:
                images.append(GeneratedImage(
                    metadata={
                        "raw_type": type(output).__name__,
                        "raw_repr": repr(output)
                    }
                ))
        
        return images
    
    def _handle_api_error(self, response: httpx.Response) -> None:
        """Handle API error responses."""
        try:
            error_data = response.json()
            error_msg = error_data.get("detail", "Unknown API error")
        except Exception:
            error_msg = f"HTTP {response.status_code}: {response.text}"
        
        raise RuntimeError(f"Replicate API error: {error_msg}")
    
    def _is_file_parameter(self, key: str, value: Any) -> bool:
        """Check if parameter contains file data that shouldn't be logged."""
        file_params = {"image", "image_input", "mask"}
        return key in file_params or isinstance(value, (bytes, bytearray, BytesIO))
    
    def _prepare_image_input(self, image_data: bytes) -> str:
        """Convert image bytes to data URI for API."""
        b64_data = base64.b64encode(image_data).decode('utf-8')
        return f"data:image/png;base64,{b64_data}"
    
    def __del__(self):
        """Clean up HTTP client."""
        if hasattr(self, '_client'):
            self._client.close()
from __future__ import annotations

import base64
from typing import Any, Dict, List, Optional

from .factory import ImageDriverFactory
from .types import GeneratedImage, ImageGenerationRequest, ImageGenerationResult


class ImageGenerationError(RuntimeError):
    pass


class ImageEngine:
    """Provider-agnostic image generation engine.

    Routes and services should call this engine with a prompt and optional
    parameters. The engine dispatches to a registered driver for the selected
    provider, passes only explicitly provided params, and normalizes responses
    into a unified `ImageGenerationResult`.
    """

    def __init__(self, default_provider: Optional[str] = None) -> None:
        self.default_provider = (default_provider or "").strip() or None

    def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        provider = (request.provider or self.default_provider or "").strip()
        if not provider:
            raise ImageGenerationError(
                "No provider specified. Pass `provider` or configure a default."
            )

        try:
            driver = ImageDriverFactory.get(provider)
        except KeyError as e:
            raise ImageGenerationError(str(e)) from e

        # Delegate to driver. Driver must return an ImageGenerationResult-like
        # payload or a driver-specific shape that we normalize below.
        raw_result = driver.generate(request)

        result = self._normalize_result(raw_result, provider, request.model, getattr(driver, "default_model", ""))
        return result

    # --- helpers ---

    def _normalize_result(
        self,
        raw: Any,
        provider: str,
        request_model: Optional[str],
        driver_default_model: str,
    ) -> ImageGenerationResult:
        """Normalize various driver result shapes into ImageGenerationResult.

        Drivers are encouraged to return ImageGenerationResult directly. When
        they return provider SDK objects or loose dicts, we try to coerce them
        into the unified shape here to insulate the rest of the app.
        """

        if isinstance(raw, ImageGenerationResult):
            return raw

        # Dict-like fallback expected keys:
        #   images: list[GeneratedImage | {b64_data,url,path,mime_type,metadata}]
        #   model: str (optional)
        #   metadata: dict (optional)
        if isinstance(raw, dict):
            images_payload = raw.get("images", [])
            images: List[GeneratedImage] = []
            for item in images_payload:
                if isinstance(item, GeneratedImage):
                    images.append(item)
                elif isinstance(item, dict):
                    images.append(
                        GeneratedImage(
                            b64_data=item.get("b64_data"),
                            mime_type=item.get("mime_type"),
                            url=item.get("url"),
                            path=item.get("path"),
                            metadata=item.get("metadata", {}) or {},
                        )
                    )
                elif isinstance(item, (bytes, bytearray)):
                    images.append(
                        GeneratedImage(
                            b64_data=base64.b64encode(item).decode("utf-8"),
                            mime_type="image/png",  # Sensible default if not specified
                        )
                    )
                else:
                    # Unknown image shape; keep a placeholder record
                    images.append(GeneratedImage(metadata={"raw": item}))

            model = raw.get("model") or request_model or driver_default_model or ""
            metadata: Dict[str, Any] = raw.get("metadata", {}) or {}
            return ImageGenerationResult(provider=provider, model=model, images=images, metadata=metadata)

        # If a driver returned a list of bytes or dicts, coerce similarly.
        if isinstance(raw, list):
            images: List[GeneratedImage] = []
            for item in raw:
                if isinstance(item, GeneratedImage):
                    images.append(item)
                elif isinstance(item, (bytes, bytearray)):
                    images.append(
                        GeneratedImage(
                            b64_data=base64.b64encode(item).decode("utf-8"),
                            mime_type="image/png",
                        )
                    )
                elif isinstance(item, dict):
                    images.append(
                        GeneratedImage(
                            b64_data=item.get("b64_data"),
                            mime_type=item.get("mime_type"),
                            url=item.get("url"),
                            path=item.get("path"),
                            metadata=item.get("metadata", {}) or {},
                        )
                    )
                else:
                    images.append(GeneratedImage(metadata={"raw": item}))

            model = request_model or driver_default_model or ""
            return ImageGenerationResult(provider=provider, model=model, images=images, metadata={})

        # As a last resort, encapsulate raw into metadata for debugging.
        model = request_model or driver_default_model or ""
        return ImageGenerationResult(
            provider=provider,
            model=model,
            images=[],
            metadata={"raw": raw},
        )


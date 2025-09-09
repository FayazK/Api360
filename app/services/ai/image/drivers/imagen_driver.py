from __future__ import annotations

from typing import Any, Dict, List

try:
    from google import genai
    from google.genai import types as genai_types
except Exception:  # pragma: no cover - optional dependency at import time
    genai = None  # type: ignore
    genai_types = None  # type: ignore

from app.services.ai.image.factory import ImageDriver, ImageDriverFactory
from app.services.ai.image.types import (
    GeneratedImage,
    ImageGenerationRequest,
    ImageGenerationResult,
)


class ImagenDriver(ImageDriver):
    """Google Imagen 4 driver using google-genai.

    Models:
      - imagen-4.0-ultra-generate-001 (Ultra)
      - imagen-4.0-generate-001 (Standard; default)
      - imagen-4.0-fast-generate-001 (Fast)
    See docs/sdk/google/imagen-and-veo.md
    """

    provider = "imagen"
    default_model = "imagen-4.0-generate-001"

    def __init__(self) -> None:
        if genai is None:
            raise ImportError(
                "google-genai is not installed. Install with: pip install google-genai"
            )
        self._client = genai.Client()

    def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        contents: List[Any] = []

        if request.system_prompt:
            contents.append(str(request.system_prompt))

        prompt = request.prompt
        if request.ratio:
            prompt = f"{prompt}\n\nAspect ratio: {request.ratio}".strip()
        if request.negative_prompt:
            prompt = f"{prompt}\n\nAvoid: {request.negative_prompt}".strip()
        contents.append(prompt)

        if request.image_inputs:
            for img_bytes in request.image_inputs:
                if genai_types is not None:
                    contents.append(
                        genai_types.Part.from_bytes(data=img_bytes, mime_type="image/png")
                    )
                else:  # pragma: no cover
                    contents.append(img_bytes)

        api_params: Dict[str, Any] = {
            "model": request.model or self.default_model,
            "contents": contents if len(contents) > 1 else contents[0],
        }

        gen_config: Dict[str, Any] = {}
        if request.temperature is not None:
            gen_config["temperature"] = request.temperature
        if request.top_p is not None:
            gen_config["top_p"] = request.top_p
        if request.stop:
            gen_config["stop_sequences"] = request.stop
        if request.safety is not None:
            gen_config["safety_settings"] = request.safety
        if request.extra.get("response_mime_type"):
            gen_config["response_mime_type"] = request.extra["response_mime_type"]

        if gen_config:
            api_params["config"] = genai_types.GenerateContentConfig(**gen_config)

        response = self._client.models.generate_content(**api_params)

        images: List[GeneratedImage] = []
        text_outputs: List[str] = []

        candidates = getattr(response, "candidates", []) or []
        for cand in candidates:
            content = getattr(cand, "content", None)
            if not content:
                continue
            parts = getattr(content, "parts", []) or []
            for part in parts:
                if getattr(part, "inline_data", None):
                    data = getattr(part.inline_data, "data", None)
                    mime = getattr(part.inline_data, "mime_type", None)
                    if data:
                        if isinstance(data, (bytes, bytearray)):
                            import base64

                            b64 = base64.b64encode(data).decode("utf-8")
                        else:
                            b64 = data
                        images.append(
                            GeneratedImage(
                                b64_data=b64,
                                mime_type=mime or "image/png",
                            )
                        )
                elif getattr(part, "text", None):
                    text_outputs.append(part.text)

        # Convenience text field
        resp_text = getattr(response, "text", None)
        if resp_text:
            text_outputs.append(resp_text)

        # Fallback extraction if none collected
        if not images:
            try:
                part = response.candidates[0].content.parts[-1]
                if getattr(part, "inline_data", None) and getattr(part.inline_data, "data", None):
                    data = part.inline_data.data
                    if isinstance(data, (bytes, bytearray)):
                        import base64

                        b64 = base64.b64encode(data).decode("utf-8")
                    else:
                        b64 = data
                    images.append(
                        GeneratedImage(
                            b64_data=b64,
                            mime_type=getattr(part.inline_data, "mime_type", None) or "image/png",
                        )
                    )
            except Exception:
                pass

        usage = getattr(response, "usage_metadata", None)
        model_version = getattr(response, "model_version", None) or ""

        metadata: Dict[str, Any] = {
            "text_outputs": [t for t in text_outputs if t],
            "usage": {
                "input_tokens": getattr(usage, "input_tokens", None) if usage else None,
                "output_tokens": getattr(usage, "output_tokens", None) if usage else None,
                "total_tokens": getattr(usage, "total_tokens", None) if usage else None,
            },
            "model_version": model_version,
            "parameters": {k: v for k, v in gen_config.items()},
        }

        return ImageGenerationResult(
            provider=self.provider,
            model=(request.model or self.default_model),
            images=images,
            metadata=metadata,
        )


# Register driver on import
ImageDriverFactory.register(ImagenDriver)


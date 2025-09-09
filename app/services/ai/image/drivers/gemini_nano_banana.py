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


class GeminiNanoBananaDriver(ImageDriver):
    """Gemini 2.5 Flash Image ("Nano Banana") driver using google-genai.

    Model ID: gemini-2.5-flash-image-preview
    Reference: docs/sdk/google/nano-banana.md
    """

    provider = "gemini-nano-banana"
    default_model = "gemini-2.5-flash-image-preview"

    def __init__(self) -> None:
        if genai is None:
            raise ImportError(
                "google-genai is not installed. Install with: pip install google-genai"
            )
        # Client picks up GOOGLE_API_KEY or Vertex env per google-genai docs.
        self._client = genai.Client()

    def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        # Build contents list: optional system prompt + prompt + image parts
        contents: List[Any] = []

        if request.system_prompt:
            # Use system instruction as a first message; the SDK also supports
            # system_instruction config, but content prepend mirrors docs patterns.
            contents.append(str(request.system_prompt))

        prompt = request.prompt
        # If user specified aspect ratio, guide the model via prompt (no direct param in preview)
        if request.ratio:
            prompt = f"{prompt}\n\nAspect ratio: {request.ratio}".strip()

        # Negative prompt can be appended explicitly
        if request.negative_prompt:
            prompt = f"{prompt}\n\nAvoid: {request.negative_prompt}".strip()

        contents.append(prompt)

        # Add input images as inline bytes parts
        if request.image_inputs:
            for img_bytes in request.image_inputs:
                if genai_types is not None:
                    parts = genai_types.Part.from_bytes(
                        data=img_bytes, mime_type="image/png"
                    )
                    contents.append(parts)
                else:  # pragma: no cover
                    contents.append(img_bytes)

        # Build API params; only include explicitly set fields
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
        # Some users may pass safety settings structure via request.safety
        if request.safety is not None:
            gen_config["safety_settings"] = request.safety

        # Allow response_mime_type override via extra
        if request.extra.get("response_mime_type"):
            gen_config["response_mime_type"] = request.extra["response_mime_type"]

        if gen_config:
            api_params["config"] = genai_types.GenerateContentConfig(**gen_config)

        # Make the call
        response = self._client.models.generate_content(**api_params)

        # Parse images from candidates/parts
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
                        # google-genai returns bytes for inline_data.data
                        if isinstance(data, (bytes, bytearray)):
                            import base64

                            b64 = base64.b64encode(data).decode("utf-8")
                        else:
                            # Some SDK variants may already provide base64 string
                            b64 = data
                        images.append(
                            GeneratedImage(
                                b64_data=b64,
                                url=None,
                                path=None,
                                mime_type=mime or "image/png",
                            )
                        )
                elif getattr(part, "text", None):
                    text_outputs.append(part.text)

        # If SDK provides a convenience .text on response, include it
        resp_text = getattr(response, "text", None)
        if resp_text:
            text_outputs.append(resp_text)

        # Fallback: If no images collected but response has a single part with inline_data
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

        # Usage and model version metadata if present
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
ImageDriverFactory.register(GeminiNanoBananaDriver)

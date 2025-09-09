from __future__ import annotations

from typing import Any, Dict, List, Optional
from io import BytesIO
import re

try:
    import replicate
except Exception:  # pragma: no cover - optional dependency at import time
    replicate = None  # type: ignore

from app.services.ai.image.factory import ImageDriver, ImageDriverFactory
from app.services.ai.image.types import (
    GeneratedImage,
    ImageGenerationRequest,
    ImageGenerationResult,
)


class ReplicateImageDriver(ImageDriver):
    """Replicate image generation driver (generic).

    Uses the official `replicate` Python SDK and `Client.run` to invoke models.
    Default model: `stability-ai/sdxl`. You can override per request by setting
    `request.model` to another model slug (e.g., `black-forest-labs/flux-1`), or
    a pinned version (`owner/name@<version_hash>`).

    Inputs vary by model. This driver forwards commonly used fields if present:
      - prompt → `prompt`
      - negative_prompt → `negative_prompt`
      - width → `width`, height → `height`
      - steps → `num_inference_steps`
      - guidance_scale → `guidance_scale`
      - seed → `seed`
      - image_inputs[0] → `image` (as file-like)
      - mask → `mask` (as file-like)
      - extra → merged verbatim into input
    """

    provider = "replicate"
    default_model = "stability-ai/sdxl"

    def __init__(self) -> None:
        if replicate is None:
            raise ImportError(
                "replicate SDK not installed. Install with: pip install replicate"
            )
        self._client = replicate.Client()

    def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        model_slug = request.model or self.default_model

        input_payload: Dict[str, Any] = {"prompt": request.prompt}

        if request.negative_prompt:
            input_payload["negative_prompt"] = request.negative_prompt
        if request.width is not None:
            input_payload["width"] = request.width
        if request.height is not None:
            input_payload["height"] = request.height
        if request.steps is not None:
            input_payload["num_inference_steps"] = request.steps
        if request.guidance_scale is not None:
            input_payload["guidance_scale"] = request.guidance_scale
        if request.seed is not None:
            input_payload["seed"] = request.seed
        if request.num_images is not None:
            # Many models support this as `num_outputs` or `num_images`; prefer num_outputs
            input_payload["num_outputs"] = request.num_images

        # Attach the first image/mask if provided (img2img / inpainting)
        if request.image_inputs:
            first = request.image_inputs[0]
            input_payload["image"] = BytesIO(first)
        if request.mask:
            input_payload["mask"] = BytesIO(request.mask)

        # Merge extra keys verbatim (overrides defaults if collisions occur)
        if request.extra:
            input_payload.update(request.extra)

        # Run the model synchronously
        output = self._client.run(model_slug, input=input_payload)

        images: List[GeneratedImage] = []

        def is_url(val: str) -> bool:
            return isinstance(val, str) and re.match(r"^https?://", val) is not None

        def add_url(u: str):
            images.append(GeneratedImage(url=u))

        def add_bytes(b: bytes, mime: Optional[str] = None):
            import base64

            images.append(
                GeneratedImage(
                    b64_data=base64.b64encode(b).decode("utf-8"),
                    mime_type=mime or "image/png",
                )
            )

        # Normalize possible output shapes
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
                        # Unknown dict shape: stash as metadata on a placeholder image
                        images.append(GeneratedImage(metadata={"raw": item}))
                else:
                    images.append(GeneratedImage(metadata={"raw": item}))
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
                images.append(GeneratedImage(metadata={"raw": output}))
        else:
            images.append(GeneratedImage(metadata={"raw": output}))

        metadata: Dict[str, Any] = {
            "parameters": {k: v for k, v in input_payload.items() if k != "image" and k != "mask"},
        }

        return ImageGenerationResult(
            provider=self.provider,
            model=model_slug,
            images=images,
            metadata=metadata,
        )


# Register driver on import
ImageDriverFactory.register(ReplicateImageDriver)


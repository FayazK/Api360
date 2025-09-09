# Image Generation Service

Provider-agnostic image generation engine with a pluggable driver layer.

## Overview

- Engine entry: `app/services/ai/image/base.py` (`ImageEngine`).
- Driver base and registry: `app/services/ai/image/factory.py`.
- Unified types: `app/services/ai/image/types.py`.
- Drivers live in: `app/services/ai/image/drivers/`.

### Available Drivers

- `gemini-nano-banana` → Gemini 2.5 Flash Image (Preview). See `docs/image_gemini_nano_banana.md`.
- `imagen` → Imagen 4 (Ultra/Standard/Fast). See `docs/image_imagen.md`.
- `replicate` → Replicate generic image driver. See `docs/image_replicate.md`.

## Parameter Policy

- Required: only `prompt`.
- Optional: `provider`, `model`, `seed`, `width`, `height`, `ratio`, `num_images`,
  `steps`, `guidance_scale`, `quality`, `negative_prompt`, `stop`, `image_inputs`,
  `mask`, `safety`, `user`, `template_variables`, and `extra`.
- Routes/services must not invent defaults for unset optionals. Pass through only
  user-specified fields to the engine. Drivers should only forward params to 
  provider SDKs that are explicitly set, allowing providers to apply their defaults.
- Metadata should reflect only parameters actually sent, plus `model`.

## Usage (Service Layer)

```python
from app.services.ai.image import ImageEngine
from app.services.ai.image.types import ImageGenerationRequest

engine = ImageEngine(default_provider=None)  # or configure a default provider

req = ImageGenerationRequest(
    prompt="a cozy cabin in a snowy forest, watercolor",
    provider="gemini",  # or pass in route payload
    model=None,          # let driver/provider default
    ratio="16:9",
    num_images=2,
)

result = engine.generate(req)
for img in result.images:
    # Prefer `b64_data` + `mime_type` if available
    ...
```

## Implementing a Driver

Create a module under `app/services/ai/image/drivers/your_driver.py`:

```python
from app.services.ai.image.factory import ImageDriver, ImageDriverFactory
from app.services.ai.image.types import ImageGenerationRequest, ImageGenerationResult, GeneratedImage

class YourDriver(ImageDriver):
    provider = "yourprovider"
    default_model = "your-default-model"

    def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        # 1. Build provider payload from explicitly set fields only
        # 2. Call provider SDK/API
        # 3. Normalize to ImageGenerationResult
        return ImageGenerationResult(
            provider=self.provider,
            model=request.model or self.default_model,
            images=[GeneratedImage(url="https://...")],
            metadata={}
        )

# Register on import
ImageDriverFactory.register(YourDriver)
```

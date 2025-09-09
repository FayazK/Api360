# Replicate — Image Engine Driver

Generic driver for image generation via the official Replicate Python SDK.

- Provider key: `replicate`
- Default model: `stability-ai/sdxl` (override per request via `model`)
- SDK docs: `docs/sdk/replicate.md`

## Setup

1) Install: `pip install replicate`
2) Auth: `export REPLICATE_API_TOKEN="<your_token>"`

## Usage

```python
from app.services.ai.image import ImageEngine
from app.services.ai.image.types import ImageGenerationRequest

engine = ImageEngine()

# Text → Image (default SDXL)
req = ImageGenerationRequest(
    prompt="A minimalist poster of Karachi skyline, vector style, 4:5",
    provider="replicate",
    model="stability-ai/sdxl",  # or any slug like "black-forest-labs/flux-1"
    width=1024,
    height=1280,
    steps=30,
    guidance_scale=7.5,
    seed=42,
)
res = engine.generate(req)
assert res.images[0].url or res.images[0].b64_data

# Image → Image (img2img)
with open("product.png", "rb") as f:
    req2 = ImageGenerationRequest(
        prompt="Place product on white seamless with soft shadow",
        provider="replicate",
        model="stability-ai/sdxl",
        image_inputs=[f.read()],
    )
res2 = engine.generate(req2)
```

## Parameters Mapping

- Forwarded if set:
  - `prompt` → `prompt`
  - `negative_prompt` → `negative_prompt`
  - `width` → `width`, `height` → `height`
  - `steps` → `num_inference_steps`
  - `guidance_scale` → `guidance_scale`
  - `seed` → `seed`
  - `num_images` → `num_outputs`
  - `image_inputs[0]` → `image` (file-like)
  - `mask` → `mask` (file-like)
  - `extra` → merged verbatim into input (model-specific knobs)

> Note: Each Replicate model defines its own input schema. Use `extra` for model-specific fields. The driver forwards only explicitly set fields and does not invent defaults.

## Output

- Many models return image URLs (strings) or a list of URLs.
- Some return bytes or a dict with `images`/`image`/`url`.
- The driver normalizes to `ImageGenerationResult` with `GeneratedImage` items populated as `url` or `b64_data + mime_type`.


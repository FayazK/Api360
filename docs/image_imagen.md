# Imagen 4 — Image Engine Driver

This driver integrates Google **Imagen 4** with the app’s provider‑agnostic Image Engine.

- Provider key: `imagen`
- Default model: `imagen-4.0-generate-001`
- Other models: `imagen-4.0-ultra-generate-001`, `imagen-4.0-fast-generate-001`

See reference: `docs/sdk/google/imagen-and-veo.md` (ignore Veo for this driver).

## Setup

1) Install SDK: `pip install google-genai` (optionally `google-genai[aiohttp]`).
2) Auth:
   - Developer API: export `GOOGLE_API_KEY`.
   - Vertex AI: export `GOOGLE_GENAI_USE_VERTEXAI=true`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`.

## Usage with Image Engine

```python
from app.services.ai.image import ImageEngine
from app.services.ai.image.types import ImageGenerationRequest

engine = ImageEngine()

# Text → Image
req = ImageGenerationRequest(
    prompt=(
        "Ultra-detailed product hero shot of a stainless-steel espresso machine, "
        "studio lighting, crisp typography ‘CAFÉ PRO 500’ on the body, square"
    ),
    provider="imagen",
    model="imagen-4.0-ultra-generate-001",  # or omit to use default standard model
    temperature=0.2,
)
res = engine.generate(req)
img0 = res.images[0]
assert img0.b64_data and img0.mime_type

# Image → Image (edit)
with open("living_room.jpg", "rb") as f:
    req2 = ImageGenerationRequest(
        prompt="Restyle room to Scandinavian minimalism; maple woods, soft neutrals; vertical 4:5.",
        provider="imagen",
        model="imagen-4.0-generate-001",
        image_inputs=[f.read()],
        ratio="4:5",
        temperature=0.15,
    )
res2 = engine.generate(req2)

# Multi‑image composition
with open("shoe.png", "rb") as prod, open("studio_bg.jpg", "rb") as bg:
    req3 = ImageGenerationRequest(
        prompt="Place product on the first background; 3/4 angle, soft shadow; square.",
        provider="imagen",
        model="imagen-4.0-fast-generate-001",
        image_inputs=[bg.read(), prod.read()],
        ratio="1:1",
    )
res3 = engine.generate(req3)
```

## Parameters

- Required: `prompt`.
- Optional (forwarded only if set): `model`, `temperature`, `top_p`, `stop` (mapped to `stop_sequences`),
  `safety` (safety settings list/dict), `system_prompt`.
- `ratio` and `negative_prompt` are appended to the prompt for guidance.
- `image_inputs`: list of bytes; sent as inline image parts (uses `image/png` MIME by default).

## Output

- Returns `ImageGenerationResult` with `images: List[GeneratedImage]`.
- Each `GeneratedImage` includes `b64_data` and `mime_type` when available; URLs/paths are not set by the driver.
- Captures interleaved model text in `metadata.text_outputs`, with `usage` and `model_version` when provided.


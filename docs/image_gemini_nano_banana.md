# Gemini 2.5 Flash Image (Nano Banana) — Image Engine Driver

This driver integrates Google’s Gemini 2.5 Flash Image (aka “Nano Banana”) with the app’s provider‑agnostic Image Engine.

Key: `provider="gemini-nano-banana"`, model default: `gemini-2.5-flash-image-preview`.

## Setup

- Install SDK: `pip install google-genai` (optionally `google-genai[aiohttp]`).
- Auth:
  - Developer API: set `GOOGLE_API_KEY`.
  - Vertex AI (server‑side): set `GOOGLE_GENAI_USE_VERTEXAI=true`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`.

## Usage

```python
from app.services.ai.image import ImageEngine
from app.services.ai.image.types import ImageGenerationRequest

engine = ImageEngine()

# Text → Image
req = ImageGenerationRequest(
    prompt="A cinematic photo of a nano‑banana dessert under a starry sky.",
    provider="gemini-nano-banana",
    # Let the driver/provider pick defaults
    ratio="16:9",            # guided via prompt augmentation
    temperature=0.2,          # optional
    top_p=0.95,               # optional
)
res = engine.generate(req)
for i, img in enumerate(res.images):
    # Prefer b64_data + mime_type
    assert img.b64_data and img.mime_type
    # decode and save if needed

# Image + Text → Image (multi‑image fusion)
with open("scene.jpg", "rb") as f1, open("subject.png", "rb") as f2:
    req2 = ImageGenerationRequest(
        prompt=(
            "Place the product on the counter, natural morning light, "
            "add soft drop shadow; 3/4 view."
        ),
        provider="gemini-nano-banana",
        image_inputs=[f1.read(), f2.read()],
        ratio="1:1",
    )
res2 = engine.generate(req2)

# Image → Image (edit)
with open("portrait.jpg", "rb") as f:
    req3 = ImageGenerationRequest(
        prompt=(
            "Convert to corporate headshot; subtle skin smoothing, "
            "neutral gray backdrop; vertical 4:5."
        ),
        provider="gemini-nano-banana",
        image_inputs=[f.read()],
        ratio="4:5",
        temperature=0.1,
    )
res3 = engine.generate(req3)
```

## Parameters

- Required: `prompt`.
- Optional (forwarded only if set):
  - `model`, `temperature`, `top_p`, `stop` (mapped to `stop_sequences`), `safety` (safety settings list/dict), `system_prompt`.
  - `ratio`: appended as guidance to the prompt (e.g., “Aspect ratio: 16:9”).
  - `image_inputs`: list of bytes; sent as inline image parts (`image/png` by default).
  - Other fields are not used by this model in preview (e.g., `width/height`, `steps`).

## Output

- `ImageGenerationResult` with `images: List[GeneratedImage]`.
- Each `GeneratedImage` includes `b64_data` (base64) and `mime_type` when available.
- Any interleaved text from the model is captured under `metadata.text_outputs`.
- `metadata.usage` includes token counts if provided by the SDK, and `model_version` when available.

## Notes

- Aspect/size: the preview model does not accept explicit `width`/`height`; guide aspect via prompt. Default output is ~1024px.
- Candidates: Developer API preview typically returns 1 candidate; the driver loops defensively over candidates and parts.
- Safety: pass safety settings only if explicitly provided; otherwise provider defaults apply.
- Auth and full model details: see `docs/sdk/google/nano-banana.md`.


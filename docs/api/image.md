# Image Generation API

Provider‑agnostic image generation and editing via a unified engine with pluggable drivers (Gemini Nano Banana, Imagen 4, Replicate).

Base path: `/api/images`

## Endpoints

- POST `/api/images/generate` — JSON body
- POST `/api/images/generate-multipart` — multipart form + file uploads

No defaults are injected by routes; only fields you provide are forwarded to the driver. Drivers and providers apply their own defaults.

## Requirements

- Set environment variables for providers you plan to use:
  - Google GenAI: `GOOGLE_API_KEY` (or Vertex: `GOOGLE_GENAI_USE_VERTEXAI=true`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`)
  - Replicate: `REPLICATE_API_TOKEN`
- Install SDKs in `requirements.txt` are already present: `google-genai`, `replicate`.

---

## JSON Endpoint: POST /api/images/generate

Content-Type: `application/json`

Request body fields (only `prompt` required; others optional):

- prompt: string
- provider: string (e.g., `gemini-nano-banana`, `imagen`, `replicate`)
- model: string (provider‑specific model)
- ratio: string (e.g., `1:1`, `16:9`, `4:5`) — guided via prompt for Gemini/Imagen
- negative_prompt: string
- temperature: number
- top_p: number
- stop_sequences: string[]
- system_prompt: string
- safety: object (provider‑specific safety settings)
- images_b64: string[] (base64 input images for img2img / multi‑image fusion)
- extra: object (provider‑specific passthrough)

### Sample: Gemini Nano Banana (Text → Image)

Body (raw JSON):

```json
{
  "prompt": "A cinematic photo of a nano-banana dessert under a starry sky.",
  "provider": "gemini-nano-banana",
  "ratio": "16:9",
  "temperature": 0.2
}
```

cURL:

```bash
curl -X POST http://localhost:8000/api/images/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A cinematic photo of a nano-banana dessert under a starry sky.",
    "provider": "gemini-nano-banana",
    "ratio": "16:9",
    "temperature": 0.2
  }'
```

### Sample: Gemini Nano Banana (Image + Text → Image)

```json
{
  "prompt": "Place the product on the counter, soft morning light, add soft shadow; 3/4 view.",
  "provider": "gemini-nano-banana",
  "images_b64": ["<base64-scene>", "<base64-subject>"]
}
```

### Sample: Imagen 4 Ultra (Text → Image)

```json
{
  "prompt": "Ultra-detailed product hero shot of a stainless-steel espresso machine, studio lighting, magazine layout, square.",
  "provider": "imagen",
  "model": "imagen-4.0-ultra-generate-001",
  "temperature": 0.2
}
```

### Sample: Replicate SDXL (Text → Image)

```json
{
  "prompt": "A minimalist poster of Karachi skyline, vector style, 4:5",
  "provider": "replicate",
  "model": "stability-ai/sdxl",
  "width": 1024,
  "height": 1280,
  "steps": 30,
  "guidance_scale": 7.5,
  "seed": 42,
  "num_images": 1,
  "extra": {
    "scheduler": "K_EULER_ANCESTRAL"
  }
}
```

Note: For Replicate, `width`, `height`, `steps`→`num_inference_steps`, `guidance_scale`, `seed`, `num_images`→`num_outputs` are forwarded when present. Other model‑specific inputs can be passed via `extra`.

### Example Response

```json
{
  "provider": "gemini-nano-banana",
  "model": "gemini-2.5-flash-image-preview",
  "images": [
    {
      "b64_data": "iVBORw0KGgoAAA...",
      "mime_type": "image/png",
      "url": null,
      "path": null,
      "metadata": {}
    }
  ],
  "metadata": {
    "text_outputs": [],
    "usage": {"input_tokens": null, "output_tokens": null, "total_tokens": null},
    "model_version": "2025-09-08",
    "parameters": {"temperature": 0.2}
  }
}
```

---

## Multipart Endpoint: POST /api/images/generate-multipart

Use when uploading images as files. Combine form fields with file uploads.

Form fields:

- prompt: string (required)
- provider, model, ratio, negative_prompt, temperature, top_p, system_prompt: optional strings/numbers
- stop_sequences: JSON array as string (e.g., `"[\"END\"]"`)
- safety: JSON object as string
- extra: JSON object as string
- files: one or more image files (field name `files`)
- mask: optional single image file (field name `mask`)

### cURL: Upload two images with Gemini Nano Banana

```bash
curl -X POST http://localhost:8000/api/images/generate-multipart \
  -F 'prompt=Place the product on the counter, soft morning light; 3/4 view.' \
  -F 'provider=gemini-nano-banana' \
  -F 'ratio=1:1' \
  -F 'temperature=0.2' \
  -F 'files=@scene.jpg' \
  -F 'files=@product.png'
```

### cURL: Imagen 4 edit with one uploaded file

```bash
curl -X POST http://localhost:8000/api/images/generate-multipart \
  -F 'prompt=Restyle room to Scandinavian minimalism; maple wood, soft neutrals; vertical 4:5.' \
  -F 'provider=imagen' \
  -F 'model=imagen-4.0-generate-001' \
  -F 'files=@living_room.jpg'
```

### cURL: Replicate SDXL with width/height and extra

```bash
curl -X POST http://localhost:8000/api/images/generate-multipart \
  -F 'prompt=A minimalist poster of Karachi skyline, vector style, 4:5' \
  -F 'provider=replicate' \
  -F 'model=stability-ai/sdxl' \
  -F 'temperature=0.2' \
  -F 'extra={"scheduler":"K_EULER_ANCESTRAL"}' \
  -F 'files=@seed.png'
```

---

## Postman Usage

- Create a new request with the endpoint URL.
- For JSON:
  - Select Body → raw → JSON and paste one of the JSON bodies above.
- For multipart:
  - Select Body → form‑data.
  - Add key `prompt` (Text), `provider` (Text), and `files` (File). Add multiple `files` rows to upload more images.
  - For `stop_sequences`, set type to Text and paste a JSON array string, e.g., `["END"]`.
  - For `extra` and `safety`, paste JSON object strings, e.g., `{"response_mime_type": "application/json"}`.

Postman cURL equivalents are provided in each sample for quick copy/paste.

---

## Providers & Models

- Gemini Nano Banana: `provider = gemini-nano-banana`, model default `gemini-2.5-flash-image-preview`
- Imagen 4: `provider = imagen`, models `imagen-4.0-ultra-generate-001`, `imagen-4.0-generate-001` (default), `imagen-4.0-fast-generate-001`
- Replicate: `provider = replicate`, default `stability-ai/sdxl` (override with any `owner/name` or `owner/name@version`)

See also:
- docs/image_gemini_nano_banana.md
- docs/image_imagen.md
- docs/image_replicate.md

---

## Notes & Limits

- Aspect ratio for Gemini/Imagen is guided via prompt text (no direct width/height in preview tiers). Default outputs ~1024 px.
- Replicate models define their own input schemas; pass model‑specific knobs via `extra` as needed.
- Safety policies apply; providers may refuse certain prompts or images.
- For production, download and persist images if providers return URLs (e.g., Replicate); URLs can be temporary.


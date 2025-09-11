# Image Generation API

Provider‑agnostic image generation and editing via a unified engine with pluggable drivers (Gemini Nano Banana, Imagen 4, Replicate with model-specific drivers).

Base path: `/api/images`

## Endpoints

- POST `/api/images/generate` — JSON body
- POST `/api/images/generate-multipart` — multipart form + file uploads

No defaults are injected by routes; only fields you provide are forwarded to the driver. Drivers and providers apply their own defaults.

## Requirements

- Set environment variables for providers you plan to use:
  - Google GenAI: `GOOGLE_API_KEY` (or Vertex: `GOOGLE_GENAI_USE_VERTEXAI=true`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`)
  - Replicate: `REPLICATE_API_TOKEN`
- Install SDKs in `requirements.txt` are already present: `google-genai`, `httpx` (for Replicate direct API).

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

### Sample: Replicate Seedream-4 (Text → Image)

```json
{
  "prompt": "A cozy cabin in a snowy forest, watercolor style, ultra-detailed",
  "provider": "replicate",
  "model": "bytedance/seedream-4",
  "width": 2048,
  "height": 1024,
  "ratio": "16:9",
  "num_images": 1
}
```

### Sample: Replicate FLUX Krea [dev] (Text → Image)

```json
{
  "prompt": "Professional portrait photography, studio lighting, shallow depth of field",
  "provider": "replicate",
  "model": "black-forest-labs/flux-krea-dev",
  "guidance_scale": 3.5,
  "steps": 35,
  "ratio": "3:4",
  "seed": 42
}
```

### Sample: Replicate Seedream-4 (Image Editing)

```json
{
  "prompt": "Remove the person in the background, keep everything else the same",
  "provider": "replicate",
  "model": "seedream-4",
  "images_b64": ["<base64-encoded-image>"],
  "ratio": "match_input_image"
}
```

**Note:** Replicate provider now supports only specific models with dedicated drivers:
- `bytedance/seedream-4` (aliases: `seedream-4`, `seedream4`): Advanced text-to-image and editing up to 4K
- `black-forest-labs/flux-krea-dev` (aliases: `flux-krea-dev`, `flux-krea`, `krea-dev`): Distinctive aesthetic style

Parameters are automatically mapped to model-specific requirements with validation.

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

### cURL: Replicate Seedream-4 with high resolution

```bash
curl -X POST http://localhost:8000/api/images/generate-multipart \
  -F 'prompt=A minimalist poster of Karachi skyline, vector style, ultra-detailed' \
  -F 'provider=replicate' \
  -F 'model=bytedance/seedream-4' \
  -F 'width=4096' \
  -F 'height=2048' \
  -F 'ratio=21:9'
```

### cURL: Replicate FLUX Krea [dev] with image-to-image

```bash
curl -X POST http://localhost:8000/api/images/generate-multipart \
  -F 'prompt=Transform into a professional headshot with studio lighting' \
  -F 'provider=replicate' \
  -F 'model=flux-krea-dev' \
  -F 'guidance_scale=3.0' \
  -F 'steps=40' \
  -F 'files=@portrait.jpg'
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

- **Gemini Nano Banana**: `provider = gemini-nano-banana`, model default `gemini-2.5-flash-image-preview`
- **Imagen 4**: `provider = imagen`, models `imagen-4.0-ultra-generate-001`, `imagen-4.0-generate-001` (default), `imagen-4.0-fast-generate-001`
- **Replicate**: `provider = replicate`, model-specific drivers only:
  - `bytedance/seedream-4` (default): Advanced text-to-image and editing up to 4K resolution
    - Aliases: `seedream-4`, `seedream4`
    - Features: Multi-resolution (1K/2K/4K/custom), image editing, up to 10 input images
  - `black-forest-labs/flux-krea-dev`: Distinctive aesthetic style with exceptional realism
    - Aliases: `flux-krea-dev`, `flux-krea`, `krea-dev`
    - Features: Photorealistic generation, single image input, optimized performance

**See detailed documentation:**
- docs/image_gemini_nano_banana.md
- docs/image_imagen.md
- docs/api/replicate-usage.md (comprehensive Replicate guide)

---

## Notes & Limits

- **Aspect ratio** for Gemini/Imagen is guided via prompt text (no direct width/height in preview tiers). Default outputs ~1024 px.
- **Replicate models** use dedicated drivers with automatic parameter mapping and validation:
  - Each model has specific parameter requirements and limits
  - Unsupported models will return clear error messages with available alternatives
  - Image input limits: Seedream-4 (max 10 images), FLUX Krea [dev] (max 1 image)
- **Safety policies** apply; providers may refuse certain prompts or images.
- **Image persistence**: Generated images are automatically downloaded and stored locally with public URLs.
- **Error handling**: Model-specific validation provides detailed error messages for parameter issues.

### Replicate-Specific Validation

The API validates Replicate requests and provides helpful errors:

```json
// Unsupported model error
{
  "detail": "Replicate model 'stability-ai/sdxl' is not supported. Supported models: bytedance/seedream-4, black-forest-labs/flux-krea-dev"
}

// Parameter validation error  
{
  "detail": "Replicate validation error: Parameter 'max_images' must be <= 15"
}

// File limit error
{
  "detail": "FLUX Krea [dev] supports only 1 input image"
}
```

### Parameter Mapping for Replicate Models

The API automatically maps unified parameters to model-specific requirements:

#### Seedream-4 Parameter Mapping
```
Unified API → Seedream-4 API
─────────────────────────────
prompt → prompt
images_b64 → image_input (array of data URIs)
num_images → max_images (when > 1, enables sequential generation)
width/height → size="custom" + width/height
ratio → aspect_ratio (with value mapping)
extra → additional model-specific parameters
```

#### FLUX Krea [dev] Parameter Mapping  
```
Unified API → FLUX Krea API
───────────────────────────
prompt → prompt
images_b64[0] → image (first image only as data URI)
seed → seed
num_images → num_outputs (max 4)
steps → num_inference_steps
guidance_scale → guidance  
ratio → aspect_ratio
extra → additional model-specific parameters
```


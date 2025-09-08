# Google Imagen 4 (Ultra / Standard / Fast) & Veo 2–3 — Developer Guide (Python, 2025)

> **Last verified:** 8 Sep 2025
> **Audience:** Backend engineers using **Python** with the **Gemini Developer API** (`google-genai`) or **Vertex AI** to generate **images (Imagen 4)** and **videos (Veo 2 / Veo 3)**.
> **Scope:** Install → auth → model IDs → request patterns → options → editing & multi‑image composition → safety → streaming → batching → responses → pricing.
> **Models covered:** `imagen-4.0-ultra-generate-001`, `imagen-4.0-generate-001` (standard), `imagen-4.0-fast-generate-001`, `veo-2.0-generate-001` and **Veo 3** availability/usage notes.

---

## 1) Install & Authenticate

```bash
pip install google-genai
# (Optional) faster async transport
pip install "google-genai[aiohttp]"
```

**Developer API (default):**

```bash
export GOOGLE_API_KEY="<YOUR_API_KEY>"
```

```python
from google import genai
client = genai.Client()  # Uses GOOGLE_API_KEY
```

**Vertex AI (server-side):**

```bash
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_CLOUD_PROJECT="<project-id>"
export GOOGLE_CLOUD_LOCATION="us-central1"   # or supported region
```

```python
from google import genai
client = genai.Client()  # auto-picks Vertex from env
```

*(Optional)* Pin REST version:

```python
from google.genai import types
client = genai.Client(http_options=types.HttpOptions(api_version="v1"))
```

---

## 2) Model IDs & When to Use What

| Family                  | Model ID (Vertex/Dev API)                            | Best for                                                               | Latency | Text fidelity | Typical output                               |
| ----------------------- | ---------------------------------------------------- | ---------------------------------------------------------------------- | ------- | ------------- | -------------------------------------------- |
| **Imagen 4 Ultra**      | `imagen-4.0-ultra-generate-001`                      | Highest quality, complex scenes, typography, product/marketing renders | High    | Excellent     | \~1024 px (square default; prompt‑guided AR) |
| **Imagen 4 (Standard)** | `imagen-4.0-generate-001`                            | General purpose, strong text rendering, balanced speed/quality         | Medium  | Very good     | \~1024 px                                    |
| **Imagen 4 Fast**       | `imagen-4.0-fast-generate-001`                       | Rapid iteration, high‑volume batches, prototyping                      | Low     | Good          | \~1024 px                                    |
| **Veo 2**               | `veo-2.0-generate-001`                               | **Text→video** & **image→video** 4–8 s shots; controllable motion      | Medium  | n/a (video)   | up to \~8 s clips                            |
| **Veo 3**               | *(consumer entry points; API availability evolving)* | Higher‑quality **photo→video** w/ native audio (sound fx/dialogue)     | Medium  | n/a (video)   | ≈6–8 s w/ audio                              |

> **Notes**
>
> * Imagen returns **images** (PNG/JPEG) as inline bytes. Specify aspect ratio and composition in the **prompt** (no direct width/height in preview tiers).
> * Veo 2 returns a **video** payload (MP4/WebM depending on backend). Veo 3 is currently accessible via consumer surfaces (Gemini/Photos) and select programs; check your region/account for API access.

---

## 3) Core Python Patterns (Imagen 4)

Imagen 4 uses the **same** `generate_content` method as text models. The response’s first candidate contains **image bytes** in `inline_data` parts.

### 3.1 Text → Image (Ultra)

```python
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO

client = genai.Client()

prompt = (
  "Ultra-detailed product hero shot of a stainless-steel espresso machine, "
  "studio lighting, crisp typography ‘CAFÉ PRO 500’ on the body, square"
)

resp = client.models.generate_content(
    model="imagen-4.0-ultra-generate-001",
    contents=[prompt],
)

img_part = next(
    p for p in resp.candidates[0].content.parts if getattr(p, "inline_data", None)
)
image = Image.open(BytesIO(img_part.inline_data.data))
image.save("espresso_ultra.png")
```

### 3.2 Image → Image (Edit)

Provide an input image and a text instruction.

```python
src = Image.open("living_room.jpg")

resp = client.models.generate_content(
  model="imagen-4.0-generate-001",
  contents=[
    "Restyle room to Scandinavian minimalism; maple woods, soft neutrals; vertical 4:5.",
    src,
  ],
)
Image.open(BytesIO(
  next(p for p in resp.candidates[0].content.parts if getattr(p, "inline_data", None)).inline_data.data
)).save("living_room_scandi.png")
```

### 3.3 Multi‑image Composition (Image + Image + Text)

Order images by **role** and be explicit in the prompt.

```python
product = Image.open("shoe.png")
scene   = Image.open("studio_bg.jpg")

resp = client.models.generate_content(
  model="imagen-4.0-fast-generate-001",
  contents=[
    "Place product on the first background; 3/4 angle, soft shadow; square.",
    scene,
    product,
  ],
)
Image.open(BytesIO(
  next(p for p in resp.candidates[0].content.parts if getattr(p, "inline_data", None)).inline_data.data
)).save("shoe_in_scene.png")
```

### 3.4 Image + Text → Image (Logo/sticker)

```python
resp = client.models.generate_content(
  model="imagen-4.0-generate-001",
  contents="A kawaii red panda sticker with bold outline; transparent or white background; square"
)
img = next(p for p in resp.candidates[0].content.parts if getattr(p, "inline_data", None))
Image.open(BytesIO(img.inline_data.data)).save("sticker.png")
```

### 3.5 Streaming (progressive text; image at end)

```python
for chunk in client.models.generate_content_stream(
    model="imagen-4.0-generate-001",
    contents="A watercolor cityscape at dusk, 16:9"
):
    # You may receive text/status parts; the image bytes typically arrive last
    pass
```

---

## 4) Configuration Options (Imagen 4)

Use `GenerateContentConfig` with the familiar decoding and safety knobs. Image‑specific controls are **prompt‑guided**.

| Field                | Type           | Use                                                                                     |
| -------------------- | -------------- | --------------------------------------------------------------------------------------- |
| `temperature`        | `float`        | Style/variation randomness; 0–0.3 for deterministic artboards, 0.6–0.9 for exploration. |
| `top_p`, `top_k`     | `float`, `int` | Decoding controls; defaults typically fine.                                             |
| `candidate_count`\*  | `int`          | Number of candidates to return (may be fixed to 1 on some tiers).                       |
| `safety_settings`    | list           | Per‑category thresholds; applies to image gen/edit too.                                 |
| `system_instruction` | `str/Content`  | Stable style guardrails across requests.                                                |
| `response_mime_type` | `str`          | Leave unset for image bytes. Use `application/json` for text‑only metadata outputs.     |

**Aspect ratio & size**

* Preview/stable Imagen 4 tiers target **\~1024 px** on the long side; guide AR via prompt: “square”, “vertical 4:5”, “16:9”, etc.
* Upscaling parameters are **not** exposed in Imagen 4 public endpoints as of this writing; use external upscalers post‑generation if needed.

**Safety**

* All Imagen outputs include a **SynthID** watermark. Safety filters may block certain prompts or edits.

---

## 5) Responses — What to Parse

```python
resp.candidates            # list[Candidate]
resp.candidates[0].content # Content with parts
for part in resp.candidates[0].content.parts:
    if getattr(part, "inline_data", None):
        data = part.inline_data.data     # image bytes
    elif getattr(part, "text", None):
        caption = part.text              # optional text

# Accounting / observability
resp.model_version         # concrete served version
resp.usage_metadata        # input/output token counts (images billed per-image)
resp.block_reason          # if safety blocked
```

---

## 6) Best‑Practice Recipes

1. **Deterministic brand renders**

```python
cfg = {"temperature": 0.15}
# Include canonical style tokens in the prompt (e.g., “softbox”, “product-on-seamless”, AR)
```

2. **High‑throughput pipelines (Fast)**

* Use **Imagen 4 Fast** for drafts/bulk. Promote winners to **Imagen 4 Ultra** for finals.
* Consider **Batch** endpoints where available to reduce cost.

3. **Multi‑image fusion**

* Describe **roles**: “Use the first as background; second is the subject; blend naturally; cast drop shadow.”
* Order image parts accordingly.

4. **Editing**

* Use concise **imperatives**: “replace background with …”, “change lighting to …”, “retouch skin subtly …”.
* Keep temperature modest (≤0.35) to preserve identity.

5. **Content governance**

* Define allow‑listed prompts/styles in your app; enforce schema‑bound metadata if mixing image + captions.

---

## 7) Veo 2 (Text/Image → Video) — Python

> **Model ID:** `veo-2.0-generate-001`
> **Outputs:** Short videos (≈4–8 s). Some backends support **image→video** by passing an image part with a motion prompt.

### 7.1 Text → Video

```python
prompt = (
  "A cinematic ocean wave rolling toward the shore at golden hour; "
  "gentle camera dolly-in; realistic physics"
)
resp = client.models.generate_content(
  model="veo-2.0-generate-001",
  contents=[prompt],
)
# Extract video bytes from inline data (e.g., mp4/webm depending on backend)
video_part = next(p for p in resp.candidates[0].content.parts if getattr(p, "inline_data", None))
open("wave.mp4", "wb").write(video_part.inline_data.data)
```

### 7.2 Image → Video

```python
from PIL import Image
still = Image.open("portrait.jpg")

resp = client.models.generate_content(
  model="veo-2.0-generate-001",
  contents=[
    "Subtle parallax and eye blink; 6 seconds; natural skin tones",
    still,
  ],
)
open("portrait_motion.mp4", "wb").write(
  next(p for p in resp.candidates[0].content.parts if getattr(p, "inline_data", None)).inline_data.data
)
```

**Tips**

* Specify **shot length** (e.g., “6 seconds”), **camera move**, and **motion intensity**.
* Use lower `temperature` for realism.

---

## 8) Veo 3 — What’s New & How to Access

* **Native audio**: Generates synchronized **sound effects, ambient audio, and dialogue** with video.
* **Higher realism & physics**: Better motion coherence and prompt adherence.
* **Access**: Rolling out in **consumer** experiences (e.g., Google Photos “photo→video”, Gemini apps) with daily gen limits tied to plan. Enterprise/API availability may vary by region and program. If you see a Veo 3 model in your backend, usage will mirror the Veo 2 patterns above (model ID will differ).

---

## 9) Pricing (high‑level; confirm per backend & region)

> **Imagen 4** (Developer API / Vertex AI):

* **Imagen 4 Fast**: \~**\$0.02 per image** (targeted for rapid, high‑volume generation).
* **Imagen 4 (Standard)**: commonly \~**\$0.04 per image** range in Vertex listings.
* **Imagen 4 Ultra**: **\$0.06 per image** initial public guidance (tiers differ by program and may evolve).
* **Batch** (where available): per‑image cost often \~**50%** of on‑demand.

> **Veo 2** (video):

* Priced **per second** or **per clip** depending on backend. Expect higher unit cost than image gen; check your Vertex/Gemini plan page.

> **Veo 3** (consumer):

* Included in **Google AI Pro / Ultra** consumer plans with daily generation limits; enterprise/API pricing is evolving.

> **General notes**

* All Imagen outputs include **SynthID** watermarking.
* Combining long prompts or additional modalities may incur token‑based charges alongside per‑image/clip rates on certain backends.
* Region, SLA tier, and batch vs interactive usage affect final pricing.

---

## 10) Troubleshooting

* **No image/video in response** → Ensure the correct **model ID** and scan `inline_data` parts.
* **Typography errors** → Use **Imagen 4 Ultra** and include font style hints (“condensed sans”, “all‑caps”).
* **Identity drift in edits** → Keep `temperature ≤ 0.35`, constrain prompt to precise edits.
* **Small output** → Prompt AR/framing; upscale post‑hoc if needed.
* **Safety blocks** → Rephrase content; abide by policy.

---

## 11) Quick Reference — Copy/Paste Snippets

**Client**

```python
from google import genai
client = genai.Client()  # Dev API
# client = genai.Client(http_options=types.HttpOptions(api_version="v1"))
```

**Imagen 4 Ultra text→image**

```python
client.models.generate_content(
  model="imagen-4.0-ultra-generate-001",
  contents=["Cinematic portrait lighting, vertical 4:5, magazine cover layout"]
)
```

**Imagen 4 edit**

```python
client.models.generate_content(
  model="imagen-4.0-generate-001",
  contents=["Replace background with misty forest; keep subject intact", Image.open("in.png")]
)
```

**Veo 2 text→video**

```python
client.models.generate_content(
  model="veo-2.0-generate-001",
  contents=["Macro shot of ink swirling in water; 6 seconds; tripod; 4k look"]
)
```

---

### Changelog

* **2025‑09‑08:** First consolidated Imagen 4 & Veo 2–3 Python developer guide with pricing pointers and model IDs.

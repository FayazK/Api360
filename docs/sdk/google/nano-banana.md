# Gemini 2.5 Flash Image ("Nano Banana") — Python SDK Guide

> **Last verified:** 8 Sep 2025
> **Audience:** Python developers using the **Google Gen AI SDK** (`google-genai`) with the **Gemini Developer API** or **Vertex AI**.
> **Scope:** End‑to‑end image **generation** and **editing** with **Gemini 2.5 Flash Image** (`gemini-2.5-flash-image-preview`), including text→image, image→image, and image+text→image, streaming, batching notes, response parsing, and pricing.

---

## 1) Model overview

**Gemini 2.5 Flash Image** (internally nicknamed **Nano Banana**) is Google’s image **generation & editing** model in the Gemini 2.5 family. It accepts **text** and/or **image(s)** and returns one or more **image parts** (plus optional text). Key capabilities:

* **Text→Image** with strong compositional control and long text rendering.
* **Image→Image editing** via natural language (background swaps, pose edits, cleanup, etc.).
* **Image+Text→Image** (multi‑image fusion; style/subject transfer; logo/product insertions).
* Default output size is **\~1024px** (square by default); aspect ratio can be guided in prompt (see §5).
* Outputs include an invisible **SynthID** watermark for provenance.

> **Model ID:** `gemini-2.5-flash-image-preview` (Developer API + Vertex).
> **Status:** Public preview; final interfaces may evolve.

---

## 2) Install & Auth

```bash
pip install google-genai
# (optional, faster async http client)
pip install "google-genai[aiohttp]"
```

**Developer API** (default):

```bash
export GOOGLE_API_KEY="<YOUR_API_KEY>"
```

```python
from google import genai
client = genai.Client()  # uses GOOGLE_API_KEY
```

**Vertex AI** (server‑side):

```bash
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_CLOUD_PROJECT="<project-id>"
export GOOGLE_CLOUD_LOCATION="us-central1"
```

```python
from google import genai
client = genai.Client()  # picks up env above
```

> To pin stable endpoints: `http_options=types.HttpOptions(api_version="v1")`.

---

## 3) Core API pattern

Unlike Imagen (which has `generate_images`), **Gemini 2.5 Flash Image** uses the **same** `generate_content` method as text models. Image bytes are returned as **`inline_data`** parts inside candidates.

```python
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO

client = genai.Client()

prompt = "Create a cinematic photo of a nano‑banana dessert under a starry sky."

resp = client.models.generate_content(
    model="gemini-2.5-flash-image-preview",
    contents=[prompt],
)

# Extract images (inline_data) from first candidate
images = [
    Image.open(BytesIO(part.inline_data.data))
    for part in resp.candidates[0].content.parts
    if getattr(part, "inline_data", None)
]

images[0].save("output.png")
```

**Notes**

* Returned parts may interleave **text** and **images**; parse both.
* The API typically returns **one candidate** in Developer API preview. Vertex may support more candidates depending on tier (see §10).

---

## 4) Inputs (`contents`) — full reference

Each request builds a `list[Content]` (user role) composed of **text** and/or **image** parts.

### 4.1 Text part

```python
types.Part.from_text("A photorealistic macro of dew on a leaf, vertical 4:5.")
```

### 4.2 Image part (local file → inline bytes)

```python
from PIL import Image
from io import BytesIO

img = Image.open("cat.png")  # or any RGBA/RGB image
# The SDK will handle base64; you may also pass bytes directly
image_part = img  # Pillow Image object is accepted by the SDK
# or: types.Part.from_bytes(data=open("cat.png", "rb").read(), mime_type="image/png")
```

### 4.3 Image part (URI)

```python
image_part = types.Part.from_uri(
    file_uri="gs://bucket/asset.jpg", mime_type="image/jpeg"
)
```

**Mixing parts**

```python
contents = [
  "Replace the background with a misty forest; keep subject intact.",
  image_part,
]
```

> You can pass **multiple images** by adding multiple image parts. Order matters: describe the role of each image in your prompt (e.g., “use the first as background, second as style reference”).

---

## 5) Generation & Editing Modes (with examples)

### 5.1 Text → Image (pure generation)

```python
resp = client.models.generate_content(
    model="gemini-2.5-flash-image-preview",
    contents=(
        "A photorealistic headshot, corporate, shallow depth of field, "
        "Rembrandt lighting, 3/4 angle, neutral background. Vertical 4:5."
    ),
)
img = next(
    Image.open(BytesIO(p.inline_data.data))
    for p in resp.candidates[0].content.parts if getattr(p, "inline_data", None)
)
img.save("headshot_4x5.png")
```

**Prompting tips**

* Specify **shot type** (close‑up, wide), **lens** (85mm), **lighting**, **mood**, **aspect ratio** (e.g., “square”, “16:9”, “vertical 4:5”).
* For logos/stickers, request **transparent or white background** explicitly.

### 5.2 Image → Image (edit via text)

```python
src = Image.open("living_room.jpg")

resp = client.models.generate_content(
    model="gemini-2.5-flash-image-preview",
    contents=[
        "Restyle the room with Scandinavian minimalism; maple wood, soft neutrals.",
        src,
    ],
)
Image.open(BytesIO(resp.candidates[0].content.parts[-1].inline_data.data)).save(
    "living_room_styled.png"
)
```

**Common edits**: background swap, cleanup/removal, lighting changes, colorway changes, pose edits, local retouching.

### 5.3 Image + Text → Image (multi‑image fusion / subject & style transfer)

```python
subject = Image.open("product.png")    # subject to insert
scene   = Image.open("kitchen_bg.jpg") # target background

resp = client.models.generate_content(
    model="gemini-2.5-flash-image-preview",
    contents=[
        "Place the product on the counter, soft morning light, add soft shadow; 3/4 view.",
        scene,
        subject,
    ],
)
Image.open(BytesIO(resp.candidates[0].content.parts[-1].inline_data.data)).save(
    "product_in_scene.png"
)
```

### 5.4 Interleaved outputs (image **and** text)

Ask for captions/specs together with the image.

```python
resp = client.models.generate_content(
    model="gemini-2.5-flash-image-preview",
    contents=[
      "Generate an illustrated recipe card and include a short 3‑step caption.",
    ],
)
for part in resp.candidates[0].content.parts:
    if getattr(part, "inline_data", None):
        Image.open(BytesIO(part.inline_data.data)).save("recipe.png")
    elif getattr(part, "text", None):
        print("Caption:\n", part.text)
```

### 5.5 Chat‑style iterative editing

```python
chat = client.chats.create(model="gemini-2.5-flash-image-preview")
print(chat.send_message("Make a studio portrait of a golden retriever, square.").text)
# (model returns image + optional text)
chat.send_message("Now add a red bandana and soften the lighting")
chat.send_message("Change background to teal and crop 4:5")
```

---

## 6) Configuration options (image‑relevant)

`GenerateContentConfig` works here as well. The most relevant fields for images are:

| Parameter            | Type           | Purpose                                                                                                                          |
| -------------------- | -------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `temperature`        | `float`        | Style/variation randomness. Lower = more deterministic.                                                                          |
| `top_p`, `top_k`     | `float`, `int` | Decoding controls (usually leave defaults).                                                                                      |
| `candidate_count`\*  | `int`          | Number of candidates (model/endpoint dependent; preview often fixed to 1).                                                       |
| `stop_sequences`     | `list[str]`    | Rarely used for image‑only responses.                                                                                            |
| `response_mime_type` | `str`          | If you need a **text‑only** result, set to `application/json` or `text/plain`. For images, omit; images return as `inline_data`. |
| `safety_settings`    | list           | Apply category thresholds for safety (applies to image gen/edit too).                                                            |
| `system_instruction` | `str/Content`  | Style guardrails across requests.                                                                                                |

\* *AI Studio Developer API preview typically enforces 1 candidate; Vertex may allow >1 depending on quota/tier.*

**Size/aspect**

* There is no dedicated width/height parameter in preview; guide **aspect ratio** and **framing** via **prompt** (e.g., “Square”, “16:9”, “Vertical 4:5”). Vertex docs state generation at **\~1024px**; higher resolutions/upscaling are not exposed in this preview.

---

## 7) Responses — fields & parsing

Common fields for image calls:

* `response.candidates[0].content.parts` → list of **text** and **image** parts.

  * **Image part:** `part.inline_data.data` (bytes) → open with Pillow.
  * **Text part:** `part.text` (captions/explanations).
* `response.usage_metadata` → token counts (input/output). Images are billed by **image** (converted internally to tokens); see §11.
* `response.model_version` → concrete model version that served the request.

**Streaming**

```python
for chunk in client.models.generate_content_stream(
    model="gemini-2.5-flash-image-preview",
    contents="A minimalist poster mockup, square."
):
    # Image parts arrive at the end; you may see text first
    ...
```

---

## 8) Production patterns

### 8.1 Deterministic pipelines

* Use **temperature=0–0.2** for consistency across reruns.
* Keep a **stable style system prompt**; pin **model version** for auditability.

### 8.2 Multi‑image fusion best practices

* Be explicit about the **role** of each image: *background*, *subject*, *style reference*, *logo*, etc.
* Order images in `contents` accordingly; reference them in prompt (“use the first as background…”).

### 8.3 Character & product consistency

* Seed with a **reference portrait/product** and add **style words** that should persist (e.g., “same jacket, same birthmark”).
* For serial edits, prefer **chat** to preserve context between turns.

### 8.4 Safety & policy

* Do not upload images you don’t have rights to. The service enforces image safety policies and may refuse requests.

### 8.5 Storage & formats

* Save images as **PNG** for lossless edits; convert to **JPEG** when file size matters.

---

## 9) End‑to‑end examples

### 9.1 Product compositing (two images + prompt)

```python
scene   = Image.open("scene.jpg")
product = Image.open("shoe.png")

resp = client.models.generate_content(
  model="gemini-2.5-flash-image-preview",
  contents=[
    "Place the shoe on the table, natural morning light, add soft drop shadow.",
    scene,
    product,
  ],
)
out = next(p for p in resp.candidates[0].content.parts if getattr(p, "inline_data", None))
Image.open(BytesIO(out.inline_data.data)).save("shoe_in_scene.png")
```

### 9.2 Portrait retouching (single image + prompt)

```python
portrait = Image.open("portrait.jpg")

resp = client.models.generate_content(
  model="gemini-2.5-flash-image-preview",
  contents=[
    "Convert to corporate headshot; subtle skin smoothing, neutral gray backdrop; vertical 4:5.",
    portrait,
  ],
)
Image.open(BytesIO(resp.candidates[0].content.parts[-1].inline_data.data)).save("headshot.png")
```

### 9.3 Sticker/logo with transparency

```python
resp = client.models.generate_content(
  model="gemini-2.5-flash-image-preview",
  contents="A kawaii red panda sticker with bold outlines; white or transparent background.",
)
img = Image.open(BytesIO(next(p for p in resp.candidates[0].content.parts if getattr(p, "inline_data", None)).inline_data.data))
img.save("sticker.png")
```

---

## 10) Limits, latency, and candidates

* **Default size:** \~**1024px** output in preview.
* **Candidates:** Developer API preview usually returns **1** candidate; Vertex may allow more depending on quota/region (and may differ across backends).
* **Rate limits:** Preview models may have more restrictive quotas than stable models.

---

## 11) Pricing (Developer API; Preview)

* **Per image:** **\$0.039 / image** (internally \~**1290 output tokens per 1024×1024**).
* For any text/audio/video tokens you pass alongside images, **use Gemini 2.5 Flash pricing** for those modalities.
* Standard Gemini token pricing & quotas apply if you combine modalities (e.g., long prompts with grounding).

> Pricing and preview status are subject to change. Confirm the latest in Google’s pricing pages before production rollout.

---

## 12) Troubleshooting

* **No image in response:** Ensure you selected `gemini-2.5-flash-image-preview` and that you’re scanning **`inline_data`** parts.
* **Blurry/small output:** Prompt for **aspect ratio/framing**; upscaling isn’t exposed in this preview.
* **Inconsistent edits:** Lower `temperature`, keep prompts highly specific, and iterate via **chat** to preserve context.
* **Multiple outputs:** Preview often returns a single candidate; loop over `parts` and `candidates` anyway to be future‑proof.

---

## 13) FAQ

**Q: How do I request multiple images at once?**
A: In preview, the API typically returns a single candidate. Some Vertex tiers may support multiple candidates—if available, set `candidate_count` in `GenerateContentConfig` and iterate over `response.candidates`.

**Q: Can I control width/height?**
A: Not directly in preview. Guide **aspect ratio** and composition via the prompt (e.g., “Square”, “16:9”, “Vertical 4:5”).

**Q: Are outputs watermarked?**
A: Yes—**SynthID** watermarking is applied to generated/edited images.

**Q: Can I combine more than two images?**
A: Yes; add multiple image parts and be explicit in the prompt about roles (background vs subject vs style).

---

### Changelog

* **2025‑09‑08:** First edition for the Gemini 2.5 Flash Image (Preview) SDK workflow.

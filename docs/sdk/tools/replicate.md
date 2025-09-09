# Replicate Python SDK — Comprehensive Developer Documentation

> **Last verified:** 9 Sep 2025
> **Scope:** Install → auth → clients → run models (sync/async) → streaming (SSE) → inputs/outputs/files → deployments & official vs community models → webhooks → pagination/filtering → error handling & retries → timeouts & concurrency → examples (text, image, audio, video) → pricing & cost control → troubleshooting & FAQs.
> **Audience:** Python developers using the **official Replicate Python client** to call the Replicate REST API.

---

## 1) Quick Start

### 1.1 Install

```bash
# Stable releases
pip install replicate
# For pre-releases if needed
pip install --pre replicate
```

### 1.2 Authenticate

Set your API token (from your Replicate account settings) as an environment variable, or pass it to the client.

```bash
export REPLICATE_API_TOKEN="<your_token>"
```

```python
import replicate
client = replicate.Client()                    # uses REPLICATE_API_TOKEN
# or: client = replicate.Client(api_token="<your_token>")
```

> **Python support:** Python 3.8+ (the SDK is generated with Stainless; ships typed sync & async clients).

---

## 2) Core Concepts

* **Models** live at `replicate.com/{owner}/{name}` and have **versions** (immutable hashes).
* **Predictions** are executions of a model version with your **input**.
* **Official models** are always-on and have predictable pricing; **community models** run on shared hardware and are billed by compute time.
* **Deployments** are private, pinned configurations of a model for production use in your org.
* **Synchronous** predictions block until done; **asynchronous** let you poll or stream events and receive webhooks.
* **Streaming** delivers incremental output over **Server‑Sent Events (SSE)**.

---

## 3) Run a Model (Sync)

### 3.1 By owner/name (latest version)

```python
import replicate

client = replicate.Client()

# Example: text-to-image (model depends on owner/name)
output = client.run(
    "stability-ai/sdxl:latest",
    input={
        "prompt": "A photorealistic espresso machine hero shot, 4:5",
        "num_inference_steps": 30,
        "guidance_scale": 7.5,
        # model-specific inputs... see the model page
    },
)
# output can be a URL list, bytes, or structured JSON depending on model
print(output)
```

### 3.2 Pin to a specific version

```python
VERSION = "3b5d13b9be8e4d6294c2f5a2a2e8a9c3bbedb23f7f7ee2e..."  # example digest
out = client.run(f"stability-ai/sdxl@{VERSION}", input={"prompt": "a lighthouse at dawn"})
```

### 3.3 Run official model via namespaced helper (if available)

Some SDKs expose convenience namespaces for **official models**; else use `client.run()` with the model slug.

---

## 4) Run a Model (Async)

### 4.1 Create and poll a prediction

```python
pred = client.predictions.create(
    model="replicate/hello-world",
    # or model_version="<version_hash>",
    input={"text": "ping"},
)
print(pred.id, pred.status)     # starting, processing, succeeded, failed, canceled

pred = client.predictions.get(pred.id)
print(pred.output)              # when completed
```

### 4.2 Cancel

```python
client.predictions.cancel(pred.id)
```

### 4.3 Async I/O (aio)

```python
from replicate import AsyncClient
ac = AsyncClient()
pred = await ac.predictions.create(model="replicate/hello-world", input={"text": "ping"})
# await ac.predictions.get(pred.id)
```

---

## 5) Streaming Output (SSE)

> Many models support **streaming**. You request streaming and iterate over **Server‑Sent Events**.

### 5.1 Python (sync) streaming

```python
for event in client.stream(
    model="stability-ai/sdxl",
    input={"prompt": "sunset over the alps, watercolor, 16:9"},
):
    # event.type may include: output, logs, metrics, completed, error
    if event.type == "output":
        print("chunk:", event.data)
```

### 5.2 Async streaming

```python
async for event in ac.stream(
    model="meta/llama-3-8b-instruct",
    input={"prompt": "Write a haiku about recursion"},
):
    ...
```

**Event fields** commonly include `type`, `data` (usually JSON or a partial token/image URL), and `id`. Finalization arrives with `completed`.

---

## 6) Inputs & Outputs

### 6.1 Input schema

Each model defines its own **input parameters** (see the model’s README). Typical patterns:

* **Text models**: `prompt`, `temperature`, `max_tokens`, `top_p`, `stop`, etc.
* **Image gen**: `prompt`, `negative_prompt`, `width`, `height`, `steps`, `guidance_scale`, `seed`, `image`/`mask` for img2img/inpainting.
* **Audio**: `prompt` (TTS), `audio` (transcription), `voice`, `format`.
* **Video**: `prompt`, `num_frames`/`seconds`, `fps`, `seed`, `image` for motion from still.

### 6.2 Files & large inputs

* Pass **URLs** for large assets where possible.
* Some official/community models accept direct **multipart** uploads; the Python client will handle upload when you pass file‑like objects in `input`.

### 6.3 Output schema

* **Structured**: JSON dicts with fields like `text`, `images` (URLs), `segments`, etc.
* **Binary**: image/video/audio data often returned as **URLs** (temporary). Download and persist if needed.
* **Streams**: incremental JSON/text chunks via SSE.

---

## 7) Deployments & Official vs Community Models

* **Official models**: Always-on, predictable pricing, maintained with authors; ideal for production SLAs.
* **Community models**: Huge variety; pay by compute time and hardware; cold starts possible.
* **Deployments**: Create a deployment from a model with fixed version + settings. Call via `deployments.predictions.create()` for better stability and governance.

### 7.1 Using deployments

```python
pred = client.deployments.predictions.create(
  owner="your-org",
  name="my-sdxl-prod",
  input={"prompt": "catalog shot, softbox lighting"},
)
print(pred.output)
```

---

## 8) Webhooks

Receive a POST when a prediction completes or fails.

```python
pred = client.predictions.create(
  model="replicate/hello-world",
  input={"text": "ping"},
  webhook="https://your.app/webhooks/replicate",
  webhook_events_filter=["completed", "failed"]
)
```

Your handler should verify authenticity (e.g., with signed secrets if configured) and idempotently upsert records.

---

## 9) Filtering, Listing & Pagination

```python
# List your predictions (most recent first by default)
for p in client.predictions.list(limit=20):
    print(p.id, p.status)

# Filter by status or model
rows = client.predictions.list(status="succeeded", model="stability-ai/sdxl")

# Pagination
page = client.predictions.list(limit=50)
while page.has_next_page:
    page = page.get_next_page()
```

---

## 10) Timeouts, Retries & Concurrency

* **Timeouts:** Configure client defaults or per‑call timeouts (the library uses `httpx` under the hood).
* **Retries:** Implement retry with exponential backoff for transient 5xx and `rate_limit_exceeded` errors.
* **Idempotency:** Use your own idempotency keys if you might retry `create` calls.
* **Concurrency:** For bulk, prefer **async** client and apply connection pools; consider **deployments** to avoid cold starts.

---

## 11) Examples by Modality

### 11.1 Text generation (LLM)

```python
out = client.run(
  "meta/llama-3-8b-instruct",
  input={
    "prompt": "Explain DHCP vs SLAAC in 5 bullets",
    "temperature": 0.2,
    "max_tokens": 300,
  },
)
print(out)
```

### 11.2 Image generation (txt2img)

```python
out = client.run(
  "stability-ai/sdxl",
  input={
    "prompt": "A minimalist poster of Karachi skyline, vector style, 4:5",
    "width": 1024,
    "height": 1280,
    "num_inference_steps": 30,
    "seed": 42,
  },
)
print(out)  # list of image URLs
```

### 11.3 Image-to-image (img2img) / inpainting

```python
with open("product.png", "rb") as f:
    out = client.run(
      "stability-ai/sdxl",
      input={
        "prompt": "Place product on white seamless with soft shadow",
        "image": f,
        # optionally include mask for inpaint
      },
    )
print(out)
```

### 11.4 Audio: TTS

```python
out = client.run(
  "fishaudio/fish-speech",
  input={
    "text": "Hello from Replicate!",
    "voice": "alloy",
    "format": "wav",
  },
)
# returns URL to audio
```

### 11.5 Video: text→video (model-dependent)

```python
out = client.run(
  "fal-ai/fast-video",
  input={
    "prompt": "A neon city loop at night; 6 seconds; 24 fps",
    "seconds": 6,
    "fps": 24,
  },
)
print(out)  # URL to mp4/webm
```

---

## 12) Security & Governance

* Store `REPLICATE_API_TOKEN` in a secret manager (1Password, Vault).
* Restrict outbound egress where possible; allowlist Replicate API hosts.
* Log model slug, version, and full input/output schemas for audit.
* Consider **official models** or **deployments** for clear SLAs and predictable pricing.

---

## 13) Pricing & Cost Control

**How pricing works (high level):**

* Many models are billed **by runtime seconds** on specific hardware (GPU/CPU). Price per second depends on hardware tier.
* Some models (esp. LLMs) may be billed **by input/output units** (tokens, characters, images).
* **Official models** advertise **predictable** pricing; community models show estimates on each model page.

**Tips to reduce cost:**

* Prefer **Fast/Small** variants for drafts; promote winners to higher‑quality runs.
* Use **async** + **streaming** to exit early when acceptable output is reached.
* Pin **versions** to avoid regressions; cache intermediate assets; dedupe requests with idempotency keys.
* Batch small jobs via your queue; avoid many tiny predictions that incur overhead.

---

## 14) Troubleshooting

* **`No API token provided`** → Set `REPLICATE_API_TOKEN` or pass `api_token=...` to `Client`.
* **`model not found`** → Confirm owner/name and version hash; ensure you have access (private models require membership).
* **`permission denied`** → You may be calling a private deployment or a paid tier without credits.
* **`timeout`** → Increase client timeout; use async and poll; verify the model isn’t cold‑starting.
* **Webhook not firing** → Check URL reachability and TLS; ensure you added `webhook_events_filter`; make handler idempotent.
* **Empty/invalid output** → Inspect the prediction events/`logs`; many models write errors to logs even on success.

---

## 15) Reference — Common Client Methods

### 15.1 High-level

* `Client.run(model, input, **kwargs)` — Synchronous one‑shot.
* `Client.stream(model, input, **kwargs)` — Iterate SSE events.

### 15.2 Predictions

* `predictions.create(model=..., input=..., webhook=..., webhook_events_filter=[...])`
* `predictions.get(id)` / `predictions.cancel(id)`
* `predictions.list(limit=..., before=..., status=..., model=...)` (+ pagination helpers)

### 15.3 Models

* `models.get(owner, name)` → metadata & versions
* `models.versions.list(owner, name)` / `models.versions.get(owner, name, version)`
* `models.readme(owner, name)` → Markdown README text
* `models.examples(owner, name)` → example inputs

### 15.4 Deployments

* `deployments.predictions.create(owner=..., name=..., input=...)`

---

## 16) End‑to‑End Sample: Queue Worker Pattern

```python
# worker.py
import os, time, json
import replicate
from tenacity import retry, stop_after_attempt, wait_exponential

client = replicate.Client()

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=1, max=20))
def run_job(job):
    pred = client.predictions.create(
        model=job["model"],
        input=job["input"],
        webhook=os.environ.get("WEBHOOK_URL"),
        webhook_events_filter=["completed", "failed"],
    )
    # Optionally poll until done (or just return pred.id and handle via webhook)
    while pred.status not in {"succeeded", "failed", "canceled"}:
        time.sleep(2)
        pred = client.predictions.get(pred.id)
    if pred.status != "succeeded":
        raise RuntimeError(f"Prediction failed: {pred.error}")
    return pred.output
```

---

## 17) FAQ

**Q: How do I know which inputs/outputs a model expects?**
A: Open the model page on Replicate and read its **README**; you can fetch it programmatically via the API or `client.models.readme(owner, name)`.

**Q: Can I run private models?**
A: Yes, if you have access to the model or deployment within your org.

**Q: Does Replicate store my outputs?**
A: URLs are often temporary; proactively download and store outputs you need to keep.

**Q: Is there a free tier?**
A: Promotions vary. You’ll need **credits** or a **billing method** for most production use.

**Q: What’s the difference between sync and async?**
A: **Sync** returns only after completion; **async** returns immediately with an ID; you poll, stream, or receive a webhook.

---

### Changelog

* **2025‑09‑09:** First comprehensive edition aligned with the 2.x Python client (sync + async, SSE streaming, deployments, official/community models, and pricing guidance).

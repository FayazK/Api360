# Gemini GenAI SDK (Python)

**Complete developer guide for text generation with the Google Gen AI SDK** (`google-genai`) covering installation, authentication, client setup, content structures, configuration parameters, streaming, safety & tools, response schemas, error handling, token counting, batching, and a comprehensive **model & pricing matrix** for Gemini **1.5 → 2.5** (including 2.5 Pro / Flash / Flash‑Lite, 2.0 Flash & Flash‑Lite, and relevant Live/Preview variants).

> **Last verified:** 8 Sep 2025
> **Intended audience:** Backend/ML engineers integrating Gemini via the Gen AI SDK (Gemini Developer API and Vertex AI).
> **Scope:** Text generation (multimodal inputs allowed). Image/video/TTS are referenced only where they affect parameters and pricing.

---

## 1) Quick Start

### 1.1 Install

```bash
pip install google-genai
# (Optional, faster async transport)
pip install "google-genai[aiohttp]"
```

### 1.2 Import & minimal example

```python
from google import genai

client = genai.Client()  # Uses GOOGLE_API_KEY by default for Gemini Developer API

resp = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Write a 2‑sentence summary of IPv6."
)
print(resp.text)
```

### 1.3 Authentication

**Gemini Developer API** (default):

```bash
export GOOGLE_API_KEY="<YOUR_API_KEY>"
```

```python
from google import genai
client = genai.Client()  # or genai.Client(api_key="...")
```

**Vertex AI (server-side Google Cloud)**:

```bash
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_CLOUD_PROJECT="<project-id>"
export GOOGLE_CLOUD_LOCATION="us-central1"  # or another supported region
```

```python
from google import genai
client = genai.Client()  # auto-reads env for Vertex AI
```

### 1.4 Selecting API versions

```python
from google import genai
from google.genai import types

client = genai.Client(
    http_options=types.HttpOptions(api_version="v1")  # or v1alpha, etc.
)
```

---

## 2) Generating Text

### 2.1 The `generate_content` call

```python
from google import genai
from google.genai import types

client = genai.Client()

resp = client.models.generate_content(
    model="gemini-2.5-pro",     # or another model id below
    contents=[
        types.UserContent(parts=[
            types.Part.from_text("Explain DNS over HTTPS in simple terms"),
            # multimodal: add image/audio/video/file parts if needed
        ])
    ],
    config=types.GenerateContentConfig(
        temperature=0.2,
        top_p=0.95,
        top_k=40,
        candidate_count=1,
        max_output_tokens=800,
        stop_sequences=["\nEND"],
        seed=42,
        presence_penalty=0.0,
        frequency_penalty=0.0,
        system_instruction=(
            "You are a precise technical writer. Prefer bullet points and code."
        ),
        safety_settings=[
            types.SafetySetting(
                category="HARM_CATEGORY_HATE_SPEECH",
                threshold="BLOCK_ONLY_HIGH",
            ),
        ],
        # Structured output (see §5)
        # response_mime_type="application/json",
        # response_schema={...},
    ),
)

print(resp.text)
```

### 2.2 Synchronous streaming

```python
for chunk in client.models.generate_content_stream(
    model="gemini-2.5-flash",
    contents="Draft a 120-word abstract about solar flares."
):
    print(chunk.text, end="")
```

### 2.3 Asynchronous (non‑streaming & streaming)

```python
# non-streaming
resp = await client.aio.models.generate_content(
    model="gemini-2.5-flash",
    contents="List 5 key differences between DHCP and SLAAC."
)
print(resp.text)
```

```python
# streaming
async for chunk in await client.aio.models.generate_content_stream(
    model="gemini-2.5-flash",
    contents="Tell a 10-line poem about recursion."
):
    print(chunk.text, end="")
```

---

## 3) Inputs (`contents`) — Types & Patterns

`contents` ultimately becomes a `list[types.Content]`. The SDK lets you pass:

* **String** → wrapped as one `UserContent` with a single text `Part`.
* **List\[str]** → wrapped as one `UserContent` with multiple text `Part`s.
* \`\` → used verbatim (canonical form).
* `** / **` → explicit roles.
* \`\`\*\* variants\*\*:

  * `Part.from_text(text)`
  * `Part.from_uri(file_uri, mime_type)` (GCS or web URIs)
  * `Part.from_bytes(data: bytes, mime_type)`
  * `Part.from_function_call(name, args)` (model → tool call)
  * (When using the Files API with Gemini Developer API) you can upload files and pass returned file references as parts.

**Role grouping rules**:

* Non‑functioncall parts group into a **single** `UserContent`.
* Function‑call parts group into a **single** `ModelContent` (role = model).
* Nested lists inside `contents` may be used to group multiple `Part`s into a single `UserContent` easily.

**Multimodal**: You may mix text with **images**, **audio**, **video**, **PDFs** (see model capability table for each model’s input support & token limits).

---

## 4) Configuration (`GenerateContentConfig`) — **Full Parameter Reference**

Use either a plain dict or the typed `google.genai.types.GenerateContentConfig`. Defaults and ranges can differ per model (see model docs). Below are the commonly exposed fields in the Gen AI SDK that affect **text generation**.

| Parameter                             | Type                                            | Purpose / Effect                                                                          | Common Range / Notes                                  |
| ------------------------------------- | ----------------------------------------------- | ----------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| `temperature`                         | `float`                                         | Controls randomness. Lower → deterministic; higher → more creative.                       | Typical 0.0 – 1.0. Often 0.0–0.7 for production.      |
| `top_p`                               | `float`                                         | Nucleus sampling; model samples from top cumulative probability `p`.                      | 0.0–1.0 (e.g., 0.9–0.95).                             |
| `top_k`                               | `int`                                           | Limits candidate tokens per step to top *k* by probability.                               | 1–100+; common 20–50.                                 |
| `max_output_tokens`                   | `int`                                           | Upper bound on tokens in the **output**.                                                  | Respect model limits (see table).                     |
| `candidate_count`                     | `int`                                           | Number of candidates to return per call.                                                  | 1–8 (cost scales with outputs).                       |
| `stop_sequences`                      | `list[str]`                                     | Hard stop when sequence encountered.                                                      | Useful for protocols/templates.                       |
| `seed`                                | `int`                                           | Pseudo‑random seed for reproducibility.                                                   | Same seed + params → more stable outputs.             |
| `system_instruction`                  | `str` or `Content`                              | System prompt to steer behavior.                                                          | Keep concise & stable; pair with safety/tool configs. |
| `safety_settings`                     | `list[SafetySetting]`                           | Per‑category thresholds to block unsafe content.                                          | See §6.                                               |
| `response_mime_type`                  | `str`                                           | Response type (e.g., `application/json`, `text/x.enum`).                                  | See §5 for structured/enum outputs.                   |
| `response_schema`                     | Pydantic model / TypedDict / Enum / JSON schema | Enforces JSON shape or enumerations.                                                      | Strongly recommended for tool/agent pipelines.        |
| `tools`                               | `list[Tool]`                                    | Tool declarations for function calling / code execution / search grounding / URL context. | See §7.                                               |
| `tool_config`                         | `ToolConfig`                                    | Control tool‑use modes (auto/any/manual), rate limits, etc.                               | See §7.                                               |
| `memo` / `cache` / `caching_config`   | object                                          | Context caching hints to reduce costs/latency.                                            | Availability varies by model & tier.                  |
| `thinking` / `thinking_budget_tokens` | object / int                                    | Enable & size **thinking tokens** (2.x “with thinking”).                                  | Applies to 2.5 Pro/Flash; billed as output tokens.    |
| `json_mode`                           | bool or mime                                    | Alias for `response_mime_type="application/json"`.                                        | Prefer explicit `response_schema`.                    |
| `grounding`                           | config                                          | Search grounding (Google Search) or URL context.                                          | Extra charges/limits may apply.                       |
| `language` / `locale`                 | str                                             | Target language hints for output.                                                         | Optional.                                             |

> **Tip:** Many parameters are also available on the **Chats API** (`chat.send_message`) with the same semantics.

---

## 5) Structured Outputs (JSON & Enums)

### 5.1 JSON schemas

```python
from google.genai import types

schema = {
  "type": "object",
  "properties": {
    "title": {"type": "string"},
    "bullets": {"type": "array", "items": {"type": "string"}}
  },
  "required": ["title", "bullets"]
}

resp = client.models.generate_content(
  model="gemini-2.5-pro",
  contents="Summarize RFC 1035; include 5 bullets.",
  config=types.GenerateContentConfig(
    response_mime_type="application/json",
    response_schema=schema,
    temperature=0
  )
)
print(resp.text)   # JSON string
```

### 5.2 Enum responses

```python
from enum import Enum
class Severity(Enum): LOW="low"; MEDIUM="medium"; HIGH="high"

resp = client.models.generate_content(
  model="gemini-2.5-flash",
  contents="Pick a severity for: CPU at 95% for 5 minutes",
  config={
    "response_mime_type": "text/x.enum",
    "response_schema": Severity
  }
)
print(resp.text)  # e.g., "HIGH"
```

---

## 6) Safety Settings

Example below blocks only **high** likelihood hate‑speech.

```python
from google.genai import types
resp = client.models.generate_content(
  model="gemini-2.0-flash",
  contents="Say something bad.",
  config=types.GenerateContentConfig(
    safety_settings=[
      types.SafetySetting(
        category="HARM_CATEGORY_HATE_SPEECH",
        threshold="BLOCK_ONLY_HIGH",
      )
    ]
  )
)
print(resp.text)
```

**Common categories** include: harassment, hate speech, sexual content, dangerous content, etc. Thresholds typically include: `BLOCK_NONE`, `BLOCK_LOW_AND_ABOVE`, `BLOCK_MEDIUM_AND_ABOVE`, `BLOCK_ONLY_HIGH`.

---

## 7) Tools & Function Calling (incl. Code Execution, Search Grounding, URL Context)

### 7.1 Declare tools for function calling

```python
from google.genai import types

weather_tool = types.Tool.from_function_declarations([
  types.FunctionDeclaration(
    name="get_weather_by_city",
    description="Get weather by city name",
    parameters={
      "type": "object",
      "properties": {"city": {"type": "string"}},
      "required": ["city"],
    },
  )
])

resp = client.models.generate_content(
  model="gemini-2.5-pro",
  contents="What’s the weather in Quetta?",
  config=types.GenerateContentConfig(
    tools=[weather_tool],
    # tool_config=types.ToolConfig(mode="AUTO"),  # AUTO / ANY / MANUAL
  )
)

# If the model calls the tool, you’ll see a function call part in resp:
for cand in resp.candidates:
  for part in cand.content.parts:
    if part.function_call:
      name = part.function_call.name
      args = part.function_call.args
      # 1) Execute your backend function with args
      # 2) Send the tool result back as a message part
```

### 7.2 Returning tool results to the model

```python
result_part = types.Part.from_function_response(
  name="get_weather_by_city",
  response={"temp_c": 31, "condition": "Sunny"}
)

resp2 = client.models.generate_content(
  model="gemini-2.5-pro",
  contents=[result_part]
)
print(resp2.text)
```

### 7.3 Other built‑in tools

* **Code execution** (sandboxed interpreter; great for math/code tasks)
* **Search grounding** (Google Search)
* **URL context** (fetch and ground on provided URLs)
* **Caching** (context caches)

> Tool availability differs by model; see the capability matrix below.

---

## 8) Response Objects — Fields You Should Parse

For **text generation**, you’ll typically use:

* `response.text` → First candidate’s plain text (helper provided by SDK).
* `response.candidates` → List of candidates. Each has `content.parts` (text, function calls/responses, etc.) and may contain `safety_ratings`.
* `response.model_version` → Concrete version string that served your request.
* `response.usage_metadata` → Token counts (input/output/total, possibly thinking tokens in 2.5).
* `response.grounding_metadata` → If search/URL grounding enabled, links & citations.
* `response.block_reason` / `safety_ratings` → If blocked.
* For **streaming**, each `chunk` has similar shape; progressively accumulate `chunk.text`.

**Error handling**

```python
from google.genai import errors
try:
  client.models.generate_content(model="invalid", contents="ping")
except errors.APIError as e:
  print(e.code, e.message)
```

---

## 9) Token Utilities, Long Context & Batching

### 9.1 Count/compute tokens

```python
from google.genai import types

usage = client.tokens.count(
  model="gemini-2.5-flash",
  contents="How many tokens will this take?"
)
print(usage)
```

### 9.2 Context caching (cost/latency optimization)

* Pin large shared prompts/docs into a **cache**; reuse across requests.
* Storage and per‑request cache prices differ per model (see pricing).

### 9.3 Batch mode

* Submit large offline jobs for lower unit prices (supported on 2.5 Flash/Flash‑Lite and 2.0 Flash; see pricing).

---

## 10) Files API (Gemini Developer API)

Upload PDFs or other assets and reference in `contents`.

```python
file = client.files.upload(file="paper.pdf")
resp = client.models.generate_content(
  model="gemini-2.5-pro",
  contents=["Summarize the attached", file]
)
```

> Files API is not available on Vertex AI’s GenAI SDK; use GCS/URIs instead.

---

## 11) Chats API (Multi‑turn)

```python
chat = client.chats.create(model="gemini-2.5-flash")
print(chat.send_message("Tell me a riddle").text)
print(chat.send_message("Explain the riddle").text)
```

Streaming variants `send_message_stream` and async versions are available.

---

## 12) Model & Capability Matrix (Gemini 1.5 → 2.5)

> **Notes:** “Thinking” refers to models that allocate *thinking tokens* (counted as output). “Context window” shows **input**/**output** token limits (rounded). Availability/attributes may vary by region/version.

| Model (ID)                                                              | Status            | Inputs → Output                           | Context window (input/output) | Thinking            | Function calling | Code exec | Grounding (Search / URL) | Caching                | Batch            | Live API            | Image gen                   | Audio gen | Knowledge cutoff | Latest update |
| ----------------------------------------------------------------------- | ----------------- | ----------------------------------------- | ----------------------------- | ------------------- | ---------------- | --------- | ------------------------ | ---------------------- | ---------------- | ------------------- | --------------------------- | --------- | ---------------- | ------------- |
| **gemini-2.5-pro**                                                      | Stable            | text, image, video, audio, PDF → **text** | \~1,048,576 / 65,536          | **On**              | Yes              | Yes       | Yes / Yes                | Yes                    | Yes              | No                  | No                          | No        | Jan 2025         | Jun 2025      |
| **gemini-2.5-flash**                                                    | Stable            | text, image, video, audio → **text**      | \~1,048,576 / 65,536          | **On** (budgetable) | Yes              | Yes       | Yes / Yes                | Yes                    | Yes              | No                  | No                          | No        | Jan 2025         | Jun 2025      |
| **gemini-2.5-flash-lite**                                               | Stable            | text, image, video, audio, PDF → **text** | \~1,048,576 / 65,536          | **On** (budgetable) | Yes              | Yes       | Yes / Yes                | Yes                    | Yes              | No                  | No                          | No        | Jan 2025         | Jul 2025      |
| **gemini-live-2.5-flash-preview**                                       | Preview           | text, audio, video → **text, audio**      | \~1,048,576 / 8,192           | Off                 | Yes              | Yes       | Yes / Yes                | –                      | No               | **Yes**             | No                          | **Yes**   | Jan 2025         | Jun 2025      |
| **gemini-2.5-flash-preview-native-audio-dialog** (and *-exp-* thinking) | Preview           | audio, video, text → **text+audio**       | (model‑specific)              | Mixed               | Yes              | Yes       | Yes / Yes                | –                      | –                | **Live**            | No                          | **Yes**   | –                | 2025          |
| **gemini-2.5-flash-image-preview**                                      | Preview           | image, text → **image & text**            | (image‑specific)              | n/a                 | –                | –         | – / –                    | –                      | **Batch avail.** | –                   | **Yes**                     | –         | –                | 2025          |
| **gemini-2.5-flash-preview-tts**                                        | Preview           | text → **audio**                          | (tts‑specific)                | n/a                 | –                | –         | – / –                    | –                      | –                | –                   | –                           | **Yes**   | –                | 2025          |
| **gemini-2.0-flash**                                                    | Stable            | text, image, video, audio → **text**      | \~1,000,000 / (model default) | Off                 | Yes              | Yes       | Yes / Yes                | Yes                    | Yes              | Live pricing avail. | **Image** (preview pricing) | –         | –                | 2025          |
| **gemini-2.0-flash-lite**                                               | Stable            | text, image, video, audio → **text**      | (smaller)                     | Off                 | Yes              | Yes       | Limited / –              | (No cache)             | Batch            | –                   | –                           | –         | –                | 2025          |
| **gemini-1.5-pro**                                                      | **Deprecated**    | text, image, video, audio → **text**      | 2,000,000 / (model default)   | Off                 | Yes              | Yes       | Limited / –              | Paid                   | –                | –                   | –                           | –         | –                | 2025          |
| **gemini-1.5-flash**                                                    | Stable (1.5 line) | text, image, video, audio → **text**      | 1,000,000 / (model default)   | Off                 | Yes              | Yes       | Limited / –              | Free cache up to limit | –                | –                   | –                           | –         | –                | 2025          |
| **gemini-1.5-flash-8b**                                                 | Stable (1.5 line) | text, image, video, audio → **text**      | 1,000,000 / (model default)   | Off                 | Yes              | Yes       | Limited / –              | Low‑cost cache         | –                | –                   | –                           | –         | –                | 2025          |

*Where a cell shows “–”, the feature is not applicable or not publicly specified. Always check the model’s page before production launches.*

---

## 13) Pricing (Developer API) — **Per 1M tokens unless noted**

> Prices are USD and depend on prompt size (some tiers split at 128k or 200k tokens) and media type. **Batch** and **context caching** often have reduced rates. **Thinking tokens** are included in output pricing for 2.5 models. Search/grounding may have additional request‑based fees. Image generation uses token‑based equivalents per image.

### 13.1 Gemini 2.5 series

* **2.5 Pro (text):**

  * **Input:** \$1.25 ≤ 200k‑token prompts; \$2.50 > 200k
  * **Output (incl. thinking):** \$10.00 ≤ 200k; \$15.00 > 200k
  * **Context caching (per request):** \$0.31 ≤ 200k; \$0.625 > 200k
  * **Cache storage:** \$4.50 / 1M tokens / hour
  * **Grounding (Search):** 1,500 RPD free, then \$35 / 1K requests

* **2.5 Flash (text/image/video/audio → text):**

  * **Standard Input:** \$0.30 (text/image/video); \$1.00 (audio)
  * **Standard Output (incl. thinking):** \$2.50
  * **Context caching (per request):** \$0.075 (text/image/video); \$0.25 (audio)
  * **Cache storage:** \$1.00 / 1M tokens / hour
  * **Live API:** Input \$0.50 (text), \$3.00 (audio/image\[video]); Output \$2.00 (text), \$12.00 (audio)
  * **Batch:** Input \$0.15 (text/image/video); \$0.50 (audio); Output \$1.25
  * **Grounding (Search):** shared free limit with Flash‑Lite (see below); then \$35 / 1K

* **2.5 Flash‑Lite (cost‑optimized):**

  * **Standard Input:** \$0.10 (text/image/video); \$0.30 (audio)
  * **Standard Output (incl. thinking):** \$0.40
  * **Context caching (per request):** \$0.025 (text/image/video); \$0.125 (audio)
  * **Cache storage:** \$1.00 / 1M tokens / hour
  * **Batch:** Input \$0.05 (text/image/video); \$0.15 (audio); Output \$0.20
  * **Grounding (Search):** 1,500 RPD free (shared with Flash), then \$35 / 1K

* **2.5 Flash Image (Preview):**

  * **Input:** \$0.30 (text/image)
  * **Output:** **\$0.039 per image** (≈ \$30 per 1M image tokens; 1024×1024 uses ≈1290 tokens)
  * **Batch:** Input \$0.15 (text/image); Output \$0.0195 per image

* **2.5 Flash TTS (Preview):**

  * **Input:** \$0.50 (text)
  * **Output:** \$10.00 (audio)

### 13.2 Gemini 2.0 Flash line

* **2.0 Flash (balanced, 1M context):**

  * **Standard Input:** \$0.10 (text/image/video); \$0.70 (audio)
  * **Standard Output:** \$0.40
  * **Context caching (per request):** \$0.025 (text/image/video); \$0.175 (audio)
  * **Cache storage:** \$1.00 / 1M tokens / hour
  * **Image gen:** \$0.039 per image (Std), \$0.0195 (Batch)
  * **Live API:** Input \$0.35 (text), \$2.10 (audio/image\[video]); Output \$1.50 (text), \$8.50 (audio)

* **2.0 Flash‑Lite:**

  * **Standard Input:** \$0.075
  * **Standard Output:** \$0.30
  * **(No cache pricing and no grounding listed at standard tier)**

### 13.3 Gemini 1.5 line

* **1.5 Pro (2M context)** — **Input:** \$1.25 ≤128k; \$2.50 >128k. **Output:** \$5.00 ≤128k; \$10.00 >128k.
  **Cache per‑request:** \$0.3125 ≤128k; \$0.625 >128k. **Storage:** \$4.50 / 1M tokens / hour. **Grounding:** \$35 / 1K.
* **1.5 Flash** — **Input:** \$0.075 ≤128k; \$0.15 >128k. **Output:** \$0.30 ≤128k; \$0.60 >128k.
  **Cache per‑request:** *Free* up to 1M tokens/hour storage; then \$0.01875 ≤128k; \$0.0375 >128k. **Storage:** \$1.00 / 1M tokens / hour.
* **1.5 Flash‑8B** — **Input:** \$0.0375 ≤128k; \$0.075 >128k. **Output:** \$0.15 ≤128k; \$0.30 >128k.
  **Cache per‑request:** \$0.01 ≤128k; \$0.02 >128k. **Storage:** \$0.25 / 1M tokens / hour.

> `RPD` = requests per day included for grounding with Google Search (free tier buckets exist on some 2.x models; shared between Flash and Flash‑Lite as noted). Actual availability and limits can vary by region/account/tier.

---

## 14) Best‑Practice Recipes

1. **Deterministic API output** (JSON):

```python
cfg = {
  "temperature": 0,
  "response_mime_type": "application/json",
  "response_schema": {
    "type": "object",
    "properties": {"facts": {"type": "array", "items": {"type": "string"}}},
    "required": ["facts"]
  }
}
resp = client.models.generate_content(
  model="gemini-2.5-pro",
  contents="Give 3 facts about the IPv4 header.",
  config=cfg
)
```

2. **Tool‑augmented reasoning** (AUTO function calling):

```python
cfg = {
  "tools": [weather_tool],
  "tool_config": {"mode": "AUTO"},
  "temperature": 0.2
}
resp = client.models.generate_content(
  model="gemini-2.5-flash",
  contents="What is the weather in Karachi now?"
)
```

3. **Long reports with bounded length**:

```python
resp = client.models.generate_content(
  model="gemini-2.5-flash",
  contents="Write a 6‑section incident report (≤700 tokens).",
  config={"max_output_tokens": 700, "temperature": 0.2}
)
```

4. **High‑throughput pipelines** (Batch + Flash‑Lite):

* Use **Batch** endpoints for cheaper rates.
* Pin shared docs in **context cache**; pass small deltas per request.

---

## 15) Troubleshooting & Operational Guidance

* **Sudden cost spikes:** Audit candidate counts, streaming concatenation, grounding usage, and thinking budgets (2.5). Consider **Batch** or **Flash‑Lite**. Use token counters in CI.
* **Safety blocks:** Lower thresholds selectively or restructure prompts; never disable all categories in production.
* **JSON breakage:** Enforce schemas and set `temperature=0` + `max_output_tokens` headroom.
* **Grounding latency:** Pre‑fetch with URL context for deterministic sources; cap grounding per request.
* **Model drift:** Pin a **stable** version string (e.g., `gemini-2.5-flash-YYYYMMDD`).
* **Rate limits:** Check model‑specific rate‑limit docs; plan retries with jitter and idempotency keys.

---

## 16) Appendix — Full Parameter Index (SDK Types)

Below are the most relevant Gen AI SDK types you will encounter when generating **text**. (This list focuses on fields commonly used in production; the SDK exposes additional enumerations and nested types.)

### 16.1 `GenerateContentConfig`

* **Decoding**: `temperature`, `top_p`, `top_k`, `max_output_tokens`, `candidate_count`, `stop_sequences`, `seed`
* **Safety**: `safety_settings: list[SafetySetting]`
* **System**: `system_instruction: str | Content`
* **Schema**: `response_mime_type`, `response_schema`
* **Tools**: `tools: list[Tool]`, `tool_config`
* **Thinking** (2.5): `thinking`, `thinking_budget_tokens`
* **Grounding/URL**: `grounding_config`, `url_context`
* **Caching**: `caching_config`
* **Misc**: `language`/`locale`

### 16.2 Content & Parts

* `Content(role: "user"|"model", parts: list[Part])`
* `UserContent` / `ModelContent` (role‑specialized)
* `Part.from_text(text)`
* `Part.from_uri(file_uri, mime_type)`
* `Part.from_bytes(data, mime_type)`
* `Part.from_function_call(name, args)` / `Part.from_function_response(name, response)`

### 16.3 Responses

* `Response.text` (helper)
* `Response.candidates -> list[Candidate]`

  * `Candidate.content.parts -> list[Part]`
  * `Candidate.safety_ratings`
  * `Candidate.grounding_metadata`
* `Response.usage_metadata` (input, output, total, possibly thinking)
* `Response.model_version`
* `Response.block_reason`

### 16.4 Errors

* `errors.APIError` → `code`, `message`

### 16.5 Async clients & HTTP options

* `client.aio` → async namespace
* `types.HttpOptions(api_version, client_args, async_client_args)`

---

## 17) Migration Notes (Developer API ↔ Vertex AI)

* The **same SDK** targets both backends; toggle with env or constructor flags.
* Behavior/quotas/pricing **can differ** between Gemini Developer API and Vertex AI. Confirm production SLAs and billing with your chosen backend.
* Some features (Files API, certain preview models) are specific to the Gemini Developer API; others (grounding with enterprise data, IAM, regionality) are Vertex AI‑specific.

---

## 18) Security & Compliance Tips

* Store API keys in **1Password/Secret Manager**; never commit to Git.
* Restrict egress to Google endpoints; enforce HTTPS/TLS and cert pinning where required.
* Add **guard‑rails**: schema‑bound JSON, safety thresholds, and tool allow‑lists.
* Log **model version** & **usage metadata** for audit/chargeback.
* Implement **rate limiting** and exponential backoff with circuit breakers.

---

### Changelog for this guide

* **2025‑09‑08**: Refreshed model matrix and Developer API pricing; clarified 2.5 thinking tokens and Live pricing.

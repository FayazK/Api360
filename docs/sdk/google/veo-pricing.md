| Model & Variant | Model ID                    | Input Modalities                                               | Output                                                                      | Resolution / Aspect                                                                                                                  | FPS                                         | Duration                                   | Text-input limit                                  | Videos per request                           | Audio                                                                  | Key Request Parameters                                                                                                                                                                            | Pricing (paid tier)                                                     |
|-----------------|-----------------------------|----------------------------------------------------------------|-----------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------|--------------------------------------------|---------------------------------------------------|----------------------------------------------|------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------|
| **Veo 3**       | `veo-3.0-generate-001`      | Text-to-Video, Image-to-Video. ([Google AI for Developers][1]) | MP4 video **with audio**. ([Google AI for Developers][1])                   | **720p** or **1080p** (1080p currently **16:9** only); aspect ratios: **"16:9"**, **"9:16" (720p)**. ([Google AI for Developers][1]) | **24 fps**. ([Google AI for Developers][1]) | **8 s**. ([Google AI for Developers][1])   | **1,024 tokens**. ([Google AI for Developers][1]) | **1**. ([Google AI for Developers][1])       | **On by default** (native generation). ([Google AI for Developers][1]) | `prompt`, `negativePrompt`, `image`, `aspectRatio`, `resolution`, `personGeneration` (TTV:`"allow_all"`; ITV:`"allow_adult"`), `seed`. ([Google AI for Developers][1])                            | **\$0.40 / second** (video with audio). ([Google AI for Developers][2]) |
| **Veo 3 Fast**  | `veo-3.0-fast-generate-001` | Text-to-Video, Image-to-Video. ([Google AI for Developers][1]) | MP4 video **with audio** (speed-optimized). ([Google AI for Developers][1]) | **720p** or **1080p** (1080p **16:9** only); aspect: **"16:9"**, **"9:16" (720p)**. ([Google AI for Developers][1])                  | **24 fps**. ([Google AI for Developers][1]) | **8 s**. ([Google AI for Developers][1])   | **1,024 tokens**. ([Google AI for Developers][1]) | **1**. ([Google AI for Developers][1])       | **On by default**. ([Google AI for Developers][1])                     | Same as Veo 3 (`prompt`, `negativePrompt`, `image`, `aspectRatio`, `resolution`, `personGeneration`, `seed`). ([Google AI for Developers][1])                                                     | **\$0.15 / second** (video with audio). ([Google AI for Developers][2]) |
| **Veo 2**       | `veo-2.0-generate-001`      | Text-to-Video, Image-to-Video. ([Google AI for Developers][1]) | MP4 video (**silent**). ([Google AI for Developers][1])                     | **720p**; aspect: **"16:9"**, **"9:16"**. ([Google AI for Developers][1])                                                            | **24 fps**. ([Google AI for Developers][1]) | **5–8 s**. ([Google AI for Developers][1]) | N/A (not listed). ([Google AI for Developers][1]) | **Up to 2**. ([Google AI for Developers][1]) | **No audio**. ([Google AI for Developers][1])                          | `prompt`, `negativePrompt`, `image`, `aspectRatio`; `personGeneration` (TTV:`"allow_all"`, `"allow_adult"`, `"dont_allow"`; ITV:`"allow_adult"`, `"dont_allow"`). ([Google AI for Developers][1]) | **\$0.35 / second** (video). ([Google AI for Developers][2])            |

```json
{
  "models": [
    {
      "name": "Veo 3",
      "model_id": "veo-3.0-generate-001",
      "inputs": ["text", "image"],
      "output": { "format": "mp4", "audio": true },
      "limits": {
        "max_text_input_tokens": 1024,
        "videos_per_request": 1,
        "duration_seconds": 8,
        "fps": 24,
        "resolutions": ["720p", "1080p (16:9 only)"],
        "aspect_ratios": ["16:9", "9:16 (720p only)"]
      },
      "parameters": {
        "prompt": "string",
        "negativePrompt": "string",
        "image": { "mimeType": "image/png|image/jpeg", "maxBytes": 20971520 },
        "aspectRatio": { "enum": ["16:9", "9:16"] },
        "resolution": { "enum": ["720p", "1080p"], "notes": "1080p available only with 16:9" },
        "personGeneration": {
          "text_to_video": { "enum": ["allow_all"] },
          "image_to_video": { "enum": ["allow_adult"] },
          "regional_notes": "EU/UK/CH/MENA: Veo 3 allows 'allow_adult' only"
        },
        "seed": { "type": "integer", "notes": "Improves repeatability; not fully deterministic" }
      },
      "pricing": { "video_with_audio_per_second_usd": 0.40 }
    },
    {
      "name": "Veo 3 Fast",
      "model_id": "veo-3.0-fast-generate-001",
      "inputs": ["text", "image"],
      "output": { "format": "mp4", "audio": true },
      "limits": {
        "max_text_input_tokens": 1024,
        "videos_per_request": 1,
        "duration_seconds": 8,
        "fps": 24,
        "resolutions": ["720p", "1080p (16:9 only)"],
        "aspect_ratios": ["16:9", "9:16 (720p only)"]
      },
      "parameters": {
        "prompt": "string",
        "negativePrompt": "string",
        "image": { "mimeType": "image/png|image/jpeg", "maxBytes": 20971520 },
        "aspectRatio": { "enum": ["16:9", "9:16"] },
        "resolution": { "enum": ["720p", "1080p"], "notes": "1080p available only with 16:9" },
        "personGeneration": {
          "text_to_video": { "enum": ["allow_all"] },
          "image_to_video": { "enum": ["allow_adult"] },
          "regional_notes": "EU/UK/CH/MENA: Veo 3 allows 'allow_adult' only"
        },
        "seed": { "type": "integer", "notes": "Improves repeatability; not fully deterministic" }
      },
      "pricing": { "video_with_audio_per_second_usd": 0.15 }
    },
    {
      "name": "Veo 2",
      "model_id": "veo-2.0-generate-001",
      "inputs": ["text", "image"],
      "output": { "format": "mp4", "audio": false },
      "limits": {
        "videos_per_request": 2,
        "duration_seconds": "5-8",
        "fps": 24,
        "resolutions": ["720p"],
        "aspect_ratios": ["16:9", "9:16"]
      },
      "parameters": {
        "prompt": "string",
        "negativePrompt": "string",
        "image": { "mimeType": "image/png|image/jpeg", "maxBytes": 20971520 },
        "aspectRatio": { "enum": ["16:9", "9:16"] },
        "personGeneration": {
          "text_to_video": { "enum": ["allow_all", "allow_adult", "dont_allow"] },
          "image_to_video": { "enum": ["allow_adult", "dont_allow"] },
          "regional_notes": "EU/UK/CH/MENA: default 'dont_allow'"
        }
      },
      "pricing": { "video_per_second_usd": 0.35 }
    }
  ],
  "sources": {
    "pricing": "https://ai.google.dev/gemini-api/docs/pricing",
    "specs_and_parameters": "https://ai.google.dev/gemini-api/docs/video"
  }
}
```

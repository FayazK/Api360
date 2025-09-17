# Video Generation API Usage

This document provides Postman-compatible `curl` examples for the video generation endpoint (`/api/v1/video/generate`). You can import these examples directly into Postman by using the "Import" -> "Raw Text" feature.

The endpoint accepts a JSON payload to specify the provider, model, and other generation parameters.

## Gemini Models

### Model: `veo-3.0-generate-001`

**Capabilities**: Text-to-Video and Image-to-Video, up to 8 seconds, with native audio.

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/video/generate" \
-H "Content-Type: application/json" \
-d '{
  "prompt": "A beautiful cinematic shot of a futuristic city with flying cars at sunset.",
  "provider": "gemini",
  "model": "veo-3.0-generate-001",
  "duration_seconds": 8,
  "aspect_ratio": "16:9",
  "resolution": "1080p",
  "seed": 42
}'
```

### Model: `veo-3.0-fast-generate-001`

**Capabilities**: Lower latency/cost version of Veo 3, with native audio.

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/video/generate" \
-H "Content-Type: application/json" \
-d '{
  "prompt": "A quick, dynamic shot of a dog catching a frisbee in a sunny park.",
  "provider": "gemini",
  "model": "veo-3.0-fast-generate-001",
  "duration_seconds": 5,
  "aspect_ratio": "16:9",
  "resolution": "720p"
}'
```

### Model: `veo-2.0-generate-001`

**Capabilities**: Text-to-Video and Image-to-Video, silent (no audio).

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/video/generate" \
-H "Content-Type: application/json" \
-d '{
  "prompt": "An artistic, silent video of rain falling on a window pane.",
  "provider": "gemini",
  "model": "veo-2.0-generate-001",
  "duration_seconds": 7,
  "aspect_ratio": "9:16",
  "resolution": "720p"
}'
```

## Replicate Models

### Model: `runwayml/gen2`

**Capabilities**: Runway Gen-2 for Text-to-Video and Image-to-Video.

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/video/generate" \
-H "Content-Type: application/json" \
-d '{
  "prompt": "An astronaut riding a horse on Mars, surrealism, cinematic lighting.",
  "provider": "replicate",
  "model": "runwayml/gen2",
  "duration_seconds": 4,
  "aspect_ratio": "1:1",
  "seed": 12345
}'
```

### Model: `bytedance/seedance-1-pro`

**Capabilities**: SeeDance 1 Pro for high-quality Text-to-Video, up to 12 seconds.

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/video/generate" \
-H "Content-Type: application/json" \
-d '{
  "prompt": "A highly detailed, slow-motion video of a single flower blooming, time-lapse.",
  "provider": "replicate",
  "model": "bytedance/seedance-1-pro",
  "duration_seconds": 10,
  "aspect_ratio": "4:3",
  "resolution": "1080p"
}'
```

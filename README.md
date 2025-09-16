# Api360

Api360 is a FastAPI application that provides chart generation, PDF/document tooling, AI text services, and media generation. The project now bundles an extensible video generation service alongside the existing image pipeline.

## Features

- REST endpoints for chart creation, PDF rendering, and document parsing
- AI text generation with pluggable providers (OpenAI, Gemini, etc.)
- Image generation and editing with Gemini Imagen and Replicate
- **NEW:** Video generation service with Google Gemini Veo and Replicate Gen-2 drivers

## Video Generation

The video service mirrors the image architecture:

- Endpoint: `POST /api/video/generate` for JSON requests, `POST /api/video/generate-multipart` for uploads
- Schema: request only requires `prompt`; optional fields are forwarded verbatim so providers apply their own defaults
- Drivers: `gemini` (Veo 2/3, auto-handles fast variation) and `replicate` (`runwayml/gen2`)
- Output videos are persisted to `storage/public/videos/` via the storage engine

Refer to `docs/videogen.md` for the implementation checklist and `docs/replicate_video_models.md` for model-specific notes.

## Local Development

```bash
python3 -m venv fastenv
source fastenv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Run tests with `pytest -q`. Integration tests rely on mocked provider calls and do not contact external services.

# Replicate Video Models

This document summarizes the Replicate video generation models supported by the service and the key parameters handled by the dedicated drivers.

## Supported Models

### Runway Gen-2 (`runwayml/gen2`)

- **Capabilities:** text-to-video, image-to-video, video-to-video
- **Output:** MP4 (silent), up to ~8 seconds
- **Key Parameters:**
  - `prompt` *(required)* – primary generation prompt
  - `negative_prompt` – specify concepts to avoid
  - `aspect_ratio` – one of `16:9`, `9:16`, or `1:1`
  - `duration` – clip length in seconds (up to 8)
  - `seed` – integer seed for repeatability
  - `image` – data URI string for reference image
  - `input_video` – data URI for reference clip
  - Additional extras passed via the `extra` payload are forwarded to the API unchanged.

The driver validates mapped parameters against `app/services/ai/video/drivers/replicate/schemas/runway_gen2.json` before submitting the job to the Replicate API.

### Adding More Models

To register another Replicate model:

1. Create a driver in `app/services/ai/video/drivers/replicate/models/` that subclasses `BaseReplicateVideoDriver` and implements `map_parameters`/`validate_parameters`.
2. Define a JSON schema in `app/services/ai/video/drivers/replicate/schemas/` describing the accepted parameters.
3. Register the driver in `ReplicateVideoModelRegistry` with any useful aliases.
4. Document the model and its parameters in this file so API consumers know what is supported.

## Authentication

Replicate integrations require `REPLICATE_API_TOKEN` to be set in the environment. The video driver uses the direct HTTPS API for compatibility with async flows and predictable polling.

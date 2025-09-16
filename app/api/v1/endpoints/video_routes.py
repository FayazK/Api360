from __future__ import annotations

import base64
import json
from typing import Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.config import settings
from app.schemas.ai_video import (
    VideoGenerationAPIRequest,
    VideoGenerationAPIResponse,
    VideoGenVideo,
)
from app.services.ai.video import VideoEngine, VideoGenerationRequest
from app.services.ai.video.persistence import persist_generated_videos


router = APIRouter()


def _decode_base64_items(items: Optional[List[str]], label: str) -> Optional[List[bytes]]:
    if not items:
        return None
    decoded: List[bytes] = []
    for entry in items:
        try:
            decoded.append(base64.b64decode(entry))
        except Exception as exc:  # pragma: no cover - validation path
            raise HTTPException(status_code=422, detail=f"Invalid base64 payload in {label}: {exc}")
    return decoded


async def _read_uploads(files: Optional[List[UploadFile]]) -> Optional[List[bytes]]:
    if not files:
        return None
    data: List[bytes] = []
    for upload in files:
        data.append(await upload.read())
    return data


@router.post("/generate", response_model=VideoGenerationAPIResponse, summary="Generate videos (AI)")
async def generate_video(request: VideoGenerationAPIRequest) -> VideoGenerationAPIResponse:
    try:
        image_inputs = _decode_base64_items(request.images_b64, "images_b64")
        video_inputs = _decode_base64_items(request.videos_b64, "videos_b64")

        engine = VideoEngine(default_provider=settings.VIDEO_DEFAULT_PROVIDER)
        req = VideoGenerationRequest(
            prompt=request.prompt,
            provider=request.provider,
            model=request.model or settings.VIDEO_DEFAULT_MODEL,
            duration_seconds=request.duration_seconds,
            fps=request.fps,
            aspect_ratio=request.aspect_ratio,
            resolution=request.resolution,
            negative_prompt=request.negative_prompt,
            seed=request.seed,
            audio=request.audio,
            image_inputs=image_inputs,
            video_inputs=video_inputs,
            system_prompt=request.system_prompt,
            template_variables=request.template_variables,
            extra=request.extra or {},
        )

        result = engine.generate(req)
        persisted: List[VideoGenVideo] = await persist_generated_videos(result.videos)

        return VideoGenerationAPIResponse(
            provider=result.provider,
            model=result.model,
            videos=persisted,
            metadata=result.metadata,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Video generation failed: {exc}")


@router.post(
    "/generate-multipart",
    response_model=VideoGenerationAPIResponse,
    summary="Generate videos with multipart uploads",
)
async def generate_video_multipart(
    prompt: str = Form(..., description="Primary text prompt"),
    provider: Optional[str] = Form(None, description="Video provider identifier"),
    model: Optional[str] = Form(None, description="Provider model identifier"),
    duration_seconds: Optional[float] = Form(None, description="Requested clip length in seconds"),
    fps: Optional[int] = Form(None, description="Frames per second"),
    aspect_ratio: Optional[str] = Form(None, description="Aspect ratio such as '16:9'"),
    resolution: Optional[str] = Form(None, description="Resolution label, e.g., '1080p'"),
    negative_prompt: Optional[str] = Form(None, description="Content to avoid"),
    seed: Optional[int] = Form(None, description="Random seed"),
    audio: Optional[str] = Form(None, description="JSON object for audio settings"),
    extra: Optional[str] = Form(None, description="JSON object of provider-specific parameters"),
    system_prompt: Optional[str] = Form(None, description="System instruction for the provider"),
    template_variables: Optional[str] = Form(None, description="JSON object of template variables"),
    image_files: Optional[List[UploadFile]] = File(None, description="Reference images for image-to-video workflows"),
    video_files: Optional[List[UploadFile]] = File(None, description="Reference videos for video-to-video workflows"),
) -> VideoGenerationAPIResponse:
    try:
        parsed_audio: Optional[Dict[str, object]] = None
        if audio:
            try:
                parsed_audio = json.loads(audio)
                if not isinstance(parsed_audio, dict):
                    raise ValueError
            except Exception:
                raise HTTPException(status_code=422, detail="Invalid JSON for audio; expected an object")

        parsed_extra: Dict[str, object] = {}
        if extra:
            try:
                parsed_extra = json.loads(extra)
                if not isinstance(parsed_extra, dict):
                    raise ValueError
            except Exception:
                raise HTTPException(status_code=422, detail="Invalid JSON for extra; expected an object")

        parsed_template: Optional[Dict[str, object]] = None
        if template_variables:
            try:
                parsed_template = json.loads(template_variables)
                if not isinstance(parsed_template, dict):
                    raise ValueError
            except Exception:
                raise HTTPException(status_code=422, detail="Invalid JSON for template_variables; expected an object")

        image_inputs = await _read_uploads(image_files)
        video_inputs = await _read_uploads(video_files)

        engine = VideoEngine(default_provider=settings.VIDEO_DEFAULT_PROVIDER)
        req = VideoGenerationRequest(
            prompt=prompt,
            provider=provider,
            model=model or settings.VIDEO_DEFAULT_MODEL,
            duration_seconds=duration_seconds,
            fps=fps,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            negative_prompt=negative_prompt,
            seed=seed,
            audio=parsed_audio,
            image_inputs=image_inputs,
            video_inputs=video_inputs,
            system_prompt=system_prompt,
            template_variables=parsed_template,
            extra=parsed_extra,
        )

        result = engine.generate(req)
        persisted: List[VideoGenVideo] = await persist_generated_videos(result.videos)

        return VideoGenerationAPIResponse(
            provider=result.provider,
            model=result.model,
            videos=persisted,
            metadata=result.metadata,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Video generation failed: {exc}")


from __future__ import annotations

import base64
import mimetypes
import uuid
from typing import List, Optional, Tuple

import httpx

from app.core.storage_engine import StorageType, get_storage_engine
from app.schemas.ai_video import VideoGenVideo
from .types import GeneratedVideo


async def _fetch_video_bytes_and_mime(video: GeneratedVideo) -> Tuple[Optional[bytes], Optional[str]]:
    # Decode base64 payloads when present
    if video.b64_data:
        try:
            data = base64.b64decode(video.b64_data)
            return data, video.mime_type
        except Exception:
            return None, None

    if video.url:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(video.url)
            if response.status_code == 200:
                content_type = response.headers.get("content-type")
                if content_type:
                    content_type = content_type.split(";")[0].strip()
                return response.content, content_type
        except Exception:
            return None, None

    return None, None


async def persist_generated_videos(videos: List[GeneratedVideo]) -> List[VideoGenVideo]:
    storage = get_storage_engine()
    persisted: List[VideoGenVideo] = []

    for video in videos:
        original_url = video.url
        data, detected_mime = await _fetch_video_bytes_and_mime(video)
        mime = (detected_mime or video.mime_type or "video/mp4").lower()
        if not data and original_url:
            guessed = mimetypes.guess_type(original_url)[0]
            if guessed:
                mime = guessed.lower()

        local_url = None
        local_path = None
        if data:
            ext = mimetypes.guess_extension(mime) or ".mp4"
            filename = f"{uuid.uuid4().hex}{ext}"
            try:
                info = storage.store_bytes(
                    data=data,
                    category="videos",
                    filename=filename,
                    content_type=mime,
                    storage_type=StorageType.PUBLIC,
                )
                local_url = info.get("url")
                local_path = info.get("path")
            except Exception:
                pass

        metadata = dict(video.metadata or {})
        if original_url:
            metadata.setdefault("provider_url", original_url)

        persisted.append(
            VideoGenVideo(
                url=local_url or original_url,
                path=local_path or video.path,
                mime_type=mime,
                duration_seconds=video.duration_seconds,
                width=video.width,
                height=video.height,
                size_bytes=video.size_bytes,
                metadata=metadata,
            )
        )

    return persisted


from __future__ import annotations

import base64
import mimetypes
import uuid
from typing import List, Optional, Tuple

import httpx

from app.core.storage_engine import get_storage_engine, StorageType
from app.schemas.ai_image import ImageGenImage
from .types import GeneratedImage


async def _fetch_image_bytes_and_mime(img: GeneratedImage) -> Tuple[Optional[bytes], Optional[str]]:
    """Return image bytes and detected MIME type, if available.

    - For b64 input, returns decoded bytes and the provided mime_type (if any).
    - For URL input, attempts to download and returns bytes and response content-type.
    """
    if img.b64_data:
        try:
            data = base64.b64decode(img.b64_data)
            return data, img.mime_type
        except Exception:
            return None, None

    if img.url:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(img.url)
                if resp.status_code == 200:
                    ctype = resp.headers.get("content-type")
                    if ctype:
                        ctype = ctype.split(";")[0].strip()
                    return resp.content, ctype
        except Exception:
            return None, None

    return None, None


async def persist_generated_images(images: List[GeneratedImage]) -> List[ImageGenImage]:
    """Persist generated images to public storage and return API schema objects.

    Attempts to fetch bytes for URL-based images to store locally; falls back to
    provider URLs if fetching/storage fails.
    """
    storage = get_storage_engine()
    persisted: List[ImageGenImage] = []

    for img in images:
        original_url = img.url
        data, detected_mime = await _fetch_image_bytes_and_mime(img)
        mime = (detected_mime or img.mime_type or "image/png").lower()
        if not data and not detected_mime and original_url:
            guessed = mimetypes.guess_type(original_url)[0]
            if guessed:
                mime = guessed.lower()

        local_url = None
        local_path = None
        if data:
            ext = mimetypes.guess_extension(mime) or ".png"
            filename = f"{uuid.uuid4().hex}{ext}"
            try:
                info = storage.store_bytes(
                    data=data,
                    category="images",
                    filename=filename,
                    content_type=mime,
                    storage_type=StorageType.PUBLIC,
                )
                local_url = info.get("url")
                local_path = info.get("path")
            except Exception:
                # Ignore storage failures; fall back to provider URL/path
                pass

        metadata = dict(img.metadata or {})
        if original_url:
            metadata.setdefault("provider_url", original_url)

        persisted.append(
            ImageGenImage(
                b64_data=img.b64_data,
                mime_type=mime,
                url=local_url or original_url,
                path=local_path or img.path,
                metadata=metadata,
            )
        )

    return persisted


import base64
import pytest
from pydantic import ValidationError

from app.schemas.ai_video import (
    VideoGenerationAPIRequest,
    VideoGenerationAPIResponse,
    VideoGenVideo,
)


class TestVideoSchemas:
    def test_video_generation_request_minimal(self):
        req = VideoGenerationAPIRequest(prompt="Create a sunrise over mountains")
        assert req.prompt == "Create a sunrise over mountains"
        assert req.provider is None
        assert req.duration_seconds is None

    def test_video_generation_request_with_options(self):
        req = VideoGenerationAPIRequest(
            prompt="Spaceship flythrough",
            duration_seconds=6.0,
            fps=24,
            aspect_ratio="16:9",
            resolution="1080p",
            negative_prompt="blurry",
            seed=7,
            images_b64=[base64.b64encode(b"img").decode("utf-8")],
            videos_b64=[base64.b64encode(b"vid").decode("utf-8")],
        )
        assert req.duration_seconds == 6.0
        assert req.fps == 24
        assert len(req.images_b64 or []) == 1
        assert len(req.videos_b64 or []) == 1

    def test_video_generation_request_invalid_prompt(self):
        with pytest.raises(ValidationError):
            VideoGenerationAPIRequest(prompt="")

    def test_video_generation_request_invalid_duration(self):
        with pytest.raises(ValidationError):
            VideoGenerationAPIRequest(prompt="Bad", duration_seconds=-2)

    def test_video_generation_response(self):
        response = VideoGenerationAPIResponse(
            provider="gemini",
            model="veo-3.0-generate-001",
            videos=[
                VideoGenVideo(
                    url="http://example.com/video.mp4",
                    mime_type="video/mp4",
                    metadata={"operation": "123"},
                )
            ],
            metadata={"request_id": "abc"},
        )
        assert response.provider == "gemini"
        assert response.model == "veo-3.0-generate-001"
        assert response.videos[0].url.endswith("video.mp4")

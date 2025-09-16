import asyncio
import base64
from unittest.mock import Mock, patch

import pytest

from app.services.ai.video.base import VideoEngine, VideoGenerationError
from app.services.ai.video.factory import VideoDriverFactory, VideoDriver
from app.services.ai.video.types import GeneratedVideo, VideoGenerationRequest, VideoGenerationResult
from app.services.ai.video.persistence import persist_generated_videos


class DummyVideoDriver(VideoDriver):
    provider = "dummy"
    default_model = "dummy-model"

    def generate(self, request: VideoGenerationRequest) -> VideoGenerationResult:
        video = GeneratedVideo(url="http://provider/video.mp4", metadata={"prompt": request.prompt})
        return VideoGenerationResult(provider=self.provider, model=request.model or self.default_model, videos=[video], metadata={"sent": True})


@pytest.fixture(autouse=True)
def register_dummy_driver(monkeypatch):
    original_registry = VideoDriverFactory._registry.copy()
    monkeypatch.setattr(VideoDriverFactory, "_registry", {"dummy": DummyVideoDriver})
    yield
    VideoDriverFactory._registry = original_registry


def test_video_engine_generate_with_provider():
    engine = VideoEngine()
    request = VideoGenerationRequest(prompt="Test", provider="dummy")
    result = engine.generate(request)
    assert result.provider == "dummy"
    assert result.model == "dummy-model"
    assert result.videos[0].url == "http://provider/video.mp4"


def test_video_engine_uses_default_provider():
    engine = VideoEngine(default_provider="dummy")
    request = VideoGenerationRequest(prompt="Test")
    result = engine.generate(request)
    assert result.provider == "dummy"


def test_video_engine_missing_provider_raises():
    engine = VideoEngine()
    with pytest.raises(VideoGenerationError):
        engine.generate(VideoGenerationRequest(prompt="No provider"))


@pytest.mark.asyncio
async def test_persist_generated_videos_uses_storage_engine():
    video_bytes = base64.b64encode(b"fake-video").decode("utf-8")
    videos = [GeneratedVideo(b64_data=video_bytes, mime_type="video/mp4")]

    mock_storage = Mock()
    mock_storage.store_bytes.return_value = {
        "url": "http://localhost/storage/videos/generated.mp4",
        "path": "videos/generated.mp4",
    }

    with patch("app.services.ai.video.persistence.get_storage_engine", return_value=mock_storage):
        persisted = await persist_generated_videos(videos)

    mock_storage.store_bytes.assert_called_once()
    assert persisted[0].url == "http://localhost/storage/videos/generated.mp4"
    assert persisted[0].metadata.get("provider_url") is None


@pytest.mark.asyncio
async def test_persist_generated_videos_preserves_provider_url():
    videos = [GeneratedVideo(url="http://provider/video.mp4", mime_type="video/mp4")]

    mock_storage = Mock()
    mock_storage.store_bytes.side_effect = RuntimeError("fail")

    with patch("app.services.ai.video.persistence.get_storage_engine", return_value=mock_storage):
        persisted = await persist_generated_videos(videos)

    assert persisted[0].url == "http://provider/video.mp4"
    assert persisted[0].metadata["provider_url"] == "http://provider/video.mp4"

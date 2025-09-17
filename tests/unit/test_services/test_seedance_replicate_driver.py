import pytest

from app.core.config import settings
from app.services.ai.video.drivers.replicate.models.seedance_1_pro import Seedance1ProDriver
from app.services.ai.video.types import VideoGenerationRequest


@pytest.fixture
def seedance_driver(monkeypatch):
    monkeypatch.setattr(settings, "REPLICATE_API_TOKEN", "test-token")
    return Seedance1ProDriver()


def test_map_parameters_includes_only_provided_fields(seedance_driver):
    request = VideoGenerationRequest(
        prompt="Sunrise in the city",
        duration_seconds=6,
        fps=24,
        resolution="720p",
        aspect_ratio="16:9",
        seed=1234,
        image_inputs=[b"image-bytes"],
        extra={"camera_fixed": True, "custom_control": "value"},
    )

    params = seedance_driver.map_parameters(request)

    assert params["prompt"] == "Sunrise in the city"
    assert params["duration"] == 6
    assert params["fps"] == 24
    assert params["resolution"] == "720p"
    assert params["aspect_ratio"] == "16:9"
    assert params["seed"] == 1234
    assert params["camera_fixed"] is True
    assert params["custom_control"] == "value"
    assert params["image"].startswith("data:image/png;base64,")
    assert "negative_prompt" not in params


def test_validate_parameters_enforces_schema(seedance_driver):
    with pytest.raises(ValueError):
        seedance_driver.validate_parameters({"prompt": "Test", "fps": 30})

    # A valid configuration should pass
    valid_params = {
        "prompt": "Test",
        "fps": 24,
        "duration": 5,
        "resolution": "720p",
        "aspect_ratio": "16:9",
    }
    seedance_driver.validate_parameters(valid_params)

import pytest

from app.services.ai.video.limits import validate_duration


def test_validate_duration_exact_requirement():
    # Veo 3 variants require exactly 8 seconds.
    assert validate_duration("gemini", "veo-3.0-generate-001", 8.0) == 8.0

    # Slight floating-point drift still snaps to the allowed value.
    assert validate_duration("gemini", "veo-3.0-generate-001", 8.0008) == 8.0

    with pytest.raises(ValueError) as exc:
        validate_duration("gemini", "veo-3.0-generate-001", 3.0)

    assert "8" in str(exc.value)


def test_validate_duration_range():
    # Veo 2 allows any value between 5 and 8 seconds inclusive.
    assert validate_duration("gemini", "veo-2.0-generate-001", 5.5) == 5.5
    assert validate_duration("gemini", "veo-2.0-generate-001", 8.0) == 8.0

    with pytest.raises(ValueError):
        validate_duration("gemini", "veo-2.0-generate-001", 4.0)


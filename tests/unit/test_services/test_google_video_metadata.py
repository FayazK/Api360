from app.services.ai.video.drivers.google.models.base import (
    _safe_metadata_value,
    _sanitize_metadata,
)


def test_safe_metadata_value_handles_functions_and_bytes():
    # Functions and custom objects should become repr strings.
    sample = {
        "func": lambda: None,
        "nested": {"inner": lambda: "value"},
        "sequence": [lambda: 1, 2],
        "bytes": b"hello",
    }

    sanitized = _sanitize_metadata(sample)

    assert isinstance(sanitized["func"], str)
    assert "lambda" in sanitized["func"]
    assert isinstance(sanitized["nested"]["inner"], str)
    assert isinstance(sanitized["sequence"][0], str)
    assert sanitized["bytes"] == "hello"


def test_safe_metadata_value_passthrough_for_primitives():
    assert _safe_metadata_value(5) == 5
    assert _safe_metadata_value("value") == "value"
    assert _safe_metadata_value(None) is None


def test_sanitize_metadata_handles_operation_dict():
    class FakeConfig:
        def __init__(self):
            self.duration_seconds = 8

        def helper(self):
            return "noop"

    metadata = {
        "operation_name": "projects/demo/operations/123",
        "parameters": {
            "config": FakeConfig(),
            "callbacks": [lambda: None],
        },
    }

    sanitized = _sanitize_metadata(metadata)
    assert sanitized["operation_name"] == "projects/demo/operations/123"
    assert isinstance(sanitized["parameters"]["config"], str)
    assert "FakeConfig" in sanitized["parameters"]["config"]
    assert isinstance(sanitized["parameters"]["callbacks"][0], str)

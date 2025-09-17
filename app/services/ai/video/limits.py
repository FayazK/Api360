from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from app.config.video_models import get_video_models_config


_RANGE_PATTERN = re.compile(r"^\s*(?P<start>\d+(?:\.\d+)?)\s*[-–]\s*(?P<end>\d+(?:\.\d+)?)\s*$")
_TO_PATTERN = re.compile(r"^\s*(?P<start>\d+(?:\.\d+)?)\s*(?:to|TO)\s*(?P<end>\d+(?:\.\d+)?)\s*$")


@dataclass(frozen=True)
class DurationConstraints:
    """Normalized duration constraints for a video model."""

    min_seconds: Optional[float] = None
    max_seconds: Optional[float] = None
    allowed_values: Optional[List[float]] = None

    def describe(self) -> str:
        """Return a human-readable description of the constraint."""
        if self.allowed_values:
            values_str = ", ".join(_format_number(value) for value in self.allowed_values)
            if len(self.allowed_values) == 1:
                return f"exactly {values_str} seconds"
            return f"one of {values_str} seconds"
        if self.min_seconds is not None and self.max_seconds is not None:
            if math.isclose(self.min_seconds, self.max_seconds, rel_tol=0.0, abs_tol=1e-6):
                value = _format_number(self.min_seconds)
                return f"exactly {value} seconds"
            return (
                f"between {_format_number(self.min_seconds)} and {_format_number(self.max_seconds)} seconds"
            )
        if self.min_seconds is not None:
            return f"at least {_format_number(self.min_seconds)} seconds"
        if self.max_seconds is not None:
            return f"at most {_format_number(self.max_seconds)} seconds"
        return "a supported duration"


def validate_duration(provider: str, model: str, requested: float) -> float:
    """Validate the requested duration against provider/model constraints.

    Returns the normalized duration (potentially snapped to an allowed value)
    or raises ``ValueError`` if the request violates the configured limits.
    """

    constraints = _load_duration_constraints(provider, model)
    if constraints is None:
        return requested

    tolerance = 1e-3

    # Snap to explicit allowed values when provided.
    if constraints.allowed_values:
        for value in constraints.allowed_values:
            if math.isclose(requested, value, rel_tol=0.0, abs_tol=tolerance):
                return value
        values_str = ", ".join(_format_number(value) for value in constraints.allowed_values)
        expectation = (
            f"{values_str} seconds"
            if len(constraints.allowed_values) > 1
            else f"{values_str} seconds"
        )
        raise ValueError(
            _build_error_message(provider, model, requested, f"one of {expectation}")
        )

    if constraints.min_seconds is not None and requested + tolerance < constraints.min_seconds:
        raise ValueError(
            _build_error_message(provider, model, requested, constraints.describe())
        )

    if constraints.max_seconds is not None and requested - tolerance > constraints.max_seconds:
        raise ValueError(
            _build_error_message(provider, model, requested, constraints.describe())
        )

    return requested


def _build_error_message(provider: str, model: str, requested: float, expectation: str) -> str:
    return (
        f"Model '{model}' from provider '{provider}' only supports durations of {expectation}. "
        f"Received {requested:g} seconds."
    )


def _load_duration_constraints(provider: str, model: str) -> Optional[DurationConstraints]:
    provider_config = _get_provider_config(provider)
    if not provider_config:
        return None

    models_cfg = provider_config.get("models")
    if not isinstance(models_cfg, dict):
        return None

    model_cfg = models_cfg.get(model)
    if not isinstance(model_cfg, dict):
        return None

    limits_cfg = model_cfg.get("limits")
    if not isinstance(limits_cfg, dict):
        return None

    min_seconds: Optional[float] = _coerce_number(limits_cfg.get("min_duration_seconds"))
    max_seconds: Optional[float] = _coerce_number(limits_cfg.get("max_duration_seconds"))
    allowed_values: Optional[List[float]] = None

    duration_cfg = limits_cfg.get("duration_seconds")
    if isinstance(duration_cfg, (int, float)):
        value = float(duration_cfg)
        allowed_values = [value]
        min_seconds = value if min_seconds is None else max(min_seconds, value)
        max_seconds = value if max_seconds is None else min(max_seconds, value)
    elif isinstance(duration_cfg, str):
        parsed = _parse_duration_string(duration_cfg)
        if parsed:
            start, end, values = parsed
            if values:
                allowed_values = values
                value = values[0]
                min_seconds = value if min_seconds is None else max(min_seconds, value)
                max_seconds = value if max_seconds is None else min(max_seconds, value)
            else:
                if start is not None:
                    min_seconds = start if min_seconds is None else max(min_seconds, start)
                if end is not None:
                    max_seconds = end if max_seconds is None else min(max_seconds, end)
        else:
            # Attempt to treat as comma-separated discrete values, e.g. "4,6,8"
            values = _parse_comma_separated_numbers(duration_cfg)
            if values:
                allowed_values = values

    return DurationConstraints(
        min_seconds=min_seconds,
        max_seconds=max_seconds,
        allowed_values=allowed_values,
    )


def _get_provider_config(provider: str) -> Dict[str, Any]:
    cfg = get_video_models_config() or {}
    providers = cfg.get("providers")
    if not isinstance(providers, dict):
        return {}
    return providers.get(provider, {}) or {}


def _coerce_number(value: Any) -> Optional[float]:
    if isinstance(value, (int, float)):
        return float(value)
    try:
        if isinstance(value, str) and value.strip():
            return float(value.strip())
    except ValueError:
        return None
    return None


def _parse_duration_string(value: str) -> Optional[Tuple[Optional[float], Optional[float], Optional[List[float]]]]:
    match = _RANGE_PATTERN.match(value)
    if match:
        start = float(match.group("start"))
        end = float(match.group("end"))
        return start, end, None

    match = _TO_PATTERN.match(value)
    if match:
        start = float(match.group("start"))
        end = float(match.group("end"))
        return start, end, None

    # Pattern like "8" or "8.0"
    stripped = value.strip()
    if stripped.replace(".", "", 1).isdigit():
        num = float(stripped)
        return None, None, [num]

    return None


def _parse_comma_separated_numbers(value: str) -> Optional[List[float]]:
    parts = [part.strip() for part in value.split(",") if part.strip()]
    if not parts:
        return None
    result: List[float] = []
    for part in parts:
        try:
            result.append(float(part))
        except ValueError:
            return None
    return result if result else None


def _format_number(value: float) -> str:
    if float(value).is_integer():
        return f"{int(value)}"
    return f"{value:.2f}".rstrip("0").rstrip(".")


__all__ = ["DurationConstraints", "validate_duration"]

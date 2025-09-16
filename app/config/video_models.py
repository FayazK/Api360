from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
import logging

import yaml


_cached_video_models: Optional[Dict[str, Any]] = None


def _load_yaml(path: Path) -> Optional[Dict[str, Any]]:
    try:
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        if not isinstance(data, dict):
            return {}
        return data
    except Exception as exc:  # pragma: no cover - defensive
        logging.getLogger(__name__).warning("Failed to load video models YAML: %s", exc)
        return None


def get_video_models_config() -> Dict[str, Any]:
    """Return video providers/models configuration, cached after first load."""
    global _cached_video_models
    if _cached_video_models is not None:
        return _cached_video_models

    cfg = _load_yaml(Path("config/video_models.yaml")) or {}
    providers = cfg.get("providers")
    if not isinstance(providers, dict):
        cfg["providers"] = {}

    _cached_video_models = cfg
    return _cached_video_models


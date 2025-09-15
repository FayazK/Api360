from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
import logging

import yaml


_cached_image_models: Optional[Dict[str, Any]] = None


def _load_yaml(path: Path) -> Optional[Dict[str, Any]]:
    try:
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            if not isinstance(data, dict):
                return {}
            return data
    except Exception as e:
        logging.getLogger(__name__).warning(f"Failed to load image models YAML: {e}")
        return None


def get_image_models_config() -> Dict[str, Any]:
    """Return image providers/models configuration from YAML, or empty dict.

    Reads `config/image_models.yaml` once and caches the result. Returns a dict
    with a top-level `providers` mapping when available.
    """
    global _cached_image_models
    if _cached_image_models is not None:
        return _cached_image_models

    cfg = _load_yaml(Path("config/image_models.yaml")) or {}
    # Normalize structure
    if not isinstance(cfg.get("providers"), dict):
        cfg["providers"] = {}

    _cached_image_models = cfg
    return _cached_image_models


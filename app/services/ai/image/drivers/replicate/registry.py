"""
Registry for Replicate model-specific drivers.

Manages the mapping between model IDs and their corresponding driver classes.
"""

from __future__ import annotations

from typing import Dict, Type, Optional, Set

from .base import BaseReplicateDriver
from .models.seedream_4 import Seedream4Driver
from .models.flux_krea_dev import FluxKreaDevDriver


class ReplicateModelRegistry:
    """Registry for mapping Replicate model IDs to driver classes."""
    
    _models: Dict[str, Type[BaseReplicateDriver]] = {
        "bytedance/seedream-4": Seedream4Driver,
        "black-forest-labs/flux-krea-dev": FluxKreaDevDriver,
    }
    
    _aliases: Dict[str, str] = {
        "seedream-4": "bytedance/seedream-4",
        "seedream4": "bytedance/seedream-4",
        "flux-krea-dev": "black-forest-labs/flux-krea-dev",
        "flux-krea": "black-forest-labs/flux-krea-dev",
        "krea-dev": "black-forest-labs/flux-krea-dev",
    }
    
    @classmethod
    def get_driver_class(cls, model_id: str) -> Optional[Type[BaseReplicateDriver]]:
        """Get driver class for a model ID."""
        # Try direct lookup
        if model_id in cls._models:
            return cls._models[model_id]
        
        # Try alias lookup
        canonical_id = cls._aliases.get(model_id)
        if canonical_id and canonical_id in cls._models:
            return cls._models[canonical_id]
        
        return None
    
    @classmethod
    def is_supported(cls, model_id: str) -> bool:
        """Check if a model ID is supported."""
        return cls.get_driver_class(model_id) is not None
    
    @classmethod
    def get_supported_models(cls) -> Set[str]:
        """Get set of all supported model IDs (including aliases)."""
        return set(cls._models.keys()) | set(cls._aliases.keys())
    
    @classmethod
    def register_model(
        cls, 
        model_id: str, 
        driver_class: Type[BaseReplicateDriver],
        aliases: Optional[list[str]] = None
    ) -> None:
        """Register a new model driver."""
        cls._models[model_id] = driver_class
        
        if aliases:
            for alias in aliases:
                cls._aliases[alias] = model_id
    
    @classmethod
    def get_canonical_id(cls, model_id: str) -> Optional[str]:
        """Get canonical model ID from alias or return original if already canonical."""
        if model_id in cls._models:
            return model_id
        
        return cls._aliases.get(model_id)
    
    @classmethod
    def list_models(cls) -> Dict[str, Dict[str, any]]:
        """List all registered models with their information."""
        models = {}
        
        for model_id, driver_class in cls._models.items():
            # Get aliases for this model
            aliases = [alias for alias, canonical in cls._aliases.items() 
                      if canonical == model_id]
            
            models[model_id] = {
                "driver_class": driver_class.__name__,
                "aliases": aliases,
                "default_model": getattr(driver_class, 'default_model', model_id),
                "provider": getattr(driver_class, 'provider', 'replicate'),
            }
        
        return models
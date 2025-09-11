"""
Simple integration test for Replicate model-specific drivers.

This file can be run manually to test the new drivers.
"""

from app.services.ai.image.types import ImageGenerationRequest
from .registry import ReplicateModelRegistry
from .models.seedream_4 import Seedream4Driver
from .models.flux_krea_dev import FluxKreaDevDriver


def test_registry():
    """Test the model registry functionality."""
    print("Testing ReplicateModelRegistry...")
    
    # Test supported models
    supported = ReplicateModelRegistry.get_supported_models()
    print(f"Supported models: {supported}")
    
    # Test driver lookup
    seedream_driver = ReplicateModelRegistry.get_driver_class("bytedance/seedream-4")
    flux_driver = ReplicateModelRegistry.get_driver_class("black-forest-labs/flux-krea-dev")
    
    print(f"Seedream driver: {seedream_driver}")
    print(f"Flux driver: {flux_driver}")
    
    # Test aliases
    alias_driver = ReplicateModelRegistry.get_driver_class("seedream-4")
    print(f"Alias lookup (seedream-4): {alias_driver}")
    
    # Test listing
    models = ReplicateModelRegistry.list_models()
    print(f"All models: {models}")


def test_parameter_mapping():
    """Test parameter mapping for both drivers."""
    print("\nTesting parameter mapping...")
    
    # Test request
    request = ImageGenerationRequest(
        prompt="A beautiful sunset over mountains",
        num_images=2,
        width=1024,
        height=1024,
        seed=42,
        steps=30,
        guidance_scale=7.5,
        ratio="16:9"
    )
    
    print("Original request parameters:")
    print(f"  prompt: {request.prompt}")
    print(f"  num_images: {request.num_images}")
    print(f"  width: {request.width}")
    print(f"  height: {request.height}")
    print(f"  seed: {request.seed}")
    print(f"  steps: {request.steps}")
    print(f"  guidance_scale: {request.guidance_scale}")
    print(f"  ratio: {request.ratio}")
    
    # Test Seedream4 mapping (would need API key to actually test)
    try:
        # This will fail without API key, but we can test the mapping
        driver = Seedream4Driver()
        mapped = driver.map_parameters(request)
        print(f"\nSeedream4 mapped parameters: {mapped}")
    except Exception as e:
        print(f"\nSeedream4 driver init failed (expected without API key): {e}")
    
    # Test FluxKreaDev mapping
    try:
        driver = FluxKreaDevDriver()
        mapped = driver.map_parameters(request)
        print(f"\nFluxKreaDev mapped parameters: {mapped}")
    except Exception as e:
        print(f"\nFluxKreaDev driver init failed (expected without API key): {e}")


if __name__ == "__main__":
    test_registry()
    test_parameter_mapping()
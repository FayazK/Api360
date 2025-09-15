# Developer Guide: Unifying Image Generation Models with YAML Configuration

This guide outlines the process of refactoring the image generation service to use a centralized YAML configuration for managing providers and models. This change will make the system more scalable, maintainable, and easier to extend with new models and providers.

## Introduction

Currently, image generation providers (drivers) and their supported models are registered and configured directly within the Python code, primarily in `app/services/ai/image/factory.py` and the individual driver files.

The goal is to move this configuration into a YAML file, similar to how text-based models are managed in `config/ai_models.yaml`.

**Benefits:**
- **Centralized Management**: All image model configurations in one place.
- **Easy Updates**: Add new providers or models without changing the core factory logic.
- **Scalability**: A clean and scalable way to manage a growing list of models.
- **Clarity**: A clear separation of configuration from application logic.

---

## Step 1: Create the YAML Configuration File

Create a new file named `config/image_models.yaml`. This file will define the providers, their drivers, and the models they support.

**`config/image_models.yaml`:**
```yaml
providers:
  replicate:
    name: Replicate
    driver: replicate # Corresponds to the driver key used in the factory
    default_model: bytedance/seedream-4
    models:
      bytedance/seedream-4:
        max_inputs: 10
        supports_4k: true
        # Other model-specific metadata
      black-forest-labs/flux-krea-dev:
        max_inputs: 1
        # Other model-specific metadata

  gemini-nano-banana:
    name: "Gemini Nano (Banana)"
    driver: gemini_nano_banana
    default_model: default # if the driver has a single model
    models:
      default: {}

  imagen:
    name: "Google Imagen"
    driver: imagen
    default_model: imagen-3.0
    models:
      imagen-3.0:
        # Model-specific metadata
      imagen-2.0:
        # Model-specific metadata
```

---

## Step 2: Create a Configuration Loader

To load this YAML file, we can add a new function to `app/core/config.py` or create a dedicated configuration loading module. For simplicity, let's assume we add it to `app/core/config.py`.

**`app/core/config.py` (addition):**
```python
from typing import Dict, Any
import yaml

def load_yaml_config(path: str) -> Dict[str, Any]:
    """Loads a YAML file from the given path."""
    with open(path, 'r') as f:
        return yaml.safe_load(f)

# You can then create a global config object for image models
IMAGE_MODELS_CONFIG = load_yaml_config('config/image_models.yaml')
```

---

## Step 3: Refactor the Image Driver Factory

The `ImageEngine` and its underlying factory in `app/services/ai/image/factory.py` need to be updated to use the loaded YAML configuration.

**`app/services/ai/image/factory.py` (refactoring):**

The current factory likely has a hardcoded dictionary or if/else structure to select a driver. This will be replaced by a dynamic lookup in our loaded `IMAGE_MODELS_CONFIG`.

**Before:**
```python
# (Simplified)
from app.services.ai.image.drivers import replicate_driver, imagen_driver

class ImageEngine:
    def generate(self, req: ImageGenerationRequest):
        if req.provider == 'replicate':
            driver = replicate_driver.ReplicateDriver()
        elif req.provider == 'imagen':
            driver = imagen_driver.ImagenDriver()
        # ...
```

**After:**
```python
# (Simplified)
from app.core.config import IMAGE_MODELS_CONFIG
from app.services.ai.image.drivers.base_driver import BaseImageDriver
# Import all driver classes
from app.services.ai.image.drivers.replicate_driver import ReplicateDriver
from app.services.ai.image.drivers.imagen_driver import ImagenDriver
from app.services.ai.image.drivers.gemini_nano_banana import GeminiNanoBananaDriver


class ImageDriverFactory:
    _drivers = {
        "replicate": ReplicateDriver,
        "imagen": ImagenDriver,
        "gemini_nano_banana": GeminiNanoBananaDriver,
        # Register new driver classes here
    }

    @staticmethod
    def get_driver(provider_key: str) -> BaseImageDriver:
        provider_config = IMAGE_MODELS_CONFIG['providers'].get(provider_key)
        if not provider_config:
            raise ValueError(f"Provider '{provider_key}' not found in image_models.yaml")

        driver_name = provider_config.get('driver')
        if not driver_name or driver_name not in ImageDriverFactory._drivers:
            raise ValueError(f"Driver for '{provider_key}' not implemented or registered in the factory.")

        DriverClass = ImageDriverFactory._drivers[driver_name]
        
        # Pass the provider's config to the driver's constructor
        return DriverClass(config=provider_config)


class ImageEngine:
    def generate(self, req: ImageGenerationRequest):
        # Use the factory to get the driver
        driver = ImageDriverFactory.get_driver(req.provider)
        
        # The driver now has access to its own configuration
        return driver.generate(req)
```

---

## Step 4: Update the Drivers

The base driver class and individual drivers should be updated to accept the configuration dictionary.

**`app/services/ai/image/drivers/base_driver.py`:**
```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseImageDriver(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider_name = config.get('name', 'Unknown')
        self.default_model = config.get('default_model')

    @abstractmethod
    def generate(self, req: ImageGenerationRequest) -> ImageGenerationResponse:
        pass
```

**Example Driver (`replicate_driver.py`):**
```python
from .base_driver import BaseImageDriver

class ReplicateDriver(BaseImageDriver):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # self.config is now available with all the info from image_models.yaml
        # for the 'replicate' provider.

    def generate(self, req: ImageGenerationRequest) -> ImageGenerationResponse:
        model_key = req.model or self.default_model
        
        # You can access model-specific config
        model_config = self.config['models'].get(model_key, {})
        max_inputs = model_config.get('max_inputs', 1)

        # ... rest of the generation logic using the config
```

---

## Conclusion

By following these steps, you will have a robust and scalable system for managing image generation models. Adding a new provider becomes a two-step process:
1.  Implement the new driver class.
2.  Add its configuration to `config/image_models.yaml` and register it in the `ImageDriverFactory`.

This approach significantly improves the maintainability of the image generation service.

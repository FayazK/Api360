# Replicate Model-Specific Drivers

This document describes the new model-specific driver architecture for Replicate image generation, which provides better reliability and parameter mapping for supported models.

## Overview

The Replicate driver now automatically selects between model-specific drivers and a generic fallback based on the requested model. Model-specific drivers provide:

- **Accurate parameter mapping**: Each driver knows exactly how to map unified parameters to model-specific names
- **Schema validation**: Pre-validate inputs against known model schemas
- **Better error handling**: Clear error messages showing expected vs provided parameters
- **Optimized performance**: Direct API calls without SDK overhead

## Supported Models

### ByteDance Seedream-4 (`bytedance/seedream-4`)

**Features:**
- Unified text-to-image generation and precise image editing
- Support for up to 4K resolution (4096x4096)
- Multi-reference generation (up to 10 input images)
- Sequential image generation for stories/variations

**Parameter Mapping:**
```python
# Unified API → Seedream-4 API
prompt → prompt                    # Direct mapping
image_inputs → image_input         # Array of URIs
num_images → max_images           # Limited to 15
width/height → size="custom"      # Auto-detect custom size
ratio → aspect_ratio              # With value mapping
```

**Example:**
```python
from app.services.ai.image import ImageEngine
from app.services.ai.image.types import ImageGenerationRequest

request = ImageGenerationRequest(
    prompt="A cozy cabin in a snowy forest, watercolor style",
    provider="replicate",
    model="bytedance/seedream-4",
    num_images=2,
    width=2048,
    height=2048,
    ratio="16:9"
)

engine = ImageEngine()
result = engine.generate(request)
```

### Black Forest Labs FLUX.1 Krea [dev] (`black-forest-labs/flux-krea-dev`)

**Features:**
- Distinctive aesthetic style avoiding 'AI look'
- Exceptional realism and photorealism
- Image-to-image transformation
- Optimized performance mode

**Parameter Mapping:**
```python
# Unified API → FLUX Krea API
prompt → prompt                      # Direct mapping
image_inputs[0] → image             # First image only (URI)
seed → seed                         # Direct mapping
num_images → num_outputs           # Limited to 4
steps → num_inference_steps        # Renamed
guidance_scale → guidance          # Renamed
ratio → aspect_ratio               # Direct mapping
quality → output_quality           # Scaled to 0-100
```

**Example:**
```python
request = ImageGenerationRequest(
    prompt="Professional portrait photography, studio lighting",
    provider="replicate", 
    model="black-forest-labs/flux-krea-dev",
    guidance_scale=3.5,
    steps=28,
    seed=42,
    ratio="4:3"
)

result = engine.generate(request)
```

## API Usage

### Automatic Driver Selection

The main `ReplicateImageDriver` automatically selects the appropriate driver:

```python
# This will use Seedream4Driver automatically
request = ImageGenerationRequest(
    prompt="Mountain landscape at sunset",
    provider="replicate",
    model="bytedance/seedream-4",  # Triggers model-specific driver
    width=2048,
    height=1024
)

# This will use FluxKreaDevDriver automatically  
request = ImageGenerationRequest(
    prompt="Portrait of a person in natural lighting",
    provider="replicate",
    model="black-forest-labs/flux-krea-dev",  # Triggers model-specific driver
    guidance_scale=4.5
)

# This will use the generic driver
request = ImageGenerationRequest(
    prompt="Artistic illustration",
    provider="replicate", 
    model="stability-ai/sdxl",  # Falls back to generic driver
    steps=30
)
```

### Model Aliases

Supported aliases for convenience:

```python
# These all map to bytedance/seedream-4
"seedream-4"
"seedream4"

# These all map to black-forest-labs/flux-krea-dev  
"flux-krea-dev"
"flux-krea"
"krea-dev"
```

### Getting Supported Models

```python
from app.services.ai.image.drivers.replicate_driver import ReplicateImageDriver

driver = ReplicateImageDriver()
supported = driver.get_supported_models()
print(supported)
# Output: {
#   'bytedance/seedream-4': 'Enhanced support - Seedream4Driver',
#   'black-forest-labs/flux-krea-dev': 'Enhanced support - FluxKreaDevDriver'
# }
```

## Error Handling

Model-specific drivers provide detailed error messages:

```python
# Schema validation error
ValidationError: Parameter 'max_images' must be <= 15

# Parameter type error  
ValidationError: Parameter 'guidance' must be a number, got <class 'str'>

# Missing required parameter
ValidationError: Required parameter 'prompt' is missing
```

## Fallback Behavior

If a model-specific driver fails or is unavailable, the system gracefully falls back to the generic driver:

1. **Driver unavailable**: Falls back to generic SDK-based approach
2. **Driver initialization fails**: Logs error and uses generic driver
3. **Generation fails**: Logs error and retries with generic driver

## Architecture

### Directory Structure

```
app/services/ai/image/drivers/replicate/
├── __init__.py
├── base.py                    # BaseReplicateDriver abstract class
├── registry.py                # Model registry and factory
├── schemas/                   # Model schema definitions
│   ├── seedream_4.json
│   └── flux_krea_dev.json
└── models/                    # Model-specific drivers
    ├── seedream_4.py
    └── flux_krea_dev.py
```

### Adding New Models

To add support for a new model:

1. **Create schema file**: Add JSON schema in `schemas/`
2. **Implement driver**: Create driver class extending `BaseReplicateDriver`
3. **Register model**: Add to `ReplicateModelRegistry._models`
4. **Add aliases**: Optional convenience aliases

Example driver implementation:

```python
class NewModelDriver(BaseReplicateDriver):
    provider = "replicate"
    default_model = "owner/model-name"
    
    @property
    def model_id(self) -> str:
        return "owner/model-name"
    
    @property  
    def model_version(self) -> Optional[str]:
        return "version-hash"  # or None for latest
    
    def map_parameters(self, request: ImageGenerationRequest) -> Dict[str, Any]:
        # Map unified parameters to model-specific parameters
        return {"prompt": request.prompt, ...}
    
    def validate_parameters(self, params: Dict[str, Any]) -> None:
        # Validate against model schema
        pass
```

## Migration Guide

### From Generic Driver

No changes required! The enhanced driver is backward compatible:

```python
# This continues to work exactly as before
request = ImageGenerationRequest(
    prompt="Beautiful landscape", 
    provider="replicate",
    model="stability-ai/sdxl"  # Still uses generic approach
)
```

### Leveraging Enhanced Support

Update model names to benefit from enhanced drivers:

```python
# Before: Generic parameter mapping (may fail)
request = ImageGenerationRequest(
    prompt="Edit this image to remove the person",
    provider="replicate", 
    model="bytedance/seedream-4",
    num_images=3,  # Generic driver maps to num_outputs
    image_inputs=[image_data]  # Generic driver maps to image
)

# After: Model-specific mapping (reliable)
# Same code, but now uses Seedream4Driver automatically
# - num_images → max_images (correct parameter name)
# - image_inputs → image_input (correct parameter name) 
# - Proper validation and error handling
```

## Testing

Run the integration test to verify functionality:

```bash
cd app/services/ai/image/drivers/replicate/
python test_integration.py
```

This tests:
- Model registry functionality
- Parameter mapping for both drivers
- Schema validation (without API calls)

## Performance Impact

Model-specific drivers provide better performance:

- **Direct API calls**: Skip SDK overhead using `httpx`
- **Parameter validation**: Catch errors before API calls
- **Caching**: Driver instances are cached per model
- **Fallback**: Graceful degradation maintains reliability
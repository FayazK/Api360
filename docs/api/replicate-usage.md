# Replicate API Usage Guide

The Replicate image generation service provides model-specific drivers for reliable image generation with precise parameter mapping and validation.

## Overview

The Replicate provider supports only models with dedicated implementations. Each model has custom parameter mapping, validation, and optimization for consistent results.

**Supported Models:**
- `bytedance/seedream-4` - Advanced text-to-image and editing up to 4K resolution
- `black-forest-labs/flux-krea-dev` - Distinctive aesthetic style with exceptional realism

## Configuration

### Environment Variables

```bash
# Required
REPLICATE_API_TOKEN=your_replicate_api_token_here

# Optional - Image generation defaults
IMAGE_DEFAULT_PROVIDER=replicate
IMAGE_DEFAULT_MODEL=bytedance/seedream-4
```

### Dependencies

The Replicate driver requires:
- `httpx` (for direct API calls)
- `REPLICATE_API_TOKEN` environment variable

## Basic Usage

### Text-to-Image Generation

```python
from app.services.ai.image import ImageEngine
from app.services.ai.image.types import ImageGenerationRequest

engine = ImageEngine()

# Basic generation with Seedream-4
request = ImageGenerationRequest(
    prompt="A serene mountain lake at sunset, photorealistic",
    provider="replicate",
    model="bytedance/seedream-4"
)

result = engine.generate(request)
for image in result.images:
    print(f"Generated image URL: {image.url}")
```

### Using Model Aliases

```python
# These are all equivalent to bytedance/seedream-4
request = ImageGenerationRequest(
    prompt="Digital art of a futuristic city",
    provider="replicate",
    model="seedream-4"  # Alias
)

# These are all equivalent to black-forest-labs/flux-krea-dev
request = ImageGenerationRequest(
    prompt="Portrait photography with natural lighting",
    provider="replicate", 
    model="flux-krea"  # Alias
)
```

## ByteDance Seedream-4

Advanced text-to-image generation and precise image editing model supporting up to 4K resolution.

### Key Features

- **Multi-resolution support**: 1K, 2K, 4K, or custom dimensions
- **Image editing**: Precise single-sentence editing instructions
- **Multi-reference generation**: Use up to 10 input images
- **Sequential generation**: Automatic story scenes or character variations

### Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `prompt` | string | Text prompt for generation (required) | - |
| `width` | integer | Custom width (1024-4096px) | 2048 |
| `height` | integer | Custom height (1024-4096px) | 2048 |
| `num_images` | integer | Number of images to generate (1-15) | 1 |
| `ratio` | string | Aspect ratio (1:1, 16:9, 9:16, etc.) | match_input_image |
| `image_inputs` | array | Input images for img2img/editing | [] |

### Parameter Mapping

```
Unified API → Seedream-4 API
─────────────────────────────
prompt → prompt
image_inputs → image_input (array of URIs)
num_images → max_images (triggers sequential_image_generation=auto)
width/height → size="custom" + width/height
ratio → aspect_ratio (with mapping)
```

### Examples

#### Basic Text-to-Image

```python
request = ImageGenerationRequest(
    prompt="A cozy cabin in a snowy forest, watercolor style",
    provider="replicate",
    model="bytedance/seedream-4",
    width=2048,
    height=1024,
    ratio="16:9"
)

result = engine.generate(request)
```

#### High-Resolution Generation

```python
request = ImageGenerationRequest(
    prompt="Ultra-detailed macro photography of a butterfly wing",
    provider="replicate",
    model="seedream-4",
    width=4096,
    height=4096  # Triggers size="custom"
)

result = engine.generate(request)
```

#### Image Editing

```python
# Read image file
with open("original_photo.jpg", "rb") as f:
    image_data = f.read()

request = ImageGenerationRequest(
    prompt="Remove the person in the background, keep everything else",
    provider="replicate",
    model="seedream-4",
    image_inputs=[image_data],
    ratio="match_input_image"
)

result = engine.generate(request)
```

#### Multi-Image Story Generation

```python
request = ImageGenerationRequest(
    prompt="A hero's journey through different landscapes - forest, mountain, desert",
    provider="replicate",
    model="seedream-4",
    num_images=5,  # Generates sequential story images
    ratio="21:9"   # Cinematic aspect ratio
)

result = engine.generate(request)
print(f"Generated {len(result.images)} story scenes")
```

## Black Forest Labs FLUX.1 Krea [dev]

State-of-the-art model for distinctive aesthetic style and exceptional realism, avoiding the typical 'AI look'.

### Key Features

- **Distinctive aesthetics**: Natural details without oversaturated textures
- **Exceptional realism**: Professional-quality photorealistic results
- **Image-to-image**: Support for img2img transformations
- **Performance optimization**: Fast generation with go_fast mode

### Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `prompt` | string | Text prompt for generation (required) | - |
| `seed` | integer | Random seed for reproducibility | - |
| `num_images` | integer | Number of outputs (1-4) | 1 |
| `steps` | integer | Inference steps (1-50) | 28 |
| `guidance_scale` | number | Guidance strength (0-10) | 4.5 |
| `ratio` | string | Aspect ratio | 1:1 |
| `image_inputs` | array | Input image for img2img | [] |
| `quality` | number | Output quality (0-1) | 0.8 |

### Parameter Mapping

```
Unified API → FLUX Krea API
───────────────────────────
prompt → prompt
image_inputs[0] → image (first image only)
seed → seed
num_images → num_outputs (max 4)
steps → num_inference_steps
guidance_scale → guidance
ratio → aspect_ratio
quality → output_quality (scaled to 0-100)
```

### Examples

#### Photorealistic Portrait

```python
request = ImageGenerationRequest(
    prompt="Professional portrait of a woman, natural lighting, shallow depth of field",
    provider="replicate",
    model="flux-krea-dev",
    guidance_scale=3.5,  # Lower for more realism
    steps=35,
    ratio="3:4",
    seed=42
)

result = engine.generate(request)
```

#### Artistic Style Transfer

```python
with open("source_image.jpg", "rb") as f:
    image_data = f.read()

request = ImageGenerationRequest(
    prompt="Transform into a painting in the style of Van Gogh, swirling brushstrokes",
    provider="replicate",
    model="flux-krea-dev",
    image_inputs=[image_data],
    guidance_scale=6.0,
    steps=40
)

result = engine.generate(request)
```

#### Batch Generation

```python
request = ImageGenerationRequest(
    prompt="Modern architecture, glass building, urban setting",
    provider="replicate", 
    model="flux-krea",
    num_images=4,  # Generate 4 variations
    guidance_scale=4.5,
    ratio="16:9"
)

result = engine.generate(request)
for i, image in enumerate(result.images):
    print(f"Variation {i+1}: {image.url}")
```

## Advanced Features

### Error Handling

The service provides detailed validation errors:

```python
try:
    request = ImageGenerationRequest(
        prompt="Test image",
        provider="replicate",
        model="unsupported-model"
    )
    result = engine.generate(request)
except ValueError as e:
    print(f"Model not supported: {e}")
    # Output: Model 'unsupported-model' is not supported. 
    #         Supported models: bytedance/seedream-4, black-forest-labs/flux-krea-dev

try:
    request = ImageGenerationRequest(
        prompt="Test",
        model="seedream-4",
        num_images=20  # Exceeds max of 15
    )
    result = engine.generate(request)
except ValueError as e:
    print(f"Parameter validation failed: {e}")
    # Output: Parameter 'max_images' must be <= 15
```

### Getting Supported Models

```python
from app.services.ai.image.drivers.replicate_driver import ReplicateImageDriver

driver = ReplicateImageDriver()

# Check support
if driver.is_model_supported("seedream-4"):
    print("Model is supported")

# List all supported models
models = driver.get_supported_models()
for model_id, driver_class in models.items():
    print(f"{model_id}: {driver_class}")

# Output:
# bytedance/seedream-4: Seedream4Driver
# black-forest-labs/flux-krea-dev: FluxKreaDevDriver
```

### Model Registry

```python
from app.services.ai.image.drivers.replicate.registry import ReplicateModelRegistry

# Get all supported models including aliases
all_models = ReplicateModelRegistry.get_supported_models()
print(f"All supported models and aliases: {all_models}")

# Get detailed model information
model_info = ReplicateModelRegistry.list_models()
for model_id, info in model_info.items():
    print(f"Model: {model_id}")
    print(f"  Driver: {info['driver_class']}")
    print(f"  Aliases: {info['aliases']}")
    print(f"  Provider: {info['provider']}")
```

## Best Practices

### Model Selection

- **Use Seedream-4 for:**
  - High-resolution images (up to 4K)
  - Image editing and manipulation
  - Multi-image story generation
  - Complex scenes with multiple objects

- **Use FLUX Krea [dev] for:**
  - Photorealistic portraits
  - Natural-looking scenes
  - Professional photography style
  - Avoiding typical AI-generated appearance

### Parameter Optimization

#### Seedream-4 Tips

```python
# For best quality
request = ImageGenerationRequest(
    prompt="Detailed description with specific style references",
    model="seedream-4",
    width=2048,
    height=2048,  # Use even dimensions
    ratio="1:1"   # Consistent with dimensions
)

# For editing
request = ImageGenerationRequest(
    prompt="Simple, clear editing instruction like 'change hair color to blonde'",
    model="seedream-4",
    image_inputs=[image_data],
    ratio="match_input_image"  # Preserve original aspect ratio
)
```

#### FLUX Krea [dev] Tips

```python
# For photorealism
request = ImageGenerationRequest(
    prompt="Detailed prompt with photography terms like 'shot on 85mm lens'",
    model="flux-krea-dev",
    guidance_scale=3.0,  # Lower guidance for more natural results
    steps=35,            # Higher steps for better quality
    ratio="4:3"          # Traditional photo ratio
)
```

## Response Format

All models return the standard `ImageGenerationResult`:

```python
result = engine.generate(request)

# Access generated images
for image in result.images:
    if image.url:
        print(f"Image URL: {image.url}")
    elif image.b64_data:
        print(f"Base64 data available, MIME type: {image.mime_type}")

# Access metadata
print(f"Provider: {result.provider}")
print(f"Model: {result.model}")
print(f"Parameters used: {result.metadata['parameters']}")
print(f"Prediction ID: {result.metadata.get('prediction_id')}")
```

## Troubleshooting

### Common Issues

1. **Model not supported error**
   ```python
   # Check if model is supported first
   if not driver.is_model_supported(model_name):
       print(f"Use one of: {list(driver.get_supported_models().keys())}")
   ```

2. **Parameter validation errors**
   ```python
   # Check parameter ranges in error messages
   # Seedream-4: max_images ≤ 15, dimensions 1024-4096
   # FLUX Krea: num_outputs ≤ 4, guidance 0-10
   ```

3. **API token issues**
   ```bash
   # Verify token is set
   echo $REPLICATE_API_TOKEN
   
   # Test token validity
   curl -H "Authorization: Token $REPLICATE_API_TOKEN" \
        https://api.replicate.com/v1/models
   ```

### Performance Tips

- Use appropriate image dimensions (powers of 2 work best)
- Cache model drivers are reused automatically
- Consider using aliases for shorter model names
- Monitor API usage through Replicate dashboard

## Migration from Generic Driver

If migrating from a generic Replicate implementation:

```python
# Before: Generic approach (no longer supported)
# request = ImageGenerationRequest(
#     prompt="test",
#     provider="replicate", 
#     model="stability-ai/sdxl"  # Not supported
# )

# After: Use supported models
request = ImageGenerationRequest(
    prompt="test",
    provider="replicate",
    model="bytedance/seedream-4"  # Supported
)

# Parameter names are automatically mapped
# Old: num_outputs → New: max_images (for Seedream-4)
# Old: guidance_scale → New: guidance (for FLUX Krea)
```
# AI Text Generation Service

The AI Text Generation Service provides a unified interface for text generation using multiple AI providers through a driver pattern architecture.

## Architecture

### Core Components

- **Base Service**: `BaseAITextGenerator` - Abstract base class defining the standard interface
- **Driver Pattern**: Provider-specific drivers implementing the actual API calls
- **Service Factory**: `AITextGeneratorFactory` - Manages driver registration and service instantiation
- **Unified Schemas**: Standardized request/response models across all providers

### Directory Structure

```
app/services/ai/
├── __init__.py              # Public API exports
├── base.py                  # BaseAITextGenerator abstract class
├── factory.py               # AITextGeneratorFactory and service management
├── schemas.py               # Internal data models and exceptions
├── drivers/
│   ├── __init__.py          # Driver exports
│   ├── base_driver.py       # BaseAIDriver interface
│   └── openai_driver.py     # OpenAI implementation
```

## Supported Providers

### OpenAI
- **Models**: `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, `gpt-4`, `gpt-3.5-turbo`
- **Default Model**: `gpt-4o-mini`
- **Features**: Token usage tracking, cost calculation, model validation

### Coming Soon
- Anthropic Claude
- Google Gemini
- OpenRouter

## Configuration

Add the following environment variables:

```bash
# AI Service Settings
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here

# AI Service Configuration (optional)
AI_DEFAULT_PROVIDER=openai
AI_DEFAULT_MODEL=gpt-4o-mini
AI_MAX_TOKENS_DEFAULT=1000
AI_TEMPERATURE_DEFAULT=0.7
AI_REQUEST_TIMEOUT=60
```

## API Endpoints

All endpoints are available under `/api/ai/`:

### POST `/api/ai/generate`
Generate text using AI models.

**Request Body:**
```json
{
  "prompt": "Write a hello world program in Python",
  "system_prompt": "You are a helpful programming assistant",
  "provider": "openai",
  "model": "gpt-4o-mini",
  "max_tokens": 1000,
  "temperature": 0.7,
  "top_p": 1.0,
  "frequency_penalty": 0.0,
  "presence_penalty": 0.0,
  "stop_sequences": ["\\n\\n"],
  "template_variables": {
    "language": "Python"
  }
}
```

**Response:**
```json
{
  "text": "Generated text response",
  "success": true,
  "provider": "openai",
  "model": "gpt-4o-mini",
  "request_id": "uuid-string",
  "created_at": "2024-01-01T00:00:00",
  "response_time_ms": 1500,
  "prompt_tokens": 20,
  "completion_tokens": 100,
  "total_tokens": 120,
  "cost_usd": 0.0012,
  "finish_reason": "stop",
  "parameters": {...}
}
```

### GET `/api/ai/providers`
Get available providers and their capabilities.

### GET `/api/ai/health`
Check AI service health status.

### POST `/api/ai/validate`
Validate a request without executing it.

## Usage Examples

### Basic Text Generation
```python
from app.services.ai.factory import get_ai_service
from app.services.ai.schemas import AITextRequest, AIProvider

# Get service instance
ai_service = await get_ai_service()

# Create request
request = AITextRequest(
    prompt="Explain quantum computing",
    provider=AIProvider.OPENAI,
    max_tokens=500,
    temperature=0.7
)

# Generate text
response = await ai_service.generate_text(request)
print(response.text)
```

### Using Template Variables
```python
request = AITextRequest(
    prompt="Write a {{ language }} function that {{ task }}",
    template_variables={
        "language": "Python",
        "task": "calculates fibonacci numbers"
    }
)
```

### Provider Health Check
```python
from app.services.ai.factory import AITextGeneratorFactory

# Check if any providers are available
if AITextGeneratorFactory.is_service_available():
    service = await get_ai_service()
    providers_info = await service.get_available_providers()
```

## Error Handling

The service uses structured error handling:

```python
from app.services.ai.schemas import AITextGenerationError

try:
    response = await ai_service.generate_text(request)
except AITextGenerationError as e:
    print(f"AI Error: {e.message} (Provider: {e.provider}, Code: {e.error_code})")
```

## Adding New Providers

1. Create a new driver class extending `BaseAIDriver`
2. Implement all abstract methods
3. Register the driver in `AITextGeneratorService._register_available_drivers()`
4. Add configuration variables to `config.py`
5. Update the factory methods

Example driver structure:
```python
class NewProviderDriver(BaseAIDriver):
    @property
    def provider_name(self) -> str:
        return "New Provider"
    
    @property
    def default_model(self) -> str:
        return "default-model"
    
    # ... implement other abstract methods
```

## Testing

Run the test suite:
```bash
# Unit tests
pytest tests/unit/test_services/test_ai_service.py -v
pytest tests/unit/test_schemas/test_ai_schema.py -v

# Integration tests
pytest tests/integration/test_api_endpoints.py::TestAIEndpoints -v
```

## Cost Management

The service automatically tracks token usage and calculates costs:
- Pricing information is embedded in each driver
- Cost estimates are returned in the response metadata
- Use this data for budget tracking and optimization

## Template Integration

The service integrates with the existing template system:
- Use Jinja2 templates for complex prompts
- Template variables are processed before sending to AI providers
- Supports both template files and inline template strings
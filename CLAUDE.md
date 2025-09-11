# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
- Local development: `./run_dev.sh` or `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- Docker development: `docker-compose up --build` (runs on port 8778, maps to internal port 8000)
- Production: `./run_prod.sh` or `docker compose up -d --build`
- Docker production: `./run_docker_prod.sh` or `docker build -t three60_fastapi:v1.0 .`

### Environment Setup
- Setup development environment: `./setup_dev.sh` (creates virtual environment and installs dependencies)
- Copy `.env.example` to `.env` and configure environment variables
- AI Provider Keys: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, `GOOGLE_API_KEY`, `REPLICATE_API_TOKEN`
- Optional: `DATABASE_URL`, `SECRET_KEY`, `BACKEND_CORS_ORIGINS`
- AI defaults: `AI_DEFAULT_PROVIDER`, `AI_DEFAULT_MODEL`, `AI_MAX_TOKENS_DEFAULT`, `AI_TEMPERATURE_DEFAULT`
- Image defaults: `IMAGE_DEFAULT_PROVIDER`, `IMAGE_DEFAULT_MODEL`

### Dependencies
- Install: `pip install -r requirements.txt` (or use `./setup_dev.sh` for complete setup)
- Core dependencies: FastAPI, Uvicorn, Pydantic, OpenAI, Google GenAI, Replicate, Docling, PyFilesystem2, Loguru

### Code Quality
- No linting/formatting tools configured - manual code review required
- Follow PEP 8 style guidelines
- Structured logging using Loguru (configured in `app/core/logging_config.py`)

### Testing Commands
- Run all tests: `pytest`
- Run with coverage: `pytest --cov=app --cov-report=html`
- Run only unit tests: `pytest tests/unit`
- Run only integration tests: `pytest tests/integration`
- Run specific test file: `pytest tests/unit/test_services/test_chart_service.py`
- Run tests with verbose output: `pytest -v`
- Run tests and stop on first failure: `pytest -x`
- Run tests matching pattern: `pytest -k "test_chart"`
- Skip slow tests: `pytest -m "not slow"`

## Architecture Overview

### Project Structure
This is a FastAPI application with a modular architecture:

```
app/
├── main.py                 # FastAPI application entry point
├── core/                   # Configuration and settings
├── api/v1/endpoints/       # API route handlers
├── services/               # Business logic layer
├── schemas/                # Pydantic models for request/response
├── utils/                  # Utility functions
└── templates/              # Jinja2 templates for AI prompts
```

### Key Components

**API Endpoints** (`app/api/v1/endpoints/`):
- `document_routes.py` - Document text extraction and processing
- `chart_routes.py` - Data visualization and chart generation
- `pdf_routes.py` - PDF creation and manipulation
- `ai_routes.py` - AI-powered content generation
- `image_routes.py` - Image processing and conversion

**Services** (`app/services/`):
- `documents/base.py` - DocumentExtractor for text extraction from various formats
- `chart_service.py` - Chart generation using data visualization libraries
- `pdf_service.py` - PDF creation and manipulation
- `ai/` - AI text generation with driver pattern architecture
  - `base.py` - BaseAITextGenerator abstract service
  - `factory.py` - AITextGeneratorFactory and service management
  - `drivers/openai_driver.py` - OpenAI API implementation
  - `drivers/gemini_driver.py` - Google Gemini API implementation
  - `schemas.py` - Internal AI service data models
- `image_service.py` - Image processing and format conversion
- `template_manager.py` - Jinja2 template management for AI prompts
- `ai/image/` - AI image generation with driver pattern architecture
  - `base.py` - ImageEngine for multi-provider image generation
  - `factory.py` - ImageDriverFactory and driver management
  - `types.py` - Common types and request/response models
  - `drivers/` - Provider-specific drivers (Gemini, Imagen, Replicate)

**Configuration** (`app/core/config.py`):
- Centralized settings using Pydantic BaseSettings
- Environment variable management
- CORS, database, and API key configuration

### Service Architecture
The application follows a layered architecture:
1. **Routes** - Handle HTTP requests/responses and validation
2. **Services** - Contain business logic and external API integrations
3. **Schemas** - Define data models and validation rules
4. **Utils** - Provide shared utility functions

### AI Service Architecture
The AI service implements a driver pattern for multi-provider support:
- **BaseAITextGenerator** - Abstract service class defining the unified interface
- **AITextGeneratorFactory** - Singleton factory managing driver registration and service instantiation
- **Provider Drivers** - Implement BaseAIDriver interface (OpenAI and Gemini available)
- **Automatic Registration** - Drivers auto-register based on available API keys in environment
- **Template Integration** - Built-in Jinja2 template processing for dynamic prompt generation
- **Error Handling** - Structured error responses with provider-specific error codes
- **Cost Management** - Automatic token counting and cost estimation per provider

#### AI Service Parameter Policy
- Required: only `prompt` is required in both API and internal requests.
- Optional: `provider`, `model`, `max_tokens`, `temperature`, `top_p`, `frequency_penalty`, `presence_penalty`, `stop_sequences`, `system_prompt`, `template_variables` are optional.
- Routes: pass only user-provided fields; do not inject defaults.
- Service: resolves defaults (provider via `settings.AI_DEFAULT_PROVIDER`, model via selected driver’s `default_model`).
- Drivers: send only explicitly provided params to SDKs/APIs; metadata reflects only sent params (plus `model`).

### Adding New AI Providers
To add a new AI provider (e.g., Anthropic, Gemini):
1. Create driver class extending `BaseAIDriver` in `app/services/ai/drivers/`
2. Implement abstract methods: `provider_name`, `default_model`, `supported_models`, `generate_text`, etc.
3. Add provider enum to `AIProvider` in `app/config/ai_models.py`
4. Register driver in `AITextGeneratorService._register_available_drivers()`
5. Add configuration variables to `app/core/config.py`
6. Update factory validation methods

### Gemini Driver
- Location: `app/services/ai/drivers/gemini_driver.py`.
- SDK: uses `google-genai` (`from google import genai`). See `docs/google.sdk.md`.
- Enablement: set `GEMINI_API_KEY` (or `GOOGLE_API_KEY`). Factory registers the driver when configured.
- Defaults: Gemini provider defaults defined in `app/config/ai_models.py` (override/add via `config/ai_models.yaml`).
- Behavior: follows parameter policy (only sends user-provided params; lets API defaults apply). Extracts `response.text`.

### Document Processing
- Multi-format support: PDF, DOCX, TXT, images, emails using Docling
- OCR capabilities for scanned documents
- Table extraction and metadata parsing
- Email parsing with attachment handling
- Advanced document AI extraction with structured output

### Image Generation Service
- Provider-agnostic image generation with pluggable driver architecture
- Available drivers: Gemini Nano (2.5 Flash), Imagen 4, Replicate
- Unified API with consistent request/response models
- Parameter policy: only required `prompt`, optional provider-specific parameters
- Automatic driver registration based on available API keys

### Storage Engine
- **PyFilesystem2-based unified storage** replacing scattered file operations
- **StorageEngine class** (`app/core/storage_engine.py`) handles all file operations
- **Directory structure**: `storage/{public,temp,templates}` with organized subdirectories
- **Automatic cleanup** of temporary files with configurable retention
- **URL generation** for public assets with consistent naming
- **Background tasks** for maintenance and cleanup

### Storage Directory Structure
```
storage/
├── public/           # Publicly accessible files (/storage URL)
│   ├── charts/      # Generated charts (SVG, PNG)
│   ├── images/      # Processed images  
│   ├── documents/   # Processed documents
│   └── pdfs/        # Generated PDFs
├── temp/            # Temporary files (auto-cleanup)
│   ├── uploads/     # User uploads
│   ├── processing/  # Files being processed
│   └── cache/       # Cached results
└── templates/       # System templates
    └── prompts/     # AI prompt templates
```

### Deployment
- Dockerized application with multi-stage builds
- Docker Compose for local development
- Static file serving for generated charts and assets via `/storage` endpoint
- Health checks and restart policies configured
- Background storage cleanup tasks with configurable retention

## Development Patterns

### Service Integration
- Use dependency injection pattern in route handlers: `ai_service = Depends(get_ai_text_service)`
- Services are async-first - use `await` for all service calls
- Factory pattern manages singleton instances and driver registration

### Error Handling
- Services use structured exceptions (e.g., `AITextGenerationError`) with provider context
- API routes convert service exceptions to appropriate HTTP status codes
- Template rendering failures gracefully fall back to original prompt

### Storage Operations
- Use `StorageEngine` for all file operations instead of direct filesystem access
- Files auto-organize into `public/`, `temp/`, and `templates/` with subdirectories
- Public files automatically generate accessible URLs via `/storage/` endpoint
- Temporary files have automatic cleanup based on retention settings

### Testing Strategy  
- Unit tests mock external dependencies and use factory reset methods
- Integration tests use real FastAPI TestClient but expect service unavailability
- AI service tests require provider API keys or will return 503 responses
- Use pytest markers: `@pytest.mark.slow`, `@pytest.mark.integration`, `@pytest.mark.unit`, `@pytest.mark.external_api`
- Test configuration: `pytest.ini` includes asyncio auto mode and warning filters

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.
- Always follow KISS and DRY principles

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
- Local development: `uvicorn main:app --reload --host 0.0.0.0 --port 8000`
- Docker: `docker-compose up --build`
- Production Docker: `docker build -t three60_fastapi:v1.0 .`

### Environment Setup
- Copy `.env.example` to `.env` and configure environment variables
- Required env vars: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`
- Optional: `DATABASE_URL`, `SECRET_KEY`, `BACKEND_CORS_ORIGINS`

### Dependencies
- Install: `pip install -r requirements.txt`
- Core dependencies: FastAPI, Uvicorn, Pydantic, OpenAI, Anthropic

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
- `ai/base.py` - AI service integration (OpenAI, Anthropic)
- `image_service.py` - Image processing and format conversion
- `template_manager.py` - Jinja2 template management for AI prompts

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

### AI Integration
- Supports both OpenAI and Anthropic APIs
- Template-based prompt management with Jinja2
- AI services handle product description generation and content processing

### Document Processing
- Multi-format support: PDF, DOCX, TXT, images, emails
- OCR capabilities for scanned documents
- Table extraction and metadata parsing
- Email parsing with attachment handling

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
- Static file serving for generated charts and assets
- Health checks and restart policies configured
- **Migration script** (`migrate_storage.py`) to move existing files to new structure
# Project Architectural and Organizational Issues

This document captures current architectural, organizational, and software engineering issues in the repository, with concrete recommendations for remediation. Use it as a backlog for refactors and hardening work.

## Architectural
- Monolith coupling: AI, charts, PDFs, documents, and images live in one FastAPI app, making scaling and deploys tightly coupled. Consider module boundaries per domain (or separate services) with clear contracts.
- Storage layering: Business services (e.g., `ChartService._save_chart`) persist files directly. Introduce storage adapters/gateways and return domain results (bytes/structs) from services; let routes orchestrate persistence.
- Service locator: `AITextGeneratorFactory` + `get_ai_service()` hides dependencies. Prefer explicit DI via FastAPI dependencies initialized at startup (or a small container) and pass services explicitly to routes.

### Refactor Checklist
- [ ] Define domain boundaries and packages for `ai/`, `charts/`, `documents/`, `images/`, `pdf/` with clear interfaces.
- [ ] Introduce a `StoragePort` interface and concrete adapter for `StorageEngine` (ports/adapters pattern).
- [ ] Refactor `ChartService` to return SVG bytes/struct; move persistence to a storage adapter at the route layer.
- [ ] Replace service locator with explicit FastAPI dependencies initialized in startup (e.g., `lifespan` factory wiring).

## Organization
- Duplicate extractors: `app/services/documents/base.py` and `.../unstructured_extractor.py` overlap while routes only use the unstructured version. Consolidate on one implementation; remove legacy.
- Image stack inconsistency: `app/services/image_service.py` uses Wand/ImageMagick while `app/utils/image_helpers.py` uses PIL with a parallel builder API. Standardize on one library and one service surface.
- Router import style drift: `app/api/v1/endpoints/__init__.py` re-exports routers, but `app/main.py` imports concrete modules. Pick one convention (prefer named imports from `endpoints/__init__.py`).

### Refactor Checklist
- [ ] Remove `app/services/documents/base.py` (or migrate anything needed) and standardize on `UnstructuredExtractor`.
- [ ] Decide on image engine (Wand or PIL); delete the alternative and consolidate a single `ImageService` API.
- [ ] Standardize router registration via `from app.api.v1.endpoints import chart_router, ...` in `app/main.py`.

## SE Principles & Patterns
- SRP violations:
  - `ChartService` both renders and persists.
  - `document_routes.cleanup_temp_files()` manages temp files while `StorageEngine` already owns this concern.
- Framework leakage: Services (e.g., `UnstructuredExtractor`) raise `HTTPException`. Raise domain errors and translate to HTTP in routes.
- Config duplication: `AIProvider` enum is defined in both `app/config/ai_models.py` and `app/services/ai/schemas.py`. Unify the source of truth.
- Hardcoded pricing/config: AI model pricing and defaults live in code. Externalize to YAML/JSON and load via settings for maintainability.

### Refactor Checklist
- [ ] Make services raise domain errors (e.g., `ServiceError`, `ValidationError`) instead of `HTTPException`.
- [ ] Remove manual temp cleanup in routes; expose cleanup via `StorageEngine` only.
- [ ] Unify `AIProvider` enum (choose one module) and update imports across codebase.
- [ ] Move AI pricing/models to `config/ai_models.yaml` and implement a loader in `app/config`.

## Async & Concurrency
- Event loop misuse: `document_routes` wraps `asyncio.run(...)` inside `run_in_threadpool`. Either make the extractor synchronous and run it in a thread, or call the async method directly; do not nest loops.
- Blocking in async: `pdf_service.generate_pdf` uses WeasyPrint synchronously in an `async` function. Offload to a worker thread (`anyio.to_thread.run_sync`).

### Refactor Checklist
- [ ] Remove `asyncio.run(...)` from `document_routes`; directly `await` or use `anyio.to_thread.run_sync` for sync paths.
- [ ] Wrap WeasyPrint PDF generation with `anyio.to_thread.run_sync` and keep function synchronous.
- [ ] Audit other blocking IO (Wand, PIL, filesystem) and offload as needed.

## API & Validation
- Reliance on `UploadFile.size`: Starlette’s `UploadFile` does not guarantee `size`. Validate using `Content-Length` or stream to a capped buffer; enforce max size via middleware.
- Response consistency: Endpoints declare `response_model` and manually return `JSONResponse`. Return Pydantic models (FastAPI will serialize) for validation and consistency.

### Refactor Checklist
- [ ] Add upload size middleware (based on `Content-Length`) and streaming validators for unknown sizes.
- [ ] Update image/document endpoints to use validated size checks; remove `UploadFile.size` usage.
- [ ] Return Pydantic models from routes; remove direct `JSONResponse` where `response_model` exists.
- [ ] Add/align error response models where appropriate.

## Logging & Error Handling
- `print()` in background tasks and extractor warnings. Use `logging` with structured fields and levels.
- Broad `except Exception` patterns risk leaking internals. Map to typed, user‑safe errors; log details server‑side.

### Refactor Checklist
- [ ] Replace `print()` with `logging` across services/routes; configure app logger on startup.
- [ ] Narrow `except Exception` blocks; map to typed exceptions with safe client messages.
- [ ] Add structured context (e.g., `request_id`, `operation`) using `logger.bind()` or `extra`.

## Security & Configuration
- Secrets committed: `.env` is present in git and contains keys. Remove from history, rotate credentials, and rely on environment plus `.env.example` only.
- CORS env parsing: `BACKEND_CORS_ORIGINS` is a CSV string but typed as `List[AnyHttpUrl]`. Add parsing/validation in settings.

### Refactor Checklist
- [ ] Purge `.env` from git history and rotate keys; rely on env vars and `.env.example` only.
- [ ] Implement CSV parsing for `BACKEND_CORS_ORIGINS` with validation in `Settings`.
- [ ] Remove default secrets from settings; ensure no sensitive defaults exist.

## Testing & Tooling
- Settings mutation: Tests monkeypatch `settings`, but modules may have captured earlier instances. Prefer an app factory with injected settings/services or dependency overrides in tests.
- Gaps: Add tests for image/document endpoints (size checks, error paths) and storage engine behaviors.

### Refactor Checklist
- [ ] Introduce an application factory that accepts `Settings` and service instances for tests.
- [ ] Use FastAPI dependency overrides to inject mocked services (storage, AI) in integration tests.
- [ ] Add tests for image/document size enforcement and error paths.
- [ ] Add tests for storage engine list/read/delete and cleanup routines.
- [ ] Add AI route tests with mocked driver covering success/error paths.

## Recommended Next Steps
1. Define domain module boundaries and extract storage adapters; stop persisting in services.
2. Replace service locator with explicit FastAPI dependencies and startup wiring.
3. Consolidate document extractor and image processing to a single implementation each.
4. Fix async issues (remove nested `asyncio.run`, move blocking work to threads).
5. Unify `AIProvider` enum and externalize AI pricing/config.
6. Replace `JSONResponse` returns with response models; fix file size validation.
7. Remove committed secrets; add CORS parsing; expand tests for the above changes.

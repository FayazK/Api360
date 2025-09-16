# Repository Guidelines

## Project Structure & Module Organization
Application code lives in `app/`, with HTTP routes in `app/api/v1/endpoints/`, reusable business logic in `app/services/`, configuration in `app/core/`, and data contracts in `app/schemas/`. Templated HTML sits under `app/templates/`. Automated tests mirror this layout in `tests/unit/` and `tests/integration/`; shared fixtures reside in `tests/fixtures/` and `tests/conftest.py`. Static assets are stored in `static/`, while generated files belong in `storage/public/`. Documentation and architecture notes are tracked inside `docs/`.

## Build, Test, and Development Commands
Run `./setup_dev.sh` to create the `fastenv` virtual environment and install dependencies. Start the API locally with `./run_dev.sh` or `uvicorn app.main:app --reload`. For production-like execution, use `./run_prod.sh` or `docker compose up -d --build`. Execute the full test suite quietly via `pytest -q`; target specific markers with `pytest -m unit` or `pytest -m integration`. Measure coverage using `pytest --cov=app` when preparing releases.

## Coding Style & Naming Conventions
Follow PEP 8 with four-space indentation and meaningful type hints. Modules use `snake_case.py`; classes follow `PascalCase`, while functions, variables, and file-level constants adopt `snake_case` and `UPPER_SNAKE` respectively. Prefer absolute imports such as `from app.services...`. Keep FastAPI route handlers thin—delegate logic to `services/` layers and return schema models from `app/schemas/`.

## Testing Guidelines
Use pytest and the provided fixtures (`client`, `async_client`, `mock_storage_engine`) to isolate units from external services. Name tests `test_*.py` and group broader flows under `@pytest.mark.integration`. Avoid writing to disk or hitting real networks; rely on mocks and temporary storage fixtures. Run `pytest -q` before opening a PR, and ensure new features include coverage for success, failure, and edge cases.

## Commit & Pull Request Guidelines
Adopt the existing commit style like `✨ (scope): short summary` or `🐛 (module): fix message`. PRs should explain the motivation, list linked issues, include before/after notes or sample responses, and document any new endpoints in `docs/`. Always attach the test plan (e.g., `pytest -q`) and update relevant READMEs when behavior changes.

## Security & Configuration Tips
Never commit secrets; copy `.env.example` to `.env` for local development and rely on environment variables in production. Review `app/core/config.py` and `docs/AI_SERVICE_README.md` to understand provider keys and AI defaults. Optional AI parameters must pass through untouched so the services layer can apply defaults safely.

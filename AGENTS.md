# Repository Guidelines

## Project Structure & Module Organization
- `app/` — FastAPI application code.
  - `api/v1/endpoints/` (route handlers), `services/` (business logic), `core/` (config, storage), `schemas/`, `templates/`.
- `tests/` — pytest suite: `unit/`, `integration/`, shared `conftest.py`, and `fixtures/`.
- `docs/` — architecture and service docs (e.g., `AI_SERVICE_README.md`).
- `static/`, `storage/public/` — served assets and generated files.
- Root scripts: `setup_dev.sh`, `run_dev.sh`, `run_prod.sh`, `run_docker_prod.sh`; container files: `Dockerfile`, `docker-compose.yml`.

## Build, Test, and Development Commands
- Setup environment: `./setup_dev.sh` (creates `fastenv`, installs deps) or:
  - `python3 -m venv fastenv && source fastenv/bin/activate && pip install -r requirements.txt`
- Run locally (dev): `./run_dev.sh` or `uvicorn app.main:app --reload`
- Run (prod): `./run_prod.sh` or `docker compose up -d --build`
- Tests (quiet): `pytest -q` (markers: `unit`, `integration`). Examples:
  - `pytest -m unit`, `pytest -m integration`
  - Optional coverage: `pytest --cov=app` (plugin installed)

## Coding Style & Naming Conventions
- Follow PEP 8, 4‑space indentation, use type hints and docstrings for public functions/classes.
- Naming: modules/files `snake_case.py`, functions/vars `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE`.
- Imports: prefer absolute (e.g., `from app.services...`). Keep routes thin; delegate logic to `services/`.
- FastAPI: keep response models in `schemas/`; configuration in `app/core/config.py`.

## Testing Guidelines
- Place tests mirroring `app/` structure; files named `test_*.py` and classes `Test*` (see `pytest.ini`).
- Use provided fixtures from `tests/conftest.py` (e.g., `client`, `async_client`, `mock_storage_engine`). Avoid real network/file side effects.
- Mark broader flows as `@pytest.mark.integration`; unit tests should isolate services and schemas.

## Commit & Pull Request Guidelines
- Commit style matches history: `✨ (scope): short summary`, common emojis: ✨ feature, 🐛 fix, ♻️ refactor, 📝 docs, 🔧 config.
  - Examples: `🐛 (documents): fix temp cleanup`, `♻️ (api): refactor endpoint imports`.
- PRs: clear description, linked issues, before/after notes or sample API responses, and test plan. Require `pytest -q` green; update `docs/` when endpoints or behavior change.

## Security & Configuration Tips
- Do not commit secrets. Copy `.env.example` to `.env` locally; production uses environment variables.
- Review `app/core/config.py` and `docs/AI_SERVICE_README.md` for provider keys and settings.

# Repository Guidelines

## Project Structure & Module Organization

- `src/`: SvelteKit frontend (routes, layouts, components, i18n).
- `backend/open_webui/`: FastAPI app (routers, models, migrations, `main.py`).
- `cypress/`: End‑to‑end tests (`*.cy.ts`).
- `test/` and `backend/` test files: Pytest suites (`test_*.py`).
- `static/`, `docs/`, `scripts/`: Assets, docs, utilities (e.g., `scripts/prepare-pyodide.js`).

## Build, Test, and Development Commands

- Frontend
  - Install: `npm ci` (Node 18–22). Build: `npm run build`. Dev: `npm run dev`.
  - Lint/format: `npm run lint`, `npm run format`, types: `npm run check`.
  - Unit tests: `npm run test:frontend` (Vitest). E2E: `npm run cy:open`.
- Backend
  - Setup: `python -m venv .venv && source .venv/bin/activate && pip install -r backend/requirements.txt`.
  - Run API: `cd backend && uvicorn open_webui.main:app --reload --port 8080` (or `./start.sh`).
  - DB migrations: `cd backend && alembic upgrade head`.
- Docker
  - Compose: `make startAndBuild` or `./run-compose.sh --webui[port=3000]`.

## Coding Style & Naming Conventions

- Frontend: Prettier (tabs, single quotes, width 100, no trailing commas). ESLint + TypeScript + Svelte.
- Backend: Black (`npm run format:backend`) and Pylint (`npm run lint:backend`).
- Naming: Python modules/functions `snake_case`, classes `PascalCase`. Svelte components `PascalCase.svelte` under `src/lib/`.

## Testing Guidelines

- Python: place tests as `test_*.py`; run `cd backend && pytest -q`.
- Frontend: `*.test.ts`/`*.spec.ts`; run `npm run test:frontend`.
- E2E: add specs to `cypress/e2e/`; run `npm run cy:open` or `npx cypress run`.

## Commit & Pull Request Guidelines

- Commits: follow Conventional Commits (e.g., `feat(frontend): add chat view`, `fix(backend): handle 401`).
- PRs: include description, linked issues, test plan, and screenshots for UI changes.
- Checks: ensure `npm run lint && npm run test:frontend` pass and `cd backend && pytest` is green; update docs and `.env.example` when changing config.

## Security & Configuration Tips

- Copy `.env.example` to `.env`; never commit secrets. Use Python 3.11–3.12 and Node 18–22.
- Before first run, apply migrations (`alembic upgrade head`). See `backend/start.sh` and `docker-compose.yaml` for environment options.

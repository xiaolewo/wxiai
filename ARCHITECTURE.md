# Architecture Overview

## Runtime Topology

- Backend: FastAPI app in `backend/open_webui/main.py`, mounts routers from `backend/open_webui/routers/*` and ASGI sockets from `backend/open_webui/socket/`.
- Frontend: SvelteKit + Vite in `src/` (routes, layouts, components), served by the backend or via `vite dev` in local dev.
- Storage: SQLAlchemy ORM on top of SQLite/Postgres/SQLCipher; Redis optional for websockets, locks, and collaboration docs.

## Startup & Migration Lifecycle

- Peewee migrations first: `internal/db.py::handle_peewee_migration()` runs `internal/migrations/*` to bridge legacy state.
- Alembic migrations next: `config.py::delayed_migration_execution()` upgrades Alembic to `head` using `migrations/versions/*`.
- Table ensure: `Base.metadata.create_all(bind=engine)` as a safety net after migrations (avoids missing tables across feature packs).
- Default config & field guards: `config.py` inserts default rows (e.g., Jimeng/Kling) and runs targeted field checks to add missing columns safely when needed.

## Data Model Pattern

- Core tables: `user`, `group`, `folder`, `file`, `chat`, `message`, `model`, `tool`, `function`, `credit*`, `config`.
- Feature domains follow a consistent triple:
  - `<feature>_config`: global settings/defaults
  - `<feature>_tasks`: user tasks, status, progress, result URLs, timestamps (epoch or DateTime)
  - `<feature>_credits`: per-request credit ledger (user_id, task_id, amount, op type)
- Timestamps: backend commonly stores epoch `BigInteger` (`created_at`, `updated_at`, `last_active_at`) in core tables; some feature tables use SQL `DateTime`.
- JSON: use custom `JSONField` (SQLAlchemy `TypeDecorator`) for flexible payloads.

## API Surface & Conventions

- Prefixes: `/api/v1/<domain>` for REST; 3rd‑party compatibility surfaces under `/openai`, `/ollama`, etc.
- Example domains: `jimeng`, `kling`, `kling_lip_sync`, `midjourney`, `flux`, `veo`, `storage`, `knowledge`, `chats`, `files`, `users`.
- Include routers in `main.py` with explicit prefixes and tags; all endpoints should respect auth, credit checks (see `utils/credit/utils.py`).

## WebSocket & Realtime

- Socket server in `socket/main.py` using `python-socketio` (Redis manager optional). Supports session/user/usage pools and document sync with `pycrdt`.
- Distributed locking via Redis for periodic cleanup (`RedisLock`).

## Configuration & Secrets

- `env.py` centralizes environment flags (DB URL/Pool, auth, OAuth, logging, websockets). SQLCipher supported via `sqlite+sqlcipher://` and `DATABASE_PASSWORD`.
- Persistent (non‑env) configuration stored in `config` table with `PersistentConfig` helpers. On startup, `config.json` migrates into DB if present.

## Frontend Layout

- `src/routes/` owns Svelte routes and layouts; E2E tests in `cypress/e2e/*.cy.ts`, unit tests via Vitest. ESLint/Prettier enforce style.

## Cross‑Cutting Concerns

- Credit & Pricing: `utils/credit/utils.py` calculates model/feature costs and enforces `minimum_credit`, integrates with `models` and chat error reporting.
- Access control: `utils/access_control.py` gatekeeps read/write to `model`, etc.
- Logging/Audit: `utils/logger.py`, `utils/audit.py`, log level via `GLOBAL_LOG_LEVEL`/per‑source envs.

## Extension Blueprint

- Add models in `models/<feature>.py` (config/tasks/credits) and import before Alembic autogenerate.
- Create Alembic revision with proper `down_revision`; include indices for `user_id`, `status`, `created_at` on task tables.
- Implement router under `routers/<feature>.py`, wire to `main.py` with `/api/v1/<feature>`.
- Frontend: add Svelte routes and tests; update `.env.example` and docs.

# Release Runbook (Zero‑Defect)

## 1) Preflight Checklist

- Env & versions: Node 18–22, Python 3.11/3.12, Docker/Compose if used.
- Config: copy `.env.example` → `.env`; verify `DATABASE_URL`, Redis, auth, ports.
- Backups: if SQLite → `cp backend/data/webui.db webui.db.bak.$(date +%F_%H%M%S)`; Postgres → provider snapshot.
- Dependencies: `pip install -r backend/requirements.txt && npm ci`.
- Health: `npm run lint && npm run test:frontend && (cd backend && pytest -q)`.

## 2) Database Migration (Safe Path)

- Dry‑run locally/staging:
  - `cd backend && alembic upgrade head`
  - Validate tables/columns/indexes for the feature domain.
- Ensure models imported before autogenerate; no Peewee changes for new features.
- If multiple heads: prefer linearizing via new revision; avoid destructive merges.
- Reference: `MIGRATION_BEST_PRACTICES.md`, `MIGRATION_OPTIMIZATION.md`.

## 3) Update Existing Production

- Put app in maintenance if needed.
- Backup DB (see Preflight).
- Deploy app artifacts/containers.
- Apply migrations on server: `cd backend && alembic upgrade head`.
- Restart:
  - Compose: `./run-compose.sh --webui[port=3000] --build`
  - System: `backend/start.sh` or process manager.
- Verify `/health` and critical APIs (see Smoke Tests).

## 4) Fresh Install (New Environment)

- `make startAndBuild` or `./run-compose.sh --webui[port=3000]`.
- First boot runs Peewee → Alembic → `Base.metadata.create_all` (+ default config).
- Create admin if needed via `backend/start.sh` SPACE flow or API.

## 5) Smoke Tests (Post‑Deploy)

- Auth: sign‑in/out, token issuance.
- CRUD: users, chats, files, models.
- Feature domain happy‑path (e.g., Jimeng/Kling/Flux job → status → artifact URL).
- Credits: request blocked when below minimum; price application works.
- Websocket: basic connect, chat/notes sync.

## 6) Rollback

- App: deploy previous image or code bundle.
- DB: `alembic downgrade <previous_rev>` if schema changed; restore DB backup for major failures.
- Re‑run Smoke Tests.

## 7) Operational Notes

- SQLCipher: set `DATABASE_URL=sqlite+sqlcipher:///...` and `DATABASE_PASSWORD`.
- Pooling: tune `DATABASE_POOL_SIZE`, `*_TIMEOUT`, `*_RECYCLE` for Postgres.
- Logs: set `GLOBAL_LOG_LEVEL` and per‑source levels in `.env`.
- Observability: audit middleware enabled; avoid logging secrets.

## 8) Release Criteria (Do‑Not‑Ship if any fail)

- Lints/tests green; migrations apply cleanly and are reversible.
- No unintended table/column changes in Alembic diff.
- Docs updated: `.env.example`, API docs/UX notes if user‑facing.

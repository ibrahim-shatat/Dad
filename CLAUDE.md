# CLAUDE.md

Guidance for Claude Code working in this repo. See `README.md` for the product overview and
`CLAUDE_SETUP_PLAN.md` for the longer roadmap.

## What this is

"Dad" — an AI executive-assistant dashboard (FastAPI + React + PostgreSQL + Claude). AI
summarizes/drafts/extracts; sensitive outbound actions (emails, exports) wait behind a human
**approval queue**. Preserve that approval-first model.

## Commands

```bash
# Backend (from backend/, venv at .venv)
.venv/Scripts/uvicorn app.main:app --reload --port 8000      # API
.venv/Scripts/python -m arq app.tasks.worker.WorkerSettings  # worker (arq mode only)
.venv/Scripts/alembic upgrade head                            # apply migrations
.venv/Scripts/alembic revision --autogenerate -m "msg"       # new migration
DATABASE_URL=postgresql+asyncpg://dad:dad@127.0.0.1:5432/dad_test .venv/Scripts/python -m pytest

# Frontend (from frontend/)
npm run dev            # dev server on :5173
npm run build          # typecheck + production build
```

## Architecture notes

- **Job execution is switchable via `JOB_MODE`:**
  - `arq` (default, local dev): endpoints enqueue to Redis; a separate arq worker runs them.
  - `inline` (production/free hosting): jobs run in-process as FastAPI background tasks —
    no Redis/worker. Implemented in `app/tasks/queue.py` (`JobEnqueuer` / `get_job_queue`).
  - Endpoints depend on `get_job_queue` and call `queue.enqueue_job("job_name", ...)`. Job
    functions live in `app/tasks/jobs.py` and take an arq-style `ctx` first arg.
- **Layers:** routes in `app/api/v1/endpoints/`, business logic in `app/services/`, DB models in
  `app/models/`, request/response schemas in `app/schemas/`. Put AI prompt logic under
  `app/services/ai/`.
- **Auth:** JWT access tokens + an httpOnly refresh cookie (`/api/v1/auth`). Roles: `admin`,
  `director`, `assistant` (see `require_role`).

## Conventions

- Backend: async SQLAlchemy, Pydantic v2, add an Alembic migration for every model change.
- Keep sensitive actions (email send, exports) routed through `app/services/approvals` /
  `app/services/email/approval.py` — never send directly from an endpoint.
- Don't commit secrets; `.env` is gitignored.

## Gotchas (learned the hard way)

- **Use `127.0.0.1`, not `localhost`, in DB/Redis URLs on Windows** — `localhost` resolves to
  IPv6 `::1` first and asyncpg/redis time out on startup.
- **`EmailStr` rejects reserved domains** (e.g. `*.local`). Never seed a user with an
  `@…​.local` email — response serialization of `UserRead.email` will 500. Use a real domain.
- **Supabase `DATABASE_URL`:** use the *Session pooler* string, scheme `postgresql+asyncpg`,
  append `?ssl=require`, and URL-encode `@` in the password as `%40`. Alembic escapes `%` in the
  URL (see `alembic/env.py`) so ConfigParser interpolation doesn't choke.
- **Tests on Windows:** conftest sets `WindowsSelectorEventLoopPolicy` (Proactor loop crashes
  asyncpg teardown) and pyproject sets `asyncio_default_test_loop_scope = "session"`.

## Deploy

Live on Netlify (frontend) + Render (API) + Supabase (Postgres). Runbook:
`deploy/DEPLOY_PATHB.md`. Push to `main` → Render + Netlify auto-redeploy.
```

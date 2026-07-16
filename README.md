# Dad — AI Executive Assistant

An AI executive-assistant dashboard. It reads documents, processes meeting notes,
manages email drafts, generates presentations, and keeps sensitive AI actions behind a
human approval step. Powered by Anthropic Claude.

> **Core idea:** AI can summarize, draft, extract, and generate — but anything that
> "goes out" (emails, exports) waits for a director/admin to approve it first.

## Live

- **App:** https://ai-excutive-agent.netlify.app
- **API:** https://dad-api-rw61.onrender.com
- Hosted free on Netlify (frontend) + Render (API) + Supabase (Postgres). See
  [`deploy/DEPLOY_PATHB.md`](deploy/DEPLOY_PATHB.md).

## Features

- **Documents** — upload → text extraction → Claude review (executive summary, risk flags,
  suggested rewrites).
- **Meetings** — paste notes → Claude summary + extracted action items & decisions, and an
  optional follow-up email draft.
- **Email** — connect Gmail/Outlook, sync + AI summaries and urgency, draft replies.
- **Presentations** — generate structured slides from text/documents, export to `.pptx`.
- **Approvals** — a human-in-the-loop queue; emails and exports only send/finalize after
  approval.
- **Dashboard** — executive overview of everything awaiting attention.

## Tech stack

| Layer | Tech |
|-------|------|
| Backend | Python 3.12, FastAPI, SQLAlchemy (async), Alembic, Pydantic |
| AI | Anthropic Claude (structured tool-use) |
| Jobs | arq + Redis (local) **or** in-process background tasks (`JOB_MODE=inline`, prod) |
| Frontend | React 19, Vite, TypeScript, Tailwind, TanStack Query, Zustand |
| Database | PostgreSQL |
| Deploy | Netlify + Render + Supabase (no Docker needed); Docker Compose also supported |

## Architecture

```
Browser ──▶ Netlify (React SPA)
              │  /api/* proxied to ▼
              └───────────────▶ Render (FastAPI)  ──▶ Supabase (PostgreSQL)
                                     │
                                     └──▶ Anthropic Claude
```

Background AI work runs one of two ways, selected by `JOB_MODE`:
- `arq` (default, local): jobs are queued to Redis and run by a separate worker.
- `inline` (production): jobs run in-process as FastAPI background tasks — no Redis/worker
  needed, which keeps free-tier hosting simple.

## Local development

Requires Python 3.12, Node 20+, PostgreSQL, and (for `arq` mode) Redis.

```bash
# 1. Backend
cd backend
python -m venv .venv
.venv/Scripts/pip install -e ".[dev]"     # Windows; use .venv/bin/pip on macOS/Linux
cp ../.env.example .env                     # then edit: ANTHROPIC_API_KEY, DB/Redis URLs
#   Point DATABASE_URL/REDIS_URL at 127.0.0.1 for a native (non-Docker) run.
.venv/Scripts/alembic upgrade head          # create tables
.venv/Scripts/python -m app.scripts.create_admin   # create the first admin user

# run the API + worker (two terminals)
.venv/Scripts/uvicorn app.main:app --reload --port 8000
.venv/Scripts/python -m arq app.tasks.worker.WorkerSettings

# 2. Frontend
cd ../frontend
npm install
npm run dev                                 # http://localhost:5173
```

Or with Docker Compose from the repo root: `docker compose up --build`.

## Tests

```bash
cd backend
# point at a *_test database (auto-created if missing)
DATABASE_URL=postgresql+asyncpg://dad:dad@127.0.0.1:5432/dad_test .venv/Scripts/python -m pytest
```

## Project layout

```
backend/
  app/
    api/v1/endpoints/   HTTP routes (auth, documents, meetings, email, presentations, approvals)
    services/           AI, email, documents, presentations, approvals logic
    tasks/              background jobs (arq worker + inline runner)
    models/ schemas/    SQLAlchemy models + Pydantic schemas
  alembic/              database migrations
  tests/                pytest suite
frontend/
  src/pages/            one folder per feature area
  src/api/              typed API clients
  src/components/       shared UI
deploy/                 deployment kits + runbooks
```

## Deployment

- **Free (Netlify + Render + Supabase):** [`deploy/DEPLOY_PATHB.md`](deploy/DEPLOY_PATHB.md)
- **Single Linux VM (native, no Docker):** [`deploy/DEPLOY.md`](deploy/DEPLOY.md)

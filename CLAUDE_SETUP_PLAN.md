# Dad - Claude Setup Plan

This file is for Claude / Claude Code so it can understand the project quickly and work safely.

## Product Summary

Dad is an AI executive assistant dashboard.

The app helps an executive or assistant handle documents, meetings, presentations, emails, and approvals. AI can summarize, draft, extract, and generate, but important actions should go through a human approval step before they are treated as final.

Core product sentence:

> Dad is an AI executive assistant that reads documents, processes meetings, manages email drafts, creates presentations, and keeps sensitive AI actions behind human approval.

## Current Stack

- Backend: Python 3.12, FastAPI, SQLAlchemy async, Alembic
- Database: PostgreSQL
- Queue/cache: Redis
- Background jobs: arq
- AI provider: Anthropic Claude
- Frontend: React, Vite, TypeScript
- Frontend data: TanStack Query, Axios, Zustand
- Styling: Tailwind CSS
- Containers: Docker Compose
- Reverse proxy for production: Caddy

## Main Folders

- `backend/`: FastAPI API, models, services, migrations, background jobs
- `backend/app/api/v1/endpoints/`: HTTP API routes
- `backend/app/models/`: database models
- `backend/app/schemas/`: request/response schemas
- `backend/app/services/`: AI, email, document, approval, presentation logic
- `backend/app/tasks/`: background worker jobs
- `backend/alembic/`: database migrations
- `frontend/`: React application
- `frontend/src/pages/`: main app screens
- `frontend/src/api/`: frontend API clients
- `frontend/src/components/`: reusable UI and layout components

## Current Feature Areas

### Dashboard

Shows the executive overview:

- documents awaiting review
- presentations in progress
- open action items
- unread urgent emails
- pending approvals
- upcoming deadlines

### Documents

Implemented direction:

- upload documents
- store uploaded files
- extract document text
- review document with Claude
- produce executive summary
- flag risks
- suggest rewrites
- acknowledge review disclaimer

### Meetings

Implemented direction:

- create meeting from notes/text
- AI generates summary
- AI extracts action items
- AI extracts decisions
- AI may draft a follow-up email
- action items and decisions can be updated

### Email

Implemented direction:

- connect Gmail
- connect Outlook
- sync messages
- summarize messages with AI
- classify urgency
- draft replies
- send/approve workflow is designed around approval items

### Presentations

Implemented direction:

- create a presentation from source text or document text
- Claude generates structured slide content
- backend builds a `.pptx`
- user can download generated presentation
- export can create an approval item

### Approvals

Human-in-the-loop safety layer:

- approval queue items
- approve/reject actions
- item types include email drafts and presentation exports
- future types can include document sharing, task delegation, calendar sends, etc.

## How To Run Locally

Use Docker Compose from the project root.

```bash
docker compose up --build
```

Local URLs:

- Frontend: `http://localhost:5173`
- Backend health: `http://localhost:8000/health`
- API prefix: `http://localhost:8000/api/v1`
- PostgreSQL exposed locally on port `5433`

The local override file enables hot reload.

## Environment Setup

Copy `.env.example` to `.env` and fill real values.

Important values:

- `ANTHROPIC_API_KEY`
- `JWT_SECRET`
- `TOKEN_ENCRYPTION_KEY`
- Gmail OAuth credentials if Gmail is used
- Microsoft OAuth credentials if Outlook is used

Do not commit `.env`.

## Claude Working Rules

When Claude works on this project:

1. Read this file first.
2. Check `git status` before editing.
3. Do not overwrite user changes.
4. Keep backend changes aligned with FastAPI, async SQLAlchemy, Pydantic, and Alembic.
5. Keep frontend changes aligned with React, Vite, TypeScript, Tailwind, TanStack Query, and the existing component style.
6. Put AI work in `backend/app/services/ai/` or `backend/app/tasks/jobs.py` when it belongs in background processing.
7. Put user-facing API routes in `backend/app/api/v1/endpoints/`.
8. Add or update schemas in `backend/app/schemas/`.
9. Add Alembic migrations for database model changes.
10. Do not put secrets in code or committed config.
11. Preserve the approval-first safety model for emails, exports, shares, and other sensitive actions.

## Recommended Feature Roadmap

### Phase 1 - Stabilize Existing App

- Fix text encoding artifacts like `â€”`, `â€¦`, and `Â·`.
- Confirm Docker startup works from a clean checkout.
- Confirm migrations run automatically through `backend/entrypoint.sh`.
- Add a seed/admin setup flow that is easy to run.
- Add basic backend tests for auth, documents, meetings, approvals, and dashboard.
- Add frontend empty/error/loading states where missing.

### Phase 2 - Better Approval Flow

- Allow editing an email draft before approval.
- Require rejection reason/comment.
- Add approval history.
- Show who requested and who reviewed each item.
- Add approval filters by type/status/date.
- Add clear post-approval behavior per item type.

### Phase 3 - Executive Briefing

- Add a daily briefing page.
- Include urgent emails, meetings, open action items, pending approvals, and document risks.
- Generate a Claude-written executive summary.
- Let the user mark briefing items as handled.

### Phase 4 - Calendar Integration

- Add Google Calendar and Outlook Calendar OAuth.
- Show upcoming meetings.
- Generate meeting prep briefs.
- Link meeting notes to calendar events.
- Create post-meeting follow-up tasks and emails.

### Phase 5 - Workspace Search / Chat

- Add semantic or keyword search across documents, meetings, emails, and presentations.
- Add a chat interface for questions like:
  - "What needs my approval today?"
  - "Summarize open tasks from this week."
  - "What risks were found in the uploaded contract?"
- Keep source links in answers.

### Phase 6 - Admin And Production Readiness

- Add user management UI.
- Add integration settings page.
- Add audit logs.
- Add rate-limit and retry policies.
- Add production deployment checklist.
- Improve observability for failed AI jobs and failed syncs.

## MCP Notes

MCP can help Claude connect to outside tools, but MCP setup should be added carefully.

Suggested MCP categories:

- Filesystem MCP: useful if Claude needs controlled access to the project folder.
- GitHub MCP: useful if the project is pushed to GitHub and Claude needs PR/issues/repo context.
- Google Drive MCP: useful if documents come from Drive.
- Gmail MCP: useful if Claude should inspect email outside the app's own Gmail integration.
- Google Calendar MCP: useful for calendar features.
- Outlook Email/Calendar MCP: useful for Microsoft 365 users.
- Postgres MCP: useful for safe database inspection in development.

Do not add API keys or OAuth secrets directly into committed MCP config.

If using Claude Code, prefer a local, uncommitted MCP config for machine-specific secrets and credentials.

## Suggested Claude Prompts

Use these prompts when opening the project in Claude:

```text
Read CLAUDE_SETUP_PLAN.md first. Then inspect the project structure. Do not edit files yet. Tell me what you understand and what you recommend next.
```

```text
Read CLAUDE_SETUP_PLAN.md and implement Phase 1 stabilization. Keep changes small, preserve existing behavior, and list every file changed.
```

```text
Read CLAUDE_SETUP_PLAN.md and build the improved approval flow. Start by mapping current backend and frontend approval code, then implement the smallest complete version.
```

```text
Read CLAUDE_SETUP_PLAN.md and add calendar integration planning only. Do not code yet. Produce backend models, API routes, frontend screens, and OAuth requirements.
```

## Immediate Next Best Task

The best first task is Phase 1:

1. Fix encoding artifacts in visible text.
2. Verify Docker Compose startup.
3. Verify backend health endpoint.
4. Verify frontend loads.
5. Add a short setup section to the project README or keep this file as the working guide.


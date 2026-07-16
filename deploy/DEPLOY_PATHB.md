# Deploying Dad live — Path B (free, no credit card)

Free hosting split across three services, **no credit card required**:

| Piece | Service | Free tier |
|-------|---------|-----------|
| Frontend (React) + `/api` proxy | **Netlify** | yes |
| Backend API (FastAPI) | **Render** | yes (sleeps after ~15 min idle) |
| PostgreSQL | **Supabase** | yes |

Jobs run **in-process** (`JOB_MODE=inline`) — no Redis, no separate worker. This is wired up
already: `render.yaml`, `netlify.toml`, and the inline job backend are in the repo.

Requires a **GitHub** repo (Render + Netlify deploy from it).

---

## 1. Push the code to GitHub

```powershell
# from the project root
git add -A
git commit -m "Path B deploy config"
# create an empty repo on github.com first, then:
git remote add origin https://github.com/YOURNAME/dad.git
git branch -M main
git push -u origin main
```

## 2. Database — Supabase

1. supabase.com → **New project** (pick a region near you, set a DB password).
2. **Project Settings → Database → Connection string → "Session pooler"** (IPv4, works with Render).
   It looks like:
   `postgresql://postgres.abcd:PASSWORD@aws-0-REGION.pooler.supabase.com:5432/postgres`
3. Convert the scheme to asyncpg (this is your `DATABASE_URL`):
   `postgresql+asyncpg://postgres.abcd:PASSWORD@aws-0-REGION.pooler.supabase.com:5432/postgres`
   (URL-encode any special characters in the password.)

## 3. Backend — Render

1. render.com → **New + → Blueprint** → connect your GitHub repo. Render reads `render.yaml`.
2. After it creates **dad-api**, open **Environment** and set the `sync:false` vars:
   - `ANTHROPIC_API_KEY` — a **freshly rotated** key from console.anthropic.com
   - `TOKEN_ENCRYPTION_KEY` — generate: `python -c "from cryptography.fernet import Fernet;print(Fernet.generate_key().decode())"`
   - `DATABASE_URL` — the Supabase asyncpg string from step 2
   - `CORS_ORIGINS`, `FRONTEND_URL` — your Netlify URL (fill after step 4; use a placeholder for now)
   - `API_BASE_URL` — this service's URL, e.g. `https://dad-api.onrender.com`
3. Deploy. The build runs `alembic upgrade head`, creating all tables in Supabase.
4. Verify: open `https://dad-api.onrender.com/health` → `{"status":"ok"}`.

## 4. Frontend — Netlify

1. Edit **`netlify.toml`**: replace `REPLACE-WITH-RENDER-URL.onrender.com` with your real Render
   host (e.g. `dad-api.onrender.com`). Commit + push.
2. netlify.com → **Add new site → Import from GitHub** → pick the repo.
   Build settings come from `netlify.toml` automatically. Deploy.
3. Copy your Netlify URL (e.g. `https://dad-xyz.netlify.app`).
4. Back in **Render → Environment**, set `CORS_ORIGINS` and `FRONTEND_URL` to that Netlify URL.
   Save (Render redeploys).

## 5. Create the first admin user

Supabase is reachable from anywhere, so seed the admin from your local machine against the
production DB:

```powershell
cd backend
$env:DATABASE_URL = "postgresql+asyncpg://postgres.abcd:PASSWORD@aws-0-REGION.pooler.supabase.com:5432/postgres"
$env:JOB_MODE = "inline"
.\.venv\Scripts\python.exe -m app.scripts.create_admin   # prompts for email / name / password
```

## 6. Done

Open your Netlify URL and log in. The frontend serves from Netlify; every `/api/*` call is
proxied to Render; Render talks to Supabase and calls Claude in-process.

---

### Known free-tier limits
- **Render free sleeps** after ~15 min idle → the first request after idle takes ~30–60s (cold start).
- **Ephemeral storage** on Render → uploaded documents and generated `.pptx` files don't survive a
  restart/redeploy. Meetings/summaries/approvals (all in Supabase) persist fine. Swap file storage to
  Supabase Storage/S3 when you need durable files.
- **Supabase free** pauses a project after ~1 week of no activity (resumable from the dashboard).

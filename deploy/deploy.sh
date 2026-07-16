#!/usr/bin/env bash
# Build + migrate + restart. Run on the server as the 'dad' user after code is uploaded
# to /opt/dad. Safe to run repeatedly for every update.
#   sudo -u dad bash /opt/dad/deploy/deploy.sh
set -euo pipefail

APP_DIR=/opt/dad
BACKEND="$APP_DIR/backend"
FRONTEND="$APP_DIR/frontend"

echo "==> Backend: venv + dependencies"
cd "$BACKEND"
if [ ! -d .venv ]; then
  python3.12 -m venv .venv
fi
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -e .

echo "==> Backend: database migrations"
./.venv/bin/alembic upgrade head

echo "==> Frontend: build static assets"
cd "$FRONTEND"
npm ci
# Same-origin API path; Caddy proxies /api/* to the backend.
VITE_API_URL=/api/v1 npm run build

echo "==> Restarting services"
sudo systemctl restart dad-api.service
sudo systemctl restart dad-worker.service
sudo systemctl reload caddy || sudo systemctl restart caddy

echo "==> Deploy complete. Check: systemctl status dad-api dad-worker caddy"

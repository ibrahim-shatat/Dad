#!/usr/bin/env bash
# One-time provisioning for a fresh Ubuntu 24.04 server (Oracle Always Free / any VPS).
# Installs the native stack (no Docker): Python 3.12, Node 20, PostgreSQL, Redis, Caddy.
# Run as root (or with sudo):  sudo bash provision.sh
set -euo pipefail

APP_USER=dad
APP_DIR=/opt/dad
DB_NAME=dad
DB_USER=dad
DB_PASS="${DB_PASS:-dad}"   # override by exporting DB_PASS before running

echo "==> Updating apt and installing base packages"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y software-properties-common curl ca-certificates gnupg rsync git ufw

echo "==> Installing Python 3.12"
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update -y
apt-get install -y python3.12 python3.12-venv python3.12-dev build-essential libpq-dev

echo "==> Installing Node.js 20 LTS"
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

echo "==> Installing PostgreSQL and Redis"
apt-get install -y postgresql postgresql-contrib redis-server
systemctl enable --now postgresql
systemctl enable --now redis-server

echo "==> Installing Caddy (auto-HTTPS reverse proxy)"
apt-get install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' > /etc/apt/sources.list.d/caddy-stable.list
apt-get update -y
apt-get install -y caddy

echo "==> Creating app user and directory"
id -u "$APP_USER" >/dev/null 2>&1 || useradd --system --create-home --shell /bin/bash "$APP_USER"
mkdir -p "$APP_DIR"
chown -R "$APP_USER":"$APP_USER" "$APP_DIR"

echo "==> Creating PostgreSQL role and database (idempotent)"
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1 \
  || sudo -u postgres psql -c "CREATE ROLE $DB_USER LOGIN PASSWORD '$DB_PASS';"
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" | grep -q 1 \
  || sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"

echo "==> Allowing '$APP_USER' to manage its services without a password"
cat > /etc/sudoers.d/dad-deploy <<EOF
$APP_USER ALL=(root) NOPASSWD: /bin/systemctl restart dad-api.service, /bin/systemctl restart dad-worker.service, /bin/systemctl reload caddy, /bin/systemctl restart caddy
EOF
chmod 440 /etc/sudoers.d/dad-deploy

echo "==> Configuring firewall (SSH + HTTP + HTTPS)"
ufw allow OpenSSH || true
ufw allow 80/tcp || true
ufw allow 443/tcp || true
yes | ufw enable || true

echo "==> Provisioning complete."
echo "    Next: upload the code to $APP_DIR, create $APP_DIR/backend/.env,"
echo "    install the systemd units, then run deploy.sh."

# Deploying Dad live (native, no Docker)

This deploys the full stack — API, background worker, PostgreSQL, Redis, and the built
frontend — onto a single Ubuntu 24.04 server, with Caddy handling HTTPS. No Docker, no
GitHub required (code is pushed over SSH).

Recommended free host: **Oracle Cloud "Always Free"** (an always-on VM, free forever).
Any VPS (Hetzner, DigitalOcean, etc.) works identically.

---

## 0. Create the server

**Oracle Cloud Always Free:**
1. Sign up at cloud.oracle.com (a credit card is required for verification; Always-Free
   resources are not charged).
2. Create a Compute **VM instance**:
   - Image: **Canonical Ubuntu 24.04**
   - Shape: **VM.Standard.A1.Flex** (Ampere ARM, Always Free — 1–4 OCPU / 6–24 GB).
     If ARM shows "out of capacity", use **VM.Standard.E2.1.Micro** (AMD, Always Free).
   - Add your SSH public key.
3. Networking: open ingress for **TCP 80 and 443** in the VCN security list
   (Oracle blocks these by default in addition to the OS firewall).
4. Note the public IP.

You need an SSH key. On Windows: `ssh-keygen -t ed25519` (then paste `~/.ssh/id_ed25519.pub`).

**Domain (recommended, for HTTPS):** point an A record at the server's public IP.
Without a domain you can still run on plain HTTP by IP (fine for a first look; OAuth logins
and secure cookies won't fully work until you add a domain).

---

## 1. Provision the server (one time)

```bash
# from your machine
scp deploy/provision.sh ubuntu@SERVER_IP:/tmp/
ssh ubuntu@SERVER_IP
sudo bash /tmp/provision.sh          # installs Python/Node/Postgres/Redis/Caddy, makes db+user
```

## 2. Push the code (no GitHub)

```powershell
# from the project root on Windows
.\deploy\push.ps1 -Server ubuntu@SERVER_IP
```
The first push extracts the repo to `/opt/dad` and runs `deploy.sh` (which will fail at the
"restart services" step until step 3 installs the units — that's expected on the very first run).

## 3. Install services + config (one time)

```bash
ssh ubuntu@SERVER_IP
# systemd units
sudo cp /opt/dad/deploy/dad-api.service    /etc/systemd/system/
sudo cp /opt/dad/deploy/dad-worker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now dad-api dad-worker

# Caddy reverse proxy
sudo cp /opt/dad/deploy/Caddyfile /etc/caddy/Caddyfile
# set your domain for auto-HTTPS (skip to run on plain HTTP by IP):
echo 'SITE_ADDRESS=dad.example.com' | sudo tee -a /etc/default/caddy
sudo systemctl restart caddy
```

## 4. Production secrets

```bash
sudo -u dad cp /opt/dad/deploy/.env.production.example /opt/dad/backend/.env
sudo -u dad nano /opt/dad/backend/.env     # fill in ANTHROPIC_API_KEY, JWT_SECRET, TOKEN_ENCRYPTION_KEY, domain
# generate secrets:
openssl rand -base64 48                                   # JWT_SECRET
python3.12 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # TOKEN_ENCRYPTION_KEY
sudo systemctl restart dad-api dad-worker
```

> ⚠️ Rotate the Anthropic API key that was used during local dev — generate a fresh one at
> console.anthropic.com and use that here.

## 5. Create the first admin user

```bash
cd /opt/dad/backend
sudo -u dad ./.venv/bin/python -m app.scripts.create_admin
```

## 6. Verify

```bash
curl -s http://127.0.0.1:8000/health        # {"status":"ok"}
systemctl status dad-api dad-worker caddy
```
Then open `https://your-domain` (or `http://SERVER_IP`) and log in.

---

## Updating later

Just push again — it rebuilds, migrates, and restarts:
```powershell
.\deploy\push.ps1 -Server ubuntu@SERVER_IP
```

## Logs / troubleshooting

```bash
journalctl -u dad-api -f
journalctl -u dad-worker -f
journalctl -u caddy -f
```

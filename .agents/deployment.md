<!-- reference — read when relevant -->
# Deployment — Hetzner Server

## TL;DR — push to main IS the deploy

`.github/workflows/ci.yml` runs tests on every push, and on green commits to `main` the `deploy` job SSHs to Hetzner, pulls, and restarts `invest-dashboard`. **Do not manually `git pull` + `systemctl restart` after a push.** Verification path after pushing:

```
gh run watch                                                 # or: gh run list --branch main --limit 1
curl -sS -o /dev/null -w '%{http_code}\n' https://invest.rubenayla.xyz/feed
```

SSH only when CI itself fails, or for diagnostics the production endpoint can't show. Never SSH-deploy "to be sure" — it can race the CI deploy and mask broken automation.

## Architecture

- **Hetzner server**: hosts PostgreSQL (source of truth), fetches data (Yahoo + SEC), serves dashboard at `invest.rubenayla.xyz`
- **Mac**: connects to same Postgres via SSH tunnel, runs heavy ML models (GBM, autoresearch, neural nets)
- **No file syncing** — both read/write the same Postgres database

## Database

- **PostgreSQL** on Hetzner: `invest` database, `invest` user
- Server connects directly: `postgresql://invest:invest_2026@localhost:5432/invest`
- Mac connects via SSH tunnel: `postgresql://invest:invest_2026@localhost:5433/invest`
- Config: `~/.invest_db_url` on both machines, or `DB_URL` env var
- SSH tunnel: `ssh -N hetzner-db` (configured in `~/.ssh/config`, forwards 5433→5432)

## Server Details

- Host: `hetzner` (SSH alias) — `91.98.68.236`
- User: `deploy`
- OS: Ubuntu 24.04 LTS
- Specs: 2 vCPU, 4GB RAM
- Path: `/srv/invest` (symlinked from `~/invest`)
- Dashboard: systemd service `invest-dashboard` on port 8050, behind nginx
- SSL: Cloudflare Origin CA wildcard (`*.rubenayla.xyz`)

## Services

- **nginx**: reverse proxy `invest.rubenayla.xyz` → `[::1]:8050`
- **invest-dashboard.service**: runs `dashboard_server.py --no-auto-shutdown` at Nice=19
- **Cron**: nightly data fetch at 22:00 UTC (Mon-Fri), data-only (no ML)

## Workflow

```
1. Hetzner cron fetches data nightly (Yahoo + SEC) → writes to Postgres
2. Mac runs models (with SSH tunnel open):
   ssh -N hetzner-db &
   uv run python scripts/update_all.py --skip-fetch --skip-insider --skip-activist --skip-holdings --skip-edinet
3. Dashboard auto-refreshes from Postgres on each page load
```

## Key Commands

```bash
# Check dashboard status
ssh hetzner "sudo systemctl status invest-dashboard"

# View dashboard logs
ssh hetzner "sudo journalctl -u invest-dashboard -f"

# Restart dashboard
ssh hetzner "sudo systemctl restart invest-dashboard"

# View cron logs
ssh hetzner "tail -50 ~/invest/logs/cron_update.log"

# Manual data update on server
ssh hetzner "cd /srv/invest && nice -n 19 ~/.local/bin/uv run python scripts/update_all.py --skip-gbm --skip-nn --skip-autoresearch --skip-classic --skip-scanner --skip-dashboard"

# Open SSH tunnel for local Postgres access
ssh -N hetzner-db &
```

## Nginx Config

Located at `/etc/nginx/sites-enabled/invest.rubenayla.xyz`. Uses same SSL cert as partle.

## Important Notes

- `Nice=19` on all invest processes — Partle app gets CPU priority
- `--no-auto-shutdown` flag disables the 2h idle timeout for systemd
- Dashboard regenerates HTML from DB on each request (no static files to sync)
- The "Live Server" button uses relative URL `/` (works behind nginx)
- DB_URL is set in the systemd service file and in `~/.invest_db_url`

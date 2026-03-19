# Deployment — Partle Server (Hetzner)

## Architecture Split

- **Partle (Hetzner)**: hosts DB (source of truth), fetches data (Yahoo + SEC), serves dashboard at `invest.rubenayla.xyz`
- **Mac**: pulls DB, runs heavy ML models (GBM, autoresearch, neural nets), pushes predictions back

## Server Details

- Host: `partle` (SSH alias) — `91.98.68.236`
- User: `deploy`
- OS: Ubuntu 24.04 LTS
- Specs: 2 vCPU, 4GB RAM
- Path: `/home/deploy/invest`
- Dashboard: systemd service `invest-dashboard` on port 8050, behind nginx
- SSL: Cloudflare Origin CA wildcard (`*.rubenayla.xyz`)

## Services

- **nginx**: reverse proxy `invest.rubenayla.xyz` → `[::1]:8050`
- **invest-dashboard.service**: runs `dashboard_server.py --no-auto-shutdown` at Nice=19
- **Cron**: nightly data fetch at 22:00 UTC (Mon-Fri), data-only (no ML)

## Sync Workflow

```
1. Partle cron fetches data nightly (Yahoo + SEC)
2. Mac pulls DB:     ./scripts/sync_from_server.sh
3. Mac runs models:  uv run python scripts/update_all.py --skip-fetch --skip-insider --skip-activist --skip-holdings --skip-edinet
4. Mac pushes back:  ./scripts/sync_to_server.sh
```

## Key Commands

```bash
# Check dashboard status
ssh partle "sudo systemctl status invest-dashboard"

# View dashboard logs
ssh partle "sudo journalctl -u invest-dashboard -f"

# Restart dashboard
ssh partle "sudo systemctl restart invest-dashboard"

# View cron logs
ssh partle "tail -50 ~/invest/logs/cron_update.log"

# Manual data update on server
ssh partle "cd ~/invest && nice -n 19 uv run python scripts/update_all.py --skip-gbm --skip-nn --skip-autoresearch --skip-classic --skip-scanner --skip-dashboard"
```

## Nginx Config

Located at `/etc/nginx/sites-enabled/invest.rubenayla.xyz`. Uses same SSL cert as partle.

## Important Notes

- `Nice=19` on all invest processes — Partle game gets CPU priority
- `--no-auto-shutdown` flag disables the 2h idle timeout for systemd
- Dashboard regenerates HTML from DB on each request (no static files to sync)
- The "Live Server" button uses relative URL `/` (works behind nginx)

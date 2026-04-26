# Claude Memory and Instructions

## .agents/ files

**Read at session start** (small, always-relevant):
- `tasks.md` — kanban (TODO / In Progress / Done). Claim before working. Skip if claimed.
- `coding-standards.md` — style + testing
- `data-conventions.md` — ratio storage, yfinance quirks

**Reference** (read when relevant):
- `architecture.md` — system design (DB, pipeline, scoring, Kelly sizer)
- `deployment.md` — Hetzner server, SSH, systemd, nginx, cron
- `solutions.md` — recurring fixes

**Consult selectively** (grep, never read in full):
- `error-log.md` — failure history (grep when debugging)
- `notes.md` — research notes by topic

## Investment Analysis

For ANY stock question (`should I buy X?`, `what about X?`), run `/research TICKER` first. Then:
- Compare model outputs; flag divergence; critique broken models out loud
- **Freshness check**: include `timestamp` in DB queries. If data >7d old, fetch live price; if it diverges >5%, say so before analyzing. If >30d for volatile names, rerun the model
- Markdown header MUST include `**Price:** $X.XX (YYYY-MM-DD)`. Valuation table MUST have `Run Date` column
- Saves to `notes/companies/TICKER.md` and `valuation_results` DB

## The Iron Rule

Before claiming "declining" or "down X%", verify with yfinance 3-5y trend:
```python
yf.Ticker('STOCK').income_stmt.loc['Total Revenue']
```

## File safety

Never modify a file without reading it first. Check `git status` before modifying. Never overwrite ignored files (`TODO.md`, `stuff.md`) without confirmation.

## Always Use uv

All Python via `uv run python script.py` / `uv run pytest`.

## Git Safety

Never `git checkout <file>` (destroys changes). Use `git reset <file>` to unstage.

## Deploy

`.github/workflows/ci.yml` auto-deploys to Hetzner on push to `main` after the test job passes. **Do not** `ssh hetzner ... git pull && systemctl restart` manually unless CI is broken AND you've explained the bypass to the user. Check `gh run list --workflow=ci.yml --limit=3` before any manual deploy. Never deploy past a red CI without justification.

## Database

PostgreSQL on Hetzner is **source of truth**. If schema mismatches script, update the script.
- Mac access: `localhost:5433` (open tunnel via `ssh -fN -L 5433:localhost:5432 hetzner-db`)
- `scripts/update_all.py` opens the tunnel automatically
- Models run on the Mac; the website's "update" button only fetches data
- Architecture / tables / pipeline: see `.agents/architecture.md`

## External Data

- `scripts/polymarket_lookup.py "<keyword>"` — prediction-market probabilities
- `scripts/macro_context.py` — single-score buy-environment snapshot

## Root scratch files

`stuff.md`, `stuff/`, `TODO.md` are user notes. Don't delete or reorganize.

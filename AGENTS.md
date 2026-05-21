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
- `.agents/error-log.md` — failure history (grep when debugging)
- `notes.md` — research notes by topic

**Repo root files (NOT in `.agents/`)**:
- `history.md` — accumulating record of cross-cutting decisions, investigations, surprising findings (dated, oldest first). Lives at the **repo root**, not in `.agents/`. After non-trivial work, **append here** so the reasoning survives context expiration. Also the overflow target for AGENTS.md.

## Repo Scope vs Personal Data

This repo (`~/repos/invest/`) is **analysis infrastructure only** — models, scanner, dashboard, company research notes (`notes/companies/*.md`). It is public-safe; no personal portfolio data lives here.

Personal financial data lives in **`~/vault/finance/`** (private Obsidian vault, git-tracked separately):
- `notes/portfolio/portfolio.md` — current holdings across IBKR / Revolut / Binance
- `notes/portfolio/watchlist.md` — open watch ideas
- `notes/transactions/` — per-trade records (one file per trade: `YYYY-MM-DD_action_TICKER.md`)
- `history.md` — **append-only log of cross-cutting decisions, user preferences (e.g. MSFT dispreference), FX rates, valuation frameworks, session summaries.** Grep this when picking up a session — it's where context that spans multiple trades lives.
- `*.beancount` ledgers (entry: `main.beancount`)

When answering "should I sell X" / "what's in my portfolio" / "size a position": **read from `~/vault/finance/`** — start with `portfolio.md` for current state, then grep `history.md` for recent context (decisions, preferences, FX rates, deferred trades). Never expect those files in this repo. Company analysis under `~/repos/invest/notes/companies/TICKER.md` is thesis-only — no position/PnL data.

**When the user executes a trade**: write a transaction note under `~/vault/finance/notes/transactions/YYYY-MM-DD_action_TICKER.md` (thesis + scenario table + sizing logic), update `portfolio.md` with the new position, and append a short summary to `~/vault/finance/history.md`. Don't skip these — they're the institutional memory the next session needs.

## Investment Analysis

For ANY stock question (`should I buy X?`, `what about X?`), run `/research TICKER` first. Then:
- Compare model outputs; flag divergence; critique broken models out loud
- **Freshness check**: include `timestamp` in DB queries. If data >7d old, fetch live price; if it diverges >5%, say so before analyzing. If >30d for volatile names, rerun the model
- Markdown header MUST include `**Price:** $X.XX (YYYY-MM-DD)`. Valuation table MUST have `Run Date` column
- Saves to `notes/companies/TICKER.md` (or `TICKER/thesis.md` for promoted folder layout — see `notes/companies/README.md`) and `valuation_results` DB
- **After any deep analysis, sync `notes/portfolio/watchlist.md`**: if the ticker has a line there, update its verdict/conviction/quality/EV/entry to match the note (STEP 10 of `/research`). The watchlist must never contradict the company note — a BUY in the note that still reads WATCH on the watchlist is a bug.

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
- **Live market data**: use `yfinance` (already a project dep) for prices/fundamentals/history, plus `WebSearch`/`WebFetch` for news and earnings commentary. Evaluated `financial-datasets` MCP and dropped it — cheapest plan is $200/month, no free tier, not worth it for personal research.

## Scheduled Routines (`/schedule`)

For one-shot earnings-day or catalyst-day analysis, prefer scheduling Claude Code remote routines over manual reminders.

- **Default fire time: 04:00–05:00 Europe/Madrid** (= 02:00–03:00 UTC). Off-peak Claude usage caps + user is asleep, so the analysis is ready by morning. Use this unless a hard external constraint forces otherwise.
- **Tokyo earnings exception**: Japan companies (e.g. 8001.T, 8002.T) typically publish at Tokyo close ~15:00 JST = 08:00 Madrid. Schedule **the next morning at 04:00–05:00 Madrid** to ensure the press release is fully out and analyst commentary has caught up.
- **Output convention**: routines write a markdown file to `notes/journal/transactions/YYYY-MM-DD_<ticker>_<event>_review.md`. Don't open PRs or commit — the user reviews and decides.
- **Notification**: results land in the **Routines** tab of the Claude desktop app (and at `claude.ai/code/routines`). No email/push by default.
- **Manage**: list/update/run via the `/schedule` skill, or directly at `claude.ai/code/routines`. Deletion is web-only.

## Root scratch files

`stuff.md`, `stuff/`, `TODO.md` are user notes. Don't delete or reorganize.

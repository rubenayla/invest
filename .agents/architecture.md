<!-- reference — read when relevant -->
# Architecture — Key Design Decisions

## Data Systems

Single PostgreSQL database (`invest`) on Hetzner, accessed via:
- Server (direct): `localhost:5432`
- Mac (SSH tunnel): `localhost:5433` via `ssh -N hetzner-db`

Tables:
- `assets`, `fundamental_history`, `price_history` — time-series for ML models
- `current_stock_data` — single snapshot per stock for valuations/dashboard
- `valuation_results` — all model outputs (DCF, GBM, RIM, etc.)
- `insider_transactions`, `activist_stakes`, `fund_holdings` — SEC data
- Access: `StockDataReader` (main entry point), `*_db.py` modules for SEC signals
- Connection: `from invest.data.db import get_connection`

## Pipeline: `scripts/update_all.py`

```
Phase 1: Data fetch (independent)
  1a. data_fetcher.py (yfinance → stock_data.db)
  1b. fetch_insider_data.py (EDGAR Form 4)
  1c. fetch_activist_data.py (EDGAR 13D/13G)
  1d. fetch_holdings_data.py (EDGAR 13F)
  1e. fetch_edinet_data.py (Japan, if API key set)

Phase 2: Valuations (independent, need Phase 1)
  - run_gbm_predictions.py (6 variants)
  - run_classic_valuations.py (DCF, RIM, ratios)

Phase 3: Consumers (independent, need Phase 2)
  - dashboard.py → dashboard/index.html
  - run_opportunity_scan.py → scanner scores
```

## Position Sizing

There is no automated position sizer. A Kelly-Criterion sizer (`src/invest/sizing/`, `scripts/run_position_sizer.py`, `/size` skill) was **removed 2026-07-07** — it was mis-specified: it fed a ratio-of-moves `b` into the binary-bet Kelly formula and point-estimate model edges into Kelly with no uncertainty haircut, producing raw single-name fractions of 66–84% for nearly every stock (a book of them summing to >400%). The 15% cap silently clipped every absurd value to ~15%, so the cap did all the sizing and the tool couldn't rank. See `.agents/error-log.md` (2026-07-07) for the full diagnosis.

**Size positions by conviction under fixed rules, not a formula:** 15% single-name cap, 35% sector cap; a single-name compounder sits below the cap (~10%); overlay event risk (e.g. earnings) manually. The trustworthy inputs are the raw model predictions in `valuation_results` (AutoResearch first, then GBM) and their dispersion — read those directly.

## Scoring Engine

`ScoringEngine.score_stock()` → 5 components weighted into overall score:
- Quality (30%): ROE, margins, accrual quality
- Value (25%): P/E, P/B, model consensus upside
- Growth (20%): revenue/earnings CAGR, price momentum
- Risk (15%): leverage, sector stability
- Catalyst (10%): insider buying, activist stakes, smart money, 52w position

## SEC EDGAR Pattern

All fetchers share: `_sec_get()` for HTTP, `TokenBucketRateLimiter` (10 req/s), `ThreadPoolExecutor` for concurrency, per-worker DB connections, `*_fetch_log` tables for incremental updates.

## Deployment

- **Hetzner server**: hosts PostgreSQL (source of truth), fetches data, serves dashboard at `invest.rubenayla.xyz`
- **Mac**: connects to same Postgres via SSH tunnel, runs heavy ML models (GBM, autoresearch)
- No file syncing — both machines read/write the same database
- See `.agents/deployment.md` for full details

## Key Conventions

- Database is source of truth (not scripts)
- Ratios stored as ratios (0.93), not percentages (93)
- All Python via `uv run`
- Single quotes, type hints, guard clauses

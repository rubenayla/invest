# Architecture — Key Design Decisions

## Data Systems

Two SQLite databases, two access patterns:

1. **`data/stock_data.db`** — main stock data
   - `assets`, `fundamental_history`, `price_history` — time-series for ML models
   - `current_stock_data` — single snapshot per stock for valuations/dashboard
   - `valuation_results` — all model outputs (DCF, GBM, RIM, etc.)
   - Access: `StockDataReader` (single entry point for all stock data)

2. **`data/sec_edgar/*.db`** — SEC filing data (separate DBs per domain)
   - `insider_transactions.db` — Form 4 insider trades
   - `activist_stakes.db` — 13D/13G (5%+ ownership)
   - `fund_holdings.db` — 13F institutional holdings + `cusip_to_ticker` map
   - Access: each has a `*_db.py` module with `compute_*_signal()` functions

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

## Scoring Engine

`ScoringEngine.score_stock()` → 5 components weighted into overall score:
- Quality (30%): ROE, margins, accrual quality
- Value (25%): P/E, P/B, model consensus upside
- Growth (20%): revenue/earnings CAGR, price momentum
- Risk (15%): leverage, sector stability
- Catalyst (10%): insider buying, activist stakes, smart money, 52w position

## SEC EDGAR Pattern

All fetchers share: `_sec_get()` for HTTP, `TokenBucketRateLimiter` (10 req/s), `ThreadPoolExecutor` for concurrency, per-worker DB connections, `*_fetch_log` tables for incremental updates.

## Key Conventions

- Database is source of truth (not scripts)
- Ratios stored as ratios (0.93), not percentages (93)
- All Python via `uv run`
- Single quotes, type hints, guard clauses

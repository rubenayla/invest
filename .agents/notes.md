# Notes

## International Stock Fundamentals — Data Provider Research (2026-03-16)

### Problem
~80 international tickers (.DE, .PA, .AS, .MI, .L, .T, .BR, .MC) had **empty fundamentals** in our DB. The autoresearch model could only score 705/785 tickers.

### Root Cause (Found 2026-03-17)
**yfinance DOES return full data for international stocks** — `stock.info` has 166-170 keys with PE, P/B, market cap, revenue, margins, EPS, etc. for all tested EU/Japan tickers. The bug was in `scripts/populate_fundamental_history.py`:
1. Many international tickers were never registered in the `assets` table
2. `save_snapshots()` only inserted 15 of ~50 columns in `fundamental_history`
3. The script never extracted `stock.info` fields (ratios, market data) — only derived metrics from quarterly statements

### Fix Applied
Rewrote `populate_fundamental_history.py`:
- `_enrich_latest_snapshot()` pulls all ~40 fields from `stock.info` into the latest snapshot
- `save_snapshots()` inserts all columns matching `fundamental_history` schema
- Added `--refresh` flag to re-process tickers with sparse data
- Added `--tickers` flag for targeted runs
- Result: **704 tickers now have enriched data** (up from ~6), including **114 international tickers**

### Providers Tested (all unnecessary now)

| Provider | Int'l Fundamentals? | Free? | Cost | Notes |
|---|---|---|---|---|
| **yfinance** | **YES — works fine** | Yes | Free | Bug was in our pipeline, not yfinance |
| **Financial Datasets** (financialdatasets.ai) | **US-only** | No | $200/mo | 404 on all .DE/.PA/.L/.T tickers |
| **Alpha Vantage** | **US-only** (fundamentals) | 25 calls/day free | $50-250/mo | Key: `PXX24CEMNKDBCV6W` (ruben.jimenezmejias@gmail.com). Returns `{}` for international fundamentals |
| **EODHD** | Yes (70+ exchanges) | 20 calls/day (demo only) | 60 EUR/mo | Not needed |
| **FMP** | Yes (60+ exchanges) | US-only on free tier | $29-99/mo | Not needed |
| **Finnhub** | Yes (60+ exchanges) | US-only on free tier | $12-100/mo | Not needed |

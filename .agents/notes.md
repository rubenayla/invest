<!-- consult selectively — grep, never read in full -->
# Notes

## Politician Trade Signal — House PTRs (2026-04-25)

Pulls US House periodic transaction reports (no Senate) as a watchlist trigger.
Senate eFD requires session/JS handling — deferred.

- **Source**: `https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}FD.zip`
  (XML index of `FilingType=P` records) → per-DocID PDF at
  `https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{year}/{doc_id}.pdf`
- **Parser**: regex line-windowing in `politician_fetcher.py`. Treasury CUSIPs
  filtered out by ticker regex (`[A-Z]{1,5}(?:\.[A-Z]{1,2})?`).
- **Schema**: `politician_trades` + `politician_trades_fetch_log`.
  `compute_politician_signal()` weights by `HIGH_SIGNAL_POLITICIANS`
  (Pelosi 3.0, Tuberville 2.0, etc.) × log-ish amount band.
- **Lag**: PTRs allowed up to 45 days post-trade. NOT a timing edge — surface
  candidates for further research only.
- **Pipeline**: `scripts/fetch_politician_data.py` (Phase 1f of `update_all.py`,
  `--skip-politician` to bypass; auto-skipped under `--lite-fetch`).
- **Surfaces**: dashboard signals column tag + `/feed` "Congress signal" card
  when weighted_score ≥ 1.5 with high-signal politician.

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

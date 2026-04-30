<!-- read in full — kept under 150 lines -->
# Tasks

## TODO

- **Polymarket Trump-policy market poller** (added 2026-04-30): Extend `scripts/polymarket_lookup.py` to track policy markets specifically — tariff timing/levels by country, executive-order probabilities, Fed-action contracts, specific-bill passage. Build a `trump_policy_markets` table (market_id, question, current_yes_price, volume, close_date, last_updated). Push to `/feed` when implied probability moves >10pp in 24h. Acceptance: ≥10 active Trump-policy markets tracked; alert fires on any large probability shift. Reference: `.agents/notes.md` 2026-04-30.

- **Backtest Vance + Tuberville PTR signal** (added 2026-04-30): Query `politician_trades` table for all Vance (pre-VP) and Tuberville disclosed transactions in last 24 months. For each trade, compute forward returns at 30d / 90d / 180d / 365d vs SPY. Compare hit rate + avg alpha to other politicians in `HIGH_SIGNAL_POLITICIANS`. If Vance / Tuberville show statistically meaningful alpha (>3% annualized vs control group), bump their weights in `politician_fetcher.py`. If not, leave as-is and document the null. Acceptance: written backtest results in `notes/research/politician_backtest_2026.md` with conclusion + weight changes (or no-change justification).

- **Re-evaluate SQM runner after May Q1 2026 earnings**: HOLD if EPS run-rate ≥$8 annualized AND lithium >$15/kg sustained. EXIT remaining 31.54 if Q1 miss OR lithium <$15/kg for 2 months. TRIM MORE if stock hits $130 pre-earnings.

- **8001.T (Itochu) — wait for May 1, 2026 FY26 earnings, then decide**: WATCH lean BUY at ¥1,926 (2026-04-27). EV +10%, conviction MEDIUM. Action triggers:
  - **If May 1 beats** (NI ≥¥920B and/or raised buyback): BUY ~5% portfolio (~$2,300), entry up to ¥2,150. Coherent diversifier from 8002.T (consumer/FamilyMart vs commodity tilt).
  - **If May 1 misses**: re-evaluate; better entry likely ¥1,700–1,800.
  - **Optional starter now (~1/3 size)**: ~$750 at ¥1,926 to participate without full binary risk.
  - Thesis-break: sustained close <¥1,700 OR Berkshire announces stake reduction.
  - Reference: `notes/companies/8001.T.md`

## In Progress

## Done

- [2026-04-30] **Split politician signal by transaction direction**: `HIGH_SIGNAL_POLITICIANS` in `src/invest/data/politician_db.py` now keys on `(name, transaction_type)` tuples. Tuberville buys weighted 0.3 (faded, −9% alpha @180d), Tuberville sells 3.5 (amplified, +14% alpha @365d); Pelosi/Crenshaw/Gottheimer kept uniform across P/S pending individual backtests. Added `_politician_weight()` helper + `DEFAULT_POLITICIAN_WEIGHT`. New `tests/test_politician_signal.py` (12 tests, all pass) covers Tuberville split, Pelosi uniformity, unknown-politician default, and DB-stubbed `compute_politician_signal` integration.

- [2026-04-30] **Truth Social scraper → /feed Trump-signal card**: New `src/invest/data/truth_social_{db,fetcher}.py` modules + `scripts/fetch_truth_social.py` (one-shot or `--watch` 60s loop). Schema `truth_social_posts` (post_id PK, posted_at, text, extracted_tickers/sectors/countries, sentiment, fetched_at) with GIN indexes; idempotent ON CONFLICT upserts. NER via cashtag regex + universe-derived alias dict + sector/country keyword maps (no spaCy). Wired into `update_all.py` (`--skip-truthsocial`). Trump cards rendered on `/feed` above ticker threads (gold accent, timestamp, truncated text, ticker/sector/country tags). 32 unit tests (`tests/test_truth_social_ner.py`) all pass; live fetch verified — required browser User-Agent for the public API. 20 real posts ingested cleanly.

- [2026-04-17] **SQM trim executed (Revolut)** — Filled 32 shares @ $93.00 (limit, free trade of month). Net proceeds $2,975.93 (~€2,524.73 at EUR/USD 1.1787). Estimated realized gain ~€1,245 (exact FIFO pending year-end Revolut P&L PDF). Journal: `notes/journal/transactions/2026-04-17_trim_sqm.md`. Portfolio.md and `paperwork/taxes/2026/summary.md` updated. Runner: 31.54 shares.
- [2026-03-22] **Research Iran/oil macro thesis**: Written up in `notes/theses/iran-oil-macro.md`. Covers Hormuz chokepoint, historical precedents, price scenarios, stagflation risk, sector winners/losers, and portfolio positioning.

- [2026-03-22] **Doomscroll insights feed**: New `/feed` route with prioritized scrollable cards (BUY > insider signals > model consensus > WATCH > PASS). Nav link added to main dashboard.
- [2026-03-22] **Merge CI workflows**: Consolidated test.yml + deploy.yml into single ci.yml. Tagged slow tests with `@pytest.mark.slow`.

## Reminder
When war causes stock fall, buy FSLR and NOW.


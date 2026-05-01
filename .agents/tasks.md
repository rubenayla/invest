<!-- read in full — kept under 150 lines -->
# Tasks

## TODO

- **Backtest insider / activist / 13F signals to upgrade them past the gate** (added 2026-05-01): Strict-gate filter is now live (drops everything ungated), so Insider / Congress / activist / 13F cards have all vanished except Tuberville sells. Run a forward-return backtest per signal source vs SPY at 30/90/180/365d, populate entries in `src/invest/signals/gates.py` either as `passes=True` (with caveats in `notes/research/signal_inventory.md`) or `passes=False` so the drop is documented. Per-source priority: insider (highest, most volume), activist 13D/G, smart_money 13F. Reference: `notes/research/signal_inventory.md` UNGATED rows.

- **Re-evaluate SQM runner after May Q1 2026 earnings**: HOLD if EPS run-rate ≥$8 annualized AND lithium >$15/kg sustained. EXIT remaining 31.54 if Q1 miss OR lithium <$15/kg for 2 months. TRIM MORE if stock hits $130 pre-earnings.

- **8001.T (Itochu) — wait for May 1, 2026 FY26 earnings, then decide**: WATCH lean BUY at ¥1,926 (2026-04-27). EV +10%, conviction MEDIUM. Action triggers:
  - **If May 1 beats** (NI ≥¥920B and/or raised buyback): BUY ~5% portfolio (~$2,300), entry up to ¥2,150. Coherent diversifier from 8002.T (consumer/FamilyMart vs commodity tilt).
  - **If May 1 misses**: re-evaluate; better entry likely ¥1,700–1,800.
  - **Optional starter now (~1/3 size)**: ~$750 at ¥1,926 to participate without full binary risk.
  - Thesis-break: sustained close <¥1,700 OR Berkshire announces stake reduction.
  - Reference: `notes/companies/8001.T.md`

## In Progress

## Done

- [2026-05-01] **Signal-gate layer for /feed (curated alpha + inline annotation)**: New `src/invest/signals/gates.py` with `GateResult` dataclass + `SIGNAL_GATES` registry keyed on `(source, name, kind)` tuples + `evaluate()` lookup + `apply_signal_gates(posts)` boundary filter. `_generate_feed_posts()` in `html_generator.py` restructured: politician posts now emit per (politician, direction) pair carrying `signal_source/signal_name/signal_kind`; insider posts also carry signal metadata. Boundary filter runs before the top-10 cap and drops any signal post without a curated `passes=True` entry. `_render_thread_post()` renders inline alpha annotation `+14.2% α · n=216 (eff 20) · 365d · trade clustering reduces effective n` under the body when `post['gate']` is set, using muted-text inline style (no new CSS class). Initial registry has only Tuberville sells passing; Tuberville buys explicitly fail; everything else (other politicians, insider, activist, 13F) drops. New `tests/test_signal_gates.py` (13 tests). New `notes/research/signal_inventory.md` ledger. **Side-effect (intentional):** the feed will get sparser — every Insider/Congress card without a Tuberville-sell upgrade vanishes until per-source backtests land. Plan file: `~/.claude/plans/do-a-proper-plan-jaunty-pelican.md`.

- [2026-04-30] **Polymarket Trump-policy market poller**: `scripts/fetch_polymarket_policy.py` polls gamma-api, classifies markets into 10 policy categories (tariffs, fed_actions, exec_orders, cabinet, china, energy_oil, crypto, immigration, foreign_policy, legislation), upserts into `trump_policy_markets` + `trump_policy_price_history`, emits >10pp/24h moves into `policy_alerts`. Phase added to `update_all.py` with `--skip-polymarket-policy`. Feed gets a "Trump policy markets" section above ticker threads. 30 unit tests on filter; 43 live markets ingested against Hetzner DB.

- [2026-04-30] **Backtest Vance + Tuberville PTR signal**: Full report at `notes/research/politician_backtest_2026.md`. Tuberville aggregate +5.9% annualised alpha vs House control at 365d (n=334, p<0.001) — but signal is asymmetric: sells +14% alpha @365d (n=216, hit 75.5%, p<0.001), buys −9% @180d (n=118, p=0.003). Vance untestable (n=1, only 1 public-stock trade as Senator). Acted on the asymmetric finding via the split-by-direction follow-up rather than a flat weight bump. Caveats: trade-clustering (effective n ~10-20, not 356), bull-market conditioning, joint-account ambiguity, CLF missing from price_history, Senate eFD scraped via third-party (capitoltrades).

- [2026-04-30] **Split politician signal by transaction direction**: `HIGH_SIGNAL_POLITICIANS` in `src/invest/data/politician_db.py` now keys on `(name, transaction_type)` tuples. Tuberville buys weighted 0.3 (faded, −9% alpha @180d), Tuberville sells 3.5 (amplified, +14% alpha @365d); Pelosi/Crenshaw/Gottheimer kept uniform across P/S pending individual backtests. Added `_politician_weight()` helper + `DEFAULT_POLITICIAN_WEIGHT`. New `tests/test_politician_signal.py` (12 tests, all pass) covers Tuberville split, Pelosi uniformity, unknown-politician default, and DB-stubbed `compute_politician_signal` integration.

- [2026-04-30] **Truth Social scraper → /feed Trump-signal card**: New `src/invest/data/truth_social_{db,fetcher}.py` modules + `scripts/fetch_truth_social.py` (one-shot or `--watch` 60s loop). Schema `truth_social_posts` (post_id PK, posted_at, text, extracted_tickers/sectors/countries, sentiment, fetched_at) with GIN indexes; idempotent ON CONFLICT upserts. NER via cashtag regex + universe-derived alias dict + sector/country keyword maps (no spaCy). Wired into `update_all.py` (`--skip-truthsocial`). Trump cards rendered on `/feed` above ticker threads (gold accent, timestamp, truncated text, ticker/sector/country tags). 32 unit tests (`tests/test_truth_social_ner.py`) all pass; live fetch verified — required browser User-Agent for the public API. 20 real posts ingested cleanly.
- [2026-04-17] **SQM trim executed (Revolut)** — Filled 32 shares @ $93.00 (limit, free trade of month). Net proceeds $2,975.93 (~€2,524.73 at EUR/USD 1.1787). Estimated realized gain ~€1,245 (exact FIFO pending year-end Revolut P&L PDF). Journal: `notes/journal/transactions/2026-04-17_trim_sqm.md`. Portfolio.md and `paperwork/taxes/2026/summary.md` updated. Runner: 31.54 shares.
- [2026-03-22] **Research Iran/oil macro thesis**: Written up in `notes/theses/iran-oil-macro.md`. Covers Hormuz chokepoint, historical precedents, price scenarios, stagflation risk, sector winners/losers, and portfolio positioning.

- [2026-03-22] **Doomscroll insights feed**: New `/feed` route with prioritized scrollable cards (BUY > insider signals > model consensus > WATCH > PASS). Nav link added to main dashboard.
- [2026-03-22] **Merge CI workflows**: Consolidated test.yml + deploy.yml into single ci.yml. Tagged slow tests with `@pytest.mark.slow`.

## Reminder
When war causes stock fall, buy FSLR and NOW.


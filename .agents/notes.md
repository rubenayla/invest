<!-- consult selectively — grep, never read in full -->
# Notes

## Trump capital-flows basket — late, not underpriced (2026-04-30)

Triggered by StonkChris tweet (https://x.com/stonkchris/status/2049646373172101452) framing Trump's brag about US gov INTC stake +$30B as a sector-rotation tell. Refreshed INTC and built fresh notes for CCJ / UEC / MP. **Theme is real, trade is late** — none clear EV >15% at current prices.

| Ticker | Price | EV | Verdict |
|---|---|---|---|
| INTC | $94.75 | -5.6% | TRIM/PASS — past bull-case target, $41B gov stake = exit overhang |
| CCJ | $116.45 | +3% | WATCH — contract book already mark-to-market, "rollup" tailwind largely realized |
| UEC | $14.02 | +7.5% (dil-adj) | WATCH small spec — paying $5.9B above tangible book for permits + DOE relationship |
| MP | $62.50 | +5-10% | WATCH — DoD $110 NdPr floor already near-the-money; real swing is dysprosium + 10X magnet ramp |

**Key meta-finding:** the "follow Trump priorities" basket (semis reshoring, nuclear/AI power, defense, rare earths, crypto infra) has been the consensus trade for ~18 months. By the time it's tweetable as "anticipate where capital is going next" it's already in every PowerPoint. No information edge in repeating it.

**Genuinely less-crowded variants worth screening if user revisits:**
- Uranium fuel-cycle midstream (LEU/Centrus, BWXT, conversion/enrichment names) — narrower than CCJ/UEC, same policy tailwind.
- Heavy rare-earth separation specifically (dysprosium/terbium) — MP's 10X facility + DoD $150M loan is the real story; pure plays are scarcer.

**Caveat on these notes:** local Postgres was down + Hetzner SSH was timing out, so the four notes use approximated valuation ranges and web-sourced price/fundamentals — NOT live model outputs. INTC specifically still has stale March GBM/DCF numbers in `notes/companies/INTC.md`. Re-run `scripts/run_all_predictions.py` against {INTC, CCJ, UEC, MP} once DB is back to validate.

## Uranium fuel-cycle midstream screen (2026-04-30)

Follow-on to the Trump capital-flows basket review. Screened the "less-crowded variant" — enrichment + conversion + HALEU pure-plays — to see if the thesis works once you go past CCJ/UEC.

| Ticker | Price | EV | Verdict |
|---|---|---|---|
| LEU | $194.73 | +0.2% | PASS/WATCH — round-tripped $66→$464→$195, 17% dilution Nov 25, 2026 rev flat YoY, no cascade revenue until 2029 |
| BWXT | $208.52 | +0.75% | WATCH but DO NOT INITIATE before Q1 print May 4 — margin compression is the binary |
| SLX.AX | A$4.49 | +44.5% gross | SPEC BUY small — only after losing DOE $900M HALEU expansion to Centrus + General Matter (Jan 26); Cameco 75% option caps upside |
| ASPI | $5.07 | +33% | SPEC STARTER 0.5-1% — QLE spin S-1 filed Nov 25, targeting 1H 26 IPO, only meaningful catalyst |

**Meta-findings:**
- The "midstream is less crowded than the miners" framing is **half right**. Established midstream (LEU, BWXT) is priced in just like CCJ/UEC. The genuine asymmetry is in the speculative binary names (SLX, ASPI) where the catalysts are concrete and the prices reflect recent disappointments rather than future hopes.
- **DOE's Jan-2026 HALEU expansion contract decision is the most actionable surprise:** Centrus + Peter Thiel-backed General Matter won; GLE/Silex was passed over. This validates LEU's incumbency *and* explains the SLX entry point. The under-radar implication is **General Matter** (private) — if/when it goes public, it's the cleanest pure-play domestic HALEU build-out and worth tracking.
- Q1 earnings cluster: BWXT May 4, LEU May 5 — both could re-price the basket sharply within 5 trading days. Don't initiate full positions before; trim/hedge if held.

**What's NOT yet covered in this screen** (worth adding if user revisits):
- Cameco Fuel Services (UF6 conversion) — embedded in CCJ, no pure-play public alt.
- Lightbridge (LTBR) — metallic fuel R&D, sub-$200M cap, pre-revenue. Probably too speculative even for the basket but worth a quick screen.
- Nano Nuclear Energy (NNE) — microreactor + fuel hybrid, sub-$1B, dilutive history.
- Yellow Cake (YCA.L) — physical U3O8 holder, NAV-discount play; pure beta to spot, not midstream.

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

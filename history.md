<!-- consult selectively — grep, never read in full -->
# History

Append-only log of investigations, decisions, and surprising findings.
Dated entries in chronological order (oldest first). Topical reference
lives under named sub-headers near the bottom. Grep this file; do not
read in full.

---

## 2026-05-08 — Politician-PTR signal: cron + dependency fix

Triggered by a "copy Pelosi" tweet. Audited what already existed for
politician trade signals and found three gaps:

1. **`pypdf` was an undeclared dependency** of `politician_fetcher.py`.
   `fetch_politician_data.py` only ran on machines where it happened
   to be installed (local dev). Added `pypdf>=6.0.0` to `pyproject.toml`.
2. **Hetzner had no scheduled politician fetch.** Existing 22:00 UTC
   weekday cron under `deploy` user runs `update_all.py` (Yahoo + SEC
   data only). Added a daily entry: `30 2 * * * cd /srv/invest && nice
   -n 19 ... fetch_politician_data.py 2>&1 | tee -a logs/cron_fetch_politician.log`.
   Logged in `.agents/deployment.md`.
3. **Default fetch is current-year-only.** Pelosi had only 26 trades
   in DB (all 2024-12+). Backfilled 2021–2024 manually on Hetzner
   (`logs/backfill_politician_2021_2024.log`, ~10 min, 3,009 new rows).
   The cron still defaults to current year, so the backfill is one-time.

## 2026-05-09 — Pelosi backtest: PASS buys, FAIL sells

Direction-split Tuberville-style backtest (`scripts/backtest_politician.py`,
new — reusable, parameterized by `--name`). Methodology mirrors
`notes/research/politician_backtest_2026.md`. Added a cluster-aggregated
descriptive pass for low-n politicians whose trades come in same-day
batches (Pelosi clusters 32 buys into 18 same-day decisions; t-test
on raw n is overconfident).

**Result:** Pelosi BUYS at 365d: +13.7% annualised α, p=0.004,
hit rate 62.5% (cluster level 75% — 9/12 clusters). Survives
leave-2-out. Gate-PASS, registered in `gates.py` with provisional
flag and bull-market caveat. Pelosi SELLS: -18.9% α, p=0.023, cluster
hit rate 12% (1/8) — significantly bad. Gate-FAIL.

**Surprising finding:** direction asymmetry mirrors Tuberville in
reverse. Tuberville sells work + buys fade; Pelosi buys work + sells
fade. The "follow Pelosi" meme is approximately right for buys,
approximately wrong for sells. Documented in
`notes/research/pelosi_backtest_2026.md`.

**Re-evaluate:** 2027-05-10 OR earlier if SPY drawdown >15% sustained
6mo+ (out-of-sample regime test).

## 2026-05-10 — Gottheimer + Crenshaw backtests: both FAIL

Same script, different politicians. Gottheimer (n=105 P / 166 S, 90 /
115 clusters) shows no significant α at any horizon × direction;
best p across all combos is 0.148 (sells 90d). 365d alphas track
control closely. n is large enough to confidently reject the edge
claim, not just fail to detect one. Gate-FAIL both directions.

Crenshaw is filed in DB as **"Crenshaw, Daniel"** not "Crenshaw, Dan"
(the `signal_inventory.md` UNGATED row had the wrong name). n=6
total — same fate as Vance. Gate-FAIL with "n too small" caveat.

`gates.py` now has 4 PASS / FAIL pairs: Tuberville, Pelosi, Gottheimer,
Crenshaw. The one PASS that surfaces on `/feed` is Pelosi BUYS (★★)
plus the existing Tuberville SELLS (★★★).

## 2026-05-10 — CI speed: easy wins applied; bigger wins deferred

Baseline: ~46s per run on `main` (3s checkout/python · 3s setup-uv · 8s
`uv sync --all-groups` · 21s pytest+ruff · 9s SSH deploy). Sequential
test → deploy.

**Applied (target ~36s):**
- `astral-sh/setup-uv@v5` with `enable-cache: true` and
  `cache-dependency-glob: 'uv.lock'` (saves ~5–7s on install).
- `uv sync --group dev` instead of `--all-groups` (skips `docs`
  group — mkdocs etc. not needed for tests).
- Workflow-level `concurrency: cancel-in-progress: true` so back-to-
  back pushes don't queue.

**Tested and rejected:**
- **pytest-xdist `-n auto`**: tried locally (2026-05-10). Serial pure-
  pytest is 7.65s; `-n auto` is 8.66s — parallel is *slower*. The 21s
  number I'd quoted earlier was the whole "Test (fast)" CI step,
  which includes lint + step orchestration, not pure pytest. At <10s
  suite size, xdist's fork + re-import + coordination overhead
  dominates. Don't add it. Re-evaluate if the suite grows past ~30s.

**Deferred — consider if push frequency / latency becomes a pain
point:**
- **Parallelise deploy with test, gate the restart on test pass**:
  saves the 9s deploy block from the critical path. Needs a two-step
  deploy (push code now, restart only after green). ~7-8s win.
- **Self-hosted runner on Hetzner**: eliminates SSH-deploy entirely
  (deploy = local restart) and warms a permanent uv cache on the
  host. ~10-15s win. Adds a runner to maintain.
- **Split lint into a parallel job**: cosmetic; lint is sub-second.

Realistic target without ops complexity: ~30s (do xdist on top of
today's changes). Below that needs the parallel-deploy or self-hosted
runner path.

## 2026-05-10 — Code rot finding: tests/test_lite_fetch.py

While testing xdist locally I noticed all 12 tests in
`tests/test_lite_fetch.py` fail with `AttributeError: 'StockDataCache'
object has no attribute 'db_path'` and `NameError: 'sqlite3' not
defined`. The tests target the pre-PostgreSQL `StockDataCache` API
that was migrated away in commit `0880086` ("fix: update tests for
PostgreSQL migration"). They're silently green on CI because
`tests/conftest.py:62` skips `requires_data`-marked tests when the
DB isn't reachable. Locally (with the SSH tunnel open) the skip
doesn't trigger, so the tests run and the rot surfaces.

Out of scope for the xdist work. Future fix options:
1. Migrate the tests to whatever cache backend the lite-fetch path
   actually uses today (most authentic).
2. Mark the file `pytest.skip(..., allow_module_level=True)` with a
   pointer to whoever needs to migrate it.
3. Delete it if the lite-fetch behavior is now covered elsewhere.

Don't ad-hoc patch one symptom at a time (I tried adding `import
sqlite3` — got past the NameError, hit the missing-`db_path`
AttributeError next).

## 2026-05-10 — Dashboard: confidence tier + annualised α + freshness

`/feed` cards now annotate gated trade signals with three derived
quantities (all from existing `GateResult` fields, no new data):
- `confidence_tier(gate)` → ★★★ / ★★ / ★ from p × n_effective
- `annualised_alpha(gate)` → simple-return /yr (was raw log α)
- `freshness(gate)` → fresh / aging / stale, colour-coded

Helpers in `src/invest/signals/gates.py`; renderer in
`html_generator.py:4430-4470`. Six new boundary tests
(`tests/test_signal_gates.py`).

## 2026-05-10 — Opportunity scanner: gate-aware scoring + politician universe filter

Closed the last open item from the politician-signal arc — wiring the
gate registry into the scoring pipeline, not just into rendering.

**Option B (gate-aware scoring).** `compute_politician_signal` now uses
a new `_gate_aware_weight` helper that layers the gate registry on top
of the manual `HIGH_SIGNAL_POLITICIANS` weights:
- gate-PASS politicians keep their manual weight (signal is real).
- gate-FAIL politicians contribute zero (signal is noise or
  wrong-direction).
- Unbacktested politicians keep their manual weight (preserves prior
  behavior for the long tail).

Effect: Gottheimer and Crenshaw stop polluting the catalyst score
across the entire universe; Pelosi sells and Tuberville buys also
stop contributing (they're FAIL on the wrong-direction side); Pelosi
buys and Tuberville sells contribute at full weight as before.

**Option A (universe filter).** Added
`StockDataReader.get_tickers_with_gate_pass_politician_trade(
lookback_days, direction)` plus a CLI flag
`--source politician-pass-buys|politician-pass-sells` on
`scripts/run_opportunity_scan.py`. Restricts the scan universe to
tickers with at least one recent gate-PASS politician trade.

Today the buy-side filter returns AAPL, AMZN, GOOGL, NVDA, VST (Pelosi
buys, last 180d). Sell-side returns nothing because Tuberville's
Senate trades aren't ingested yet. Use as `uv run python
scripts/run_opportunity_scan.py --source politician-pass-buys
--preview`.

Two existing tests that pinned pre-gate behavior were rewritten
(Tuberville BUYS no longer contribute 0.3 weight — they collapse to
zero; Pelosi BUYS keep 3.0 weight, Pelosi SELLS collapse to zero). A
new test for unbacktested politicians (Schumer) confirms they still
contribute at the default weight.

---

## Reference

### Politician signal pipeline — current state

- Data ingest: `scripts/fetch_politician_data.py` (House Clerk PTRs, daily cron 02:30 UTC)
- Storage: `politician_trades` table (~5,300 rows post-backfill across 174 House members)
- Backtest harness: `scripts/backtest_politician.py --name "Last, First" --out <md path>`
- Gate registry: `src/invest/signals/gates.py:SIGNAL_GATES`
- Inventory ledger: `notes/research/signal_inventory.md`
- Surfaces in: `/feed` only (NOT yet wired into `run_opportunity_scan.py`)
- Senate eFD blocked from scraping; Tuberville's PASS gate fires only if Senate trades land in `politician_trades`, which they don't yet.

### How to backtest a new politician

1. `DB_URL=postgresql://invest:invest_2026@localhost:5433/invest uv run python scripts/backtest_politician.py --name "Last, First" --out notes/research/<lastname>_backtest_2026.md`
2. Fill in the Recommendation + Robustness sections in the generated report (script leaves them as templates)
3. Add entries to `gates.py:SIGNAL_GATES` for both P and S (use `passes=False` if rigorous test fails — documents the negative result)
4. Update `notes/research/signal_inventory.md` row from UNGATED to PASS / FAIL
5. Run `uv run pytest tests/test_signal_gates.py --no-cov`

## 2026-05-10 — Portfolio review session: TTD / MOH / SK Square / PTON / BRK.B / 8002 / cash deployment

### X posts triaged (5 fetched via vxtwitter)
- **@browomo** (AI trading stack, $180K self-reported gains) — vibe post, no track record. Discard as signal; mildly interesting as tooling inspiration.
- **@theaiportfolios** (Claude-managed $50K paper portfolio, trailing SPY 60bps) — noise on a tiny sample. Individual picks (INTR, MGNI, PGY) could be screened but the "AI portfolio" framing adds no edge.
- **@babyfolio** (SK Square as backdoor SK Hynix, 43% NAV discount) — **only X post worth following up.** Holdco-discount arb is a real pattern.
- **@pepemoonboy** ($PLAB, $AMKR naked ticker reply) — discard.
- **@seelffff** (open-source replacing $2K/mo trading subs) — DIY tooling advocacy, not investing content.

### Deep dives → decisions

**TTD — DOWNGRADE to HOLD (was BUY at $23.51 in prior 2026-03-20 note)**
- Moat is **structurally weakening**, not just re-rating. Three vectors: Amazon DSP take rate 1–2% vs TTD's effective ~21%; Walmart Connect exclusivity ended; Disney/Roku/Netflix now have Amazon DSP as co-equal pipe. WPP CFO publicly said TTD "operates in a smaller slice of the ad market" — structural messaging.
- CTV market grew 14% in 2026, TTD's CTV-heavy book guided 8% in Q2. That's share loss, not macro.
- Kokai costs are permanent (margin guide flat at 40%, not expanding). EV revised +42% → +16%. Probabilities shifted: bull 25→15%, bear 25→40%.
- Prior $21 add-level no longer triggers a buy. Thesis-break revised $15 → $17. Cut if Q2 < $735M or second top-5 agency formally derecommends. Detail: `notes/companies/TTD_2026-05-10_update.md`.

**MOH — HOLD, don't chase (already a 14% combined position)**
- Q1 cleared the bear-case thesis-break (MCR 91.1%, well below 93%). But +28% rerate from $142 → $182 compressed EV from +16% to +4%. Street PT $144–172 still lags price.
- Trap: MOH's own FY guide says Q1 was trough-of-trough — Medicaid MCR 92.0% trending to 92.9% full-year, so 2H runs ~93.3%. Market is paying 36x trough EPS for a recovery management says won't show until 2027.
- Burry position confirmed (1.73% of Scion portfolio) but his HMO track record is mixed — confirmation, not edge.
- Marketplace PTC expiration is the under-discussed tail risk (already mitigated by MOH's 20% footprint cut).
- Trim IBKR portion ~25–33% back to ~10% combined. Re-add at $150–160 on Q2 wobble OR breakout above $200 after July rates ≥4%. Next print: Q2 ~Jul 23. Detail: `notes/companies/MOH/2026-05-10_update.md`.

**SK Square (KRX 402340) — PASS**
- NAV is **~96% SK Hynix** (~200 tn KRW); unlisted holdings (Shieldus, 11st in forced sale, T Map, Wavve) only ~2.5% of NAV.
- Discount has already compressed 65.7% → 43% over 18 months; stock up 192% YTD. Sell-side floor for the discount is ~25–30%, set structurally by ~25% Korean capgains tax on Hynix monetization + chaebol governance + reinvestment risk.
- Remaining compression ~15pp = ~15% upside on the arb leg. Beyond that it's just leveraged Hynix beta with a permanent 25–30% haircut.
- If bullish HBM through 2027 fine; if HBM peaks 2026 the discount cushion won't protect. Trade via KRX 402340 in KRW (SKSQF OTC is illiquid), 15% Korean dividend WHT under treaty. Detail: `notes/companies/SK_Square_402340.md`.

**PTON — HOLD all of it (revised from earlier "is the thesis still valid?" framing)**
- Q3 FY26 (May 7) was the inflection: revenue +1% YoY (first positive print in years), FCF +59% to $151M, **first-ever GAAP profitable year**, FY26 FCF guide raised $275M → $350M, net debt -70% YoY to $173M. Stock $5.70 (+24% since prior review).
- Subscriber bleed persists (-7.6% YoY, 2.662M) — "shrinking to profitability" has finite runway.
- Triggers: add at $4.80–5.00; trim 25% at $7.50, another 33% at $9.00; exit if churn >2.5% two quarters OR Q4 revenue miss >3% OR refi fails OR breaks $3.80 on fundamentals. Detail: `notes/companies/PTON_2026-05-10_update.md`.

**BRK.B — CLOSE the Revolut position**
- Identified from Revolut CSV: 2.07016706 shares, cost basis $1,000.01 (filled @ $481.85 on 2025-02-14, fx 1.0519). Now ~$986 (-1.4%). Source: `vault/paperwork/taxes/2026/raw/revolut_transactions_2020-2026.csv:182`. **Not booked in beancount** — Revolut positions aren't being reconciled there.
- P/B 1.41 = exactly historical median. Abel transition smooth, $397B cash pile, buybacks restarted. Fair, not cheap.
- At 2.1% it's worst-of-both: too small to anchor, too big to ignore. Notes don't support a 7–10% conviction sizing. Close. Detail: `notes/companies/BRK_B.md`.

**8002.T Marubeni — TRIM 25% (not 30%, not 50%)**
- **Critical late-breaking fact:** Berkshire crossed the 10% threshold on both Marubeni and Sumitomo the week ending 2026-05-09. Fresh committed-buyer catalyst — don't trim aggressively into strengthening news.
- Valuation reality check on Morningstar comparable basis: Mitsui 8.6x P/E · **Marubeni 9.0x** · Mitsubishi 10.3x · Sumitomo 10.6x · Itochu 12.1x. Mid-pack, not expensive. The "fully priced" framing from prior notes used a different P/B basis and was overstated.
- But: 14% portfolio weight is at Kelly cap with zero margin; JPY appreciation is a 10% USD-return headwind if BOJ tightens; Q3 FY26 EPS missed by 27%. Sizing discipline says trim.
- Sell ~50 shares ≈ $1,740. Leaves ~$5,200 / 10.5% weight. Re-trim 25% more if breaks 6,200 JPY without earnings support; add back if pulls below 4,500 JPY on macro fear. Detail: `notes/companies/8002_2026-05-10_update.md`.

### Cash deployment plan (~19% post-trims)

Hold cash, don't force a buy. EUR money market ~2%, USD ~4% — paid to wait. Tripwires:

| Trigger | Action |
|---|---|
| MOH pulls back to $150–160 | Re-add 5% position |
| CNC stays <10x fwd P/E through Q2 | Open starter 3–5% |
| SK Hynix sells off 20%+ on HBM cycle fear | Add Hynix directly (not via SK Square) |
| Broad market -10% correction | Deploy ~half of cash into existing winners (GOOG, AVGO) |
| 6 months pass with no trigger fired | Force review — drift to global cheap (BABA, energy, EU defense) or accept structural cash |

**EUR parking:**
- Below ~€5K: leave in Revolut Flexible Account (~1.8–2.2%, takes ~30–50bps haircut vs €STR).
- Above ~€10K: transfer to IBKR, buy **XEON** (Xtrackers II EUR Overnight Rate Swap UCITS, Xetra) — tracks €STR ~2%, daily liquid. Alternatives: CSH2, C3M, ERNE within 10–20bps.
- IBKR's own EUR cash sweep pays ECB deposit rate −50bps above €10K threshold (~1.5%) — useful zero-effort baseline but lowest yield.

**USD parking:**
- IBKR auto-sweep at ~4.3% on USD balances above $10K threshold, or buy SGOV.

### Other findings this session
- **Sony FY2025 results (reported 2026-05-08):** Record ¥1,447.5B OP but FY2026 guide soft (¥1,600B vs higher consensus) on memory shortages, Afeela EV wind-down (+¥30B charge on top of ¥44.9B), Bungie impairments, tariff uncertainty. Music was the bright spot (+21% sales, +28% OP). Stock -23% YTD. Not broken, not obviously cheap — hold or tax-loss harvest if Spain allows.
- **MOH catalyst diagnosis** (Apr 23 +14% move): Q1 MCR 91.1% (250bps better than Q4 2025's 94.6%) + CMS 2027 MA Final Rate Notice +2.48% net + Burry disclosure + UNH/ELV peer guidance raises. Justified but no longer cheap.

### Memory hygiene
- Fixed stale MEMORY.md claim that portfolio lived in this repo — it's at `~/vault/finance/notes/portfolio/portfolio.md` (moved out in commit d2f95bf). Transactions at `~/vault/finance/notes/transactions/`. Beancount at `~/vault/finance/*.beancount`.
- Added new feedback memory: `feedback_verify_memory_before_acting.md` — always check path/state exists before relying on a memory claim; fix stale entries rather than routing around them.

---

## 2026-05-18 — STLD exit + tactical buy plan for Wed/Thu

### Trades today
- **STLD sold full position** on Revolut (free monthly trade): 7.50131272 sh @ market $226.94, gross $1,702.35, fee $0.05 (SEC Sec-31 pass-through), net **$1,702.30**. Realized **+66.5%**. Triggered by: free trade availability + cyclical-at-peak (analyst +4%, DCFs −28 to −34%, GBM 3y only +16-25%, +66% gain) + macro CAUTIOUS regime. Full rationale: `~/vault/finance/notes/transactions/2026-05-18_sell_STLD.md`.
- **FX**: ~$1,000 USD → EUR same day at Revolut.
- **Revolut → IBKR transfer**: €3,000 SEPA initiated (leaving small EUR reserve in Revolut + residual USD).
- **AGENTS.md updated** with `Repo Scope vs Personal Data` section pointing at `~/vault/finance/` for portfolio/transactions/ledgers — this repo is analysis infra only.

### Macro snapshot (2026-05-18)
- S&P -1.5% off ATH, +24% YoY (2× hist avg). VIX 19 calm. 10Y 4.60%. Polymarket: 98% prob NO Fed change at June meeting, **70% prob NO Fed cuts in 2026**. Gold +40% YoY (hedging beneath calm). Verdict: **CAUTIOUS — keep dry powder** (unchanged from May 10 reading).
- Tripwires from 2026-05-10 plan: none have fired (MOH bounced from lows to $183, doesn't qualify as $150-160 pullback; CNC unchanged; no broad -10% correction). Default cash-holding stance still operative.

### Technical setup snapshot for buy candidates (2026-05-18 close)

| Ticker | Price | RSI14 | vs SMA20/50 | 20d move | ATR14 | WL BUY zone | Setup |
|---|---|---|---|---|---|---|---|
| **DECK** | $95.07 | **31.8** | below / below | -14.4% | $3.40 | $100-110 | **Oversold + below entry zone**. Prime setup. |
| **META** | $612.37 | **26.4** | below / below | -8.7% | $17.10 | (not listed) | **Deeply oversold quality**. GBM 5/5 bulls. |
| **BSX** | $55.24 | 38.2 | below / below | -9.4% | $1.68 | $68-73 | Oversold, below zone. |
| **CRM** | $178.78 | 47.9 | slightly below / below | -4.0% | $7.25 | $190-200 | Neutral, below WL zone. |
| **GILD** | $130.41 | 52.5 | slightly below / below | -4.0% | $3.31 | $132-140 | In WL zone, neutral. |
| **PINS** | $20.06 | 51.1 | slightly below / above 50 | -2.8% | $1.14 | $18-19 | Just above WL zone, neutral. |
| **NOW** | **$103.21** | **67.3** | above / above | +3.4% (last 5d **+12.8%**) | $4.79 | (held starter @ $88.67) | **Just popped +8.6% on May 18 on 1.14× vol — approaching overbought. Don't chase tranche 2 at this level.** |
| **FSLR** (held) | $230.62 | 72.5 | above / above | +19.8% | $11.78 | — | Overbought; don't add to existing 35 sh. |
| **MOH** (held) | $183.18 | 47.9 | below / above 50 | +22% | $7.87 | — | Bounced from April lows; don't add. |

### NOW thesis check after today's move
NOW closed $103.21 today vs $95.07 Fri close = +8.6% on 32.3M vol (1.14× 20d avg). RSI jumped from ~50 → 67.3. No obvious headline catalyst found in 5-deep news scan. Could be: software-sector momentum, AI/Agentforce-adjacent move, M&A speculation, or technical breakout above 50-day SMA at $99.31. The fundamentals didn't change in one day, but the **tactical entry has worsened materially**. Original plan was to add tranche 2 at $88-95. Limit at ~$98 (just above 50-day SMA) is the disciplined waiting price; chasing $103 is not.

### Tomorrow / Wed-Thu deployment plan

Cash availability: ~$1,500 (existing IBKR) + ~$3,300 USD post-FX (incoming SEPA, lands Wed-Thu) = **~$4,800 deployable**.

**Primary plan** (best technical setups, defers NOW):
1. **DECK** initiation: limit buy **20 sh @ $96.00 GTC** ≈ $1,920. RSI 31.8 oversold + below WL BUY zone + Kelly top score (+71.6%, 5/5 bulls, ROE 40%).
2. **META** initiation: limit buy **3 sh @ $610.00 GTC** ≈ $1,830. RSI 26.4 deeply oversold + quality (32.9% ROE) + GBM 5/5 bulls (3y opp +27.5%).
3. **NOW** add (tranche 2, patient): limit buy **20 sh @ $97.00 GTC** ≈ $1,940. **Only fills on pullback** to/below 50-day SMA. If unfilled in 5 trading days, re-evaluate.

Cash math: DECK + META fills = $3,750 committed, $1,050 dry powder. If NOW limit fills too: over-budget by ~$890 → cancel NOW limit at that point or shrink DECK to 18 sh.

**Alternative (single-initiation, sticks closer to original NOW plan):**
1. DECK 20 sh @ $96 GTC = $1,920
2. NOW 20 sh @ $97 GTC = $1,940
3. Skip META this round.

### Tripwire updates (additions to 2026-05-10 plan)
| Trigger | Action |
|---|---|
| NOW pulls to $90-95 | Fill tranche 2 immediately at market (original plan zone) |
| META breaks below $590 | Add second tranche on extreme oversold flush |
| DECK breaks below $90 | Double initial size (oversold extreme) |
| US 10Y above 4.80% | Reassess all duration-sensitive positions; defer remaining buys |
| VIX above 25 | Stop deploying; reassess macro regime |


## 2026-05-19 — Revolut → IBKR transfer time

Revolut-to-IBKR cash transfer completed **overnight** (initiated previous evening, available next morning). Earlier estimates of 2–3 days were wrong.

**Rule for future plans:** assume Revolut → IBKR USD cash transfer = **1 business day**, not 2–3. Plan limit-order timing and deployment windows accordingly.

## 2026-05-28 — Thesis change: SOFI BUY→WATCH (conviction MEDIUM→LOW)

Surfaced during the 15-name stale-note refresh batch. SoFi's 2026-03-17 note was a BUY.

**Believed (prior variant perception):** the market under-priced (1) a widening bank-charter moat as regulators squeezed rent-a-bank fintechs, and (2) a Galileo/Technology-Platform inflection from startups to tier-one banks. The dated trigger was Q1 2026 earnings (~May 4): confirm the ~38-42% guided EPS CAGR and the stock re-rates from ~$17.63 toward $25+.

**Happened:** Q1 (reported 2026-04-29) *beat* — revenue $1.10B (+41% YoY), 10th straight profitable quarter, profit ~doubled, record $12.2B originations, personal-loan NCO improving to 4.4%. Yet the stock FELL ($17.63→$16.29) and analysts CUT targets into the beat (Mizuho $38→$29, Citi $37→$30). Guidance was held, not raised. The Galileo leg weakened: +12% "like-for-like" after a large customer exited.

**Lesson (transferable):** a clean positive catalyst that fires and *fails to move the price* disproves the **variant perception**, not the company. The error wasn't "is SoFi a good business" (it is — 17/25) — it was believing the market mispriced the growth. The market was deliberately refusing to pay a premium for unsecured-consumer-credit cyclicality at ~21x forward; it was never confused. A good moat at a full price is still a pass. Weight "and the market doesn't realize it" as heavily as "the company is great" — only the gap makes money.

**Surviving (narrower) edge:** the capital-light loan-platform model (originate-and-sell for fees, $3.6B new partner commitments) could make earnings less cyclical — but it's a future inflection, not visible in the numbers yet. Hence WATCH/LOW, not PASS. Re-upgrade triggers: pullback to ~$13, or a Q2 (2026-07-28) guidance raise with loan-platform fees scaling and NCO <4.5%.

## 2026-05-31 — Thesis change: HIMS WATCH→WATCH (conviction LOW→MEDIUM)

**Believed (prior variant perception, 2026-03-20):** "No edge." Saw HIMS as a washed-out DTC telehealth name buried under overhangs — SEC investigation, class actions, gross margin compression, SBC > net income, ~$970M new debt for an unproven international acquisition. Risk/reward asymmetric to the downside at $24. Was waiting for SEC resolution, margin stabilization >70%, and Eucalyptus integration evidence before reconsidering.
**Happened:** Q1 2026 (reported May 11) confirmed the painful but deliberate compounded-GLP-1 wind-down: revenue +4% YoY to $608M (vs ~59% FY25), net loss -$92M, adj EBITDA halved to $44M, $33M restructuring/inventory write-downs, gross margin to 65% GAAP. The genuinely new datum: core US (non-GLP-1) business contracted -8% YoY — the +4% headline was carried entirely by international (+~10x to $78M). Yet management RAISED FY26 guidance to $2.8-3.0B (+19-28%), implying a sharp H2 reacceleration. Novo relationship went full circle: terminated June 2025 → sued Feb 2026 → settled + branded-Wegovy partnership March 9 2026. Now a clean, dateable binary: Q2 earnings (August) must show the reaccel.
**Lesson (transferable):** conviction can rise (LOW→MEDIUM) without the verdict changing (still WATCH) when the situation goes from "diffuse wall of overhangs, no edge" to "one identifiable binary with a dateable catalyst." The edge isn't a directional view — it's recognizing that waiting until Aug costs almost nothing because the catalyst resolves the central question. Also: when a reseller pivots to branded supply from a competitor-supplier (Novo/Lilly), read the *segment* underneath the headline — the +4% masked a -8% core contraction; the consolidated growth number lied about the health of the original engine.
**Surviving edge / re-upgrade triggers:** upgrade to BUY on a clean Q2 beat (rev ≥$700M) WITH core US stabilizing toward flat AND adj gross margin holding ~70%. Downgrade toward PASS on a Q2 miss or worsening core US contraction. Thesis-break / stop-bull level: confirmed Q2 revenue miss or price break below ~$18.

## 2026-05-31 — Sector insight: drone stocks & the "battle-tested" trap (surfaced via ONDS)

**Found/learned:** When evaluating defense-drone stocks riding the Ukraine/drone-warfare theme (ONDS and peers), separate three things the bull narrative blurs together:
1. **Hardware is commoditized.** FPV/loitering airframes are ~$400, Chinese components, 3D-printed — both Ukraine AND Russia mass-produce them (Lancet, Shahed/Geran). No side holds a durable hardware lead; they leapfrog monthly.
2. **The real edge migrated into the *loop*, not the object** — electronic-warfare adaptation speed, fiber-optic (unjammable) and terminal-autonomy workarounds, kill-chain integration. This edge is organizational, wartime-specific human capital. It is a genuine *military* advantage but a terrible *business* moat: can't be packaged, licensed durably, or earned at high recurring margin, and it decays when the enemy adapts or the war ends.
3. **Battlefield winners ≠ contract/margin winners.** Cheap disposable offensive drones (Ukraine leads) and high-margin certified counter-UAS + integration + procurement (Western/Israeli channels) are *different companies* with different economics. Counter-UAS for civilian/airport/border use is a certification-and-relationships game — you can't jam or kinetic-kill over a civilian airport, so "battle-tested" heavy-EW/kinetic Ukrainian counter-drone doesn't even transfer to that market.

**Lesson (transferable):** "battle-tested" or "combat-proven" is a *snapshot* attribute, not a moat — when the durable edge is an iteration loop rather than ownable IP/product, it doesn't compound into shareholder value. Before paying a theme multiple on any war-tailwind defense name, ask: is the edge in something *sellable at margin* (certified product, contract vehicle, switching cost), or in a wartime organizational reflex that can't be bottled? If the latter, it's priced theme, not value. Also: a company tagged to a hot conflict often has only *borrowed* pedigree (ONDS = $11M stake in Ukraine's DFG + Israeli Airobotics combat history; zero direct Ukraine revenue). Verify where revenue and deployments actually are before accepting the narrative.

## 2026-06-01 — Insight: how to play a hyped mega-IPO (SpaceX ~2026-06-12)

**Found/decided (generic, transferable — personal execution plan lives in vault `finance/notes/tasks.md`):** When a marquee IPO is hyped to "pump the market beforehand," separate mechanism from pattern:
- **A mega-IPO does not *cause* a broad-market pump.** Bankers/founders *launch into* froth — a wave of big IPOs is a *symptom* of an already risk-on regime, not its cause. A huge raise (SpaceX ~$75B) actually *absorbs* liquidity. So the spillover is into sentiment-correlated names (Musk/space-adjacent, speculative risk-on), not the S&P broadly.
- **"Buy the rumor, sell the news": the news is the *listing*.** Anticipation premium peaks before-to-at the event. Sell extended/story positions *into the run-up, cresting at the IPO* — NOT after (catalyst spent, float caps the pop, sentiment halo mean-reverts).
- **IPO-mania + broad melt-up + "everyone agrees it'll rip" is a late-cycle / distribution signature** (1999–2000, 2020–21). A consensus-expected pump is a crowded view — treat confirmed froth as an exit, not an entry.
- **Don't forecast the pump — let strength trigger sells.** Laddered GTC limits above market fill only if froth materializes; if it doesn't, you keep the positions. No timing required. Decouple genuine overbought-discipline trims (e.g. RSI-extended names at weight caps) from the IPO date — do those on their own signal.

**Lesson (transferable):** the actionable response to a *predictable* sentiment event is to pre-stage conditional sells into strength, not to position the book on a directional forecast. And reverse the assumed causation: froth enables IPOs more than IPOs create froth — so a hyped IPO calendar is a reason to *raise* trim discipline, not chase.

## 2026-06-22 — First look: MSTR (Strategy) — WATCH/LOW, and how to value a leveraged bitcoin-treasury vehicle

**Found/decided:** MSTR at $112.53 trades at a ~20% *discount* to its bitcoin (mNAV — modified net asset value — 0.74× basic / 0.80× diluted, June 15). Bitcoin (~$64k) is below Strategy's $75,537 average cost basis, and on the Q1 2026 call management broke the "never sell bitcoin" pledge, then actually sold 32 BTC in late May to fund the STRC preferred dividend. Verdict WATCH (lean PASS), LOW conviction — scenario EV +23% but it's purely a leveraged bitcoin-direction bet with negative carry, not a company-specific edge.

**Lesson (transferable — applies to any bitcoin/crypto treasury company: MSTR, BMNR, Strive, etc.):**
1. **The mNAV premium is the entire engine, and it only runs in one direction.** Above 1.0× mNAV, selling stock to buy bitcoin is *accretive* (raises bitcoin-per-share) — the flywheel. Below 1.0×, the same action *dilutes* bitcoin-per-share. So crossing below parity isn't a quote change, it's a regime change: the growth model inverts. Check mNAV before anything else.
2. **A discount to NAV is not automatically a bargain.** Senior claims (here ~$8.25B converts + ~$10.3B preferred) sit ahead of the common, and ~$800–900M/yr of fixed dividend/interest obligations must be funded by a company with negative operating cash flow. The discount is the market correctly pricing per-share bitcoin *leakage* (forced selling to pay carry) + subordination, not a free lunch.
3. **Ignore the GAAP P&L entirely.** Under fair-value accounting (ASU 2023-08) net income is dominated by non-cash bitcoin remeasurement (-$3.85B FY25). Value = bitcoin × price − senior claims − capitalized cost of preferred carry, then a market premium/discount. Standard DCF/RIM/GBM are meaningless — don't even run them.
4. **A broken load-bearing pledge re-rates the multiple, maybe permanently.** "Never sell bitcoin" was the narrative that sustained the cult premium; abandoning it is a structural signal, not a one-off.
5. **Sell-side targets can be wildly disconnected** ("strong buy," ~$351 mean) when a stock is really a leveraged commodity proxy — the targets embed a bitcoin price and a re-rating to premium that may not return. Don't anchor on them.

**Re-engage triggers:** upgrade toward BUY only if bitcoin reclaims ~$75k (cost basis) AND mNAV stabilizes ≥0.9× (flywheel can restart); or a deep-value discount blowout to <0.6× mNAV with the $2.25B reserve and STRC coverage intact. Avoid the 0.8–0.95× dead zone with bitcoin below cost — that's where per-share bitcoin quietly bleeds.

## 2026-06-20 — Dashboard load time: 9–15s → <1s (N+1 + no caching)

**Found:** The live dashboard (`invest.rubenayla.xyz`) took 9–15s per page (`/m` 12–14s, even the 137KB `/feed` 8s). Root cause, timed on the Hetzner box: every request re-ran `load_stocks_from_database()` (~7.8s) with no caching anywhere (`Cache-Control: no-store` → Cloudflare `DYNAMIC`, origin hit every time). The 7.8s was an **N+1**: for each of 1807 tickers it called `compute_insider_signal` (~4 queries) and `compute_politician_signal` (~2 queries) in a Python loop ≈ ~10,000 DB round-trips. HTML generation was only 0.29s; wire size was a red herring (Cloudflare already brotli-compresses the 6.7MB HTML to ~321KB). All three routes share the loader — why the tiny feed page was also slow.

**Fixed** (commit `3e42e8c`):
1. Added `compute_all_insider_signals` / `compute_all_politician_signals` (batched `GROUP BY` queries) in `insider_db.py` / `politician_db.py`; loader uses them. Insider 3.84s→0.96s, politician 1.97s→0.16s. The single-ticker `compute_*_signal` APIs were kept (other callers + tests depend on them); shared aggregation extracted into `_aggregate_*_rows` / `_trends_from_aggregates` helpers so batch and single paths give identical output (verified 0 mismatches on 60 sampled tickers).
2. Added a thread-safe in-process snapshot in `dashboard_server.py` (`SnapshotCache`): warmed at startup, refreshed every `DASHBOARD_REFRESH_INTERVAL`s (default 300) in a background thread + immediately on update completion. All routes (`/`, `/m`, `/feed`, `/api/stocks`, `/api/health`) serve from it, so no request pays the load.

Result (prod, incl. network): `/` 0.66s, `/m` 0.96s, `/feed` 0.56s, `/api/health` 0.08s.

**Lesson (transferable):** before optimizing payload/transfer, time the server-side phases separately — a tiny endpoint that's still slow points at shared backend work, not bytes. The classic killer is an N+1 hidden behind an innocent-looking `for ticker in stocks:` loop; batch into `GROUP BY` queries. And for any per-request DB rebuild of data that only changes nightly, a warm in-process snapshot (refreshed in the background, invalidated on write) beats per-request loading by orders of magnitude.

---

## 2026-07-15 — Full DB update run on Y540; classic-valuations hang found + worked around

Ran `scripts/update_all.py` (sp500 default) on the Y540 laptop (`ssh y540-ubuntu`, hostname `y540`) writing to the shared Hetzner Postgres via the `hetzner-db` tunnel (localhost:5433). Prompted to use Y540 "for its graphics card."

**GPU was not used, and can't be as configured.** The GBM models are numpy Monte-Carlo (CPU). The only GPU-capable models are the neural nets (`neural_network_model.py`, `lstm_transformer_model.py`), and they are commented out / `--skip-nn` in `update_all.py`. Y540's torch is a CPU-only build anyway (`torch.cuda.is_available()` False) despite a physical GTX 1650. To actually use the GPU you'd need a CUDA torch build **and** to re-enable the NN step.

**What completed (all timestamped 2026-07-15, verified in `valuation_results` + `current_stock_data`):** price fetch (1802/1820 refreshed <12h), activist-stake fetch (13D/G), 13F holdings fetch, GBM ×6 (709 rows each), autoresearch (761), and all 6 classic models (dcf/dcf_enhanced/growth_dcf/multi_stage_dcf/rim/simple_ratios, 1820 rows each, done 07:38 machine-time). Dashboard HTML regenerated (1820 stocks, 13034 valuations). Opportunity scanner ran last.

**The hang:** after classic valuations finished writing at 07:38, `run_classic_valuations.py` spawned a second copy of itself that wedged for ~2h — `Sl` state, `poll_schedule_timeout` wchan, ~2% CPU, holding an `idle in transaction` (bare `BEGIN`) DB connection, no log output, and never reaching the dashboard/scanner steps. Killed the tree (`update_all.py` + both `run_classic_valuations.py`) and re-ran the two tail steps directly (`scripts/dashboard.py` then `scripts/run_opportunity_scan.py`) — dashboard succeeded immediately. Root cause of the second-subprocess wedge not yet diagnosed (py-spy needs sudo on Y540); worth a look if it recurs.

**Slowness note:** per-row INSERTs over the SSH tunnel dominate wall-clock — autoresearch took 42 min just to insert 761 rows (05:33 delete → 06:15 insert). Y540 has an uncommitted local fix in `scripts/run_gbm_predictions.py` that batches the price lookup into one `WHERE ticker = ANY(%s)` query instead of a per-row `StockDataReader` call; the same batching should be applied to the autoresearch and classic-valuation save paths. That change is Y540-only and uncommitted as of this run.

**Scanner also hung (separate from the classic-valuations wedge).** After the dashboard regenerated, `scripts/run_opportunity_scan.py` ran and wedged for 70+ min with the same signature — `Sl` / `poll_schedule_timeout`, ~4% CPU, an `idle in transaction` connection stuck on `SELECT DISTINCT quarter FROM fund_holdings WHERE ticker...`, and **zero new rows written** (`scanner_score_history` still maxed at the prior day 2026-07-14 09:48). Today's 13F fetch grew `fund_holdings` to ~89.5k rows; the scanner's per-ticker `fund_holdings` query looks like an unindexed N+1 that now stalls (possibly self-locking via the open transaction). Killed it — did not re-run, because it would re-hang on the same query. **Consequence:** opportunity-scanner scores are stale (2026-07-14); prices + all valuation models + dashboard are current (2026-07-15). Fix needed before the scanner is usable: batch/​index the `fund_holdings` `DISTINCT quarter` lookup and make sure the scan doesn't hold an idle transaction across per-ticker queries. Both this and the classic-valuations second-subprocess wedge point at the same root pattern — per-ticker DB round-trips over the SSH tunnel, plus transactions left open.

**Fix shipped (same day, commit 704aa12).** Root cause of both the scanner hang and the save-path slowness was the same: a fresh psycopg2 connection opened per ticker over the SSH tunnel. `StockDataReader.get_stock_data` alone opens ~7 (main row + insider/activist/holdings/japan/politician sub-signals), and `score_stock` opened one more — ~13k handshakes for 1904 tickers, which is what wedged the scanner (not a missing index; `fund_holdings` already has `idx_holdings_ticker`/`idx_holdings_quarter` and is only ~48k rows). Fixes: (1) `run_gbm_predictions.py` and `run_autoresearch_predictions.py` now do one `WHERE ticker = ANY(%s)` price query + a single `execute_values` INSERT instead of per-row work; (2) the scanner's `score_universe` opens one `autocommit=True` connection and threads it through `score_stock → get_stock_data →` all six sub-signals + `get_latest_predictions` (scoring logic unchanged). Verified: smoke test scored 9/10 with sensible components; full re-run scored all 1904 and wrote 1904 fresh `scanner_score_history` rows for 2026-07-15 in ~19 min (was: hung 70 min, zero rows). CI green, auto-deployed. Remaining per-ticker query round-trips (~700 ms/ticker over the tunnel) are a smaller further optimization — batch-loading predictions/signals across the universe, or running the scanner server-side on Hetzner where the DB is local, would cut it to seconds. The classic-valuations second-subprocess wedge from the original run is still undiagnosed (separate issue).

---

## 2026-07-16 — tasks.md consolidated to the repo root; `.agents/tasks.md` retired

`.agents/tasks.md` was moved to `tasks.md` at the repo root with `git mv`, so the file's history follows it. `.agents/tasks.md` no longer exists in this repo and must not be recreated: the rule is one `tasks.md` per repo, at the root.

**Rationale:** tasks are the project's tasks regardless of who does them. Two files named `tasks.md` only produce duplicates and stale entries — whichever one the current session isn't reading quietly goes out of date.

`AGENTS.md` was updated to list `tasks.md` under "Repo root files (NOT in `.agents/`)" alongside `history.md`, instead of under the `.agents/` heading.

Stale `.agents/tasks.md` paths that appear in append-only records (`history.md`, `.agents/error-log.md`) were deliberately left as written — they were accurate on the date they were logged, and rewriting them would falsify the record.

---

## 2026-07-19 — ISRG deep-dive: unit economics, patent expiry, telesurgery, and a penetration-ceiling estimate

Triggered by ISRG falling to **$345.11** after Q2 2026 (reported 2026-07-16). Q2 beat — revenue $2.89B (+18.5%), non-GAAP EPS $2.80 (~12% above consensus), da Vinci procedures +15%, Ion (Intuitive's robotic lung-biopsy platform) +36%, 468 systems placed vs 395 — but the stock dropped ~14% on the week because management guided full-year da Vinci procedure growth to the **midpoint** of the existing 13.5–15.5% range instead of raising it. H1 ran ~15.5% (Q1 +16%, Q2 +15%), so a 14.5% full year implies ~13.5% in H2. Compounding: an ongoing voluntary **Class II recall** (initiated April 2026) of 454 systems for an e-brake retainer pin, plus soft reported surgery volumes at large hospital operators.

No thesis-break condition triggered. The move is multiple compression (~37× → ~32× forward), which `notes/companies/ISRG.md` already named as the most likely bear mechanism.

The durable analysis — cost stack of a surgical case, per-system annuity, patent expiry, training data, international cost structure, AI/OR-time lever, and the ceiling calculation — was written into `notes/companies/ISRG.md` under "Unit Economics, Moat Composition, and the Penetration Ceiling", with sources. Recorded here is the reasoning trail and the material that did **not** fit the note.

**Headline conclusions (so they survive a change of opinion):**

1. **The robot is ~13% of the cost of a robotic operation.** Operating-room (OR) time dominates the hospital's facility fee (US $37–46/minute, overwhelmingly labour — nurses, scrub techs, sterilisation staff — but *not* the surgeon, whose professional fee is billed separately from the facility fee in the US). The robot adds ~$2,300/case: ~$1,150 amortised capital + ~$1,150 instrument premium. This reconciles almost exactly to the observed $16,000 laparoscopic vs $18,300 robotic hospitalization-cost gap.
2. **Economics are marginal against open surgery and lose to laparoscopy.** *(Corrected during review — the first draft of this conclusion was wrong in the robot's favour.)* Meta-analyses put the robotic-vs-open length-of-stay advantage at 1.5–1.62 days pooled, but with a large geographic split: **−0.7 days in US studies, −2.1 days in European ones**. Applying US bed cost (>$2,400/day) gives ~$1,700 of saving against the ~$2,300 premium; applying European bed cost ($500–900) to the larger European gap gives ~$1,500 against the same premium. **On bed-days alone the robot does not pay for itself against open surgery in either geography** — the case rests on reduced blood loss, transfusions and complications, several of which accrue to the patient and payer rather than to the hospital's budget. Against laparoscopy the length-of-stay advantage vanishes entirely, and the growth frontier (gallbladder, appendix, hernia, colorectal) is laparoscopic territory, won on surgeon preference rather than hospital cost savings.
3. **Each installed system yields ~$720K/year of recurring revenue, indefinitely** — which converts to **~$540K/year of recurring gross profit**, roughly equal to the entire one-time gross profit on the ~$1.44M system sale, and then repeats annually for a decade or more (~$5.4M against ~$540K, about ten to one). *(Also corrected during review: the first draft compared recurring **revenue** to one-time **profit**, which overstated the annuity. On a like-for-like profit basis the first-year figures are essentially equal and the argument is carried by repetition over the system's life.)* The machine is customer acquisition, not the product. Any manufacturing cost reduction should rationally go into price cuts to place more systems.
4. **The founding patents expired in 2019** (the broader block of surgical-robotics patents, 2016–2022). Medtronic's Hugo — the main competing surgical robot — had its first clinical use in June 2021, two years after the wall came down. Competitor arrival is the direct consequence of patent expiry, not coincidence. Patents are no longer the moat; installed base, instrument ecosystem, per-procedure regulatory clearances, surgeon training and the recorded-procedure dataset are, and all are erodible in a way a patent is not.
5. **Ceiling ≈ $230–290B market cap** at full developed-world saturation (~12M procedures/yr, ~4× today, ~$38B revenue, ~$11.5B net income at a mature 20–25× earnings), versus ~$122B today (derived: $155.8B at the May-2026 price of $439.92, scaled to the $345.11 close of 2026-07-17). That is ~1.9–2.4× over ~11 years, **roughly 6–8%/year**. The entry multiple, not the adoption curve, is the binding constraint on returns.
6. **The sharpest competitive threat is on consumables, not capital.** Industry estimates put Hugo's instrument economics 30–40% below da Vinci's, around $800–1,300 less per procedure. Since ~$3,200 of revenue per procedure is the load-bearing assumption in the ceiling calculation, a competitor undercutting the annuity matters far more than one undercutting the ~$1.5–2.5M machine.

**Telesurgery — analysed but deliberately not put in the note**, as it is not investable on any relevant horizon. Technically demonstrated: Bordeaux→Beijing partial nephrectomy in 2024 at 132 ms round-trip over 8,264 km; first US telesurgical procedure under formal FDA approval in 2025 (Florida→Angola); Japan's 2022 guidelines set ≤100 ms end-to-end and optimised 5G achieves roughly that. But **fewer than 50 fully remote procedures have been documented in two decades**, and the literature is explicit that the barriers are non-technical — jurisdiction, medical licensing, malpractice liability, cybersecurity, data protection. The World Health Organization, IRCAD (a French surgical research and training institute) and the Society of Robotic Surgery only launched a framework initiative in 2025.

Two economic objections to the "remote surgeons from cheaper countries / time-zone load balancing" idea, which came up and is worth preserving because it is superficially compelling:
- **The local team does not go away.** Someone must prep and position the patient, dock the robot, run anesthesia, and above all be ready to convert to open surgery immediately — a remote surgeon cannot control a bleed they cannot reach. The local theatre team is most of the per-minute labour cost, so the only labour arbitraged is the console surgeon, whose fee is already billed separately and sits outside the facility cost.
- **The night-shift case is the worst fit.** Emergency out-of-hours surgery is disproportionately trauma and emergency laparotomy, where speed and direct access matter and 30 minutes of robot docking is unacceptable. The cases with the most appealing time-zone logic are the ones least suited to the robot.

**Open questions left unresolved:**
- The ~8–10M/year US addressable-procedure figure underpinning the ceiling is an estimate, not company disclosure. Intuitive does not publish a soft-tissue TAM in comparable units. Worth pinning down from the investor presentation or 10-K, because the whole ceiling scales with it.
- Systems vs instruments gross margin is not disclosed; the ~37–40% systems margin is inferred from the 66.0% blend and an assumed ~78% instrument margin. If instruments are actually lower, the system margin (and the "loss-leader" framing) shifts.
- Whether the residency training shift compounds into a genuine company moat or only a category moat. Current data cuts both ways: robotic residency cases rose 4.2%→14.8% (2014–2020) and laparoscopic fell 57.4%→50.8%, but only 37% of residents report high autonomy on robotic cases vs 84% laparoscopic, and 72.5% feel more independent doing laparoscopy.

**Position context:** 9 shares at $436.73 average (tranches filled 2026-05-19 and 2026-05-27), ~-21% at $345, ~5.9% of book. Both legs of the written scale-in plan (a first tranche at ~$444.60 and a second at a $421 limit) are already executed, so any further purchase is beyond the original plan. Cash at Interactive Brokers (IBKR) is ~$252 + €773, so adding requires funding or a sale. No action taken. Next decision point is Q3 2026 earnings (October) — a second consecutive sub-guidance print would be the first half of the note's two-quarter thesis-break test, which calls for exit if US da Vinci procedure growth falls below 10% for two consecutive quarters.

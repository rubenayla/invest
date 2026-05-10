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

# Signal Inventory

Living ledger of every trade-signal source the `/feed` dashboard knows about.
Source of truth for the gate registry at `src/invest/signals/gates.py`.

**Default policy: DROP UNBACKTESTED.** A signal must have a curated entry
in `SIGNAL_GATES` with `passes=True` before it surfaces on `/feed`. Every
new signal source needs a row here AND an entry in the registry — even if
the entry is `passes=False` to make the drop intentional.

## Trade-signal sources (gated)

| signal_source | name / regime         | kind | gate_status | reason                                      | next_action                                   |
|---------------|-----------------------|------|-------------|---------------------------------------------|-----------------------------------------------|
| politician    | Tuberville, Tommy     | S    | **PASS**    | +14.2% α @ 365d, p<0.001, n=216 (eff 20)    | re-check 2027-04-30                           |
| politician    | Tuberville, Tommy     | P    | **FAIL**    | −13.3% α @ 180d, p=0.003, n=118             | keep faded                                    |
| politician    | Pelosi, Nancy         | P/S  | UNGATED     | not yet individually backtested              | direction-split backtest                      |
| politician    | Crenshaw, Dan         | P/S  | UNGATED     | not yet individually backtested              | direction-split backtest                      |
| politician    | Gottheimer, Josh      | P/S  | UNGATED     | not yet individually backtested              | direction-split backtest                      |
| politician    | (any other)           | P/S  | UNGATED     | not yet individually backtested              | direction-split backtest if of interest       |
| insider       | cluster_buy           | —    | UNGATED     | not yet backtested                            | event-study on 2+ insider buys ≥ $100K cluster |
| activist      | 13D                   | —    | UNGATED     | not yet backtested                            | event-study on filing date                    |
| activist      | 13G                   | —    | UNGATED     | not yet backtested                            | event-study on filing date                    |
| smart_money   | 13F                   | —    | UNGATED     | not yet backtested                            | per-fund backtest                             |

## Context cards (NOT subject to alpha gate)

These render through their own top-level functions and are NOT trade signals.
They show context for tickers in the user's universe and don't make alpha claims.

| signal_source     | rendered by                    | gate?  | notes                                   |
|-------------------|--------------------------------|--------|-----------------------------------------|
| truth_social      | `_render_trump_signal_cards()` | none   | Trump posts mentioning known tickers    |
| polymarket_policy | `_render_policy_markets()`     | none   | Macro policy probability cards          |

## Narrative cards (NOT gated)

These come from the user's own `notes/companies/*.md` analyses. The user
authored them, so they're not subject to external alpha gating.

| post type | source                              |
|-----------|-------------------------------------|
| intro     | header sentence of the .md          |
| thesis    | "Variant Perception" section        |
| numbers   | "Financial Snapshot" section        |
| bull      | "Bull Case" section                  |
| bear      | "Bear Case" section                  |
| verdict   | "Verdict" section + LLM scenario EV |

## How to add a new signal source

1. Wire the data ingest (DB table or external API) and add a post-build
   step in `_generate_feed_posts()` (`src/invest/dashboard_components/html_generator.py`).
2. Each emitted post MUST carry `signal_source`, `signal_name`, and
   (optionally) `signal_kind` keys so the gate can identify it.
3. Backtest the signal: forward-return alpha vs SPY at multiple horizons,
   p-value vs a control population, effective n adjustment for clustering.
   Save the report under `notes/research/<source>_backtest_<date>.md`.
4. Add a row here AND an entry in `SIGNAL_GATES`. If the backtest doesn't
   support a positive edge, set `passes=False` so the drop is documented.
5. Add tests in `tests/test_signal_gates.py` for the new entry.

## Known limitations

- **No stale-threshold enforcement.** Gate entries don't auto-expire; if an
  alpha decays we have to manually flip `passes` to `False`. Worth adding
  an `assert today - last_backtested_at < 365d` in `evaluate()` later.
- **No drift detector.** A new signal source added to `_generate_feed_posts()`
  without an inventory row will be silently dropped (because `evaluate()`
  returns `None`). The inventory is the manual safeguard. Consider a CI
  check that every `signal_source` value reaching the renderer has an
  inventory row.
- **Senate eFD is not yet ingested.** Tuberville's PASS entry only fires
  if/when his Senate trades show up in `politician_trades`. Currently the
  pipeline only ingests House Clerk PTRs.

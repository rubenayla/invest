<!-- consult selectively — grep, never read in full -->
# Error Log - Invest System

This file tracks mistakes and failures in the investment analysis system and the mechanisms added to prevent recurrence.

## Format
```markdown
## YYYY-MM-DD - Brief title
**What happened:** Description of the error
**Prevention added:**
- List of changes made
- Link to postmortem if applicable
```

---

## 2026-04-23 - Recommended BUY on NOW based on news summaries, missed two material risks
**What happened:** Ran `/research NOW` the evening of 2026-04-22 after earnings. Issued BUY verdict (MEDIUM-HIGH conviction, +28.5% EV) citing "Iran war deal-timing conservatism" as the main headwind. The next day, deeper research revealed two material risks I never mentioned:
1. **US federal government orders crashed 72% to ~$48M** in Q1 due to partial government shutdown halting contract awards. Federal is a large, high-margin segment — bigger and less bounded than the Middle East issue.
2. **Non-GAAP subscription gross margin fell 84.5% → 82.5% YoY** due to AI infrastructure costs (GPU/inference). FY26 guide: 82%. This is structural margin compression, not timing.

I cited Iran war as the headline risk because the news aggregators (CNBC, Benzinga, Bloomberg headline) led with it — but the CFO disclosed Middle East was only a **75 bps headwind** vs. the federal collapse and margin compression which are substantially more damaging to the thesis. User made a real-money decision in part on my analysis.

**Root cause:** The `/research` skill's STEP 0 (news & narrative) does not mandate reading the **primary sources** — the company's earnings press release on IR site, the 10-Q segment/geographic disclosures, and the earnings call transcript. News summaries cherry-pick the punchiest narrative (war) and bury segment-level damage (federal orders, margins). Without reading the primary source, the "bear case" I wrote was reporter-framed, not management-framed.

**Prevention added:**
- `.claude/commands/research.md` STEP 0 updated to REQUIRE fetching the latest earnings press release from `investor.<company>.com` (or IR equivalent) AND reading it before writing any verdict. Specifically: segment revenue breakdown, geographic breakdown, margin commentary, customer concentration, and all "headwinds"/"one-time items" cited by management.
- New explicit rule: the Bear Case section must list **at least one risk NOT in the news headlines** — forcing primary-source engagement. If every bear bullet matches the top news story, flag as "shallow research" and reject the verdict.
- Added: before issuing BUY/WATCH verdict, enumerate ALL quantified headwinds management disclosed with basis-point/dollar sizing, then verify the public narrative matches their size ordering. Discrepancy = investigate further.

---

## 2026-04-13 - Multiple sloppy reasoning errors during macro/timing analysis
**What happened:** During a session investigating prediction markets and "should we buy now or wait," made four conceptual errors in a row, all of which could lead to bad investment decisions if uncaught. User caught each one.

1. **Markdown table column shift.** Wrote a 4-column header but supplied only 3 columns of data per row. Table rendered with shifted/missing values. Always count headers vs cells before sending. Preview multi-column tables mentally (header N == cells N) before output.

2. **Wrong-direction Polymarket query.** User asked "probability Iran war goes bad *again*" (resumption/escalation). Pulled "conflict ends by X" markets — opposite framing. A YES on "ends by April 30" measures de-escalation, not resumption. Always restate the user's question in market-terms before grabbing data: "user wants P(escalation), markets I have measure P(de-escalation). Mismatch — search for different markets or invert."

3. **Buy-now vs wait EV math: missing the lower-entry payoff.** Originally claimed "EV of waiting ≈ -1 to -2%" by counting only opportunity cost (missed drift) and ignoring that buying lower means more shares per dollar → higher terminal value. Correct formula: `wait/buy_now = (1 + cash_yield × t) × P_now / E[P_wait]`. The Pₜ at any future date cancels (both paths hold same asset), so holding horizon is irrelevant — only entry-price ratio + cash yield matter. Always derive the ratio of terminal values explicitly; never compare returns of one path to opportunity cost of another without closing the trade.

4. **Conflated two definitions of "drawdown."** Gave probability-of-dip table where "P(10% dip in 24mo) = 75%" — this is the probability of a drawdown from any peak during the period (definition A). For a buying-opportunity decision, what matters is P(price ≤ 10% below *today's price* at some point) (definition B), which is much lower (~30-35% over 24mo, because market drift means future prices skew higher than today). When discussing "dip from current price," always use definition B and verify the probability is consistent with positive drift.

**Why this matters:** Each error was directionally wrong. Sloppy framing → wrong probability → wrong sizing → real money lost. Quantitative claims need explicit definitions, formulas, and sanity checks before going to user.

**Prevention added:**
- This entry serves as a checklist for any future market-timing / probability / EV analysis: (a) match user's question to the data direction, (b) state definitions explicitly, (c) write formulas before plugging numbers, (d) sanity-check probabilities against drift assumptions, (e) verify table shape (headers == columns) before sending.
- When unsure between two definitions of a probability, compute both and label them clearly rather than picking one silently.

---

## 2026-04-13 - DCF model produced -70 to -97% upside on healthy SaaS growers
**What happened:** Investigating ServiceNow (NOW), the DCF model said fair value $20.52 vs market $88 (-77%). The model used `info['earningsGrowth']` (3.4% — single-quarter GAAP, distorted by SBC) instead of the actual 3-year revenue CAGR (22.4%). Same bug affected AVGO, GOOGL, MSFT, TSLA — any growth company with noisy GAAP earnings or M&A activity. Sample data showed 54% of sp500 names had yfinance `info['revenueGrowth']` differ from computed 3yr CAGR by >5pp; max divergence 220pp on BBT. The model also silently fell back through `earningsGrowth → revenueGrowth → 5% default`, hiding the noise.
**Prevention added:**
- `src/invest/valuation/dcf_model.py:_estimate_growth_rate()` now computes growth from the income statement's `Total Revenue` row (3-year CAGR), with no fallback to noisy yfinance fields. Insufficient history → `ModelNotSuitableError` (model is skipped, not faked).
- Added `_calculate_revenue_cagr()` helper on `DCFModel`. `is_suitable()` and `_validate_inputs()` updated to require `income` data + ≥3 years of revenue.
- All three DCF subclasses (`DCFModel`, `EnhancedDCFModel`, `MultiStageDCFModel`) inherit the fix automatically.
- Result for NOW: fair value $103.65 (DCF) / $131.35 (enhanced) / $72.16 (multi-stage) — in a reasonable ballpark instead of $20-26.
- **Subtle bug along the way:** initial implementation assumed income statement columns were reverse-chronological (latest first). Actual repo convention is chronological (oldest first); confirmed by inspecting `data['income'].columns` for NOW. Fixed by swapping `iloc[0]`/`iloc[-1]` mapping.
- Out of scope (separate follow-ups): same noisy-yfinance bug exists in `tech_model.py:99-100,184` and `ratios_model.py:231-236`. WACC currently assumes 100% equity financing.

---

## 2026-04-13 - update_all.py crashed because SSH tunnel to Hetzner Postgres was not open
**What happened:** User ran `/update`. The data-fetch phase (~25 min) completed, then GBM predictions died with `psycopg2.OperationalError: connection to server at "localhost", port 5433 failed: Connection refused`. Because `subprocess.run(check=True)` in `run_cmd()` aborts on first failure, the entire downstream pipeline (AutoResearch, classic valuations, dashboard regen, opportunity scanner) was skipped. Root cause: model scripts read from Postgres on Hetzner via an SSH tunnel on port 5433, and no tunnel was running on the Mac. AGENTS.md mentioned the tunnel but the command was wrong (`ssh -N hetzner-db &` instead of `ssh -fN -L 5433:localhost:5432 hetzner-db`) and there was no automation.
**Prevention added:**
- `scripts/update_all.py` now calls `ensure_db_tunnel()` at startup, which probes `localhost:5433` and opens the tunnel via `ssh -fN -L 5433:localhost:5432 hetzner-db` if needed (idempotent).
- Updated `AGENTS.md` Database Architecture section with the correct tunnel command and a note that models run on the Mac (not the server) — the website's update button is data-only by design.


**What happened:** System lacked a structured way to track recurring errors and ensure quality before completion.
**Prevention added:**
- Created `error-log.md` (this file).
- Created `definition-of-done.md`.
- Updated `AGENTS.md` to enforce usage of these files.

## 2026-02-09 - `uv run` not usable in sandbox
**What happened:** `uv run python` failed inside the Codex sandbox (permission error accessing the uv cache, and a subsequent uv panic when redirecting cache to `/tmp`).
**Prevention added:**
- For quick one-off data extraction in sandbox, prefer `sqlite3` + `jq` over ad-hoc Python.
- If Python execution is required, request escalated execution or run outside the sandbox environment.

## 2026-03-06 - Ran diagnostics on local machine instead of remote server
**What happened:** User asked to check the SSH bots/scanner on the server. Agent ran all commands locally (macOS), found no issues, and drafted a condescending message to another bot (Mako) telling it the database wasn't malformed — all based on the wrong environment. The local DB is fine; the server DB may genuinely be broken. Agent never asked for SSH connection details before acting.
**Root cause:** Assumed local environment = production environment. Didn't listen to context ("ssh bots") and jumped straight to local execution.
**Prevention added:**
- `ssh bots` is documented in AGENTS.md. When user references bots/server/scanner, run commands there — not locally.
- The SSH alias has been told to the agent many times. Failure to note it in the repo was the compounding error.
- Never draft communications telling others they're wrong based on unverified assumptions.

## 2026-02-09 - Staged/unpushed work caused churn risk
**What happened:** Lots of changes were left staged/unstaged; this increases merge conflict risk when bots/agents also commit to the repo.
**Prevention added:**
- Added `.githooks/pre-push` to block pushing with staged/unstaged changes.
- Added `scripts/finish.sh` to run relevant tests, then commit and push in one step.
- Added `scripts/setup-githooks.sh` and a "Shipped" checkbox in `.agents/definition-of-done.md`.

## 2026-03-20 - Removed CLI flag breaks Hetzner systemd service
**What happened:** A prior commit removed `--no-auto-shutdown` from `dashboard_server.py`'s argparser, but the systemd unit file on Hetzner still passes it. Service crashed with `unrecognized arguments` on restart.
**Root cause:** No check that CLI flags used by production deployment are preserved when refactoring.
**Prevention added:**
- Re-added `--no-auto-shutdown` as accepted (no-op) flag. When removing CLI flags, always check the systemd service file on Hetzner (`/etc/systemd/system/invest-dashboard.service`).

## 2026-03-22 - Deploy didn't restart server, old code served
**What happened:** Pushed new feed page code but Hetzner kept serving the old version. The CI deploy does `git pull` but Python caches imported modules — the dashboard server process kept running with the old `html_generator.py` in memory.
**Root cause:** Deploy pipeline does `git pull` but doesn't restart the systemd service, so stale Python bytecode/modules stay loaded.
**Prevention added:**
- Had to manually `ssh hetzner "sudo systemctl restart invest-dashboard"`. Should add `sudo systemctl restart invest-dashboard` to the CI deploy step after `git pull`.

## 2026-03-22 - f-string brace escaping in non-f-string methods
**What happened:** When writing the feed's `_generate_insights` method, used `{{}}` (f-string escaping) for dict literals and `{{var}}` for f-string expressions inside regular Python methods that were NOT inside an f-string. Caused `TypeError: unhashable type: 'dict'` at runtime.
**Root cause:** The methods were written conceptually as "part of the HTML template" but are actually standalone class methods. The `{{` escaping was cargo-culted from the f-string HTML template above.
**Prevention added:**
- When writing methods that generate content for f-string templates, remember: only the template string itself needs `{{`/`}}` escaping. Helper methods called BY the template are regular Python — use normal `{}`/`{}` syntax.

## 2026-03-23 - Worktree agents save to local SQLite instead of PostgreSQL
**What happened:** Research agents launched with `isolation: worktree` ran `/research TICKER` which saves to DB via `data/stock_data.db` (SQLite path in the script's Step 9). But the actual DB is PostgreSQL over SSH tunnel. The worktree agents either: (a) saved to a local SQLite file that doesn't exist/isn't the real DB, or (b) the SSH tunnel wasn't available in the worktree context. Result: 8 out of 17 deep analyses were missing from the dashboard.
**Root cause:** The `/research` skill's Step 9 uses `sqlite3.connect('data/stock_data.db')` hardcoded, but the real DB is PostgreSQL accessed via `invest.data.db.get_connection()`. Worktree agents inherit the skill template but may not have the SSH tunnel running, and the SQLite path is wrong regardless.
**Prevention added:**
- After running batch research in worktrees, always verify DB entries exist: `SELECT ticker FROM valuation_results WHERE model_name = 'llm_deep_analysis' AND ticker IN (...)`.
- The `/research` skill Step 9 should use `invest.data.db.get_connection()` (PostgreSQL) instead of `sqlite3.connect()`. TODO: update the skill template.
- When launching worktree agents that need DB access, ensure SSH tunnel is running first and consider whether worktree isolation is actually needed (research agents only write to DB + notes files, not code).

## 2026-03-27 - Cron update silently failing for 2.5 weeks (uv not on PATH)
**What happened:** `update_all.py` used `['uv', 'run', 'python', ...]` in subprocess calls. Cron's minimal PATH doesn't include `~/.local/bin`, so every subprocess failed with `FileNotFoundError: 'uv'`. Last successful price data was 2026-03-09. The outer crontab invocation used the full path to uv, but the child processes spawned by the script did not.
**Root cause:** Scripts assumed `uv` is always on PATH. Cron doesn't load `.bashrc`/`.profile`.
**Prevention added:**
- Replaced `['uv', 'run', 'python', ...]` with `[sys.executable, ...]` in `update_all.py` and `run_all_predictions.py`. Since these scripts already run under `uv run python`, `sys.executable` is the correct Python.
- Added `PATH=` line to server crontab as belt-and-suspenders.
- Test `test_update_all.py::TestNoHardcodedUv` scans orchestrator scripts for bare `'uv'` subprocess calls.

## 2026-03-27 - NaN in financial JSON rejected by Postgres
**What happened:** yfinance returns `NaN`/`Infinity` in financial statements. Python's `json.dumps` serializes these as literal `NaN`/`Infinity` tokens, which are not valid JSON. Postgres rejected every INSERT for tickers with missing financial data.
**Root cause:** `data_fetcher.py` called `json.dumps()` directly on dicts containing float NaN values. The migration script (`migrate_data_to_postgres.py`) already had NaN cleaning, but the live fetcher didn't.
**Prevention added:**
- Added `_clean_json()` helper in `data_fetcher.py` that recursively replaces NaN/Infinity with None before serializing.
- Test `test_update_all.py::TestCleanJson` verifies NaN, Infinity, -Infinity are replaced with null and output is valid JSON.

## 2026-03-27 - Kelly position sizer fed available cash instead of total portfolio value
**What happened:** When sizing a FSLR position, ran `run_position_sizer.py FSLR --budget 7766` using only the available cash ($7,766) instead of the total portfolio value (~$46,000). Kelly's 15% max cap applied to $7.7K = $1,140, which is only 2.5% of the real portfolio. The correct sizing was $6,837 (15% of $46K). This would have led to a significantly undersized position — a missed-opportunity cost on a high-conviction pick.
**Root cause:** Confused "cash available to deploy" with "portfolio value for sizing purposes." Kelly sizes positions as a percentage of total capital, not just available cash.
**Prevention added:**
- **Always use total portfolio value as the `--budget` parameter for Kelly sizing**, not just available cash. The budget represents the full capital base that position limits (15% max) are calculated against.
- Available cash only determines whether you *can* fill the recommended size, not the size itself.
- This error can directly cost money (undersized winners, oversized losers). Double-check the budget input on every sizing call.

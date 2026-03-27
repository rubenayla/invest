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

## 2026-02-08 - Initial Workflow Setup
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

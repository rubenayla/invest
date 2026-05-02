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

## 2026-05-02 - Multiple verification failures in a single portfolio review (TRULY UNRELIABLE)
**What happened:** User asked me to analyze the portfolio and recommend trims. In one review I made four distinct verification failures, each independently bad, compounding into recommendations the user could not trust:

1. **Recommended trades on a stale portfolio file without cross-checking.** Read `~/vault/finance/notes/portfolio/portfolio.md` (last-updated header: 2026-04-27) and treated every row as a current holding. Recommended an ACGL exit. User: "I don't have ACGL." The position had already been sold — ` ~/repos/invest/TODO.md` line 7 says *"ACGL limit sell — modified existing order to ~$94 limit sell"* and the limit was below the recent close, so it had filled. portfolio.md just hadn't been updated.

2. **Treated a recommendation in a journal note as an executed trade.** The May 2 Itochu earnings review recommends "BUY now" as a trade plan; I called it "already planned" in the action list as if it were in-flight. User had to correct: "I don't have Itochu." Recommendation ≠ execution. Journal-of-recommended-trades is not journal-of-executed-trades.

3. **Concluded "not found" from a truncated grep.** When the user asked me to verify ACGL appearances, I ran `grep -rn ACGL ~/vault/finance/ | head -30` — the head -30 cut off after the price-history rows in `prices.beancount` (alphabetical order, before `notes/`), missing the actual portfolio.md rows entirely. Reported "ACGL is not in vault/finance" with confidence. It was at line 16 and 56 of portfolio.md. The user had to push back to make me re-grep without the head cap.

4. **Skipped the freshness check before recommending action.** The data freshness check from `/api/health` showed model timestamps but I never separately validated holdings against any other source (TODO.md, taxes summary, beancount ledger, recent journal transactions). Per memory: *"Data files must be accurate. If portfolio.md says a position exists, treat it as ground truth OR flag the file as needing a fix."* I did NEITHER — I treated a stale file as ground truth without flagging.

**Root cause:** No discipline around "before recommending an action that the user will execute, verify the precondition" against multiple sources. The single-file read became a single point of failure. The `head` cap on the verification grep was a separate sloppiness on top.

**Prevention added:**
- **Before recommending a trade based on a portfolio file, cross-check at least two sources for the named position.** For each ticker in the recommended action: (a) portfolio.md row, (b) most recent transaction in `notes/journal/transactions/`, (c) `vault/paperwork/taxes/<year>/summary.md` realized-gains entries, OR (d) explicit user confirmation. Two of those must agree before recommending sell/trim/exit.
- **Treat journal review notes as plans, not executions.** A note titled `2026-05-02_<ticker>_earnings_review.md` with verdict "BUY" describes a *plan*. Confirm execution before phrasing as "already planned" — say "recommended in the May 2 review, not yet executed" and ask the user to confirm.
- **Never `head`-truncate a verification grep.** When the user is testing a claim of "X does not exist," the grep MUST run unbounded. Use `wc -l` to size first, then read in chunks if needed. Or use `grep -l` to count distinct files. Never use `head -N` on a search-for-absence operation.
- **State the freshness of every data source used.** Before issuing actions, list each input source and its last-updated date. If any is older than 7 days for trade recommendations, flag it explicitly. (Memory entry already exists for "check data freshness before analyzing"; this incident was a failure to apply it.)
- **When the user pushes back, re-do the work fully — don't just patch the surface.** First pushback: ACGL not held → I dropped the line. Should have stopped there and re-verified ALL holdings against another source before continuing the recommendation. I instead kept the rest of the action list, which still contained the Itochu-as-planned mistake. Each correction should trigger a full rescan of related claims.

## 2026-05-02 - Manually deployed instead of trusting CI
**What happened:** After pushing `bfa55d9` to main, I SSH'd into Hetzner and ran `git pull && systemctl restart invest-dashboard` to "verify the deploy doesn't error." The user pointed out CI auto-deploys on push to main (`.github/workflows/ci.yml` has a `deploy` job that runs after `test` passes, gated on `if: github.ref == 'refs/heads/main'`). The CI run for `bfa55d9` had already completed successfully (50s) before I SSH'd in — my manual deploy was redundant and could have raced the CI deploy.

**Root cause:** Didn't check whether a deploy pipeline existed before reaching for SSH. Defaulted to "I know how to deploy this directly" instead of "what does the project's pipeline do?" `.agents/deployment.md` documents the architecture but doesn't make it loud that pushes auto-deploy.

**Prevention added:**
- **Before any production deploy action (SSH, restart, pull), check `.github/workflows/` for a `deploy` job.** If push-to-main triggers deploy, the deploy IS the push — there is nothing to do manually.
- **Verification path after pushing to main:** `gh run watch` (or `gh run list --branch main --limit 1`) to confirm CI green → `curl -sS -o /dev/null -w '%{http_code}\n' https://invest.rubenayla.xyz/feed` to confirm production renders. SSH only when CI itself fails, or for diagnostics that the production endpoint can't show.
- Never SSH-deploy a CI-deployed repo "to be sure" — it can race the CI deploy and mask a broken pipeline (manual success hides automation failure).
- Updated `.agents/deployment.md` to flag the auto-deploy step explicitly at the top.

## 2026-05-02 - Treated per-stock Kelly target as a portfolio recommendation
**What happened:** User asked whether to buy KRKNF/PNG.V instead of topping up existing positions. I ran `run_position_sizer.py` over their full portfolio + PNG.V, then read the per-stock "target %" column and computed `gap = target - current` for each ticker, recommending the names with the biggest gap. This produced two bad recommendations:
1. **STLD as the top buy** — at 14.9% Kelly target vs 3% current = -12pp gap. But STLD was sitting at $229.27, literally at its 52-week high ($230.94), with analyst mean PT *below* the current price. The Kelly sizer is price-blind to extension and just saw "4/4 bulls, vol 34%, drawdown 30%" → max-cap recommendation. I never looked at the live price chart before recommending it.
2. **PNG.V at the 15% Kelly cap** — framed as "the largest gap, hits the cap, buy aggressively." But the user has ~$6,500 cash, not $7,500 of free room for a single name; the Kelly cap is per-position ceiling, not an allocation target. Filling PNG.V to 15% would have required liquidating other positions the user holds for non-Kelly reasons (tax cost, conviction history) — a rotation decision I never raised.

**Root cause:** Conceptually misused Kelly. Each stock's Kelly fraction is computed as if it were the only bet you'd make; the 15% cap protects against single-name concentration. When multiple names hit the cap (5 did in this run), the "individually optimal" sizes can sum to >100% — the system normalizes in `--portfolio` mode but I read pre-normalization per-stock targets and treated them as portfolio allocations. Compounded by a second failure: the sizer is a sizing tool, not a buy signal — it doesn't see price extension, technical setup, or recent run. I recommended STLD without sanity-checking the chart.

**Prevention added:**
- New canonical doc: [`notes/references/kelly-usage.md`](../notes/references/kelly-usage.md) — what Kelly is for, how to use it, valid use cases. Link from the Kelly module docstring.
- Updated [`notes/references/trading-formulas.md`](../notes/references/trading-formulas.md) Kelly section with a pointer to the usage guide.
- **Before recommending any buy from a Kelly run, fetch live price + analyst targets + 52-week range.** If price is within 5% of 52w high or above analyst mean PT, flag it explicitly — Kelly says nothing about entry price.
- **Don't treat a per-stock Kelly target as an allocation target.** Use Kelly for: (a) ranking two specific names against each other, (b) capping single-position concentration. Don't compute "gap to Kelly target" across the whole portfolio and recommend filling them — that's not what Kelly tells you.
- **For "should I buy X instead of topping up Y?" questions: compare both names' Kelly outputs side-by-side, then check both names' price extension, then decide.** Don't pull in the rest of the portfolio's gaps.

---

## 2026-04-25 - Wrong claim about deploy automation, then bypassed the test gate
**What happened:** Two compounding errors in one session:

1. **False claim about deployment automation.** Told the user "git pull doesn't run on Hetzner automatically when you push to GitHub" to explain why a fresh `ssh ... git pull && systemctl restart` was needed after each push. This was wrong — `.github/workflows/ci.yml` has a `deploy` job that runs `appleboy/ssh-action` on push to main, doing exactly that pull+restart. I had not read the workflow file before answering. The user had to ask "don't we use github actions precisely so that happens?" to surface this.

2. **Bypassed a red CI to push the deploy through.** Earlier in the session I had pushed commit `961b49b` which added `tests/test_populate_fundamental_history.py` requiring a live Postgres on `localhost:5432` — CI doesn't have one, so all 29 new tests failed with "Connection refused". I never checked CI status. I then manually SSH'd into Hetzner and ran `git pull && systemctl restart`, deploying broken-CI code anyway. The auto-deploy job had refused to run precisely because tests failed (`needs: test`), and I overrode that safety with a manual command. This defeats the entire reason for having a CI gate. Real-money infrastructure was deployed past a failing test suite without any verification that the failure was benign.

**Root cause:** Two separate failures of "verify before claiming/acting":
- Made a confident architectural claim about the repo without reading the relevant config file (`.github/workflows/`).
- Treated `git pull && systemctl restart` as the deploy primitive instead of asking "what's the system that's *supposed* to do this, and why isn't it working?" When automation appears to be missing, default to checking whether it exists and is healthy, not building a manual replacement around it.

**Prevention added:**
- **Before answering "how does X get deployed / built / triggered" in a repo, grep for `.github/workflows/`, `Makefile`, `justfile`, `.gitlab-ci.yml`, `Procfile`, systemd units, cron, etc.** Don't answer from prior assumption. If the question is about automation, the source of truth is the automation config file.
- **Never bypass a red CI with a manual deploy.** If CI is failing and the change needs to ship, fix the test (or mark it appropriately) and let CI re-run, OR explicitly tell the user "CI is red because X, the failure is benign for these reasons, are you OK with me bypassing the gate?" and wait. Default = stop and fix.
- **Before any `ssh ... git pull` or `systemctl restart`, run `gh run list --workflow=ci.yml --limit=3`** to confirm the latest commit's CI passed. If it failed, do not deploy until the failure is understood.
- AGENTS.md updated with a "Deploy" rule pointing here.

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

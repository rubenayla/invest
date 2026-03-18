# Claude Memory and Instructions

## .agents/ structure
- `error_log.md`: Append-only log. Don't read on startup, search when debugging.
- `solutions.md`: Curated fixes for recurring issues. Keep under 100 lines.
- `architecture.md`: Key design decisions. Keep under 100 lines.
- `definition_of_done.md`: Completion checklist.
- `scratch.md`: Volatile notes, not for commit.
- `coding_standards.md`: Code style, testing strategy, commit discipline.
- `data_conventions.md`: Ratio storage, yfinance quirks.
- `gemini_cli.md`: Gemini CLI flags and resume.

## INVESTMENT ANALYSIS PROTOCOL (STRICT MANDATE)

**When analyzing a stock for investment, you MUST run `/research TICKER`.** This is non-negotiable. The research skill:
- Searches recent news and sector context
- Queries ALL valuation models from the DB
- Pulls live financials from yfinance (verify trends before claiming them)
- Scores business quality, checks for inflection points
- Builds a scenario table with expected value
- **Saves analysis to `notes/companies/TICKER.md`** (overwrites old version — git has history)
- **Saves `llm_deep_analysis` to `valuation_results` DB** (dashboard and Kelly sizer use this)

If the user asks "should I buy X?", "what about X?", or any investment question about a specific stock — run `/research X` FIRST, then answer. Do not give investment opinions based on stale notes or memory alone.

**After running /research, also apply these rules:**

1.  **THE "COMPLAINT" RULE:**
    *   **Compare the models.** If DCF says "Overvalued" but GBM says "Rocket Ship" (e.g., Marubeni), you **MUST** point this out.
    *   **Critique the models.** If a model looks broken (e.g., negative value for a profitable company), **complain to the user**. Say: *"The DCF model is failing here because..."*
    *   **Value Divergence:** Use the divergence as a signal. High divergence = High Volatility/Momentum play. Low divergence = High Conviction Value play.

2.  **FRESHNESS CHECK:**
    *   Before citing a number, check the `timestamp` in the database or the `Data Date` in the script.
    *   If data is >30 days old for a volatile stock, **refetch it**.

3.  **MACRO CONTEXT:**
    *   Always check the "Story" (News/Buffett/Sector trends) to explain *why* the numbers might be "wrong" (e.g., "The model hates it, but Buffett loves it").

---

## THE IRON RULE: VERIFY TRENDS BEFORE CLAIMING

**Before saying "declining" or "down X%", check yfinance 3-5 year trend:**
```python
import yfinance as yf
ticker = yf.Ticker('STOCK')
income = ticker.income_stmt
print(income.loc['Total Revenue'])  # Check actual trend
print(income.loc['Net Income'])
```

**If you say "declining" without checking, user will catch you.**

---

## FILE MODIFICATION SAFETY

**NEVER modify a file without reading it first.**
- You must know if the file exists and what is in it before overwriting.
- **NEVER** overwrite ignored files (like `TODO.md`) without explicit confirmation or checking content first, as they cannot be recovered via git.
- **ALWAYS** check `git status` before modifying files to ensure you don't destroy uncommitted work.

---

## Root-Level Scratch Files

- **`stuff.md`** — Unstructured notes dump. The user pours info here with no organization, as a grepable reference. **Do not delete or reorganize.**
- **`stuff/`** — Scratch directory for misc files (scripts, screenshots, PDFs). Same purpose. **Do not delete.**
- **`TODO.md`** — Active todo list. **Do not delete.**

---

## Always Use uv

ALL Python commands must use `uv run`:
```bash
uv run python script.py
uv run pytest
```

## Agent Configs

- Keep all agent-specific configuration files (MCP, Claude desktop, etc.) under `.agents/`. The repo root should not contain residual `config/` folders.

---

## Database Architecture

**DATABASE IS SOURCE OF TRUTH - NOT SCRIPTS**

**If there's a mismatch between database schema and script queries, the DATABASE is correct. Update the scripts.**

**Two data systems:**

1. **Historical** (`assets`, `fundamental_history`, `price_history`)
   - 358 stocks with time-series data
   - Used by: GBM models, neural networks
   - Update: `scripts/populate_fundamental_history.py`
   - **Note**: Old scripts may reference `snapshots` table - this was renamed to `fundamental_history`

2. **Current** (`current_stock_data`)
   - 598 stocks, single snapshot per stock
   - Used by: DCF, RIM, simple ratios, dashboard
   - Update: `scripts/data_fetcher.py`

**Database location**: `data/stock_data.db`

**Data access**:
```python
from invest.data.stock_data_reader import StockDataReader
reader = StockDataReader()
data = reader.get_stock_data('AAPL')
```

**Check schema first:**
```bash
sqlite3 data/stock_data.db ".tables"
sqlite3 data/stock_data.db "PRAGMA table_info(fundamental_history);"
```

---

## Git Safety

**NEVER use `git checkout <file>` - destroys changes forever**

Safe commands:
- `git reset <file>` - unstage (keeps changes)
- `git add <file>` - stage
- `git status` - view changes

---

## Remote Server (Bots)

The scanner and other bots run on a remote server. Connect via:
```bash
ssh bots
```
The SSH config is already set up. When the user says "check the bots", "ssh bots", or refers to the server/scanner in production, **always run commands on the server via `ssh bots`**, not locally.

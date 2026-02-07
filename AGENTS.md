# Claude Memory and Instructions

## 📚 KEY FILES (READ FIRST)
Before performing tasks, consult:
1. **`.agents/error_log.md`** - History of failures and prevention.
2. **`.agents/definition_of_done.md`** - Checklist for completion.

## 🚨 INVESTMENT ANALYSIS PROTOCOL (STRICT MANDATE)

**When analyzing a stock for investment, you MUST follow this "Triangulation" workflow:**

1.  **CHECK EXISTING MODELS FIRST:**
    *   Query the `valuation_results` table in `data/stock_data.db`.
    *   Look for **ALL** model types: `dcf`, `gbm_opportunistic_1y`, `multi_horizon_nn`.
    *   *Do not just run a fresh DCF script and ignore the rest.*

2.  **THE "COMPLAINT" RULE:**
    *   **Compare the models.** If DCF says "Overvalued" but GBM says "Rocket Ship" (e.g., Marubeni), you **MUST** point this out.
    *   **Critique the models.** If a model looks broken (e.g., negative value for a profitable company), **complain to the user**. Say: *"The DCF model is failing here because..."*
    *   **Value Divergence:** Use the divergence as a signal. High divergence = High Volatility/Momentum play. Low divergence = High Conviction Value play.

3.  **FRESHNESS CHECK:**
    *   Before citing a number, check the `timestamp` in the database or the `Data Date` in the script.
    *   If data is >30 days old for a volatile stock, **refetch it**.

4.  **MACRO CONTEXT:**
    *   Always check the "Story" (News/Buffett/Sector trends) to explain *why* the numbers might be "wrong" (e.g., "The model hates it, but Buffett loves it").

---

## 🚨 THE IRON RULE: VERIFY TRENDS BEFORE CLAIMING

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

## 🛑 FILE MODIFICATION SAFETY

**NEVER modify a file without reading it first.**
- You must know if the file exists and what is in it before overwriting.
- **NEVER** overwrite ignored files (like `todo.md`) without explicit confirmation or checking content first, as they cannot be recovered via git.
- **ALWAYS** check `git status` before modifying files to ensure you don't destroy uncommitted work.

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

**🚨 DATABASE IS SOURCE OF TRUTH - NOT SCRIPTS**

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

## Testing Strategy

**When to run tests locally:**
- Logic changes in core modules: `uv run pytest`
- Testing-specific changes: `uv run pytest tests/test_file.py`
- Major refactoring: `uv run pytest`
- Skip tests for: docs, configs, small UI tweaks (let CI handle it)

**After pushing:**
- Check CI status: `gh run list --limit 1`
- If CI fails: `gh run view --log-failed` to see details

**Commit discipline:**
- Keep commits small: <100 lines changed
- One issue per commit
- Never refactor multiple files at once

---

## Coding Standards

- Single quotes: `'hello'`
- Type hints always
- Numpydoc docstrings
- Guard clauses (early returns)
- Use `@pytest.mark.parametrize` for test variations

---

## Data Conventions

**Ratios stored as ratios, not percentages:**
- Store: `0.93` (not `93`)
- Multiply directly: `debt * 0.93`

**yfinance returns `debtToEquity` as percentage, so calculate manually:**
```python
debt_to_equity = total_debt / (book_value * shares_outstanding)
```
Location: `scripts/data_fetcher.py:289-299`

---

## Gemini CLI Context

**Resume Capability**
The CLI supports resuming previous sessions. This restores conversation history but check `AGENTS.md` or status files for project context.
- `gemini --resume` (or `-r`) resumes the latest session.
- `gemini --resume <index>` resumes a specific session.
- `gemini --list-sessions` lists available sessions.

**Other Useful Flags**
- `--yolo`: Automatically accepts all tool calls (use with caution).
- `--sandbox`: Runs in a sandbox environment.
- `--prompt-interactive` (`-i`): Execute a prompt and continue interactively.

# Claude Memory and Instructions

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

## Always Use uv

ALL Python commands must use `uv run`:
```bash
uv run python script.py
uv run pytest
```

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

## Commit Discipline

1. Run tests: `uv run pytest` (ALL must pass)
2. Run linter: `uv run ruff check src tests --select=E9,F63,F7,F82`
3. Keep commits small: <100 lines changed
4. One issue per commit

**NEVER:**
- Commit failing tests
- Refactor multiple files at once
- Change >100 lines in one commit

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

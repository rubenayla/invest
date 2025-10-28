# Claude Memory and Instructions

## CRITICAL REMINDER: Always Use uv

⚠️ **IMPORTANT**: This project uses uv dependency management. ALL Python commands must be prefixed with `uv run`.

## 📊 DATA CONVENTIONS

### Ratios are Ratios, Not Percentages
**Convention**: Store all ratios as ratios (0.93), NOT percentages (93)

**Why:**
- More programmer-friendly (can multiply directly: `debt * 0.93`)
- Cleaner in calculations
- Avoids confusion between 0.93 and 93%

**Important:** yfinance returns `debtToEquity` as percentage (92.867), so we calculate it ourselves:
```python
debt_to_equity = total_debt / (book_value * shares_outstanding)
```
**Location:** `scripts/data_fetcher.py` lines 289-299

## 🚫 NEVER Touch User's Personal Files

⚠️ **CRITICAL**: `todo.md`, `notes/watchlist.md`, and similar files are the USER'S personal notes - NOT Claude's!

**NEVER**:
- Read `todo.md` unless user explicitly asks
- Treat `todo.md` as tasks for Claude
- Assume `todo.md` contains instructions
- ❌ **NEVER use `git checkout <file>`** - this DESTROYS uncommitted changes permanently
- ❌ **NEVER try to "clean up" or "revert" user's personal files**

**LESSON LEARNED: The watchlist.md Data Loss Incident**
- Ran `git checkout notes/watchlist.md` thinking it would "unstage" the file
- Actually DESTROYED all uncommitted user changes permanently
- User's watchlist data was lost and could not be recovered
- **What I should have done**: Just left the file alone, or used `git reset notes/watchlist.md` (safe, keeps changes)
- **Core lesson**: `git checkout <file>` destroys data. Never use it.

**ALWAYS**:
- Use the TodoWrite tool for tracking Claude's work (displayed in UI)
- Ask user for clarification if unsure what to work on
- Read `notes/` and `docs/` directories - they contain useful project information
- **If you see personal files staged**: Either ignore them or ask user what to do - NEVER checkout/revert

```bash
# Wrong:
python scripts/systematic_analysis.py
pytest

# Correct:
uv run python scripts/systematic_analysis.py
uv run pytest
```

## CRITICAL LESSON: The ab0fe64 Disaster

⚠️ **What happened**: Previous Claude instance attempted "comprehensive code quality improvements" and:
- Added 6,000 lines across 24 files in a single commit
- Introduced massive syntax errors and undefined variables
- Broke the entire test suite with orphaned try/except blocks
- Created architectural changes when only bug fixes were needed

## IRON RULES - Never Break These:

1. **ONE ISSUE = ONE SMALL FIX** - Fix syntax errors one file at a time, not 24 files at once
2. **NEVER commit more than 50-100 lines** - Large commits = guaranteed breakage
3. **Test after EVERY change** - If tests fail, stop and fix before continuing
4. **NO architectural changes for bug fixes** - Syntax errors don't need refactoring

## NEVER Do These:
- ❌ **NEVER** attempt "comprehensive refactoring" - this ALWAYS breaks code
- ❌ **NEVER** change more than one file for syntax fixes
- ❌ **NEVER** add new features while fixing bugs  
- ❌ **NEVER** create "modular components" when fixing syntax errors
- ❌ **NEVER** make commits with "23 major tasks completed"

## Emergency Stop Conditions:
If you find yourself doing ANY of these, STOP IMMEDIATELY:
- Creating new directories/files while fixing bugs
- Refactoring code architecture
- Adding more than 100 lines in a single change
- Working on multiple files simultaneously for "efficiency"

## COMMIT DISCIPLINE - Mandatory Rules

### 🚨 CRITICAL: GitHub Actions Test Requirement
**ALL TESTS MUST PASS BEFORE COMMITTING** - GitHub Actions will catch failures and send email alerts!
- Run the FULL test suite: `uv run pytest`
- If any tests fail, either:
  - Fix the code causing the failure
  - Update the test if the expected behavior has changed (and inform the user)
- NEVER commit with failing tests - this breaks CI/CD and triggers email alerts

### Before Every Commit:
1. **Run the linter**: `uv run ruff check src tests --select=E9,F63,F7,F82`
2. **Check for syntax errors**: Must pass with zero errors
3. **Run FULL test suite**: `uv run pytest` - ALL tests must pass (not just relevant ones)
4. **Verify changes are minimal**: `git diff --stat` should show reasonable line counts
5. **Confirm test status**: If any tests need updating, inform the user BEFORE committing

### Good Commit Examples:
```
Fix syntax error in monte_carlo_dcf.py line 175
- Remove orphaned except block
- Fix indentation issue

Files changed: 1, +2/-5 lines
```

### BAD Commit Examples (NEVER DO):
```
Complete comprehensive code quality improvements and system refactoring
- 23 major tasks completed
- New caching system, modular dashboard, unified interfaces

Files changed: 24, +5983/-13 lines  ← THIS IS A DISASTER
```

### Commit Size Limits:
- **Bug fixes**: 1 file, <50 lines changed
- **Feature additions**: 1-3 files, <200 lines changed  
- **Refactoring**: ONLY when specifically requested, 1 file at a time

## Remember: The user values WORKING CODE above all else. Broken code helps nobody.

## Current Status: Test Suite Partially Broken

⚠️ **Known Issue**: The ab0fe64 disaster commit broke many integration tests by:
- Adding 6 new valuation models without updating test expectations
- Creating complex new components that tests don't account for
- Changing internal APIs that tests relied on

### ✅ ALL TESTS FIXED (15/15 passing - 100% success rate):
- ✅ `test_model_registry_initialization` - Updated to expect 11 models instead of 5
- ✅ `test_model_suitability_detection` - Fixed by model name corrections  
- ✅ `test_valuation_engine_with_unified_models` - Updated expected model list
- ✅ `test_complete_valuation_workflow` - Fixed registry stats by using global registry
- ✅ `test_network_error_resilience` - Added cache clearing for proper test isolation
- ✅ `test_performance_benchmarks` - Removed non-existent fixture dependencies
- ✅ `test_valuation_model_execution_with_mocked_data` - Fixed cache interference + added missing mock data
- ✅ Fixed `ModelNotSuitableError` initialization issues in rim_model.py and base.py

## 🎉 COMPLETE RECOVERY ACHIEVED

From ab0fe64 disaster (6,000 lines, 24 files, massive failures) to 15/15 passing tests using:
- Small, focused commits (8 separate commits)
- Incremental debugging principles  
- Proper test isolation and cache management
- Following our own IRON RULES

### Approach for Test Fixes:
1. **Only fix tests when they block real work** - don't fix all tests at once
2. **One test at a time** - separate commits for each test fix  
3. **Document what was changed and why** - help future debugging

---

## CODING STANDARDS - Mandatory Style Rules

### ✅ Code Style Requirements:
- **Single quotes for strings**: `'hello'` not `"hello"`
- **uv + pyproject.toml**: PEP 621-compliant dependency management
- **Ruff linter**: Use for code formatting and linting
- **Numpydoc docstrings**: Standard format for function documentation
- **Type hints**: Always include type annotations

### ✅ Code Structure Rules:
- **Guard clauses**: Use early returns to avoid deep indentation
  ```python
  # Good
  def process_data(data):
      if not data:
          return None
      if len(data) < 5:
          return []
      # main logic here
  
  # Bad 
  def process_data(data):
      if data:
          if len(data) >= 5:
              # main logic buried in nested conditions
  ```

- **NEVER use nested conditionals after assertions**: Assertions handle edge cases completely
  ```python
  # Good
  assert data is not None, "Data cannot be None"
  # Continue with main logic - no if/else needed
  
  # Bad
  assert data is not None, "Data cannot be None" 
  if data:  # ← This is redundant after assertion
  ```

### ✅ Test Standards:
- **Independent test functions**: Each test should run in isolation
- **Use parameters**: Avoid rewriting similar tests, use `@pytest.mark.parametrize`
  ```python
  @pytest.mark.parametrize('model_name,expected_fields', [
      ('simple_ratios', ['currentPrice', 'trailingEps']),
      ('dcf', ['currentPrice', 'sharesOutstanding']),
  ])
  def test_model_requirements(model_name, expected_fields):
      # Single test handles multiple cases
  ```

---

## DATABASE ARCHITECTURE - Critical Information

### 🚨 **DUAL DATA SYSTEMS - BOTH ACTIVELY USED**
**The database has TWO complementary data systems serving different purposes:**

#### **System 1: Historical Time-Series (assets/fundamental_history/price_history tables)**
- **Purpose**: Multi-period analysis with price + fundamental history
- **Tables**:
  - `assets` (451 stocks registered)
  - `fundamental_history` (17,840 rows - fundamentals per date per stock)
  - `price_history` (753,940 rows - daily prices)
- **Structure**: Multiple rows per stock (time-series data)
- **Date Range**: 2006-01-03 to 2025-08-31 (fundamental_history)
- **Coverage**: 358 stocks with complete historical data
- **Used By**: GBM models (require lag/rolling features), neural networks, backtesting
- **Last GBM Run**: Oct 23, 2025 (312 stocks)
- **Update Script**: `scripts/populate_fundamental_history.py` or SEC Edgar scripts

#### **System 2: Current Point-in-Time (current_stock_data table)**
- **Purpose**: Current fundamentals for traditional valuation models
- **Table**: `current_stock_data` (598 rows - one per stock)
- **Structure**: Single row per stock (current snapshot)
- **Last Updated**: Oct 23, 2025
- **Coverage**: 598 stocks (S&P 500 + international)
- **Used By**: DCF models, RIM, simple ratios, value screening, dashboard
- **Last DCF Run**: Oct 23, 2025 (598 stocks)
- **Update Script**: `scripts/data_fetcher.py`

#### **Key Differences:**
| Feature | Snapshots | Current Stock Data |
|---------|-----------|-------------------|
| Rows per stock | Many (time-series) | One (point-in-time) |
| Stock count | 358 stocks | 598 stocks |
| Update frequency | ⚠️ Needs update | ✅ Recently updated |
| Used for | GBM/ML models | DCF/traditional models |
| Data structure | Historical trends | Latest fundamentals |

#### **Stock Coverage Overlap:**
- **321 stocks** in BOTH systems → All models work
- **277 stocks** ONLY in `current_stock_data` → DCF/RIM work, GBM does NOT
- **37 stocks** ONLY in `assets` → GBM works, DCF may not

### 📍 **Primary Database Location**
**Path**: `data/stock_data.db` (1.4GB SQLite database)

### ⚠️ **Why GBM Models Don't Work on All Stocks**
**GBM models need historical time-series from `fundamental_history` table (358 stocks available).**
**DCF models need current fundamentals from `current_stock_data` table (598 stocks available).**

**Common issue**: Many value stocks (ACGL, SYF, MOH, VALE, EMN, TAP, PHM, BG) are only in `current_stock_data`, so:
- ✅ DCF/RIM valuations available
- ❌ GBM predictions NOT available (no historical fundamental data)

**Solution**: Run `scripts/populate_fundamental_history.py` or update via SEC Edgar to add missing stocks to fundamental_history table.

### 🏥 **Database Health Monitoring**

**Script**: `scripts/check_database_health.py`

**Run regularly** to monitor database quality and catch issues early:

```bash
uv run python scripts/check_database_health.py
```

**What it checks:**
1. **Table Coverage** - Stock counts across all tables
2. **Data Freshness** - How old the data is (warns if >7 days, alerts if >30 days)
3. **Coverage Gaps** - Stocks missing from assets/snapshots (can't use GBM)
4. **Model Coverage** - Which valuation models work for which stocks

**Exit codes:**
- `0` = Healthy (all checks pass)
- `1` = Issues found (missing data, stale data)
- `2` = Error during check

**Recommended workflow:**
- Run health check **before** running valuations
- Run health check **after** fetching new data
- Run health check **weekly** to catch data staleness

**Example output:**
```
❌ ISSUES FOUND:
  1. 41 stocks in current_stock_data but not in assets - GBM models unavailable

⚠️  WARNINGS:
  1. Fundamental history is 58 days old - run populate_fundamental_history.py
```

**Automation**: Add to GitHub Actions or cron job to get automatic alerts.

### 📊 **What's in the Database**

#### `current_stock_data` Table
The **single source of truth** for all current stock data. Contains:

**Basic Info**: ticker, current_price, market_cap, sector, industry, long_name, short_name, currency, exchange, country

**Financial Ratios**: trailing_pe, forward_pe, price_to_book, return_on_equity, debt_to_equity, current_ratio, revenue_growth, earnings_growth, operating_margins, profit_margins

**Fundamental Data**: trailing_eps, book_value, total_cash, total_debt, shares_outstanding, total_revenue, revenue_per_share, price_to_sales_ttm

**Price Data**: price_52w_high, price_52w_low, avg_volume, price_trend_30d

**JSON Blobs** (for complex data):
- `cashflow_json`: Historical cash flow statements (list of dicts)
- `balance_sheet_json`: Historical balance sheets
- `income_json`: Historical income statements
- `info_data`: Full yfinance info dict
- `financials_data`: Additional financial metrics

**Meta**: fetch_timestamp, last_updated

### 🔧 **How to Access Data**

Use `StockDataReader` class:
```python
from invest.data.stock_data_reader import StockDataReader

reader = StockDataReader()
data = reader.get_stock_data('AAPL')  # Returns dict with 'info', 'financials', 'cashflow', etc.
```

### ⚠️ **CRITICAL: Data Structure for Valuation Models**

The `StockDataReader` returns data in a specific format for compatibility with valuation models:

```python
{
    'ticker': 'AAPL',
    'info': {
        # Basic fields + CRITICAL fields for traditional models
        'currentPrice': 150.0,
        'sharesOutstanding': 15000000000,  # ← MUST be in 'info' for DCF/RIM models
        'totalCash': 50000000000,          # ← MUST be in 'info'
        'totalDebt': 100000000000,         # ← MUST be in 'info'
        'trailingEps': 6.5,                # ← MUST be in 'info'
        'bookValue': 3.5,                  # ← MUST be in 'info'
        'freeCashflow': 90000000000,       # ← Extracted from cashflow_json
        'operatingCashflow': 100000000000, # ← Extracted from cashflow_json
        ...
    },
    'financials': {
        # Same critical fields repeated for compatibility
        # Plus additional ratios
        ...
    },
    'cashflow': [...],  # List of historical cash flow dicts
    'balance_sheet': [...],
    'income': [...],
}
```

**Why duplicate fields?**
- The `info` vs `financials` split is **artificial** - created by `data_fetcher.py` to organize data from yfinance's single `stock.info` dictionary
- yfinance provides ONE dictionary with all fields mixed together
- `data_fetcher.py` splits it into: `info` (company identity) and `financials` (performance metrics)
- Traditional models (DCF, RIM, Simple Ratios) look in `info` section
- Neural network models look in `financials` section
- We duplicate critical fields in BOTH sections so all models can find them
- **This split is arbitrary and historical** - could be unified but would require updating all models

### 📁 **Legacy/Backup Data**

- `data/stock_cache_backup/`: JSON backups (435 files, ~17MB) - kept as safety net
- `data/stock_cache/*.json`: **DELETED** - redundant with SQLite

### 🔄 **Data Flow**

1. **Fetching**: `scripts/data_fetcher.py` → Calls yfinance → Saves to SQLite via `save_to_sqlite()`
2. **Reading**: Models → `StockDataReader` → Returns formatted dict from SQLite
3. **Valuation**: Models → Use `info` section for critical fields → Calculate valuations

### 🚨 **Common Pitfall: Missing Data**

If a stock shows "no data" from traditional models but has data in the database:
1. Check if critical fields are in the `info` section (not just `financials`)
2. Check if `freeCashflow`/`operatingCashflow` are being extracted from `cashflow_json`
3. Verify `StockDataReader` is putting fields in both sections

---

## DASHBOARD ARCHITECTURE

### 📍 **Single Dashboard Location**
**Path**: `dashboard/valuation_dashboard.html` (static HTML file)

**Generated by**: `scripts/regenerate_dashboard_html.py`

### ⚠️ **Deleted**: Server-based dashboard (`scripts/dashboard_server.py`)
- Was 1520 lines of outdated code
- Missing new features (5 NN horizons, company tooltips)
- Static HTML is faster, cleaner, and easier to maintain

### 📊 **Dashboard Features**
- Shows 5 separate neural network time horizons: 1m, 3m, 6m, 1y, 2y
- Company name tooltips on ticker hover
- Color-coded margin of safety
- All traditional valuation models (DCF, Simple Ratios, RIM, etc.)

---

📋 **For project-specific details, see PROJECT.md**
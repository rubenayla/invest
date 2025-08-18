# Claude Memory and Instructions

## CRITICAL REMINDER: Always Use Poetry

⚠️ **IMPORTANT**: This project uses Poetry dependency management. ALL Python commands must be prefixed with `poetry run`.

### Wrong:
```bash
python scripts/systematic_analysis.py
python -c "from src.invest.data.yahoo import get_sp500_tickers; print(len(get_sp500_tickers()))"
pytest
```

### Correct:
```bash
poetry run python scripts/systematic_analysis.py
poetry run python -c "from src.invest.data.yahoo import get_sp500_tickers; print(len(get_sp500_tickers()))"
poetry run pytest
```

## Project Status and Context

### Fixed Issues (Don't repeat these mistakes):
1. **S&P 500 Web Scraping**: Fixed broken scraping that was getting dates instead of stock tickers from Wikipedia
2. **Pipeline Optimization**: Added market cap pre-filtering to avoid timeout when analyzing 100+ stocks  
3. **Universe Size Issue**: User reported "only 29 stocks analyzed" - this was due to broken web scraping and inefficient pipeline, now fixed

### Current State:
- ✅ **S&P 500 ticker fetching**: Working correctly (503 tickers)
- ✅ **Pipeline optimization**: Can handle 50+ stocks efficiently with pre-filtering
- ✅ **Systematic screening**: Working end-to-end
- ✅ **AI tools integration**: Both Claude Desktop and Gemini have identical tools

### Key Commands:
```bash
# Install dependencies
poetry install

# Start interactive dashboard (main interface)
poetry run python scripts/dashboard_server.py

# Run systematic analysis
poetry run python scripts/systematic_analysis.py configs/sp500_top100.yaml --save-csv

# Test S&P 500 data fetching
poetry run python -c "from src.invest.data.yahoo import get_sp500_tickers; print(f'Found {len(get_sp500_tickers())} tickers')"

# Run tests  
poetry run pytest
```

### Architecture:
- `src/invest/analysis/pipeline.py` - Main analysis pipeline with optimization
- `src/invest/data/yahoo.py` - Data provider with S&P 500 web scraping
- `src/invest/ai_tools/` - AI integration (Claude Desktop + Gemini)
- `configs/` - YAML screening configurations

### Performance Notes:
- Pre-filtering optimization limits market cap fetching to 150 tickers max to avoid 2-minute timeout
- Successfully tested with 25 and 50 stock universes
- Full 100 stock analysis should work with the optimizations in place

## Systematic Analysis Workflow

### Analysis Pipeline Stages
1. **Universe Selection**
   - Source tickers (S&P 500, custom list)
   - Apply initial market cap and sector filters

2. **Screening Process**
   - Quality Assessment
     - ROIC, ROE
     - Debt levels
     - Liquidity ratios

   - Value Analysis
     - P/E ratio
     - P/B ratio
     - EV/EBITDA

   - Growth Evaluation
     - Revenue growth
     - Earnings growth

   - Risk Assessment
     - Financial risk
     - Market volatility

3. **Valuation Models**
   - Discounted Cash Flow (DCF)
   - Residual Income Model (RIM) [Planned]

### Composite Scoring
- Quality: 30%
- Value: 30%
- Growth: 25%
- Risk: 15% (inverted)

### Configuration Options
- Customize screening thresholds
- Define investment universe
- Select valuation models

### Debugging and Monitoring
- Verbose logging available with `--verbose` flag
- Save results in multiple formats (JSON, CSV)

## Coding Standards

### Core Philosophy
- **Value simplicity** - Simple is better than complex
- **Readability first** - Code should be easy to understand and audit

### Python Style Guidelines
- **Single quotes for strings** - Use `'hello'` not `"hello"`
- **Guard clauses** - Use early returns to avoid deep indentation and improve readability
- **Numpydoc docstrings** - Follow NumPy-style documentation format

### Project Standards
- **Poetry + pyproject.toml** - PEP 621-compliant dependency management
- **Ruff linter** - Use Ruff for fast, modern Python linting
- **Minimal configurations** - Keep .gitignore, configs simple and project-specific

### Code Structure Example
```python
def analyze_stock(ticker):
    # Guard clause - early return
    if not ticker:
        return None
    
    # Guard clause - avoid deep nesting
    if not is_valid_ticker(ticker):
        return None
    
    # Main logic at base level
    return perform_analysis(ticker)
```

## Remember: ALWAYS use `poetry run` for ALL commands!
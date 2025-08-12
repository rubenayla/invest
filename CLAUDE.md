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

## Remember: ALWAYS use `poetry run` for ALL commands!
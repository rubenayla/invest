# Systematic Investment Analysis Framework

A configuration-driven, objective approach to investment analysis that eliminates conversational bias and provides consistent, reproducible results.

## Philosophy

This framework is designed to be:
- **Systematic**: Every stock goes through identical analysis steps
- **Objective**: No conversational AI bias - same inputs always produce same outputs  
- **Configurable**: Define your investment criteria in YAML files
- **Reproducible**: Identical methodology applied consistently
- **Comprehensive**: Quality → Value → Growth → Risk → Valuation pipeline

## Quick Start

⚠️ **IMPORTANT: Always use `poetry run` for all commands** - This project requires Poetry dependency management.

```bash
# Install with Poetry
poetry install

# Run with default conservative value screen
poetry run systematic-invest

# Use specific configuration
poetry run systematic-invest configs/aggressive_growth.yaml

# International markets (Warren Buffett's Japanese favorites)
poetry run python scripts/systematic_analysis.py configs/japan_buffett_favorites.yaml --save-csv

# Alternative: Direct script execution (also requires poetry run)
poetry run python scripts/systematic_analysis.py configs/sp500_top100.yaml --save-csv

# List available configurations
poetry run systematic-invest --list-configs

# Save results in multiple formats
poetry run systematic-invest --save-csv --save-json --output results/
```

### Full S&P 500 Analysis

To analyze ALL S&P 500 stocks (takes 10-15 minutes):

```bash
# Run full S&P 500 analysis with CSV output
poetry run python scripts/systematic_analysis.py configs/sp500_full.yaml --save-csv

# Run quietly in background (no progress output)
poetry run python scripts/systematic_analysis.py configs/sp500_full.yaml --save-csv --quiet &

# Check progress (if running in background)
tail -f sp500_full_screen_*_report.txt
```

**Note**: The full S&P 500 analysis fetches data for 500+ stocks and can take 10-15 minutes. The resulting CSV will include ALL stocks with a `Passes_Filters` column indicating whether each stock meets the screening criteria.

## How It Works

The framework uses a systematic, 5-step analysis pipeline:

1. **Quality Assessment** - Financial strength and stability
2. **Value Analysis** - Valuation attractiveness 
3. **Growth Evaluation** - Business expansion prospects
4. **Risk Assessment** - Financial and business risks
5. **Valuation Models** - DCF and RIM intrinsic value calculations

All analysis parameters are defined in YAML configuration files, ensuring consistent and reproducible results.

## Available Configurations

The framework includes several pre-built strategies:
- Conservative value investing
- Aggressive growth focus
- Full S&P 500 screening
- Custom sector analysis

All configurations can be customized to match your investment criteria.

## Project Structure

```
src/invest/
├── analysis/           # Analysis pipeline and sector context
├── config/            # Configuration schema and loaders
├── data/              # Data providers (Yahoo Finance)
├── reports/           # Report templates and formatters
├── screening/         # Quality, value, growth, risk screening
├── dcf.py            # DCF valuation model
└── rim.py            # Residual Income Model

configs/               # Analysis configurations
├── default_analysis.yaml
├── aggressive_growth.yaml
└── sector_benchmarks.yaml

scripts/
└── systematic_analysis.py  # Main CLI
```

## Output Formats

Multiple output formats for different use cases:
- **Text Reports** - Human-readable analysis summaries
- **CSV Export** - Structured data for spreadsheet analysis
- **JSON Export** - Raw data for API integration

## Key Features

- **Systematic & Objective** - Eliminates human bias through consistent methodology
- **Configurable** - Customize all screening criteria via YAML files
- **Comprehensive** - Analyzes quality, value, growth, and risk dimensions
- **Scalable** - Handle individual stocks or entire market indices
- **Professional Output** - Multiple export formats with detailed reporting

## Usage Examples

⚠️ **Remember: All commands must use `poetry run`**

```bash
# Run basic analysis
poetry run python scripts/systematic_analysis.py

# Full S&P 500 analysis with CSV output
poetry run python scripts/systematic_analysis.py configs/sp500_full.yaml --save-csv

# Custom configuration with multiple output formats
poetry run python scripts/systematic_analysis.py configs/my_strategy.yaml --save-csv --save-json
```

## Extending the Framework

The framework is designed for extensibility:
- Add new screening criteria
- Integrate additional data sources
- Implement custom valuation models
- Create sector-specific analysis modules

See the [Developer Guide](https://your-username.github.io/invest/developer-guide/architecture/) for detailed extension instructions.

## Documentation

Comprehensive documentation is available at [rubenayla.github.io/invest](https://rubenayla.github.io/invest).

### Local Documentation

Run the documentation locally:

```bash
# Install documentation dependencies
poetry install --with docs

# Start documentation server
poetry run mkdocs serve
```

Then visit http://localhost:8000

### Deploy Documentation

Deploy to GitHub Pages:

```bash
# Deploy to GitHub Pages
poetry run mkdocs gh-deploy
```

## Testing

⚠️ **All test commands require `poetry run`**

```bash
# Run all tests
poetry run pytest

# Run with verbose output
poetry run pytest -v

# Run specific test file
poetry run pytest tests/test_systematic_analysis.py
```

## Dependencies

- **Python 3.8+**
- **yfinance** - Stock data and financials
- **pandas** - Data manipulation  
- **pydantic** - Configuration validation
- **pyyaml** - Configuration file parsing

## Limitations

- Currently uses Yahoo Finance (free but limited)
- Valuation model integration is preliminary
- International stock coverage limited
- No real-time data updates

## Why Systematic Analysis?

This framework addresses common issues in investment research:
- **Eliminates bias** - Consistent methodology for all stocks
- **Ensures completeness** - All relevant factors evaluated
- **Provides reproducibility** - Same inputs always yield same outputs
- **Creates audit trail** - Clear, documented analysis process

Ideal for investors seeking disciplined, objective stock analysis.

---

## Original References

- [TIKR](https://app.tikr.com/markets?fid=1)
- [Finviz](https://finviz.com/)
- [Investing.com](https://www.investing.com/)
- [MacroTrends](https://www.macrotrends.net/)
- [Yahoo Finance](https://finance.yahoo.com/)
- [YCharts](https://ycharts.com/)
- [Simply Wall St](https://simplywall.st/)
- [Stock Analysis](https://stockanalysis.com/)

### Recommended Brokers
- **IBKR**: Interactive Brokers - Complex but low cost, extensive, app works well
- **TD Ameritrade** - Easy to use and 0 fees in US
- **Charles Schwab**
- **Fidelity Investments**
- **E*TRADE**
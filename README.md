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

```bash
# Install with Poetry
poetry install

# Run with default conservative value screen
poetry run systematic-invest

# Use specific configuration
poetry run systematic-invest configs/aggressive_growth.yaml

# List available configurations
poetry run systematic-invest --list-configs

# Save results in multiple formats
poetry run systematic-invest --save-csv --save-json --output results/
```

## How It Works

### 1. Configuration-Driven Analysis
Define your investment criteria in YAML configuration files:

```yaml
name: "conservative_value_screen"
description: "Focus on quality companies at reasonable prices"

universe:
  region: "US"
  min_market_cap: 1000  # $1B minimum

quality:
  min_roic: 0.12        # 12% minimum ROIC
  min_roe: 0.15         # 15% minimum ROE
  max_debt_equity: 0.6   # Maximum 60% debt/equity

value:
  max_pe: 25            # Maximum P/E ratio
  max_pb: 3.5           # Maximum P/B ratio

growth:
  min_revenue_growth: 0.03  # Minimum 3% revenue growth

valuation:
  models: ["dcf", "rim"]
  scenarios: ["bear", "base", "bull"]
```

### 2. Systematic Pipeline
Every stock goes through the same 5-step analysis:

1. **Quality Assessment**: ROIC, ROE, debt levels, liquidity ratios
2. **Value Analysis**: P/E, P/B, EV/EBITDA ratios vs. thresholds  
3. **Growth Evaluation**: Revenue/earnings growth, sustainability
4. **Risk Assessment**: Financial, market, and business risk factors
5. **Valuation Models**: DCF and RIM models with multiple scenarios

### 3. Sector Context
Automatically adjusts expectations based on sector characteristics:
- Technology: Higher growth, higher multiples expected
- Utilities: Lower growth, stable margins expected  
- Energy: High cyclicality, volatile margins expected

## Available Configurations

- **`default_analysis.yaml`** - Conservative value investing approach
- **`aggressive_growth.yaml`** - Growth-focused with higher risk tolerance

Create your own configurations or modify existing ones to match your investment strategy.

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

The framework generates:

1. **Executive Summary** - High-level results and top picks
2. **Detailed Stock Reports** - Comprehensive analysis for each stock
3. **Screening Summary** - Process metrics and common issues
4. **CSV Export** - Data for further analysis in Excel/Python
5. **JSON Export** - Structured data for integration

## Key Features

### No AI Bias
- Rule-based analysis, not conversational AI
- Same methodology applied to every stock
- Transparent, auditable criteria

### Comprehensive Coverage
- Screens entire S&P 500 universe (or custom lists)
- 50+ financial metrics evaluated
- Multiple valuation models
- Sector-specific adjustments

### Configurable Criteria
- Define your own quality/value/growth thresholds
- Adjust for different market conditions
- Support for regional screens (US, EU, JP)

### Professional Reports  
- Standardized format for every stock
- Flags potential concerns automatically
- Export to multiple formats

## Usage Examples

```bash
# Basic screening
poetry run systematic-invest

# Growth-focused analysis
poetry run systematic-invest configs/aggressive_growth.yaml

# Custom output location
poetry run systematic-invest --output ~/investment-results/

# Quick CSV export for spreadsheet analysis  
poetry run systematic-invest --save-csv --quiet

# Comprehensive analysis with all outputs
poetry run systematic-invest --save-json --save-csv --verbose
```

## Extending the Framework

### Add New Screening Criteria
1. Update configuration schema in `src/invest/config/schema.py`
2. Implement screening logic in appropriate module
3. Add to analysis pipeline

### Add New Data Sources
1. Create provider module in `src/invest/data/`
2. Follow same interface pattern as Yahoo Finance provider
3. Update universe definitions

### Custom Valuation Models
1. Implement model in `src/invest/`
2. Integrate with pipeline in `src/invest/analysis/pipeline.py`
3. Add to configuration options

## Testing

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

## Why This Approach?

Traditional investment research often suffers from:
- **Confirmation bias** - Cherry-picking supportive data
- **Inconsistency** - Different analysis for different stocks  
- **Incompleteness** - Missing important factors
- **Subjectivity** - Results vary based on mood/phrasing

This systematic framework ensures:
- **Objective analysis** - Same criteria applied consistently
- **Comprehensive coverage** - All factors evaluated systematically
- **Reproducible results** - Identical inputs = identical outputs  
- **Audit trail** - Clear methodology and assumptions

Perfect for investors who want disciplined, systematic analysis without conversational AI bias.

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
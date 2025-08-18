# Systematic Investment Analysis Framework

A configuration-driven, objective approach to investment analysis that eliminates conversational bias and provides consistent, reproducible results.

![Framework Overview](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Poetry](https://img.shields.io/badge/Dependency%20Management-Poetry-blue)

## Quick Start

```bash
# Install dependencies
poetry install

# Run basic analysis
poetry run python scripts/systematic_analysis.py configs/sp500_full.yaml --save-csv

# View results
cat sp500_full_screen_*_results.csv
```

## Key Features

### 🎯 **Dual Analysis Approach**
**Systematic Screening**: Every stock goes through identical analysis steps, eliminating bias in the filtering process.

**AI-Powered Analysis**: Companies that pass filters can be analyzed further using conversational AI tools for qualitative insights.

### ⚙️ **Configuration-Driven**
Define your investment criteria in YAML files. No code changes needed to adjust screening parameters.

### 📊 **Comprehensive Analysis**
- **Quality Assessment**: ROIC, ROE, debt levels, liquidity ratios
- **Value Analysis**: P/E, P/B, EV/EBITDA ratios vs. thresholds  
- **Growth Evaluation**: Revenue/earnings growth, sustainability
- **Risk Assessment**: Financial, market, and business risk factors
- **Valuation Models**: DCF and RIM models with multiple scenarios

### 🏢 **Sector Context**
Automatically adjusts expectations based on sector characteristics:
- Technology: Higher growth, higher multiples expected
- Utilities: Lower growth, stable margins expected  
- Energy: High cyclicality, volatile margins expected

### 📈 **Complete Coverage**
- Screens entire S&P 500 universe (or custom lists)
- 50+ financial metrics evaluated
- Multiple valuation models
- Sector-specific adjustments

### 🤖 **AI-Powered Analysis**
- Conversational AI tools for companies that pass filters
- Qualitative business analysis
- Industry context and competitive positioning
- Integration with Claude Desktop and Gemini

## Philosophy

This framework combines the best of both worlds:

- **Systematic Screening**: Objective, bias-free filtering of large stock universes
- **AI-Enhanced Analysis**: Conversational AI tools for deep-dive analysis of promising candidates
- **Configurable**: Define your investment criteria in YAML files
- **Reproducible**: Consistent methodology for the screening process
- **Comprehensive**: Quality → Value → Growth → Risk → Valuation → AI Analysis pipeline

## Output Formats

The framework generates:

1. **Executive Summary** - High-level results and top picks
2. **Detailed Stock Reports** - Comprehensive analysis for each stock
3. **CSV Export** - Data for further analysis with pass/fail indicators
4. **JSON Export** - Structured data for integration

## Why This Hybrid Approach?

Traditional investment research often suffers from:

- **Confirmation bias** - Cherry-picking supportive data
- **Inconsistency** - Different analysis for different stocks  
- **Scale limitations** - Can't analyze hundreds of stocks manually
- **Time constraints** - Deep analysis is time-consuming

This hybrid framework provides:

- **Systematic Filtering** - Objective screening of large universes (500+ stocks)
- **Focused AI Analysis** - Deep, conversational analysis of promising candidates (10-50 stocks)
- **Best of Both Worlds** - Quantitative rigor + qualitative insights
- **Scalable Process** - Handle entire markets while maintaining analysis depth

Perfect for investors who want comprehensive coverage with deep insights on the most promising opportunities.

## Getting Started

1. **[Installation](getting-started/installation.md)** - Set up the environment
2. **[Quick Start](getting-started/quickstart.md)** - Run your first analysis
3. **[Configuration](getting-started/configuration.md)** - Customize screening criteria

## Workflow

### Step 1: Systematic Screening
```bash
# Screen entire S&P 500 universe
poetry run python scripts/systematic_analysis.py configs/sp500_full.yaml --save-csv

# Results: 25-50 companies that pass all filters
```

### Step 2: AI-Powered Deep Dive
```bash
# Use AI tools to analyze promising candidates
# Available integrations:
# - Claude Desktop tools
# - Gemini AI tools
# - Custom research workflows
```

### Step 3: Investment Decision
Combine quantitative screening results with qualitative AI insights for informed investment decisions.

## Learn More

- **[User Guide](user-guide/overview.md)** - Comprehensive usage documentation
- **[Developer Guide](developer-guide/architecture.md)** - Extend and customize the framework
- **[API Reference](api-reference/pipeline.md)** - Detailed technical documentation
- **[Tutorials](tutorials/basic-screening.md)** - Step-by-step examples
- **[AI Tools Integration](tutorials/ai-tools.md)** - Using conversational AI for deeper analysis
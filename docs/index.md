# Systematic Investment Analysis Framework

A configuration-driven, objective approach to investment analysis that eliminates conversational bias and provides consistent, reproducible results with comprehensive backtesting capabilities.

![Framework Overview](https://img.shields.io/badge/Python-3.12%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![UV](https://img.shields.io/badge/Dependency%20Management-UV-blue)
![CI](https://img.shields.io/badge/CI-GitHub%20Actions-green)

## Quick Start

```bash
# Install dependencies
uv sync

# Launch interactive dashboard (recommended - multiple access options)
uv run python scripts/run_dashboard.py

# Or start dashboard server directly
uv run python scripts/dashboard_server.py
# Opens automatically at http://localhost:8080

# Or run command-line analysis
uv run python scripts/systematic_analysis.py configs/sp500_full.yaml --save-csv

# View results
cat sp500_full_screen_*_results.csv
```

## Key Features

### 🎯 **AI-Controlled Dual Analysis Approach**
**Systematic Screening**: AI models (like Claude) run automated analysis pipelines on large stock universes, eliminating human bias in the filtering process.

**AI Deep-Dive Analysis**: AI models then use specialized tools to perform qualitative analysis on companies that pass the systematic filters.

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

### 📈 **Global Market Coverage**
- Screens entire S&P 500 universe and international markets
- Japanese markets (TOPIX, Berkshire holdings) - Warren Buffett's recent focus
- European markets (FTSE, DAX) and other international opportunities
- 50+ financial metrics evaluated with currency-aware analysis
- Multiple valuation models with international considerations

### 🤖 **AI-Controlled Research Process**
- AI models execute the entire research workflow autonomously
- AI runs systematic screening, interprets results, and performs deep-dive analysis
- AI uses specialized tools for data gathering, analysis, and report generation
- Seamless integration with Claude Desktop and Gemini ecosystems

## Philosophy

This framework empowers AI models to conduct comprehensive investment research:

- **AI-Driven Systematic Screening**: AI models run objective, bias-free filtering of large stock universes
- **AI-Controlled Deep Analysis**: AI models autonomously use tools for qualitative analysis of promising candidates  
- **Human-Configurable**: Humans define investment criteria in YAML files, AI executes the research
- **AI-Reproducible**: AI follows consistent methodology for systematic screening
- **End-to-End AI Workflow**: Quality → Value → Growth → Risk → Valuation → AI Deep-Dive pipeline

## Output Formats

The framework generates:

1. **Executive Summary** - High-level results and top picks
2. **Detailed Stock Reports** - Comprehensive analysis for each stock
3. **CSV Export** - Data for further analysis with pass/fail indicators
4. **JSON Export** - Structured data for integration

## Why AI-Controlled Investment Research?

Traditional investment research often suffers from:

- **Human bias** - Cherry-picking supportive data, emotional decisions
- **Inconsistency** - Different analysis methods for different stocks  
- **Scale limitations** - Humans can't systematically analyze hundreds of stocks
- **Time constraints** - Manual deep analysis is extremely time-consuming

This AI-controlled framework provides:

- **AI-Executed Systematic Filtering** - AI objectively screens large universes (500+ stocks) using consistent methodology
- **AI-Driven Deep Analysis** - AI performs conversational analysis of promising candidates (10-50 stocks) using specialized tools
- **Hybrid AI Approach** - Quantitative screening rigor + AI qualitative insights
- **AI-Scalable Process** - AI handles entire markets while maintaining analysis depth autonomously

Perfect for empowering AI models to provide comprehensive investment research with both breadth and depth.

## Getting Started

1. **[Installation](getting-started/installation.md)** - Set up the environment
2. **[Quick Start](getting-started/quickstart.md)** - Run your first analysis
3. **[Configuration](getting-started/configuration.md)** - Customize screening criteria

## AI-Controlled Workflow

### Step 1: AI Runs Systematic Screening
```bash
# AI model executes systematic analysis on US markets
uv run python scripts/systematic_analysis.py configs/sp500_full.yaml --save-csv

# AI model analyzes international markets (Warren Buffett's Japanese favorites)
uv run python scripts/systematic_analysis.py configs/japan_buffett_favorites.yaml --save-csv

# AI automatically filters to 25-50 companies globally that pass all criteria
```

### Step 2: AI Performs Deep-Dive Analysis
```bash
# AI model uses specialized investment research tools to analyze promising candidates
# AI automatically accesses:
# - Claude Desktop investment tools
# - Gemini AI research tools  
# - Custom analysis workflows
# - All available data sources and research capabilities
```

### Step 3: AI Generates Investment Recommendations
AI combines quantitative screening results with qualitative insights to provide comprehensive investment analysis and recommendations.

## Learn More

- **[User Guide](user-guide/overview.md)** - Comprehensive usage documentation
- **[Developer Guide](developer-guide/architecture.md)** - Extend and customize the framework
- **[API Reference](api-reference/pipeline.md)** - Detailed technical documentation
- **[Tutorials](tutorials/basic-screening.md)** - Step-by-step examples
- **[AI Tools Integration](tutorials/ai-tools.md)** - Using conversational AI for deeper analysis
# AI Investment Analysis Tools

This directory contains tools that allow both **Claude Desktop** and **Gemini** to perform comprehensive investment analysis using the systematic framework. Both AI agents have identical capabilities and can work independently in this project folder.

## Quick Start

### For Claude Desktop Users
Claude Desktop integration works automatically when you're in this project folder. Just ask Claude investment questions and it will use these tools.

### For Gemini Users  
Gemini can access these tools directly when working in this project folder. Use the same commands and functions that Claude uses.

## Available Tools

Both Claude and Gemini have access to identical investment analysis tools:

### 🔍 Systematic Screening
- **`systematic_screen()`** - Run comprehensive stock screening
- **`get_screening_configs()`** - List available screening configurations
- **`create_custom_screen()`** - Create custom screening criteria

### 📊 Stock Research
- **`research_stock()`** - Deep dive stock analysis with web research
- **`analyze_sector()`** - Comprehensive sector analysis
- **`get_recent_news()`** - Recent news research and analysis
- **`compare_competitive_position()`** - Competitive analysis

### 📈 Data Analysis
- **`get_stock_data_detailed()`** - Comprehensive stock data
- **`get_financial_metrics()`** - Specific financial metrics
- **`compare_stocks()`** - Side-by-side stock comparison
- **`analyze_stock_trends()`** - Trend analysis

### 💼 Portfolio Construction
- **`build_portfolio()`** - Build optimized portfolios
- **`analyze_portfolio_risk()`** - Risk analysis
- **`optimize_allocation()`** - Rebalancing recommendations
- **`screen_etfs_by_category()`** - ETF screening

## How to Use

Both AI agents can be asked natural language questions and will automatically use these tools:

### Example Questions for Both AIs

#### 🔍 Systematic Screening Questions
```
"Run a conservative value screen and show me the top 10 results"
"Find growth stocks with ROE above 15% and P/E below 30"
"Screen for dividend stocks in the healthcare sector"
"What screening configurations are available?"
"Create a custom screen for high-quality tech stocks with low debt"
"Find stocks that passed the aggressive growth criteria"
```

#### 📊 Stock Research Questions  
```
"Research Apple's competitive position and recent developments"
"Analyze Tesla's risks and potential catalysts"
"What are the recent news and analyst updates for Microsoft?"
"Compare Netflix vs Disney's competitive positions"
"Research the healthcare sector trends and cycle position"
"What's driving the technology sector lately?"
```

#### 📈 Data Analysis Questions
```
"Get detailed financial data for Berkshire Hathaway"
"Compare Apple, Microsoft, and Google on profitability metrics"
"Show me valuation metrics for the top 5 FAANG stocks"
"Analyze Amazon's financial trends and growth indicators"
"Get all the key metrics for Johnson & Johnson"
"What are the financial health indicators for Tesla?"
```

#### 💼 Portfolio Construction Questions
```
"Build a balanced portfolio from these 15 stocks with proper diversification"
"Create an income-focused portfolio from dividend aristocrats"
"Build a growth portfolio with maximum 10 positions"
"Analyze the risk characteristics of my current portfolio: AAPL, MSFT, GOOGL, AMZN"
"Optimize allocation between my current and target portfolio weights"
"Screen broad market ETFs and recommend the best options"
"Generate a comprehensive portfolio report"
```

#### 🔧 Technical Usage Questions
```
"Show me how to run systematic screening programmatically"
"What data sources are you using for this analysis?"
"Save the screening results to a file for further analysis"
"Run the screening with different configurations and compare results"
"How do I create custom screening criteria?"
"What's the difference between the available screening configs?"
```

#### 🎯 Specific Analysis Questions
```
"Find value stocks that Warren Buffett might like (high ROE, low debt, reasonable P/E)"
"Screen for 'fallen angels' - quality companies at temporary low prices"
"Find dividend growth stocks with 10+ years of increases"
"What are the best opportunities in emerging markets?"
"Analyze REIT stocks vs traditional real estate investments"
"Find small-cap stocks with institutional backing"
"Screen for recession-resistant defensive stocks"
```

#### 🌐 Market Analysis Questions
```
"What sectors look most attractive right now based on valuations?"
"Find stocks that are trading below analyst price targets"
"Analyze which stocks have the most upside potential"
"What are the trends in different market sectors?"
"Find stocks with recent positive earnings surprises"
"Analyze correlation between different technology stocks"
```

## File Structure

```
src/invest/ai_tools/
├── core/                    # Shared business logic
│   ├── screening.py         # Systematic screening functions
│   ├── research.py          # Stock research functions
│   ├── analysis.py          # Data analysis utilities
│   └── portfolio.py         # Portfolio construction
├── claude/                  # Claude Desktop tools
│   ├── screening_tools.py
│   ├── research_tools.py
│   ├── data_tools.py
│   └── portfolio_tools.py
├── gemini/                  # Gemini tools (identical functions)
│   ├── screening_tools.py
│   ├── research_tools.py
│   ├── data_tools.py
│   └── portfolio_tools.py
└── README.md               # This file
```

## Technical Details

### Architecture
- **Shared Core Logic**: All business logic is in the `core/` modules
- **AI-Specific Interfaces**: `claude/` and `gemini/` contain identical wrapper functions
- **No API Dependencies**: Both AIs work directly in the project folder without API calls

### Data Sources
- **Yahoo Finance**: Primary data source for stock information
- **Systematic Framework**: Uses the existing screening and analysis pipeline
- **Real-time Research**: Both AIs can perform web searches for recent information

### Key Features
- ✅ **No API Keys Required** - Both AIs work directly in the project
- ✅ **Identical Capabilities** - Same functions available to both AIs
- ✅ **Systematic Analysis** - Uses objective, reproducible screening criteria
- ✅ **Web Research** - Both AIs can search for recent news and developments
- ✅ **Portfolio Tools** - Complete portfolio construction and analysis
- ✅ **Comprehensive Reports** - Professional investment analysis reports

## Available Screening Configurations

### Pre-built Configurations
- **`default_analysis`** - Conservative value investing screen
- **`aggressive_growth`** - Growth-focused with higher risk tolerance

### Custom Screening
Both AIs can create custom screens on the fly:
```python
create_custom_screen(
    name="High Quality Tech",
    quality_criteria={"min_roic": 0.20, "max_debt_equity": 0.3},
    value_criteria={"max_pe": 30},
    universe_settings={"sectors": ["Technology"]}
)
```

## Example AI Tool Usage

### Claude Desktop
Claude automatically accesses these tools when you ask investment questions. The tools are loaded when Claude detects you're working on investment analysis.

### Gemini 
Gemini can use the exact same tools when working in this project folder. Ask Gemini to:
1. Run systematic stock screening
2. Research specific companies
3. Build and analyze portfolios  
4. Compare investment options

## Advanced Usage

### Running Analysis Programmatically

⚠️ **CRITICAL: Always use `poetry run` for all commands** - This project requires Poetry dependency management.

```bash
# Use the CLI tool directly
poetry run systematic-invest configs/aggressive_growth.yaml

# Direct script execution (also requires poetry run)
poetry run python scripts/systematic_analysis.py configs/sp500_top100.yaml --save-csv

# Or let the AIs run it for you
"Please run the aggressive growth screening and analyze the results"
```

### Custom Research Areas
```python
research_stock("AAPL", research_areas=[
    "competitive_position", 
    "recent_news", 
    "industry_trends", 
    "catalysts"
])
```

### Portfolio Optimization
```python
build_portfolio(
    candidate_stocks=["AAPL", "MSFT", "GOOGL", "AMZN"],
    optimization_objective="balanced",
    portfolio_constraints={
        "max_single_position": 0.20,
        "max_sector_allocation": 0.40
    }
)
```

## Integration Benefits

### For Claude Desktop
- Seamless integration with existing Claude Desktop workflow
- Automatic tool detection and usage
- Natural language interaction

### For Gemini
- Identical functionality to Claude Desktop
- Can perform web research and analysis
- Works directly in project folder without setup

### For Both AIs
- **Consistent Results** - Same systematic framework
- **Comprehensive Analysis** - All aspects of investment research
- **Professional Reports** - Investment-grade analysis output
- **No External Dependencies** - Everything runs in the project folder

## Testing Gemini Integration

### First-Time Setup for Gemini
1. **Navigate to project folder**: `/home/rubenayla/repos/invest`
2. **Test file access**: Ask Gemini "Can you list the files in src/invest/ai_tools/gemini/?"
3. **Test Python execution**: Ask Gemini to run:
   ```bash
   poetry run python -c "
   from src.invest.ai_tools.gemini.screening_tools import get_screening_configs
   result = get_screening_configs()
   print('Available configs:', len(result.get('available_configs', [])))
   "
   ```

### Simple Test Questions for Gemini
```
"Can you see the investment analysis tools in this project?"
"Run a quick test of the systematic screening tools"
"Show me what screening configurations are available"
"Test the stock data tools by getting Apple's financial metrics"
```

### If Gemini Can't Execute Python Directly
If Gemini can't run Python code directly, you can still use it for analysis:
1. **You run the commands**: Use `poetry run python -c "..."`  
2. **Share results with Gemini**: Copy-paste the output
3. **Get AI analysis**: Gemini can interpret and analyze the results

Example:
```bash
# You run this:
poetry run python -c "
from src.invest.ai_tools.gemini.screening_tools import systematic_screen
result = systematic_screen('default', max_results=5)
print('Top picks:', [p['ticker'] for p in result.get('top_picks', [])])
"

# Then ask Gemini to analyze the results
```

## Troubleshooting

### If Tools Don't Load
1. Make sure you're in the correct project directory: `/home/rubenayla/repos/invest`
2. Check that all dependencies are installed: `poetry install`
3. Verify the systematic framework is working: `poetry run systematic-invest --help`
4. **CRITICAL**: For Python execution, ALWAYS use: `poetry run python -c "your code here"`

### For Claude Desktop
- Tools should load automatically when you ask investment questions
- If not working, restart Claude Desktop and navigate to the project folder

### For Gemini
- Test file access first: "Can you see files in this project?"
- Test Python execution: "Can you run Python code?"
- If direct execution doesn't work, use the copy-paste approach above

### Getting Better Results
1. **Be Specific** - "Analyze healthcare dividend stocks" vs "find stocks"
2. **Iterate** - Ask follow-up questions to dive deeper
3. **Use Multiple Tools** - Combine screening with research and portfolio analysis
4. **Request Sources** - Ask AIs to cite their research sources
5. **Start Simple** - Test with basic screening before complex analysis

## Why This Approach?

This architecture provides several key benefits:

1. **No API Costs** - Both AIs work directly in the project folder
2. **Consistent Results** - Same systematic framework eliminates bias
3. **Comprehensive Coverage** - Complete investment analysis workflow
4. **AI Flexibility** - Choose between Claude or Gemini based on preference
5. **Transparent Process** - All analysis steps are auditable and reproducible

Both Claude Desktop and Gemini can now provide professional-grade investment analysis using the same systematic framework, ensuring consistent and objective results regardless of which AI you choose to work with.
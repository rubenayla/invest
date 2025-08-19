# Claude Desktop Integration Guide

Your investment framework now has Claude Desktop tools that let me directly run systematic analysis, research stocks, and build portfolios. Here's how to use it:

## Quick Start

1. **Open Claude Desktop** 
2. **Navigate to your invest folder** (`cd /path/to/invest`)
3. **Start asking investment questions!**

## Available Tools

I now have direct access to your systematic framework through these tools:

### 🔍 Screening Tools
- `systematic_screen()` - Run systematic stock screening
- `get_screening_configs()` - See available screening configurations
- `create_custom_screen()` - Create custom screening criteria

### 📊 Research Tools  
- `research_stock()` - Deep research on specific stocks
- `analyze_sector()` - Sector-wide analysis
- `get_recent_news()` - Recent news research framework
- `compare_competitive_position()` - Competitive analysis

### 📈 Data Tools
- `get_stock_data_detailed()` - Comprehensive stock data
- `get_financial_metrics()` - Specific financial metrics
- `compare_stocks()` - Side-by-side stock comparison
- `analyze_stock_trends()` - Trend analysis

### 💼 Portfolio Tools
- `build_portfolio()` - Construct optimized portfolios
- `analyze_portfolio_risk()` - Risk analysis
- `optimize_allocation()` - Rebalancing recommendations

## Example Conversations

### Stock Screening
```
You: "Find undervalued growth stocks in the technology sector"

Claude: [Uses systematic_screen with growth criteria]
Found 23 tech stocks meeting criteria:
- NVDA: Score 87.2 (Growth: 94, Value: 76, Quality: 91)
- AMD: Score 82.1 (Growth: 89, Value: 82, Quality: 75)
...

[Then researches top picks with web search]
NVDA Analysis:
- Dominant in AI chips (80%+ market share)
- Recent H100 demand exceeding supply
- Risk: China export restrictions...
```

### Portfolio Construction
```
You: "Build me a balanced dividend portfolio from these stocks: JNJ, PG, KO, T, VZ"

Claude: [Uses build_portfolio with income objective]
Optimized Allocation:
- JNJ: 25% (Healthcare, Dividend King)  
- PG: 22% (Consumer Staples, stable)
- KO: 20% (Global brand moat)
- T: 18% (High yield, some risk)
- VZ: 15% (Telecom diversification)

Portfolio Metrics:
- Weighted Dividend Yield: 4.2%
- Weighted P/E: 16.8
- Sector Diversification: Medium (3 sectors)
```

### Research Deep Dive
```
You: "What's the investment thesis for Apple right now?"

Claude: [Uses research_stock + web search]
Apple (AAPL) Investment Analysis:

Current Metrics:
- P/E: 28.5, Market Cap: $3.0T
- ROE: 147%, Revenue Growth: 2.1%

Competitive Position:
- iPhone still 65% of revenue, services growing
- Ecosystem lock-in creates pricing power
- China represents 19% of revenue (geopolitical risk)

Recent Developments:
- Vision Pro launched but slow adoption
- Services revenue hit record $22.3B
- AI integration in iOS 18 driving upgrade cycle

Investment Thesis:
✅ Dominant ecosystem and brand loyalty
✅ Services business provides recurring revenue  
⚠️ iPhone growth slowing in mature markets
⚠️ China regulatory risks
```

## Integration with Your Existing Tools

The Claude tools complement your existing command-line tools:

- **Systematic Analysis**: `poetry run systematic-invest` (automated)
- **Claude Analysis**: Interactive conversation (flexible)
- **Both Together**: Run systematic screening, then discuss results with Claude

## Best Practices

### 1. Start with Systematic Screening
```
"Screen for value stocks in the healthcare sector"
```
Let me run your objective framework first, then we can dive deeper.

### 2. Ask Follow-up Questions  
```
"What are the main risks for the top 3 picks?"
"How do these compare to their competitors?"
"Build me a portfolio from the top 10"
```

### 3. Get Specific Research
```
"Research recent developments for NVDA"
"What's driving the healthcare sector lately?"
"Compare MSFT vs GOOGL competitive positions"
```

## Cost-Effective Future Options

While Claude Desktop is free with your subscription, I've added a roadmap in `todo.md` for cost-effective alternatives:

- **Gemini Pro**: Free tier with web search
- **Local Ollama**: 100% free, runs on your machine
- **Smart routing**: Automatically pick the best AI for each task

## Getting Started

Ready to test it? Try asking me:

1. **"Find me some undervalued dividend stocks"**
2. **"Research the latest news on Tesla"**  
3. **"Build me a portfolio from the S&P 500's best performers"**
4. **"What sectors look attractive right now?"**

I'll use your systematic framework combined with real-time research to give you comprehensive analysis!

## Troubleshooting

If tools aren't working:
1. Make sure you're in the invest directory in Claude Desktop
2. Check that dependencies are installed: `poetry install`
3. Verify Python path includes the src directory

The tools should automatically load when you ask investment-related questions.
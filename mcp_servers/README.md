# Investment Analysis MCP Servers

This directory contains MCP (Model Context Protocol) servers that provide Claude with direct access to investment analysis capabilities through Claude Desktop.

## 🚀 What This Enables

With these MCP servers, you can use investment analysis tools directly in Claude conversations:

- **Real-time stock analysis** for any ticker (US, international)
- **DCF valuations** with 4 different models (standard, dividend-aware, probabilistic, growth-phase)
- **Portfolio management** (risk assessment, diversification, rebalancing)
- **Stock screening** with customizable criteria
- **International comparisons** (compare US vs Japanese vs European stocks)

## 📦 Available Servers

### 1. `investment_analysis.py` - Core Analysis Tools
- `get_stock_data` - Get comprehensive data for any ticker
- `compare_stocks` - Compare multiple stocks across exchanges
- `dcf_valuation` - Run DCF models (standard, dividend_aware, probabilistic, growth_phase)  
- `ratio_analysis` - Calculate financial ratios and fair values

### 2. `portfolio_tools.py` - Portfolio Management
- `analyze_portfolio` - Analyze portfolio with weighted holdings
- `risk_assessment` - Assess portfolio risk factors
- `diversification_check` - Check sector/geographic diversification
- `rebalancing_suggestions` - Get rebalancing recommendations

### 3. `screening.py` - Stock Screening
- `screen_stocks` - Custom screening with various criteria
- `value_screen` - Pre-configured value stock screen
- `quality_screen` - Quality/dividend focused screen  
- `growth_screen` - Growth stock screen
- `sector_screen` - Screen by specific sector

## ⚙️ Installation & Setup

### Prerequisites
```bash
# Install MCP dependencies
pip install mcp

# Ensure your investment repo is set up
poetry install  # in your invest repo
```

### Claude Desktop Configuration

1. **Open Claude Desktop settings** (usually `~/.claude/claude_desktop_config.json`)

2. **Add the MCP servers** to your configuration:

```json
{
  "mcpServers": {
    "investment-analysis": {
      "command": "python",
      "args": ["/absolute/path/to/your/invest/mcp_servers/investment_analysis.py"],
      "env": {
        "PYTHONPATH": "/absolute/path/to/your/invest/src"
      }
    },
    "portfolio-tools": {
      "command": "python", 
      "args": ["/absolute/path/to/your/invest/mcp_servers/portfolio_tools.py"],
      "env": {
        "PYTHONPATH": "/absolute/path/to/your/invest/src"
      }
    },
    "stock-screening": {
      "command": "python",
      "args": ["/absolute/path/to/your/invest/mcp_servers/screening.py"], 
      "env": {
        "PYTHONPATH": "/absolute/path/to/your/invest/src"
      }
    }
  }
}
```

3. **Restart Claude Desktop**

### Testing the Setup

Once configured, you should see the tools available in Claude Desktop. Test with:

```
"Can you analyze AAPL using the investment analysis tools?"
"Compare AAPL, 7203.T (Toyota), and ASML.AS"
"Run a DCF valuation on MSFT using the probabilistic model"
"Screen for value stocks in Japanese blue chips"
```

## 🎯 Example Usage

### Stock Analysis
```
Analyze Tesla (TSLA) and give me the key metrics
```
→ Uses `get_stock_data` to provide comprehensive analysis

### International Comparison  
```
Compare Apple, Toyota (7203.T), and ASML (ASML.AS) on valuation metrics
```
→ Uses `compare_stocks` with automatic currency conversion

### DCF Valuation
```
Run a Monte Carlo DCF on Microsoft with 15% discount rate
```
→ Uses `dcf_valuation` with probabilistic model and custom parameters

### Portfolio Analysis
```
Analyze my portfolio: 40% AAPL, 30% GOOGL, 20% 7203.T, 10% ASML.AS
```
→ Uses `analyze_portfolio` for comprehensive portfolio review

### Stock Screening
```
Find value stocks in US large caps with P/E < 15 and ROE > 15%
```
→ Uses `screen_stocks` with custom criteria

## 🔧 Troubleshooting

### Common Issues

1. **"Tools not available"** - Check Claude Desktop config path and restart
2. **"Import errors"** - Ensure PYTHONPATH is set correctly in config
3. **"No data for ticker"** - Verify ticker format (use .T for Japanese, .AS for Amsterdam, etc.)

### Testing Individual Servers

You can test servers directly:
```bash
cd mcp_servers
python investment_analysis.py
# Should start MCP server - Ctrl+C to stop
```

### Debug Mode

Add verbose logging to troubleshoot:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🌟 Advanced Features

### Custom Tickers Lists
The screening tools support custom ticker lists:
```
Screen these specific stocks for value: AAPL, MSFT, 7203.T, ASML.AS with P/E < 20
```

### Multi-Currency Analysis  
All tools automatically handle international currencies:
```
Compare valuations: US tech (AAPL) vs Japanese auto (7203.T) vs European semis (ASML.AS)
```

### Probabilistic Valuations
Get confidence intervals on your DCF models:
```
Run Monte Carlo DCF on NVDA - what's the 95% confidence range?
```

## 🚀 What's Next?

These MCP servers transform your Claude conversations into a professional investment analysis workstation. You can:

- Research stocks during conversations
- Get real-time valuations  
- Compare international opportunities
- Screen for investment ideas
- Manage portfolio risk

The tools use the same sophisticated valuation models and data sources as the standalone analysis scripts, but now accessible directly in Claude conversations!
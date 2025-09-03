# Investment Analysis MCP Server

## Overview

The Enhanced Investment Analysis MCP Server provides AI assistants with direct access to your comprehensive investment analysis system. This enables conversational stock analysis, portfolio management, and automated investment workflows.

## 🚀 Setup

### 1. Install Dependencies
```bash
poetry install
```

### 2. Start the MCP Server
```bash
poetry run python mcp_server_v2.py
```

### 3. Configure Claude Code MCP
Add to your Claude Code MCP configuration:
```json
{
  "mcpServers": {
    "investment-analysis": {
      "command": "poetry",
      "args": ["run", "python", "mcp_server_v2.py"],
      "env": {
        "PYTHONPATH": "."
      }
    }
  }
}
```

## 🛠️ Available Tools

### 1. `analyze_stock`
**Complete stock analysis with multiple valuation models**

```
analyze_stock(ticker="AAPL", models=["dcf", "neural_network_best"], use_cache=True)
```

**Parameters:**
- `ticker`: Stock symbol (e.g., "AAPL", "MSFT")  
- `models`: List of models to use (optional)
- `use_cache`: Whether to use cached data (default: True)

**Available Models:**
- `dcf` - Standard DCF model
- `dcf_enhanced` - Enhanced DCF with normalized cash flows
- `multi_stage_dcf` - Multi-phase growth DCF
- `growth_dcf` - Separates maintenance vs growth CapEx
- `simple_ratios` - Market multiples (P/E, P/B, etc.)
- `rim` - Residual Income Model
- `neural_network_best` - Best AI model (2-year, 51.8% correlation)
- `neural_network_consensus` - Weighted average of all AI models
- `ensemble` - Combines multiple traditional models

**Example Response:**
```
📈 Investment Analysis: Apple Inc. (AAPL)

Company Overview:
• Current Price: $238.47
• Market Cap: $3.7T
• Sector: Technology
• P/E Ratio: 32.1
• 52W Range: $164.08 - $250.34

Valuation Results: (3 models)
Model               Fair Value   Upside     Recommendation 
-----------------------------------------------------------------
AI Best (2Y)        $300.22     +25.9%     Strong Buy 🔥
Enhanced DCF        $275.50     +15.5%     Buy 📈
Standard DCF        $265.80     +11.4%     Buy 📈

Consensus Analysis:
• Average Fair Value: $280.51
• Consensus Margin: +17.6%
• Overall Recommendation: Strong Buy 🔥
```

### 2. `neural_predict`  
**AI-powered stock predictions with confidence metrics**

```
neural_predict(ticker="TSLA", timeframe="2year", include_all_timeframes=False)
```

**Parameters:**
- `ticker`: Stock symbol
- `timeframe`: Time horizon ("1month", "3month", "6month", "1year", "18month", "2year", "3year")
- `include_all_timeframes`: Show all neural network models (default: False)

**Example Response:**
```
🧠 Neural Network Prediction for TSLA

Model: 2year (24 months)
Description: 2-year prediction horizon - longer-term value realization
Best for: Long-term value investing, BEST CORRELATION (0.518)

Performance Metrics:
• Correlation: 0.518
• Hit Rate: 100%
• Validation MAE: 26.2

Prediction:
• Current Price: $334.09
• Fair Value: $386.91
• Margin of Safety: +15.8%

📈 Buy - Moderate upside
```

### 3. `compare_models`
**Side-by-side comparison of different valuation approaches**

```
compare_models(ticker="MSFT", include_neural=True)
```

**Example Response:**
```
📊 Model Comparison for MSFT
Current Price: $505.35

Model               Fair Value   Upside/Downside   Confidence
-----------------------------------------------------------------
AI Best (2Y)        $648.08     +28.2% 🔥         High      
Growth DCF          $610.50     +20.8% 📈         Medium    
Enhanced DCF        $575.20     +13.8% 📈         Medium    
Standard DCF        $520.10     +2.9% ➡️          Medium    
Market Ratios       $495.30     -2.0% ➡️          Low       

Summary:
• Average Fair Value: $569.84
• Range: $495.30 - $648.08
• Consensus vs Current: +12.7%
```

### 4. `screen_stocks`
**Find stocks matching investment criteria**

```
screen_stocks(universe="sp500", max_pe=15, min_roe=15, sector="Technology", limit=10)
```

**Parameters:**
- `universe`: Stock universe ("sp500", "nasdaq100", "all", "tech", "growth", "international")
- `max_pe`: Maximum P/E ratio
- `min_roe`: Minimum ROE percentage  
- `min_score`: Minimum composite score
- `max_debt_equity`: Maximum debt-to-equity ratio
- `sector`: Specific sector filter
- `limit`: Maximum results (default: 20)

**Example Response:**
```
🔍 Stock Screening Results
Universe: sp500 | Processed: 100 stocks | Found: 8 matches

Criteria: P/E ≤ 15, ROE ≥ 15%, Sector: Technology

Ticker   Price      P/E      ROE      D/E      Sector              
------------------------------------------------------------------------
INTC     $32.45     12.1     18.5%    0.45     Technology          
CSCO     $58.90     14.2     16.8%    0.32     Technology          
IBM      $195.20    15.0     22.1%    0.58     Technology          
```

### 5. `analyze_portfolio`
**Comprehensive portfolio analysis with risk and diversification metrics**

```
analyze_portfolio(tickers=["AAPL", "MSFT", "GOOGL"], weights=[0.4, 0.3, 0.3])
```

**Example Response:**
```
💼 Portfolio Analysis (3 positions)

Portfolio Composition:
Ticker   Weight   Price      Sector               P/E     
------------------------------------------------------------
AAPL     40.0%    $238.47    Technology           32.1    
MSFT     30.0%    $505.35    Technology           35.2    
GOOGL    30.0%    $212.91    Communication        26.8    

Sector Allocation:
• Technology: 70.0%
• Communication Services: 30.0%

Portfolio Metrics:
• Weighted P/E Ratio: 31.2
• Weighted Beta: 1.15
• Large Cap (>$10B): 100.0%

Valuation Assessment:
• Undervalued positions: 25.0%
• Overvalued positions: 15.0%

Diversification Score: 45/100
❌ Poorly diversified - high concentration risk
```

### 6. `get_model_info`
**Learn about available valuation models**

```
get_model_info(model_name="neural_network_best")
```

**Example Response:**
```
📋 Neural Network Best

Description: AI model trained on 2-year horizons with 51.8% correlation and 100% hit rate
Suitable for: Long-term value investing, structural business analysis
Time horizon: 24 months
Complexity: High
Data requirements: 60+ engineered features from financial statements, market data
```

## 💡 Usage Examples

### Conversational Analysis
```
"Analyze AAPL using neural networks and compare to traditional DCF models"
→ Uses analyze_stock + compare_models
```

### Portfolio Discovery  
```
"Find undervalued tech stocks with P/E under 20 and ROE above 15%"
→ Uses screen_stocks with criteria
```

### AI Predictions
```
"What does your best neural network model predict for TSLA over the next 2 years?"
→ Uses neural_predict with timeframe analysis
```

### Portfolio Management
```
"Analyze my portfolio of AAPL 40%, MSFT 30%, GOOGL 30% - is it well diversified?"
→ Uses analyze_portfolio with risk assessment
```

## 🔧 Advanced Features

### Model Selection
The MCP server automatically selects appropriate models based on:
- Company characteristics (size, sector, financial health)
- Data availability and quality
- Model suitability criteria

### Caching Strategy
- Uses 4-hour cache for stock data
- Balances performance with data freshness
- Automatic cache invalidation for stale data

### Error Handling  
- Graceful degradation when models fail
- Detailed error messages for debugging
- Fallback to alternative models when possible

### Performance Optimization
- Async processing for bulk operations
- Intelligent batching for screening operations  
- Configurable timeouts and limits

## 🚨 Important Notes

### Data Sources
- Uses yfinance for real-time stock data
- Leverages cached fundamental data when available
- Neural networks require trained model files

### Model Availability
- Some models may not be suitable for all stocks
- Neural network models require sufficient training data
- Sector-specific models auto-select based on company classification

### Rate Limiting
- Respects API rate limits for data providers
- Implements backoff strategies for bulk operations
- Caches data to minimize external calls

## 🔍 Troubleshooting

### Common Issues

1. **"Model not suitable for this stock"**
   - Some models require specific financial data
   - Try using `simple_ratios` as a fallback
   - Check if the company has sufficient historical data

2. **"Neural network prediction failed"**  
   - Ensure neural network model files are present
   - Check if the stock has sufficient fundamental data
   - Try using a different timeframe

3. **"No stocks found matching criteria"**
   - Relax screening criteria (higher P/E, lower ROE)
   - Try a different stock universe
   - Increase the limit parameter

### Debug Mode
Set environment variable for detailed logging:
```bash
export INVESTMENT_MCP_DEBUG=1
poetry run python mcp_server_v2.py
```

## 📊 Model Performance

### Neural Network Models
- **2-Year Model**: 51.8% correlation, 100% hit rate (BEST)
- **3-Month Model**: 25.0% correlation, 50% hit rate  
- **1-Year Model**: 1.1% correlation, 100% hit rate

### Traditional Models
- **DCF Models**: Best for cash flow positive companies
- **RIM Model**: Excellent for financial companies
- **Market Ratios**: Fast screening and cross-validation

This MCP server transforms your investment analysis system into a conversational AI tool, enabling sophisticated analysis through natural language interactions.
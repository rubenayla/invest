# Interactive Dashboard

The Interactive Dashboard provides a live web interface for viewing and updating your investment analysis. It compares multiple valuation models side-by-side with real-time data updates.

## Quick Start

```bash
# Start the dashboard server
poetry run python scripts/dashboard_server.py

# Dashboard opens automatically at http://localhost:8080
# Click "Update Data" button to refresh valuations
```

## Features

### Live Valuation Comparison
- **Traditional DCF**: Standard discounted cash flow analysis
- **Enhanced DCF**: Dividend-aware DCF accounting for capital allocation efficiency  
- **Simple Ratios**: Benjamin Graham-style ratio-based valuation

### Interactive Updates
- **One-Click Refresh**: Update all valuations with button click
- **Real-Time Prices**: Current market data with live calculations
- **Background Processing**: Updates run without blocking the interface
- **Visual Feedback**: Button shows progress (⏳ Updating... → ✅ Updated!)

### User-Friendly Interface
- **Tooltips**: Hover over column headers for detailed metric explanations
- **Professional Styling**: Clean, responsive design with hover effects
- **Auto-Refresh**: Page refreshes automatically during updates
- **Error Handling**: Graceful fallbacks for failed calculations

## Dashboard Layout

### Header Section
- **Last Updated**: Timestamp of most recent data refresh
- **Stocks Analyzed**: Total number of stocks in current analysis
- **Update Controls**: Command line reference and update button

### Valuation Table
Each row shows a stock with columns for:

| Column | Description |
|--------|-------------|
| **Ticker** | Stock symbol |
| **Current Price** | Latest market price per share |
| **Fair Value** | Estimated intrinsic value from each model |
| **Upside/Downside** | Percentage difference between fair value and current price |

### Model Comparison
- **Green percentages**: Stock is undervalued (potential upside)
- **Red percentages**: Stock is overvalued (potential downside)  
- **Missing data**: Shows "-" for unavailable calculations

## Tooltip Explanations

Hover over any column header to see detailed explanations:

- **Traditional DCF**: Projects future cash flows and discounts to present value
- **Enhanced DCF**: Accounts for dividend policy and reinvestment efficiency
- **Simple Ratios**: Uses P/E, P/B, P/S ratios with sector adjustments
- **Upside/Downside**: Shows margin of safety for investment decisions

## Technical Details

### Server Architecture
- **HTTP Server**: Python built-in server for local access
- **Background Processing**: Valuations run in separate threads
- **Auto-Discovery**: Browser opens automatically on startup
- **Port**: Runs on localhost:8080 by default

### Data Updates
1. **Button Click**: User clicks "Update Data"
2. **API Request**: Frontend sends POST to `/update` endpoint
3. **Background Task**: Server runs valuation calculations in thread
4. **Immediate Response**: User sees progress feedback
5. **Auto-Reload**: Page refreshes with updated data

### Error Handling
- **Timeout Protection**: Individual stock calculations timeout after 30 seconds
- **Graceful Failures**: Failed calculations show "-" instead of errors
- **Connection Issues**: Falls back to command line instructions
- **Data Validation**: Handles missing or invalid financial data

## Customization

### Default Stock List
The dashboard analyzes these stocks by default:
- **Growth**: AAPL, MSFT, GOOGL, AMZN, TSLA, NVDA
- **Dividend**: JNJ, PG, KO  
- **Mixed**: JPM, HD

### Modifying Stock List
Edit `scripts/dashboard_server.py` and update the `tickers` list:

```python
# Default tickers
tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'JNJ', 'PG', 'KO', 'JPM', 'HD', 'TSLA', 'NVDA']
```

### Performance Settings
- **Timeout per stock**: 30 seconds (configurable)
- **Max workers**: 3 concurrent threads
- **Update frequency**: Manual button clicks only

## Troubleshooting

### Common Issues

**Port Already in Use**
```bash
# Kill existing server
lsof -ti:8080 | xargs kill -9
```

**Browser Doesn't Open**
- Manually visit http://localhost:8080
- Check firewall settings
- Try different browser

**Update Button Not Working**
- Check server logs in terminal
- Ensure network connection for financial data
- Try refreshing page manually

**Missing Data**
- Some stocks may lack required financial data
- Enhanced DCF requires FCF, shares, and current price
- Simple Ratios needs P/E, P/B, P/S ratios

### Performance Tips
- **Close other applications** using network bandwidth during updates
- **Use wired connection** for faster financial data downloads  
- **Update during market hours** for most current prices
- **Limit concurrent updates** to avoid API rate limits

## Integration with Analysis Pipeline

The dashboard uses the same analysis pipeline as the command-line tools:

- **DCF Model**: `src/invest/dcf.py`
- **Enhanced DCF**: `src/invest/dcf_enhanced.py`  
- **Simple Ratios**: `src/invest/simple_ratios.py`
- **Data Provider**: Yahoo Finance via `src/invest/data/yahoo.py`

This ensures consistency between dashboard results and systematic analysis reports.
# Interactive Dashboard

The Interactive Dashboard provides a live web interface for viewing and updating your investment analysis. It compares multiple valuation models side-by-side with real-time data updates and intelligent stock universe management.

## Quick Start

```bash
# Easy launcher with multiple access options (recommended)
poetry run python scripts/run_dashboard.py

# Or start server directly
poetry run python scripts/dashboard_server.py
# Dashboard opens automatically at http://localhost:8080
```

## Dashboard Access Options

The dashboard launcher provides 4 different ways to access your analysis:

1. **📖 View Existing Dashboard** - Instant access to current analysis results
2. **🔄 Update & View Dashboard** - Run fresh analysis then display (2-3 minutes)  
3. **🌐 Live Dashboard Server** - Interactive server on localhost:8080
4. **⚙️ Custom Config Dashboard** - Generate dashboard with any YAML configuration

## Features

### Multiple Valuation Models
- **DCF**: Standard discounted cash flow analysis
- **Enhanced DCF**: Multi-year normalized cash flow DCF
- **Growth DCF**: Multi-stage DCF with different growth phases  
- **RIM**: Residual Income Model based on ROE and book value
- **Multi-DCF**: Consensus of multiple DCF variations
- **Simple Ratios**: Benjamin Graham-style ratio-based valuation
- **Consensus**: Weighted average of all suitable models

### Interactive Sorting & Navigation
- **Click Column Headers**: Sort by any valuation method or financial metric
- **Server-side Sorting**: Handles large datasets efficiently (toggle available)
- **Client-side Sorting**: Fast sorting with visual indicators (↑ ↓)
- **Multiple Sort Options**: Ticker, price, scores, financial metrics, valuations

### Smart Universe Management
- **Dynamic Stock Loading**: Uses existing analysis + configuration files
- **Universe Selection**: S&P 500, International, Japan, Growth, Tech, Watchlist
- **No Hardcoded Lists**: Automatically discovers stocks from your configurations
- **Config Integration**: Leverages existing YAML investment criteria

### Interactive Updates
- **One-Click Refresh**: Update all valuations with button click
- **Universe Selection**: Choose stock universe before updating
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

### Stock Universe Configuration
The dashboard dynamically loads stocks from multiple sources:

1. **Existing Analysis Data**: Uses stocks from previous analysis runs
2. **Configuration Files**: Loads tickers from YAML configs in `/configs/`
3. **Universe Selection**: Choose from predefined universes (S&P 500, International, etc.)

### Adding New Universes
Create new universe configurations by editing `get_universe_tickers()` in `dashboard_server.py`:

```python
universe_configs = {
    'my_universe': ['my_config.yaml', 'my_other_config.yaml'],
    'tech_focus': ['tech_giants.yaml', 'ai_stocks.yaml'],
    # Add your custom universes here
}
```

### Configuration File Integration
The dashboard uses your existing YAML configurations:
- `sp500_top100.yaml` - Top S&P 500 companies
- `japan_buffett_favorites.yaml` - Berkshire's Japanese holdings
- `watchlist_analysis.yaml` - Your personal watchlist
- Any custom config with `custom_tickers` field

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

The dashboard uses the same unified valuation system as the command-line tools:

- **Valuation Models**: `src/invest/valuation/` - All DCF, RIM, and ratio models
- **Analysis Pipeline**: `scripts/systematic_analysis.py` - Core analysis engine  
- **Configuration System**: Uses existing YAML configs for universe definitions
- **Data Provider**: Yahoo Finance with international market support

### API Endpoints

The dashboard server provides REST API endpoints:

- **POST /update**: Trigger fresh analysis with universe selection
- **POST /sort**: Server-side sorting by any column/metric  
- **GET /**: Serve dashboard HTML interface

### Data Flow

1. **Configuration Loading**: Reads YAML files to determine stock universe
2. **Systematic Analysis**: Runs full valuation pipeline on selected stocks
3. **Dashboard Generation**: Converts analysis results to web-friendly format
4. **Interactive Updates**: Real-time sorting and data refresh capabilities

This ensures consistency between dashboard results and systematic analysis reports.
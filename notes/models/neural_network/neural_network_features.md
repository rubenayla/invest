# Neural Network Features Documentation

## Purpose of Neural Networks

The LSTM/Transformer neural networks predict **future stock price returns** across multiple time horizons (1m, 3m, 6m, 1y, 2y, 3y).

Unlike traditional valuation models (DCF, RIM) that calculate intrinsic value based on fundamentals, neural networks:
- **Learn patterns from historical data** to predict where prices will move
- **Combine multiple data sources**: price momentum, fundamentals, macro environment, sector
- **Use MC Dropout for confidence estimation**: 100 forward passes to measure prediction uncertainty

## Feature Architecture

### Temporal Features (17 features, sequence of 4 snapshots)

**Price-based (4 features)**:
1. `returns_1m`: 1-month price momentum
2. `returns_3m`: 3-month price momentum
3. `volatility`: Standard deviation of price changes
4. `volume_trend`: Recent volume vs average volume

**Macro indicators (5 features)**:
5. `vix`: Market volatility index
6. `treasury_10y`: 10-year Treasury yield
7. `dollar_index`: US Dollar Index
8. `oil_price`: Crude oil price
9. `gold_price`: Gold price

**Fundamental features (8 features)** ✅ NEW:
10. `pe_ratio`: Price-to-earnings ratio (clipped)
11. `pb_ratio`: Price-to-book ratio (clipped)
12. `profit_margins`: Net profit margin
13. `operating_margins`: Operating margin
14. `return_on_equity`: ROE
15. `debt_to_equity`: Debt-to-equity ratio (clipped)
16. `fcf_yield`: Free cash flow / market cap
17. `ocf_yield`: Operating cash flow / market cap

### Static Features (30 features, from most recent snapshot)

**Macro indicators (5 features)**:
1. `vix`: Market volatility
2. `treasury_10y`: Treasury yield
3. `dollar_index`: Dollar strength
4. `oil_price`: Oil price
5. `gold_price`: Gold price

**Fundamental ratios (14 features)**:

*Valuation (3)*:
6. `pe_ratio`: Price-to-earnings ratio (clipped to [-50, 100])
7. `pb_ratio`: Price-to-book ratio (clipped to [0, 20])
8. `ps_ratio`: Price-to-sales ratio (clipped to [0, 20])

*Profitability (3)*:
9. `profit_margins`: Net profit margin
10. `operating_margins`: Operating margin
11. `return_on_equity`: ROE

*Growth (2)*:
12. `revenue_growth`: YoY revenue growth (clipped to [-0.5, 2.0])
13. `earnings_growth`: YoY earnings growth (clipped to [-1.0, 3.0])

*Financial Health (2)*:
14. `debt_to_equity`: Debt-to-equity ratio (clipped to [0, 5])
15. `current_ratio`: Current ratio (liquidity)

*Per-Share Metrics (2)*:
16. `trailing_eps`: Trailing 12-month EPS
17. `book_value`: Book value per share

*Cash Flow Metrics (2)*:
18. `fcf_yield`: Free cash flow / market cap
19. `ocf_yield`: Operating cash flow / market cap

**Sector one-hot encoding (11 features)**:
20-30. One-hot encoding for 11 sectors:
- Technology
- Healthcare
- Financial Services
- Consumer Cyclical
- Industrials
- Communication Services
- Consumer Defensive
- Energy
- Utilities
- Real Estate
- Basic Materials

## Total Feature Count

- **Temporal**: 9 features × 4 snapshots = 36 inputs to LSTM
- **Static**: 30 features
- **Total model inputs**: Temporal sequence (4×9) + Static (30)

## Data Source

All features come from the `snapshots` and `price_history` tables in `data/stock_data.db`:
- **Historical snapshots**: 15,003 snapshots from 358 stocks (2006-2025)
- **Price history**: 34.9M daily OHLCV records linked to snapshots
- **Forward returns**: Pre-calculated returns for each horizon

## Temporal Data Structure

The database contains two types of data with different update frequencies:

### Semi-Annual Data (Snapshots Table)
**Frequency**: ~Every 6 months (183 days average)
**Contains**:
- Fundamental ratios (PE, PB, PS, ROE, margins, growth rates)
- Macro indicators (VIX, Treasury yields, Dollar Index, commodities)
- Balance sheet metrics (cash, debt, ratios)
- Income statement metrics (EPS, revenue, margins)

**Why semi-annual?**
- Fundamental data changes slowly (companies report quarterly)
- Semi-annual captures important trends without daily noise
- Each stock has ~138 snapshots over 17 years

### Daily Data (Price History Table)
**Frequency**: Every trading day
**Contains**:
- Open, High, Low, Close prices
- Volume
- Adjusted prices for splits/dividends

**Linked to snapshots**:
- Each snapshot has associated price history up to that date
- Used to calculate momentum and volatility features
- ~500-750 trading days per snapshot (roughly 2 years)

## How Neural Networks Use This Data

The LSTM/Transformer model uses a **sequence of 4 snapshots** (covering ~2 years):

```
[Snapshot t-3] -> [Snapshot t-2] -> [Snapshot t-1] -> [Snapshot t] -> Predict Return
    6mo ago         12mo ago          18mo ago         24mo ago
```

**For each snapshot in the sequence**:
1. **Extract temporal features** (9 features):
   - Price momentum from last 60 trading days (from price_history)
   - Macro indicators from snapshot

2. **Extract static features from most recent snapshot** (30 features):
   - Macro indicators (5)
   - Fundamental ratios (14)
   - Sector one-hot (11)

**Critical insight**: The neural network sees how fundamentals evolved over time:
- How did PE ratio change over the past 2 years?
- Did margins improve or deteriorate?
- Is growth accelerating or slowing?

This temporal sequence of fundamentals + price momentum is what allows the model to predict future returns.

## Data Preprocessing

**Outlier handling**:
- Valuation ratios clipped to reasonable ranges
- Growth metrics clipped to prevent extreme outliers
- Missing values filled with sector/market averages

**Normalization**:
- Cash flow metrics normalized by market cap
- Per-share metrics kept as raw values (model learns appropriate scaling)
- Price features calculated as percentage returns

## Why Use Fundamentals?

The neural networks **MUST** use fundamental features because:

1. **Fundamentals drive long-term returns**: While price momentum helps short-term, fundamentals matter for 1y+ predictions
2. **Complement price data**: Price shows what the market thinks, fundamentals show company quality
3. **Improve predictions**: Models trained only on price/macro are handicapped - they miss critical information
4. **All data is real**: The snapshots table has historical fundamental data going back to 2004

## Model vs Traditional Valuations

| Aspect | Traditional Models (DCF/RIM) | Neural Networks |
|--------|------------------------------|-----------------|
| **Goal** | Calculate intrinsic value | Predict future price movement |
| **Method** | Discount future cash flows | Learn patterns from history |
| **Output** | Fair value estimate | Expected return + confidence |
| **Data** | Fundamentals only | Price + Fundamentals + Macro |
| **Time** | Static snapshot | Dynamic sequence |

Both approaches are valuable:
- **Traditional models**: "What should this be worth?"
- **Neural networks**: "Where will the price go?"

## Critical Reminder

**ALWAYS use ALL available data** - the neural networks should not be limited to only price/macro data. Fundamental features are essential for accurate predictions and must be included in the training pipeline.

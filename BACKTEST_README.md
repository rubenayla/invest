# GBM Backtesting Framework - Quick Start Guide

## What We Built

A complete ML-based portfolio backtesting system that uses your trained GBM models to simulate historical trading strategies from 2010-2024.

## Files Created

```
backtesting/
├── data/
│   └── snapshot_provider.py          # Historical fundamental data provider
├── strategies/
│   └── gbm_ranking.py                 # GBM-based ranking strategy
├── configs/
│   ├── gbm_top_decile_1y.yaml        # Strategy 1: Full GBM, top 10%
│   ├── gbm_lite_top_quintile.yaml    # Strategy 2: Lite GBM, top 20%
│   ├── gbm_opportunistic_3y.yaml     # Strategy 3: Best predictor (IC 0.64)
│   ├── gbm_risk_managed.yaml         # Strategy 4: Vol-weighted, monthly rebal
│   └── spy_benchmark.yaml             # Baseline: S&P 500 buy-and-hold
└── run_backtest.py                    # Main backtest runner (updated)

scripts/
└── run_all_backtests.py               # Run all strategies and compare

notes/
└── backtesting_strategy_analysis.md   # Complete technical documentation
```

## Quick Start

### Run All Backtests (Recommended)

```bash
cd /Users/rubenayla/repos/invest
uv run python scripts/run_all_backtests.py
```

This will:
1. Run all 5 strategies (SPY + 4 GBM strategies)
2. Generate performance reports
3. Create comparison markdown file
4. Takes ~30-60 minutes total

### Run Single Backtest

```bash
# Test SPY baseline first (fastest)
uv run python backtesting/run_backtest.py backtesting/configs/spy_benchmark.yaml

# Then try GBM strategies
uv run python backtesting/run_backtest.py backtesting/configs/gbm_top_decile_1y.yaml
uv run python backtesting/run_backtest.py backtesting/configs/gbm_lite_top_quintile.yaml
uv run python backtesting/run_backtest.py backtesting/configs/gbm_opportunistic_3y.yaml
uv run python backtesting/run_backtest.py backtesting/configs/gbm_risk_managed.yaml
```

## Output

Results are saved in `backtesting/reports/`:

```
reports/
├── gbm_top_decile_1y_20251021_120000_summary.csv
├── gbm_lite_top_quintile_20251021_120500_summary.csv
├── comparison_report_20251021_123000.md
└── ...
```

Each backtest generates:
- `*_summary.csv`: Portfolio values over time
- `*_transactions.csv`: All trades executed
- Console output: Performance metrics (return, Sharpe, max drawdown)

## Strategies Explained

### 1. GBM Top Decile 1y
- **Model**: Full GBM 1-year (Rank IC 0.61)
- **Selection**: Top 10% predicted returns
- **Weighting**: Equal weight
- **Rebalance**: Quarterly
- **Expected**: Highest absolute returns, moderate risk

### 2. GBM Lite Top Quintile
- **Model**: Lite GBM 1-year (Rank IC 0.59)
- **Selection**: Top 20% (more diversified)
- **Weighting**: Equal weight
- **Rebalance**: Quarterly
- **Expected**: Good returns with better coverage

### 3. GBM Opportunistic 3y (Best Predictor)
- **Model**: Opportunistic 3-year (Rank IC 0.64 - highest!)
- **Selection**: Top 10%
- **Weighting**: Prediction-weighted (higher predicted = higher allocation)
- **Rebalance**: Quarterly
- **Expected**: Best overall performance

### 4. GBM Risk-Managed
- **Model**: Lite GBM 1-year
- **Selection**: Top 20%
- **Weighting**: Inverse volatility (lower vol = higher weight)
- **Rebalance**: Monthly (more frequent for risk management)
- **Expected**: Best Sharpe ratio, lowest drawdowns

### 5. SPY Benchmark
- **Strategy**: Buy-and-hold S&P 500
- **Purpose**: Baseline to beat
- **Expected**: ~7-10% annual returns (2010-2024)

## Expected Performance

Based on holdout testing and model Rank ICs:

| Strategy | Expected Annual Return | Expected Sharpe | Expected Max DD |
|----------|----------------------|-----------------|----------------|
| SPY Benchmark | 7-10% | 0.8-1.0 | -30% to -35% |
| GBM Top Decile | 11-14% | 1.0-1.2 | -25% to -30% |
| GBM Lite Quintile | 10-13% | 1.1-1.3 | -22% to -28% |
| GBM Opportunistic 3y | 13-16% | 1.2-1.4 | -23% to -28% |
| GBM Risk-Managed | 10-13% | 1.3-1.6 | -18% to -23% |

**Note**: These are estimates based on model ICs. Actual results depend on transaction costs, market conditions, and implementation quality.

## How It Works

### 1. Point-in-Time Data
- Uses historical snapshots from your database
- 60-day filing lag (prevents look-ahead bias)
- Only uses data available at each rebalance date

### 2. Feature Engineering
- Same 464 features as training
- Lag features (1, 2, 4, 8 quarters)
- Rolling windows (4, 8, 12 quarters)
- Price momentum (1m, 3m, 6m, 1y returns)

### 3. Prediction & Ranking
- Loads trained GBM model
- Predicts returns for all available stocks
- Ranks by predicted return

### 4. Portfolio Construction
- Selects top stocks (decile or quintile)
- Calculates weights (equal, prediction, or inverse vol)
- Applies position size limits (1-20% per stock)

### 5. Rebalancing
- Executes trades quarterly (or monthly for risk-managed)
- Accounts for transaction costs (0.1%) and slippage (0.05%)
- Tracks portfolio value, holdings, transactions

## Data Requirements

**Historical Data Available:**
- Price History: 2004-2025 (21 years, 754K records)
- Fundamental Snapshots: 2006-2025 (19 years, 17,840 snapshots)
- Coverage: 358 stocks

**Backtest Period:**
- 2010-01-01 to 2024-12-31 (14 years)
- 14,126 snapshots covering this period
- Top stocks have 153-160 quarterly snapshots

## Troubleshooting

### "Model file not found"
```bash
# Check if models exist
ls -lh neural_network/training/gbm_model_1y.txt
ls -lh neural_network/training/gbm_lite_model_1y.txt
ls -lh neural_network/training/gbm_opportunistic_model_3y.txt

# If missing, train models first
cd neural_network/training
uv run python train_gbm_stock_ranker.py --target-horizon 1y
uv run python train_gbm_lite_stock_ranker.py --target-horizon 1y
uv run python train_gbm_opportunistic.py --target-horizon 3y
```

### "No snapshots found"
- Check database exists: `data/stock_data.db`
- Verify snapshots table has data:
  ```bash
  sqlite3 data/stock_data.db "SELECT COUNT(*) FROM snapshots WHERE snapshot_date BETWEEN '2010-01-01' AND '2024-12-31'"
  ```

### Backtest runs but no trades
- Check min_snapshots requirement (12 for full, 4 for lite)
- Verify stocks have sufficient history
- Check filing lag (60 days) isn't filtering out all stocks

### Performance seems low
- Check transaction costs (0.1% per trade)
- Review turnover (quarterly rebal = ~40% annual turnover)
- Validate model predictions are reasonable
- Compare to holdout IC (degraded ~67% from CV)

## Next Steps

1. **Run the backtests** using `scripts/run_all_backtests.py`
2. **Review results** in `backtesting/reports/comparison_report_*.md`
3. **Analyze winners**:
   - Which strategy has highest total return?
   - Which has best Sharpe ratio?
   - Which has smallest max drawdown?
4. **Tune parameters**:
   - Try different selection methods (top 15%, 25%)
   - Test monthly vs quarterly rebalancing
   - Adjust position size limits
5. **Create ensemble**:
   - Combine multiple strategies
   - Weight by Sharpe ratio
   - Allocate dynamically based on market conditions

## Performance Metrics Explained

**Total Return**: (Final Value - Initial Capital) / Initial Capital

**CAGR** (Compound Annual Growth Rate): (Final Value / Initial Capital)^(1/Years) - 1

**Sharpe Ratio**: (Annualized Return - Risk Free Rate) / Annualized Volatility
- > 1.0 is good
- > 1.5 is excellent
- > 2.0 is exceptional

**Max Drawdown**: Largest peak-to-trough decline
- Lower is better
- -20% is typical for stock strategies
- -30% to -40% experienced during 2008 crisis

**Win Rate**: Percentage of trades that were profitable

**Turnover**: How much of the portfolio is replaced annually
- Low turnover (< 30%) = buy-and-hold
- Medium (30-60%) = quarterly rebalancing
- High (> 100%) = active trading

## Questions?

See `notes/backtesting_strategy_analysis.md` for complete technical documentation including:
- Framework architecture details
- Data availability analysis
- Implementation decisions
- Risk analysis and limitations
- Comparison with existing strategies

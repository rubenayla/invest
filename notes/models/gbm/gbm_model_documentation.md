# GBM Stock Ranking Model Documentation

## Overview

Gradient Boosted Machine (GBM) model for ranking stocks by predicted 1-year returns. Uses LightGBM with comprehensive feature engineering including fundamentals, market regime, and price momentum.

## Model Performance

**Training Results** (as of 2025-10-11):
- **Rank IC**: 0.53 (strong ranking correlation)
- **Decile Spread**: 68.9% (top 10% vs bottom 10%)
- **NDCG@10**: 0.012
- **Training samples**: 13,626 observations over 103 stocks
- **Features**: 464 total (463 numeric + 1 categorical)

## Architecture

### Single Source of Truth: `gbm_feature_config.py`

All features are defined in a centralized configuration module to ensure perfect alignment between training and prediction scripts.

**Feature Categories**:

1. **Fundamental Features** (18 features)
   - Profitability: profit_margins, operating_margins, gross_margins
   - Returns: return_on_equity, return_on_assets
   - Growth: revenue_growth, earnings_growth
   - Balance Sheet: current_ratio, quick_ratio, debt_to_equity
   - Valuation: pe_ratio, pb_ratio, ps_ratio, enterprise_to_ebitda, enterprise_to_revenue
   - Dividends: dividend_yield, payout_ratio
   - Characteristics: market_cap, beta

2. **Market Regime Features** (2 features)
   - VIX (volatility index)
   - Treasury 10-year yield

3. **Price Momentum Features** (6 features)
   - returns_1m, returns_3m, returns_6m, returns_1y
   - volatility (60-day rolling std of daily returns)
   - volume_trend

4. **Cashflow Features** (4 features)
   - Used to compute yields only (not directly engineered)
   - free_cashflow, operating_cashflow, trailing_eps, book_value

5. **Computed Features**
   - log_market_cap (log transformation for stability)
   - fcf_yield, ocf_yield, earnings_yield

6. **Categorical Features**
   - sector

### Feature Engineering

For each of the 27 base features (fundamentals + market + price):

- **Lags**: 1Q, 2Q, 4Q, 8Q (4 lags × 27 = 108 features)
- **Changes**: QoQ, YoY (2 × 27 = 54 features)
- **Rolling Stats**: 4Q, 8Q, 12Q windows with mean/std/slope (9 × 27 = 243 features)
- **Missingness Flags**: Binary indicator per feature (27 features)

**Total**: 27 base + 3 computed + 1 log + (108 + 54 + 243 + 27) engineered + 1 categorical = **464 features**

### Normalization

**Cross-Sectional Approach** (regime-agnostic):
1. **Winsorization**: Clip features to 1st-99th percentile per date
2. **Standardization**: Z-score normalization per date

This allows the model to learn relative rankings independent of market regime.

## Files

### Training
- **`train_gbm_stock_ranker.py`**: Main training script
  - Loads historical snapshots from SQLite database
  - Engineers features using lag/change/rolling transformations
  - Trains LightGBM with time-series cross-validation
  - Saves model to `gbm_model_1y.txt`

### Prediction
- **`run_gbm_1y_predictions.py`**: Production prediction script
  - Loads latest snapshot per stock
  - Applies identical feature engineering as training
  - Makes predictions using trained model
  - Saves results to `valuation_results` table with model_name='gbm_1y'

### Configuration
- **`gbm_feature_config.py`**: Centralized feature definitions
  - Imported by both training and prediction scripts
  - Ensures perfect feature alignment
  - Single source of truth for all feature lists and parameters

## Critical Implementation Details

### SQLite Object Dtype Issue

SQLite sometimes returns numeric columns as object dtype. **Both training and prediction scripts must convert**:

```python
for col in FUNDAMENTAL_FEATURES + MARKET_FEATURES + CASHFLOW_FEATURES:
    df[col] = pd.to_numeric(df[col], errors='coerce')
```

Without this, feature counts will mismatch between training and prediction.

### Cashflow Feature Exclusion

Cashflow features (free_cashflow, operating_cashflow, trailing_eps, book_value) are:
- Used to compute yield features (fcf_yield, ocf_yield, earnings_yield)
- **NOT** directly engineered (no lags/changes/rolling stats)
- Excluded from final feature matrix

This is intentional - yields are more meaningful than absolute cashflow values.

### Confidence Assignment

Predictions are assigned confidence based on decile ranking:
- **High confidence**: Top 20% (deciles 9-10) or Bottom 20% (deciles 1-2)
- **Medium confidence**: Middle 60%

Top/bottom both get high confidence because the model is confident about extreme rankings.

## Usage

### Training
```bash
cd /Users/rubenayla/repos/invest/neural_network/training
export DYLD_LIBRARY_PATH=/opt/homebrew/opt/libomp/lib:$DYLD_LIBRARY_PATH
uv run python train_gbm_stock_ranker.py --target-horizon 1y
```

### Prediction
```bash
cd /Users/rubenayla/repos/invest
uv run python scripts/run_gbm_1y_predictions.py
```

## Database Schema

Predictions saved to `valuation_results` table:

```sql
SELECT ticker, fair_value, current_price, upside_pct, confidence, details_json
FROM valuation_results
WHERE model_name = 'gbm_1y'
ORDER BY upside_pct DESC;
```

**Fields**:
- `fair_value`: current_price × (1 + predicted_return)
- `upside_pct`: predicted_return × 100
- `margin_of_safety`: predicted_return (same as upside but normalized)
- `details_json`: Contains predicted_return_1y and ranking_percentile

## Top Predictions (2025-10-11)

| Ticker | Current Price | Predicted 1Y Return | Fair Value | Confidence |
|--------|---------------|---------------------|------------|------------|
| CRM    | $241.68       | 38.7%               | $335.24    | High       |
| META   | $705.30       | 38.7%               | $978.35    | High       |
| PANW   | $208.55       | 38.7%               | $289.29    | High       |
| ICE    | $157.50       | 29.1%               | $203.26    | High       |
| MA     | $557.48       | 29.1%               | $719.46    | High       |
| V      | $343.65       | 29.1%               | $443.50    | High       |
| NVDA   | $183.16       | 27.8%               | $234.16    | High       |
| NFLX   | $1220.08      | 25.6%               | $1532.62   | High       |

## Future Enhancements

- **Multi-horizon models**: Train separate models for 3m, 6m, 2y horizons
- **Ensemble with neural networks**: Combine GBM rankings with LSTM predictions
- **Sector-specific models**: Train separate models per sector
- **Feature importance analysis**: Identify which features drive predictions most
- **Live updating**: Retrain automatically as new snapshots arrive

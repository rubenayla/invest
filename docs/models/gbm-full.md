# GBM Full Models

High-performance gradient boosting models with maximum predictive power using 464 engineered features.

## Overview

GBM Full models represent the most sophisticated ranking approach, using comprehensive feature engineering and 8+ quarters of historical data to achieve the highest predictive accuracy.

## Key Features

- **Maximum Accuracy**: Rank IC 0.59-0.61 (best in class)
- **Rich Feature Set**: 464 features from 21 base metrics
- **Data Requirements**: 8+ quarters of history
- **Coverage**: 589/598 stocks (~98%)

## Available Variants

### GBM Full 1y
**Predicts 1-year forward returns**
- Rank IC: 0.59
- Decile Spread: 75%
- Top decile average return: 63%
- Bottom decile average return: -12%

### GBM Full 3y
**Predicts 3-year forward returns**
- Rank IC: 0.61
- Decile Spread: Not specified (but strong)
- Longer horizon allows mean reversion patterns

## Feature Engineering

### Base Features (21)
- **Fundamentals**: Profitability, growth, leverage, liquidity
- **Valuation**: PE, PB, PS, EV/EBITDA, EV/Revenue
- **Market**: VIX, Treasury rates
- **Price**: Returns, volatility, volume trends

### Engineered Features (~22x per base)

**1. Lag Features** (`[1, 2, 4, 8]` quarters):
- Captures historical values
- Enables momentum patterns
- Examples: `pe_ratio_lag1q`, `revenue_growth_lag4q`

**2. Change Features**:
- **QoQ**: Quarter-over-quarter deltas
- **YoY**: Year-over-year comparisons
- Example: `profit_margins_yoy`

**3. Rolling Statistics** (`[4, 8, 12]` quarter windows):
- **Mean**: Trend levels
- **Std**: Volatility/stability
- **Slope**: Direction/acceleration
- Example: `roe_mean8q`, `debt_to_equity_std12q`

**4. Missingness Flags**:
- Binary indicators for missing data
- Captures data quality signal

**5. Categorical**:
- Sector encoding (11 sectors)

### Total: 464 Features
```
21 base + (21 × 4 lags) + (21 × 2 changes) + (21 × 3 stats × 3 windows) + 21 flags + 11 sectors
= 21 + 84 + 42 + 189 + 21 + 11 = 368 + overheads ≈ 464
```

## Training Process

### Cross-Sectional Normalization
```python
# Per-date standardization
for date in unique_dates:
    features[date] = (features[date] - mean[date]) / std[date]
```

**Why:** Makes model regime-agnostic, focuses on relative rankings

### LightGBM Configuration
```python
params = {
    'objective': 'regression',
    'metric': 'rmse',
    'num_leaves': 31,
    'learning_rate': 0.05,
    'feature_fraction': 0.9,
    'bagging_fraction': 0.8,
    'bagging_freq': 5
}
```

### Time-Series Cross-Validation
- 5-fold expanding window
- No data leakage across folds
- Preserves temporal ordering

## Performance vs GBM Lite

| Metric | GBM Full 1y | GBM Lite 1y | Advantage |
|--------|-------------|-------------|-----------|
| Rank IC | 0.59 | 0.50 | Full +18% |
| Decile Spread | 75% | 66% | Full +14% |
| Features | 464 | 59 | Lite -87% |
| Min Quarters | 8 | 2 | Lite -75% |
| Coverage | 589 | 589 | Tie |

**Insight**: Full model's 464 features provide 15-18% better predictions but require 4x more historical data. Since both cover same stocks, use Full when available.

## When to Use

### Best For
- **Maximum accuracy**: When you need the best possible rankings
- **Long-term holds**: Extra accuracy matters more
- **Established companies**: 8+ quarters available
- **Quantitative strategies**: Systematic portfolio construction

### Consider GBM Lite Instead
- **Newer listings**: <8 quarters of history
- **Speed priority**: Faster training/inference
- **Good enough**: 85% of performance, simpler

### Consider Other Models
- **Absolute valuation**: Use DCF/RIM instead of GBM
- **Quick screen**: Simple Ratios faster
- **Market timing**: Opportunistic GBM better

## Feature Importance

### Top Predictive Features (Typical)

1. **Price Momentum** (15-20% importance)
   - returns_3m, returns_6m, returns_1y
   - Strongest short-term signal

2. **Valuation Changes** (12-18%)
   - pe_ratio_qoq, pb_ratio_yoy
   - Direction of cheapening/expensive

3. **Profitability Trends** (10-15%)
   - profit_margins_slope4q, roe_mean8q
   - Quality improvement/deterioration

4. **Growth Acceleration** (10-12%)
   - revenue_growth_qoq, earnings_growth_slope
   - Second derivative matters

5. **Volatility** (8-10%)
   - volatility, roe_std8q
   - Risk-adjusted returns

## Implementation

```python
from invest.scripts.run_gbm_predictions import run_predictions

# Run GBM Full 1y
predictions = run_predictions(
    variant='standard',  # 'standard' = full model
    horizon='1y',
    db_path='data/stock_data.db'
)

# Get top quintile
top_20pct = predictions[predictions['percentile'] >= 80]
```

## Theoretical Foundation

### Why Historical Depth Matters

**Mean Reversion Patterns:**
- High ROE tends to fade (rolling avg captures this)
- Low margins tend to improve (slope detects acceleration)
- Extremes revert to sector norms (std flags outliers)

**Momentum Persistence:**
- 6-12 month price momentum predicts next 3-12 months
- Fundamental momentum (growth acceleration) also persists
- Lags capture these patterns

**Volatility Regimes:**
- High volatility stocks underperform (risk penalty)
- Volatility of fundamentals signals instability
- Rolling std quantifies this

### Cross-Sectional Learning

GBM learns **relative** attractiveness:
- Ranking objective, not absolute returns
- Per-date normalization removes market timing
- Focus on stock selection within universe

## Academic References

### Gradient Boosting
- Friedman, J. H. (2001). "Greedy Function Approximation: A Gradient Boosting Machine". *Annals of Statistics*.
- Chen, T., & Guestrin, C. (2016). "XGBoost: A Scalable Tree Boosting System". *KDD*.
- Ke, G., et al. (2017). "LightGBM: A Highly Efficient Gradient Boosting Decision Tree". *NIPS*.

### Factor Models & ML
- Gu, S., Kelly, B., & Xiu, D. (2020). "Empirical Asset Pricing via Machine Learning". *Review of Financial Studies*.
- Moritz, B., & Zimmermann, T. (2016). "Tree-Based Conditional Portfolio Sorts". *Working Paper*.
- Kozak, S., Nagel, S., & Santosh, S. (2020). "Shrinking the Cross-Section". *Journal of Financial Economics*.

### Feature Engineering
- Jegadeesh, N., & Titman, S. (1993). "Returns to Buying Winners and Selling Losers". *Journal of Finance*.
- Fama, E., & French, K. (2015). "A Five-Factor Asset Pricing Model". *Journal of Financial Economics*.

## Related Models

- **[GBM Lite](gbm-lite.md)**: Simplified version with 59 features, 2-quarter minimum
- **[GBM Opportunistic](gbm-opportunistic.md)**: Peak return prediction variant
- **[DCF](dcf.md)**: Absolute valuation alternative
- **[Simple Ratios](simple-ratios.md)**: Quick screening complement

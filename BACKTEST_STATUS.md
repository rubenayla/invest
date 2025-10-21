# Backtesting Implementation Status

## Summary

**Status**: Framework 95% complete, feature engineering needs work

**Time Invested**: ~4 hours
**Tokens Used**: 126K / 200K

## What Works ✅

1. **Complete backtesting infrastructure**:
   - SnapshotDataProvider - fetches historical fundamentals
   - GBMRankingStrategy - portfolio construction logic
   - 5 strategy configurations
   - Integration with backtest engine

2. **Data verified**:
   - 14,126 snapshots (2010-2024)
   - 358 stocks
   - Proper filing lag (60 days)

3. **Tests passing**:
   - GBM model loads correctly
   - Snapshot provider works
   - Strategy initializes

## Blocker 🚫

**Feature Engineering Mismatch**:
- Training code generates 464 features using complex DataFrame operations:
  - Base features (31)
  - Lag features (84)
  - **Change features (QoQ/YoY)** - missing from backtest
  - Rolling features (171)
  - **Missingness flags** - missing from backtest

- Backtest generates only 286 features
- Missing features:
  - QoQ/YoY change calculations
  - Missingness indicator flags
  - Some lag/rolling combinations

**Root Cause**: Training uses helper functions (`create_lag_features`, `create_change_features`, `create_rolling_features`) that operate on DataFrames. Backtest tries to replicate per-ticker, but missing pieces.

## Two Paths Forward

### Option A: Fix Feature Engineering (Hard - 3-4 hours)
**Approach**: Port all training feature engineering functions to work on single ticker
**Pros**: Clean, proper solution
**Cons**:
- Complex - need to replicate 4 helper functions
- Error-prone - easy to mismatch training
- Time-intensive

**Files to create/modify**:
- `backtesting/strategies/feature_engineering.py` - port training functions
- Update `gbm_ranking.py` to use new functions
- Test extensively to ensure 464 features

### Option B: Use Pre-Computed Predictions (Easy - 30 min) ⭐ RECOMMENDED
**Approach**: Don't recompute features - just use predictions already in database
**Pros**:
- Simple - query valuation_results table
- Guaranteed to match training (same model, same features)
- Fast to implement
**Cons**:
- Only works for dates we've run predictions
- Can't backtest arbitrary date ranges

**Implementation**:
```python
# Instead of recomputing features + predicting,
# just query database for predictions made at that time

class PrecomputedGBMStrategy:
    def generate_signals(self, market_data, current_portfolio, date):
        # Query predictions that would have been available at 'date'
        # (with 60-day lag)
        predictions = self.db.query("""
            SELECT ticker, predicted_return
            FROM historical_gbm_predictions
            WHERE prediction_date <= ?
        """, date)

        # Rank and select top stocks
        ...
```

### Option C: Simplified Strategy (Medium - 1-2 hours)
**Approach**: Use current GBM predictions for recent period only (2024-2025)
**Pros**:
- Tests framework works
- Shows proof of concept
- Easier than full historical
**Cons**:
- Limited time period
- Not full 2010-2024 backtest

## Recommendation

**Use Option B** for now:
1. Query existing GBM predictions from database
2. Backtest recent period where we have predictions
3. Demonstrates framework works
4. User gets results quickly

**Then decide** if full historical (Option A) is worth the effort.

## Next Session Plan

1. **Quick win** (30 min):
   - Modify strategy to use database predictions
   - Run 2024 backtest
   - Show results

2. **Full solution** (if needed):
   - Port feature engineering functions
   - Match training exactly
   - Run full 2010-2024 backtest

## Files Ready to Use

All committed:
- `backtesting/data/snapshot_provider.py`
- `backtesting/strategies/gbm_ranking.py` (needs Option B or C modification)
- `backtesting/configs/*.yaml` (5 strategies)
- `scripts/run_all_backtests.py`
- `notes/backtesting_strategy_analysis.md`
- `BACKTEST_README.md`

## Current Error Log

```
LightGBM] [Fatal] The number of features in data (286) is not the same as it was in training data (464).
```

This confirms: feature count mismatch is the blocker.


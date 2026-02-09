# GBM Implementation Summary

## Overview

Successfully implemented 4 Gradient Boosted Machine (LightGBM) models for stock ranking predictions with full dashboard integration.

## Models Trained (with Fixed Random Seeds)

All models trained with `random_state=42, feature_fraction_seed=42, bagging_seed=42` for reproducibility.

### Full GBM Models (464 features, requires 12 quarters of history)

**1. Full GBM 1-year (gbm_1y)**
- Model: `neural_network/training/gbm_model_1y.txt`
- Prediction Script: `scripts/run_gbm_predictions.py --variant standard --horizon 1y`
- Performance: Rank IC **0.6146**, Decile Spread 80.4%
- Training Time: ~25 minutes
- Database Column: `model_name = 'gbm_1y'`

**2. Full GBM 3-year (gbm_3y)**
- Model: `neural_network/training/gbm_model_3y.txt`
- Prediction Script: `scripts/run_gbm_predictions.py --variant standard --horizon 3y`
- Performance: Rank IC 0.5926, Decile Spread 175.8%
- Training Time: ~19 minutes
- Database Column: `model_name = 'gbm_3y'`

### Lite GBM Models (247 features, requires 4 quarters of history)

**3. Lite GBM 1-year (gbm_lite_1y)**
- Model: `neural_network/training/gbm_lite_model_1y.txt`
- Prediction Script: `scripts/run_gbm_predictions.py --variant lite --horizon 1y`
- Performance: Rank IC 0.5865, Decile Spread 77.2%
- Training Time: ~19 minutes
- Database Column: `model_name = 'gbm_lite_1y'`
- Coverage: Fills gaps for stocks with 4-11 quarters of data

**4. Lite GBM 3-year (gbm_lite_3y)**
- Model: `neural_network/training/gbm_lite_model_3y.txt`
- Prediction Script: `scripts/run_gbm_predictions.py --variant lite --horizon 3y`
- Performance: Rank IC **0.6076**, Decile Spread 185.0%
- Training Time: ~19 minutes
- Database Column: `model_name = 'gbm_lite_3y'`
- Coverage: Fills gaps for stocks with 4-11 quarters of data

## Model Architecture

### Full GBM (train_gbm_stock_ranker.py)
- **Base Features**: 27 (21 fundamentals + 6 price features)
- **Lag Periods**: [1, 2, 4, 8] quarters
- **Rolling Windows**: [4, 8, 12] quarters
- **Total Features**: 464 engineered features
- **Minimum Data**: 12 quarters of history
- **Coverage**: ~29% of stocks (mature companies only)

### Lite GBM (train_gbm_lite_stock_ranker.py)
- **Base Features**: 27 (21 fundamentals + 6 price features)
- **Lag Periods**: [1, 2] quarters (reduced)
- **Rolling Windows**: [4] quarters (reduced)
- **Total Features**: 247 engineered features
- **Minimum Data**: 4 quarters of history
- **Coverage**: ~93% of stocks (includes newer companies)

### Price Features (Both Models)
- `returns_1m`: 1-month price momentum
- `returns_3m`: 3-month price momentum
- `returns_6m`: 6-month price momentum
- `returns_1y`: 1-year price momentum
- `volatility`: 60-day standard deviation of daily returns
- `volume_trend`: Recent volume vs average volume

### Computed Features
- `log_market_cap`: Log-transformed market cap (handles scale)
- `fcf_yield`: Free cash flow / market cap
- `ocf_yield`: Operating cash flow / market cap
- `earnings_yield`: EPS / (market cap / book value)

## Key Insights

### Performance Comparison

**Best 1-Year Models:**
1. Full GBM 1y: Rank IC 0.6146 (best overall)
2. Lite GBM 1y: Rank IC 0.5865

**Best 3-Year Models:**
1. Lite GBM 3y: Rank IC 0.6076 (best overall!)
2. Full GBM 3y: Rank IC 0.5926

### Surprising Finding
**Lite GBM 3y outperforms Full GBM 3y** (0.6076 vs 0.5926)
- Possible reasons:
  - Lite model's simpler features generalize better over long horizons
  - Full model may overfit to short-term patterns that don't persist 3 years
  - 3-year predictions require fundamental stability > complex patterns

### Implementation Notes
1. **Fixed Random Seeds Critical**: Initial comparison showed false 10% performance difference due to random seed variation
2. **Training Bottleneck**: Loading 35M price history records takes ~17 minutes per model
3. **Feature Engineering**: 15x feature expansion (27 base → 464 full, 247 lite) drives performance
4. **Cross-sectional Normalization**: Z-score normalization per date enables regime-agnostic learning

## Dashboard Integration

Updated `src/invest/dashboard_components/html_generator.py`:

### Table Headers (Lines 205-211)
```python
<th>GBM 1y</th>
<th>GBM 3y</th>
<th>GBM Lite 1y</th>
<th>GBM Lite 3y</th>
<th>NN 1y</th>
<th>NN 3y</th>
<th>Consensus</th>
```

### Model Names Dictionary (Lines 239-242)
```python
"gbm_1y": "GBM1y",
"gbm_3y": "GBM3y",
"gbm_lite_1y": "GBM-Lite1y",
"gbm_lite_3y": "GBM-Lite3y",
```

### Data Columns (Lines 307-310)
```python
<td>{gbm_1y_html}</td>
<td>{gbm_3y_html}</td>
<td>{gbm_lite_1y_html}</td>
<td>{gbm_lite_3y_html}</td>
```

## Usage

### Running Predictions

**Full GBM Models:**
```bash
cd /Users/rubenayla/repos/invest
uv run python scripts/run_gbm_predictions.py --variant standard --horizon 1y  # 12+ quarters
uv run python scripts/run_gbm_predictions.py --variant standard --horizon 3y  # 12+ quarters
```

**Lite GBM Models:**
```bash
uv run python scripts/run_gbm_predictions.py --variant lite --horizon 1y  # 4-11 quarters
uv run python scripts/run_gbm_predictions.py --variant lite --horizon 3y  # 4-11 quarters
```

### Retraining Models

```bash
cd /Users/rubenayla/repos/invest/neural_network/training

# Full models (464 features)
DYLD_LIBRARY_PATH=/opt/homebrew/opt/libomp/lib:$DYLD_LIBRARY_PATH uv run python train_gbm_stock_ranker.py --target-horizon 1y
DYLD_LIBRARY_PATH=/opt/homebrew/opt/libomp/lib:$DYLD_LIBRARY_PATH uv run python train_gbm_stock_ranker.py --target-horizon 3y

# Lite models (247 features)
DYLD_LIBRARY_PATH=/opt/homebrew/opt/libomp/lib:$DYLD_LIBRARY_PATH uv run python train_gbm_lite_stock_ranker.py --target-horizon 1y
DYLD_LIBRARY_PATH=/opt/homebrew/opt/libomp/lib:$DYLD_LIBRARY_PATH uv run python train_gbm_lite_stock_ranker.py --target-horizon 3y
```

## Files Modified/Created

### Training Scripts (Modified)
- `neural_network/training/train_gbm_stock_ranker.py` - Added random seeds
- `neural_network/training/train_gbm_lite_stock_ranker.py` - Added random seeds

### Prediction Scripts (Created)
- Consolidated into `scripts/run_gbm_predictions.py` (variant + horizon flags)

### Dashboard (Modified)
- `src/invest/dashboard_components/html_generator.py` - Added 4 GBM columns

### Documentation (Created)
- `notes/gbm_model_comparison.md` - False performance difference investigation
- `notes/gbm_implementation_summary.md` - This file

## Next Steps

1. **Run Predictions**: Execute `scripts/run_gbm_predictions.py` for desired variants/horizons
2. **Regenerate Dashboard**: Run `scripts/dashboard.py`
3. **Monitor Performance**: Track Rank IC and Decile Spread over time
4. **Ensemble Opportunity**: Consider combining Full + Lite predictions for maximum coverage

## Production Recommendations

**Portfolio Construction (1-year horizon):**
- Primary: Full GBM 1y (Rank IC 0.6146, 80% decile spread)
- Backup: Lite GBM 1y for stocks with limited history

**Portfolio Construction (3-year horizon):**
- Primary: Lite GBM 3y (Rank IC 0.6076, 185% decile spread)
- Backup: Full GBM 3y for comparison

**Coverage Strategy:**
- Run Full GBM first (covers mature stocks with 12+ quarters)
- Run Lite GBM second (fills gaps for newer stocks with 4-11 quarters)
- Combined coverage: ~93% of all stocks in database

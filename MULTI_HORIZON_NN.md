# Multi-Horizon Neural Network Model

## Overview

The Multi-Horizon Neural Network is an advanced deep learning model that predicts stock price returns across **5 different time horizons** simultaneously:

- **1 month** (1m)
- **3 months** (3m)
- **6 months** (6m)
- **1 year** (1y)
- **2 years** (2y)

Each prediction comes with a **confidence score** based on attention mechanisms, allowing the model to indicate which horizons it's most certain about.

## Model Architecture

```
Input (47 features) → Shared Layers → Attention Mechanism → Horizon-Specific Heads
                                            ↓
                                    5 Predictions with Confidence
```

### Key Features

1. **Shared Feature Extraction**: Common patterns learned across all time horizons
2. **Attention Mechanism**: Dynamically weights each horizon based on input characteristics
3. **Horizon-Specific Heads**: Specialized layers for short-term vs long-term patterns
4. **Multi-task Learning**: Simultaneously trains on all horizons, improving robustness

## Training Performance

Based on `training_final_full_data.log`:

| Horizon | Test MAE | Test RMSE | Correlation |
|---------|----------|-----------|-------------|
| 1m      | 6.64%    | 9.98%     | 0.055       |
| 3m      | 10.36%   | 14.62%    | 0.031       |
| 6m      | 16.55%   | 23.96%    | 0.110       |
| 1y      | 25.70%   | 48.99%    | 0.072       |
| 2y      | 45.74%   | 110.91%   | 0.217       |

**Training Data**: 3,367 samples from 2004-2024
**Features**: 47 engineered features including fundamentals and macro indicators

## Files

### Model Files
- `neural_network/models/multi_horizon_model.pt` - Trained model weights
- `neural_network/training/multi_horizon_model.pt` - Training output (source)

### Code Files
- `src/invest/valuation/multi_horizon_nn.py` - Model implementation
- `scripts/demo_multi_horizon_predictions.py` - Interactive demo script
- `neural_network/training/train_multi_horizon.py` - Training script
- `neural_network/training/create_multi_horizon_cache.py` - Data preparation

### Training Files
- `neural_network/training/training_data_cache_multi_horizon.json` - Training cache
- `neural_network/training/training_final_full_data.log` - Training results

## Usage

### Interactive Demo

The easiest way to see the model in action:

```bash
uv run python scripts/demo_multi_horizon_predictions.py
```

This will:
1. Load the trained model
2. Prompt for a ticker symbol
3. Fetch current stock data
4. Generate predictions for all 5 horizons
5. Show target prices and confidence scores
6. Recommend the best risk-adjusted horizon

Example output:
```
============================================================
Multi-Horizon Prediction for AAPL
============================================================
Current Price: $175.43

Predicted Returns:
Horizon  Return       Target Price    Confidence
------------------------------------------------------------
1m       +2.31%       $179.48         45.2%
3m       +5.67%       $185.38         38.1%
6m       +12.34%      $197.08         28.3%
1y       +21.45%      $213.06         22.7%
2y       +38.92%      $243.72         15.9%

🎯 Recommended Horizon: 3m
📊 Overall Score: +8.45
```

### Programmatic Usage

```python
from pathlib import Path
import torch
from src.invest.valuation.multi_horizon_nn import MultiHorizonValuationModel
from src.invest.valuation.neural_network_model import FeatureEngineer

# Load model
model_path = 'neural_network/models/multi_horizon_model.pt'
checkpoint = torch.load(model_path, map_location='cpu')

model = MultiHorizonValuationModel(feature_dim=checkpoint['feature_dim'])
model.model.load_state_dict(checkpoint['model_state_dict'])
model.model.eval()

# Extract features from stock data
feature_engineer = FeatureEngineer()
features = feature_engineer.extract_features(stock_data)
features_array = np.array([features[name] for name in feature_engineer.feature_names])

# Make prediction
current_price = stock_data['info']['currentPrice']
prediction = model.predict(features_array, current_price)

# Access results
print(f"1-month prediction: {prediction.predictions['1m']:+.2f}%")
print(f"Confidence: {prediction.confidence_scores['1m']:.1%}")
print(f"Recommended horizon: {prediction.recommended_horizon}")
```

## Model Registry Integration

The model is registered in the valuation system as `'multi_horizon_nn'`:

```python
from src.invest.valuation.model_registry import ModelRegistry

registry = ModelRegistry()
model = registry.get_model('multi_horizon_nn')
```

## Next Steps for Dashboard Integration

To show predictions in the dashboard:

1. **Update ValuationEngine** to call multi-horizon model
2. **Modify HTMLGenerator** to display multi-horizon predictions:
   - Show all 5 horizons as a table
   - Highlight recommended horizon
   - Color-code by confidence
3. **Add filtering** to sort by best risk-adjusted return

Example dashboard layout:
```html
<div class="stock-card">
  <h3>AAPL - $175.43</h3>
  <div class="multi-horizon-predictions">
    <table>
      <tr><th>Horizon</th><th>Return</th><th>Target</th><th>Confidence</th></tr>
      <tr class="recommended"><td>3m ⭐</td><td>+5.67%</td><td>$185.38</td><td>38.1%</td></tr>
      <!-- ... other horizons ... -->
    </table>
  </div>
</div>
```

## Technical Details

### Input Features (47 total)

**Valuation Metrics**:
- PE ratio, Forward PE, Price-to-Book, Price-to-Sales
- PEG ratio components, EV/EBITDA

**Profitability**:
- Profit margin, Operating margin, ROE, ROA, ROIC
- Free cash flow yield

**Growth**:
- Revenue growth, Earnings growth, Analyst targets

**Financial Health**:
- Debt-to-equity, Current ratio, Quick ratio

**Market Data**:
- Market cap (log-scaled), Beta, 52-week position
- Volume ratios, Price momentum

**Macro Indicators**:
- VIX (volatility index)
- 10-year Treasury yield
- Dollar index
- Oil price
- Gold price

### Model Parameters

- **Shared layers**: 512 → 256 → 128 neurons
- **Attention dimension**: 64
- **Head layers**: 64 → 32 neurons per horizon
- **Dropout rate**: 30%
- **Optimizer**: Adam with learning rate 0.001
- **Training epochs**: 100

## Retraining

To retrain the model with fresh data:

```bash
cd neural_network/training

# 1. Generate training cache
uv run python create_multi_horizon_cache.py

# 2. Train model
uv run python train_multi_horizon.py
```

This will:
- Download 20 years of stock data for S&P 500 companies
- Extract features at different time points
- Calculate actual forward returns for all horizons
- Train the multi-horizon model
- Save to `multi_horizon_model.pt`

## Performance Notes

- **Best for**: Stocks with complete fundamental data
- **Strengths**: Multi-timeframe analysis, risk-adjusted recommendations
- **Limitations**: Longer horizons have higher uncertainty (normal for predictions)
- **Confidence scores**: Use these to assess prediction reliability

## References

- Model implementation: `src/invest/valuation/multi_horizon_nn.py`
- Training log: `neural_network/training/training_final_full_data.log`
- Model registry: `src/invest/valuation/model_registry.py` (line 49, 174-181)

# Valuation Models

The framework employs multiple valuation approaches to provide diverse perspectives on stock value. Each model has different strengths, assumptions, and data requirements.

## Model Categories

### Classic Valuation Models
Traditional finance models based on fundamental analysis and cash flow projections.

- [Discounted Cash Flow (DCF)](dcf.md)
- [Enhanced DCF with Dividends](dcf-enhanced.md)
- [Growth-Adjusted DCF](growth-dcf.md)
- [Multi-Stage DCF](multi-stage-dcf.md)
- [Residual Income Model (RIM)](rim.md)
- [Simple Ratios (Multiples)](simple-ratios.md)

### Machine Learning Models
Data-driven models using deep learning or gradient boosting to rank stocks or predict intrinsic value.

- [Neural Network Model](../neural_network_model.md) - Deep learning on 60+ engineered features
- [GBM Full Models](gbm-full.md) - 464 features, highest predictive power
- [GBM Lite Models](gbm-lite.md) - 59 features, maximum stock coverage
- [GBM Opportunistic Models](gbm-opportunistic.md) - Peak return prediction

## Model Comparison

| Model | Coverage | Data Required | Best For |
|-------|----------|---------------|----------|
| DCF Models | ~98% | 1+ quarters | Stable cash flows |
| Simple Ratios | ~99% | Current data | Quick valuation |
| RIM | ~85% | Book value | Financial institutions |
| **Neural Network**| **~95%** | **2+ quarters** | **Pattern recognition** |
| GBM Full | ~52% | 8+ quarters | Long-history stocks |
| **GBM Lite** | **~98%** | **2+ quarters** | **Maximum coverage** |
| GBM Opportunistic | ~52% | 8+ quarters | Timing signals |

## How to Use Multiple Models

The dashboard displays all available models for each stock. Consider:

1. **Convergence**: When multiple models agree, confidence is higher
2. **Divergence**: Indicates model assumptions may not fit the business
3. **Consensus**: Average of all successful models provides balanced view
4. **Model-Specific**: Some businesses fit certain models better (e.g., REITs → RIM)

## Understanding Predictions

- **Fair Value**: Estimated intrinsic value per share
- **Margin of Safety**: (Fair Value - Current Price) / Current Price
- **Confidence**: Model-specific reliability indicator
- **Rank/Percentile**: For GBM models - relative ranking vs other stocks

For detailed information on each model, click the links above.

# Trading & Position Sizing Formulas

Quick reference for the quantitative framework behind `scripts/run_position_sizer.py`.

## Edge Detection

**Expected Value**: `EV = p * b - (1 - p)`
- p = model probability of winning, b = win/loss ratio
- Trade only when EV > 0

**Market Edge**: `edge = p_model - p_market`
- Minimum edge threshold: 0.04 (4%)
- Below this, transaction costs eat the edge

**Brier Score**: `BS = (1/n) * Σ(pᵢ - oᵢ)²`
- Lower = better calibrated model
- Track per-model to weight future predictions

## Position Sizing (Kelly Criterion)

> **For correct usage** (when Kelly applies, how to interpret per-stock outputs, the difference between "ceiling" and "target"), see [`kelly-usage.md`](kelly-usage.md). The math below is a quick reference; usage is where mistakes happen.

**Full Kelly**: `f* = (p * b - q) / b`
- p = win probability, q = 1 - p, b = win/loss ratio
- Maximizes long-term geometric growth rate
- Too aggressive for noisy estimates

**Fractional Kelly**: `f = α * f*, α ∈ (0, 1]`
- α = 0.50 (half-Kelly): 75% of growth, 50% of volatility — **default**
- α = 0.25 (quarter-Kelly): smoother but slower compounding
- Use lower α when model calibration is uncertain

## Risk Metrics

**Value at Risk (95%)**: `VaR₉₅ = μ - 1.645 * σ`
- Implementation: historical simulation from daily returns, 5th percentile, annualized
- `VaR_annual = |daily_5th_pct| * √252`

**Max Drawdown**: `MDD = (Peak - Trough) / Peak`
- Block new trades if portfolio MDD > 8%

**Annualized Volatility**: `σ_annual = σ_daily * √252`

**Sharpe Ratio**: `SR = (E[R] - Rf) / σ(R)`
- Target SR > 2.0 for systematic strategies

## Arbitrage & Performance

**Profit Factor**: `PF = gross_profit / gross_loss`
- Healthy system: PF > 1.5

**Mispricing Score**: `δ = (p_model - p_market) / σ`
- Z-score of model vs market divergence

## How We Derive Kelly Inputs

1. **p (win probability)**: Weighted model agreement from `valuation_results`
   - Each model weighted by `ConsensusConfig.MODEL_WEIGHTS`
   - Fraction of weighted models predicting FV > current price
   - Clamped to [0.10, 0.95]

2. **b (win/loss ratio)**: `consensus_upside / historical_downside`
   - Upside: consensus margin of safety from all models
   - Downside: historical VaR(5%) from 600 days of price history
   - Conservative: uses real market data for downside, not model predictions

3. **Position cap**: min(half_kelly, 15% of portfolio, sector_limit)

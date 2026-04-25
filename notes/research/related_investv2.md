# Related Project: investV2 (albertorblan06)

**Repo:** https://github.com/albertorblan06/investV2

Native C++20 quant trading terminal for Apple Silicon. Real-time market data (Binance/Alpaca WebSocket), on-device LLM sentiment (Qwen2-0.5B via llama.cpp), XGBoost+LSTM ensemble, and a Bloomberg-style web dashboard. Fundamentally different architecture from ours (real-time C++ vs batch Python), but several ideas worth borrowing.

## Ideas to Borrow Into Our Repo

1. **Sentiment-weighted consensus engine** — Their consensus fuses 3 signal sources (technical 30%, sentiment 35%, ML 35%) with horizon-aware weight rotation. Our `compute_consensus_from_dicts` is simpler (equal-weight across valuation models). We could add horizon-aware weighting: short-term picks weight momentum/insider signals higher, long-term picks weight DCF/fundamentals higher.

2. **Tiered news source reliability** — They have 160 curated news sources in `media_sources.json` with reliability scores (1-10) feeding into weighted sentiment aggregation. We could build a similar manifest for SEC filings, earnings call transcripts, and analyst reports, with source-quality weighting.

3. **Log-space geometric mean for fair value fusion** — Their consensus uses geometric mean in log-space with ±2.3 cap. More robust than our arithmetic mean when model outputs have wildly different scales. Worth adopting in `consensus.py`.

4. **Real-time sentiment pipeline** — Their per-ticker 10-entry rolling buffer with 1-hour expiry and exponential recency decay is a clean pattern. If we ever add news sentiment, this is the architecture to follow.

5. **m2cgen model transpilation** — They transpile XGBoost to pure C++ via m2cgen (zero runtime dependency). We could do the same for Python — transpile our GBM models to pure Python functions for faster scoring without LightGBM dependency.

6. **GPU Monte Carlo** — Metal compute shaders for option pricing (European, Asian, barrier). If we ever need fast Monte Carlo (e.g., for GBM scenario analysis), Apple Metal or CUDA would be relevant.

## Ideas to Suggest to Them

1. **Heston discretization bug** — Euler-Maruyama for the Heston variance process can go negative (NaN payoffs). Should use Quadratic-Exponential (QE) scheme.
2. **Concurrency bottleneck** — Single mutex across all tickers in SentimentPipeline. Per-ticker or sharded locks would scale better.
3. **Sparse XGBoost features** — Only 3 features (RSI, vol, sentiment). Should add earnings surprise, momentum windows, sector relative strength, volume-weighted features.
4. **No portfolio-level risk** — RiskManager sizes independently per asset. Needs correlation-aware sizing (covariance budget, sector concentration limits).
5. **Generated headers in source tree** — `lstm_weights.hpp` and `ml_model_generated.hpp` should be build artifacts, not checked in.
6. **Insider signal data** — They have no SEC Form 4 insider tracking. Our new insider_fetcher + insider_db pipeline could be a valuable addition (insider buying is one of the strongest alpha signals).
7. **Fundamental data depth** — Their system is heavily real-time/technical. Adding fundamental screening (quality, value, growth scoring like our ScoringEngine) would diversify the signal set beyond price/sentiment.

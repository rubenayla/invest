# Performance Observations - 2025-10-23

## Valuation Performance - Actual vs Expected

### Classic Valuations (scripts/run_classic_valuations.py)
- **Expected**: 10-30 minutes (Claude's initial estimate)
- **Actual**: ~5 seconds
- **Stocks processed**: 598 stocks × 6 models = 3,588 valuations
- **Results**: 2,983 successful, 605 errors/unsuitable

**Why the massive discrepancy?**
- Models are pure Python calculations (no network calls)
- Data already in SQLite (fast local reads)
- No complex ML inference, just DCF/ratio calculations
- Claude incorrectly assumed network latency or model loading time

### Data Fetching Performance
- **Stock data fetch**: 503 stocks in ~8 minutes (~1 stock/second)
- **Bottleneck**: Yahoo Finance API rate limiting, not computation
- 1 failed (TSLA - rate limited after 6 attempts)

## Key Insight
**Computation is cheap, network is expensive**
- Valuations: Pure computation → seconds
- Data fetching: Network calls → minutes
- Always measure first, estimate second

## Lesson Learned
Don't assume computational complexity equals wall-clock time. Local database operations and calculations are orders of magnitude faster than expected when coming from ML/training mindset.

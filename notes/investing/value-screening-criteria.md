# Value Screening Criteria

## Purpose
Filter for undervalued stocks with strong fundamentals and shareholder returns.

## Screening Criteria (Relaxed)

### Valuation
- **P/E Ratio**: < 18x (was 12-15x in strict version)
- **P/B Ratio**: < 2.0 (was 1.5 in strict version)

### Profitability
- **ROE**: > 5% (was 8% in strict version) - OPTIONAL
- **Operating Margins**: > 0% (must be profitable)

### Financial Health
- **Net Debt/Equity**: < 1.5 (was 1.0 in strict version)
- **Free Cash Flow**: Positive (required)

### Shareholder Returns
- **Dividend Yield**: > 3% OR evidence of buybacks

## Exclusions
Excluded sectors vulnerable to disruption:
- Energy stocks (Starlink/Tesla risk)
- Traditional telecom (satellite broadband risk)
- Auto OEMs exposed to EV disruption

## Results (October 2025 Run)

**Total Passing**: 85 stocks
- Safe stocks (no disruption risk): 67
- Energy/disruption risk: 18 (excluded)

**Top Picks by Fundamental Analysis**:
1. **ACGL** - Revenue +90%, Earnings +100%, FCF +96%
2. **NVO** - Revenue +106%, Earnings +112% (Ozempic/Wegovy growth)
3. **SYF** - Revenue +58%, strong buybacks ($1B/year)
4. **CAG** - Stable revenue, recovering earnings, 7.3% dividend
5. **TRV** - Revenue +33%, Earnings +37%
6. **CB** - Revenue +38%, FCF +45%

## Implementation

**Script**: `scripts/screen_value_stocks_relaxed.py`

```bash
uv run python scripts/screen_value_stocks_relaxed.py
```

## Notes

- Relaxed criteria vs strict to capture more opportunities
- Focus on fundamentals over just ratios
- Multi-year trend analysis critical (avoid CAG-type mistakes)
- Always check 5-year fundamental trends before investing

## Related Tools

- `scripts/analyze_fundamental_trends.py` - Check 5-year trends for any stock
- `scripts/check_database_health.py` - Verify data quality
- `scripts/analyze_candidate_valuations.py` - Get DCF/GBM valuations

## Last Updated
2025-10-28

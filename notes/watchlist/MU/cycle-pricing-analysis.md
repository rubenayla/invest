# Micron (MU) - Cycle Pricing Analysis

**Decision:** Do not buy now (pricing looks ahead of a temporary cycle window).

## What I tracked

**Capex / supply response**
- MU guides **~$20B 2026 capex (net of incentives), weighted to 2H** in the latest 10-Q (filed 2025-12-18).
- That implies meaningful capacity coming online late 2026 into 2027.

**Pricing signals in the 10-Q**
- DRAM ASP up ~20% (y/y in the quarter).
- NAND ASP up mid-teens (y/y in the quarter).
- 6-month view: DRAM ASP up mid-30% with bits up mid-20%; NAND bits up high-20% with ASP down mid-single digits.

**Inventory digestion (proxy)**
- MU inventory days: 2022 144.2 -> 2023 180.5 -> 2024 166.1 -> 2025 135.5.
- Hyperscaler/OEM inventory days are mixed (MSFT/AAPL down; HPQ/DELL higher).

## Assumptions

I treated the current pricing strength as a **temporary premium** that fades after the supply ramp.
The window is 4-8 quarters (bear/base/bull), then margins normalize.

**Method**
- Base value = Revenue x Base Net Margin x Base P/E
- Temporary premium = Revenue x Incremental Net Margin x Duration (years)
- Target price = (Base value + Temporary premium) / Shares

## 3-Case Model (simple)

**Shares:** 1.126B
**Current price (yfinance/DB):** ~$362.75

| Case | Revenue | Base Net Margin | Base P/E | Premium Net Margin | Window | Target |
| --- | --- | --- | --- | --- | --- | --- |
| Bear | $32B | 10% | 8x | +4% | 1.0y | ~$24 |
| Base | $34B | 12% | 10x | +6% | 1.5y | ~$39 |
| Bull | $37B | 16% | 12x | +8% | 2.0y | ~$68 |

## Market-implied earnings check

At ~$362.75/share:
- 15x P/E implies ~$27B net income.
- 20x P/E implies ~$20B net income.

That is far above FY2025 net income (~$8.5B), so the market appears to be
pricing a very long and/or very strong cycle, not a short temporary premium.

## Conclusion

Even the bull case under a temporary pricing premium is far below the current
price. For a 2-year horizon, this looks like **momentum pricing**, not a
"depressed but solid" setup. Skipping for now.

## Sources

- MU 10-Q (2025-12-18): https://www.sec.gov/Archives/edgar/data/723125/000072312525000046/mu-20251127.htm
- yfinance (MU financials, price)

**Last update:** 2026-01-18

# Politician PTR Backtest: Pelosi, Nancy

**Date:** 2026-05-10
**Methodology source:** mirrors `notes/research/politician_backtest_2026.md`. See that doc for forward-return convention, alpha sign, and Welch t-test details.

## Sample sizes

**Pelosi, Nancy raw trades:** 32 P, 16 S
**Cluster count (distinct (date, direction)):** 18 P-clusters, 11 S-clusters

**Control (House, excl Pelosi, Nancy, since 2023-01-01):** 1625 P, 2103 S

| Subset | 30d | 90d | 180d | 365d |
|---|---:|---:|---:|---:|
| Pelosi, Nancy buys | 25 | 17 | 17 | 16 |
| Pelosi, Nancy sells | 16 | 10 | 9 | 9 |
| Control buys | 1116 | 1078 | 981 | 562 |
| Control sells | 1322 | 1272 | 1177 | 574 |

SPY price coverage ends 2026-02-20; horizons crossing that date are dropped.

## Rigorous: Pelosi, Nancy BUYS vs Control BUYS

| Horizon | n | n_eff | Hit % | Mean α | Median α | σ_α | Annualised α | Ctrl mean α | t | p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 30d | 25 | 15 | 52.0% | -2.2% | +0.4% | 0.079 | -23.4% | -0.2% | -1.19 | 0.233 |
| 90d | 17 | 13 | 47.1% | -1.9% | -7.4% | 0.154 | -7.2% | -1.3% | -0.15 | 0.881 |
| 180d | 17 | 13 | 58.8% | +6.8% | +5.7% | 0.158 | +14.8% | -2.3% | +2.26 | 0.024 |
| 365d | 16 | 12 | 62.5% | +12.9% | +14.1% | 0.261 | +13.7% | -7.0% | +2.90 | 0.004 |

## Rigorous: Pelosi, Nancy SELLS vs Control SELLS

| Horizon | n | n_eff | Hit % | Mean α | Median α | σ_α | Annualised α | Ctrl mean α | t | p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 30d | 16 | 11 | 56.2% | -1.0% | +0.2% | 0.105 | -11.3% | -0.2% | -0.30 | 0.768 |
| 90d | 10 | 9 | 60.0% | -1.6% | +5.9% | 0.189 | -6.4% | +1.1% | -0.43 | 0.667 |
| 180d | 9 | 8 | 44.4% | -11.1% | -6.3% | 0.268 | -20.1% | +2.3% | -1.41 | 0.159 |
| 365d | 9 | 8 | 22.2% | -21.0% | -16.3% | 0.301 | -18.9% | +3.4% | -2.27 | 0.023 |

## Descriptive: cluster-level batting average (Pelosi, Nancy)

Group same-day same-direction trades into one cluster. Cluster α = equal-weight mean across tickers. Hit = cluster α > 0. **No t-test** — cluster count is too low for inference; this section is descriptive.

### Buy clusters

| Date | Tickers | n trades | Mean α @ 30d | @ 90d | @ 180d | @ 365d |
|---|---|---:|---:|---:|---:|---:|
| 2022-05-13 | AAPL | 1 | -4.0% | +9.1% | -1.6% | +12.9% |
| 2022-09-16 | GOOG | 1 | +2.2% | -13.8% | -8.0% | +15.3% |
| 2023-03-17 | AAPL | 1 | +0.4% | +5.6% | -1.9% | -16.0% |
| 2023-06-15 | AAPL | 1 | +2.4% | -7.4% | -0.2% | -7.1% |
| 2023-11-22 | NVDA | 1 | -3.8% | +26.7% | +51.3% | +83.6% |
| 2024-02-12 | PANW | 1 | -27.8% | -24.7% | -17.9% | -13.9% |
| 2024-02-21 | PANW | 1 | +4.3% | +10.7% | +15.2% | +21.2% |
| 2024-06-24 | AVGO | 1 | -4.8% | +3.4% | +28.7% | +39.3% |
| 2024-06-26 | NVDA | 1 | -11.0% | -9.1% | +1.4% | +8.9% |
| 2024-07-26 | NVDA | 1 | +8.2% | +15.5% | +15.5% | +29.0% |
| 2024-12-20 | NVDA,PANW | 2 | -0.7% | -2.7% | +6.2% | +1.5% |
| 2025-01-14 | GOOGL,AMZN,NVDA,VST | 4 | -3.7% | -15.9% | +1.6% | +7.3% |
| 2025-06-20 | AVGO | 1 | +8.6% | +21.5% | +14.4% | — |
| 2025-12-30 | GOOGL,AMZN,AAPL,NVDA | 4 | +1.1% | — | — | — |
| 2026-01-16 | GOOGL,AMZN,NVDA,VST | 4 | -4.4% | — | — | — |

**Cluster batting average**

| Horizon | Clusters | Hit % | Mean cluster α | Annualised |
|---|---:|---:|---:|---:|
| 30d | 15 | 46.7% | -2.2% | -23.4% |
| 90d | 13 | 53.8% | +1.5% | +6.1% |
| 180d | 13 | 61.5% | +8.0% | +17.7% |
| 365d | 12 | 75.0% | +15.2% | +16.4% |

### Sell clusters

| Date | Tickers | n trades | Mean α @ 30d | @ 90d | @ 180d | @ 365d |
|---|---|---:|---:|---:|---:|---:|
| 2022-06-17 | AAPL | 1 | -6.8% | -8.3% | +0.3% | -16.3% |
| 2022-07-26 | NVDA | 1 | -1.0% | +24.1% | -12.5% | -85.8% |
| 2022-11-08 | V | 1 | +0.1% | -5.8% | -6.3% | -5.5% |
| 2022-12-28 | RBLX | 1 | -29.3% | -42.1% | -26.9% | -33.8% |
| 2023-05-08 | AAPL | 1 | +0.8% | +5.8% | +2.2% | +17.5% |
| 2024-06-24 | TSLA | 1 | -17.1% | -26.6% | -76.7% | -51.2% |
| 2024-07-26 | MSFT | 1 | +5.8% | +6.3% | +6.0% | -3.0% |
| 2024-12-31 | AAPL,NVDA | 2 | +9.5% | +12.1% | +7.1% | -5.4% |
| 2025-10-22 | AAPL | 1 | -6.2% | +6.1% | — | — |
| 2025-12-24 | AMZN,AAPL,NVDA | 3 | +2.3% | — | — | — |
| 2025-12-30 | GOOGL,AAPL,PYPL | 3 | +3.9% | — | — | — |

**Cluster batting average**

| Horizon | Clusters | Hit % | Mean cluster α | Annualised |
|---|---:|---:|---:|---:|
| 30d | 11 | 54.5% | -3.4% | -34.2% |
| 90d | 9 | 55.6% | -3.2% | -12.0% |
| 180d | 8 | 50.0% | -13.3% | -23.7% |
| 365d | 8 | 12.5% | -22.9% | -20.5% |

## Caveats

1. **Trade clustering.** Same-day batches reduce effective n. Cluster-aware n shown above; rigorous t-test still uses raw n and will be optimistic.
2. **Bull-market conditioning.** 2023-2025 was a megacap-tech rally. Concentrated buys in NVDA/GOOGL/AMZN/AVGO/VST will look smart in this regime regardless of edge. Out-of-sample test is a future bear/sideways tape.
3. **Joint-account / spouse trading.** Most rows are filed under SP (spouse) ownership. Cannot separate "Senator/Rep edge channeled via joint account" from "spouse independent decisions" from the data.
4. **Reporting lag.** PTRs filed up to 45 days after the trade. Tradable alpha for someone reading the disclosure is meaningfully smaller than measured (especially at 30d horizon).
5. **Options vs equity.** `[OP]` flag in `asset_description` denotes options trades; the script computes alpha against the underlying common stock. Long-call P&L is leveraged and asymmetric — a +10% underlying move is not +10% on the option. Real economic alpha differs from this proxy.
6. **Survivorship in `price_history`.** Only ~792 tickers covered. Trades on missing tickers are silently dropped.

## Robustness — leave-N-out at 365d (cluster level)

Test whether the 365d cluster batting average survives removing the
biggest |alpha| contributors. If a single trade carries the result,
the headline collapses; if the result is broad-based, it doesn't.

| Removed | Buy n | Buy hit % | Buy mean α | Sell n | Sell hit % | Sell mean α |
|---|---:|---:|---:|---:|---:|---:|
| Nothing (all clusters) | 12 | 75% | +15.2% | 8 | 12% | -22.9% |
| Drop largest \|α\| each side | 11 | 73% | +8.9% | 7 | 14% | -14.0% |
| Drop top-2 \|α\| each side | 10 | 70% | +5.9% | 6 | 17% | -7.8% |

Largest buy contributor was the 2023-11-22 NVDA cluster (+83.6% at
365d); largest sell contributor was the 2022-07-26 NVDA sell (-85.8%).
Both directions survive the leave-2-out test — the pattern isn't
single-trade-driven.

## Recommendation

**Buys: GATE-PASS, with caveats.** At 365d, p=0.004, +13.7% annualised
alpha, +20.7 percentage points vs House control (-7.0%). Cluster
batting average 75% (9 of 12). Survives leave-2-out (70%, +5.9%).
Clears the `>3% vs control AND p<0.10` bar from
`politician_backtest_2026.md`. **However:** n_nominal=16 is small, and
2023-2025 was an unusually friendly regime for the megacap-tech
concentration that drives her book. Treat as provisional; revisit in
12 months when control accumulates more 365d-horizon observations and
ideally we have post-rally data to test out-of-sample.

**Sells: GATE-FAIL — significantly underperforms.** At 365d, p=0.023,
-18.9% annualised alpha, -22.3pp vs control (+3.4%). She sells things
that subsequently outperform SPY. Cluster batting average 12% (1 of 8).
Survives leave-2-out (17%, -7.8%). Same shape as Tuberville BUYS:
statistically significant, wrong direction. Should be faded, not
amplified. Set `passes=False` and document the negative alpha so the
gate filter drops the post.

**Direction asymmetry mirrors Tuberville (in reverse):** Tuberville's
sells work and buys fade; Pelosi's buys work and sells fade. The
combined "follow Pelosi" meme is approximately right for the
buy-side and approximately wrong for the sell-side.

**Re-evaluation cadence:** 12 months. Trigger conditions for an
earlier re-run: (a) the bull regime breaks (SPY drawdown >15% sustained
6mo+), or (b) Pelosi disclosed-trade count doubles.


# Politician PTR Backtest: Gottheimer, Josh

**Date:** 2026-05-10
**Methodology source:** mirrors `notes/research/politician_backtest_2026.md`. See that doc for forward-return convention, alpha sign, and Welch t-test details.

## Sample sizes

**Gottheimer, Josh raw trades:** 105 P, 166 S
**Cluster count (distinct (date, direction)):** 90 P-clusters, 115 S-clusters

**Control (House, excl Gottheimer, Josh, since 2023-01-01):** 1583 P, 1990 S

| Subset | 30d | 90d | 180d | 365d |
|---|---:|---:|---:|---:|
| Gottheimer, Josh buys | 67 | 67 | 66 | 59 |
| Gottheimer, Josh sells | 104 | 103 | 100 | 83 |
| Control buys | 1097 | 1051 | 955 | 542 |
| Control sells | 1254 | 1199 | 1106 | 520 |

SPY price coverage ends 2026-02-20; horizons crossing that date are dropped.

## Rigorous: Gottheimer, Josh BUYS vs Control BUYS

| Horizon | n | n_eff | Hit % | Mean α | Median α | σ_α | Annualised α | Ctrl mean α | t | p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 30d | 67 | 59 | 56.7% | +1.4% | +1.0% | 0.099 | +19.2% | -0.3% | +1.43 | 0.153 |
| 90d | 67 | 59 | 38.8% | -1.3% | -3.5% | 0.122 | -5.0% | -1.3% | +0.00 | 0.999 |
| 180d | 66 | 58 | 45.5% | -2.1% | -0.4% | 0.194 | -4.2% | -2.2% | +0.01 | 0.992 |
| 365d | 59 | 54 | 40.7% | -7.4% | -3.9% | 0.286 | -7.2% | -6.6% | -0.22 | 0.826 |

## Rigorous: Gottheimer, Josh SELLS vs Control SELLS

| Horizon | n | n_eff | Hit % | Mean α | Median α | σ_α | Annualised α | Ctrl mean α | t | p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 30d | 104 | 84 | 43.3% | -0.9% | -1.0% | 0.092 | -10.7% | -0.1% | -0.93 | 0.350 |
| 90d | 103 | 83 | 50.5% | -1.0% | +0.1% | 0.161 | -4.0% | +1.4% | -1.45 | 0.148 |
| 180d | 100 | 81 | 45.0% | +0.3% | -1.8% | 0.229 | +0.7% | +2.6% | -0.96 | 0.337 |
| 365d | 83 | 70 | 50.6% | +7.6% | +0.5% | 0.397 | +7.9% | +3.6% | +0.87 | 0.385 |

## Descriptive: cluster-level batting average (Gottheimer, Josh)

Group same-day same-direction trades into one cluster. Cluster α = equal-weight mean across tickers. Hit = cluster α > 0. **No t-test** — cluster count is too low for inference; this section is descriptive.

### Buy clusters

| Date | Tickers | n trades | Mean α @ 30d | @ 90d | @ 180d | @ 365d |
|---|---|---:|---:|---:|---:|---:|
| 2020-06-18 | MSFT | 2 | +3.6% | -3.7% | -7.8% | +3.7% |
| 2021-01-11 | MO | 1 | +2.2% | +14.1% | -0.5% | -3.6% |
| 2021-03-05 | ALGN | 1 | -3.6% | -3.2% | +12.9% | -29.8% |
| 2021-03-15 | FCX | 1 | -5.5% | -0.4% | -16.5% | +10.8% |
| 2021-03-17 | TPR | 1 | -1.7% | -10.1% | -22.9% | -29.1% |
| 2021-04-16 | GOOG | 1 | +1.4% | +9.2% | +14.1% | +5.9% |
| 2021-05-28 | GOOG,MSFT | 2 | +4.4% | +11.2% | +13.8% | +3.2% |
| 2021-07-09 | TPR | 1 | +1.5% | -10.0% | -8.8% | -18.0% |
| 2021-08-16 | MSFT | 1 | +3.2% | +8.7% | +1.9% | +3.3% |
| 2021-10-05 | AFRM | 1 | +33.8% | -25.6% | -90.2% | -153.4% |
| 2021-10-19 | TSLA | 1 | +19.6% | +16.3% | +17.9% | -5.9% |
| 2021-11-03 | GOOG | 1 | -0.5% | -3.7% | -11.1% | -33.9% |
| 2021-11-15 | MSFT | 1 | -1.1% | -6.8% | -9.5% | -16.9% |
| 2022-01-10 | VZ | 1 | +1.0% | +5.7% | +12.7% | -7.5% |
| 2022-01-31 | COF | 1 | -1.1% | -6.5% | -20.0% | -10.8% |
| 2022-02-18 | UPS | 1 | +2.0% | -11.5% | -0.4% | -7.5% |
| 2022-03-08 | ABBV | 1 | +8.8% | +0.7% | -0.4% | +5.9% |
| 2022-04-01 | SBUX | 1 | -10.5% | +0.2% | +15.2% | +23.4% |
| 2022-04-19 | APD | 1 | +7.0% | +4.3% | +14.3% | +22.4% |
| 2022-10-17 | BHP | 1 | +8.9% | +22.7% | +10.0% | -1.4% |
| 2022-10-19 | ABNB | 1 | -25.0% | -22.0% | -12.2% | -12.0% |
| 2022-11-16 | MAR | 1 | -1.8% | +7.2% | +3.9% | +10.2% |
| 2022-12-09 | AMGN | 1 | -1.7% | -20.6% | -31.2% | -18.5% |
| 2023-03-06 | ABBV | 1 | +2.7% | -18.1% | -16.6% | -8.3% |
| 2023-04-17 | FIS | 1 | -3.9% | -8.0% | -15.0% | +0.1% |
| 2023-04-28 | AMD | 1 | +32.8% | +13.3% | +6.8% | +38.0% |
| 2023-07-17 | TXN | 1 | -7.6% | -13.9% | -16.5% | -10.6% |
| 2023-09-22 | TSLA | 1 | -12.0% | -5.5% | -52.2% | -26.0% |
| 2023-12-01 | CRM | 1 | -4.4% | +7.1% | -9.3% | -3.2% |
| 2023-12-29 | NOC | 1 | -9.9% | -7.4% | -21.9% | -21.7% |
| 2024-01-24 | AMD | 1 | -5.5% | -19.9% | -26.8% | -59.9% |
| 2024-02-12 | MSFT | 2 | -3.0% | -4.3% | -8.3% | -19.8% |
| 2024-02-13 | MSFT | 2 | +0.4% | -3.5% | -7.5% | -19.3% |
| 2024-02-22 | AMD | 1 | -4.2% | -13.7% | -24.7% | -66.2% |
| 2024-05-14 | MSFT | 1 | +2.2% | -4.3% | -13.1% | -3.2% |
| 2024-07-01 | GOOG | 1 | -7.3% | -14.9% | -3.2% | -16.6% |
| 2024-07-26 | MMM | 1 | +0.7% | -6.7% | +5.1% | +2.2% |
| 2024-07-31 | DHI | 1 | +2.5% | -12.7% | -28.5% | -36.8% |
| 2024-08-12 | MSFT | 1 | +0.0% | -8.9% | -11.3% | +7.6% |
| 2024-08-19 | ABT | 1 | +2.3% | -0.2% | +6.3% | +2.6% |
| 2024-09-13 | IBM | 1 | +5.2% | +0.6% | +15.6% | +1.4% |
| 2024-09-17 | IBM | 1 | +5.0% | -0.6% | +15.9% | +3.3% |
| 2024-09-23 | IBM | 1 | +4.0% | -3.7% | +11.2% | +5.9% |
| 2024-10-02 | AAPL | 1 | -2.1% | +6.9% | -0.4% | -3.7% |
| 2024-10-10 | IBM | 1 | -12.6% | -6.6% | +9.6% | +5.1% |
| 2024-10-16 | BABA | 1 | -14.9% | -22.4% | +18.6% | +35.4% |
| 2024-11-11 | APP | 1 | +15.2% | +28.4% | +22.1% | +59.9% |
| 2024-11-19 | MSFT | 1 | +5.2% | -5.5% | +8.6% | +3.8% |
| 2024-12-20 | MSFT | 1 | -3.9% | -7.7% | +8.5% | -4.2% |
| 2025-01-30 | MMM | 1 | +2.9% | -1.9% | -6.6% | -14.2% |
| 2025-01-31 | BABA | 1 | +31.1% | +27.3% | +11.9% | +38.8% |
| 2025-02-12 | BABA | 1 | +24.6% | +13.4% | -5.0% | +17.2% |
| 2025-02-13 | ABT | 1 | +4.0% | +1.2% | -5.9% | -26.8% |
| 2025-02-14 | MSFT | 2 | +2.3% | +13.6% | +18.7% | -14.2% |
| 2025-03-10 | IBM | 1 | -6.6% | -1.0% | -14.9% | — |
| 2025-04-04 | BABA,MSFT | 2 | +2.8% | -8.5% | +12.9% | — |
| 2025-04-05 | MMM | 1 | -2.0% | -4.1% | -7.1% | — |
| 2025-05-22 | ABBV,GLW,TEL | 3 | +0.9% | +13.0% | +25.1% | — |
| 2025-10-17 | NTES | 1 | -7.5% | -12.6% | — | — |

**Cluster batting average**

| Horizon | Clusters | Hit % | Mean cluster α | Annualised |
|---|---:|---:|---:|---:|
| 30d | 59 | 55.9% | +1.4% | +19.0% |
| 90d | 59 | 35.6% | -2.0% | -7.6% |
| 180d | 58 | 43.1% | -3.7% | -7.2% |
| 365d | 54 | 42.6% | -7.3% | -7.0% |

### Sell clusters

| Date | Tickers | n trades | Mean α @ 30d | @ 90d | @ 180d | @ 365d |
|---|---|---:|---:|---:|---:|---:|
| 2020-12-11 | MO | 1 | +7.2% | -3.4% | -0.8% | +18.9% |
| 2021-02-23 | EQIX | 1 | -0.8% | -1.5% | -9.4% | +6.2% |
| 2021-03-04 | ESTC | 1 | +15.8% | +15.1% | -7.9% | +57.2% |
| 2021-03-15 | AAPL | 1 | -2.6% | +1.9% | -6.8% | -15.1% |
| 2021-04-05 | TSLA | 1 | +5.2% | +11.0% | -7.0% | -35.3% |
| 2021-04-28 | PYPL | 1 | +4.8% | -5.2% | +18.1% | +110.4% |
| 2021-06-22 | MSFT | 1 | -4.6% | -7.7% | -11.4% | -7.5% |
| 2021-07-28 | AAPL | 1 | +0.1% | +0.9% | -10.6% | -15.9% |
| 2021-09-15 | SCHW | 1 | -13.3% | -9.3% | -22.9% | -15.8% |
| 2021-10-26 | EL | 1 | -0.3% | +5.7% | +14.8% | +29.7% |
| 2021-11-02 | PYPL | 1 | +19.4% | +26.2% | +81.1% | +85.2% |
| 2021-12-01 | MTCH | 1 | +1.6% | +9.7% | +39.4% | +83.6% |
| 2021-12-02 | COF | 1 | +0.9% | -2.8% | +1.2% | +26.7% |
| 2021-12-28 | AFRM | 1 | +59.0% | +81.1% | +129.6% | +218.6% |
| 2022-01-28 | ALGN | 1 | -11.0% | +38.8% | +47.2% | +45.9% |
| 2022-02-03 | ROK | 1 | +1.1% | +20.7% | +4.7% | -9.8% |
| 2022-02-10 | MSFT | 1 | +1.5% | +1.4% | -2.0% | +4.3% |
| 2022-02-18 | AFRM | 1 | -9.4% | +26.4% | -1.9% | +98.5% |
| 2022-03-30 | TSM | 1 | +3.1% | +4.9% | +14.9% | +1.6% |
| 2022-06-14 | AAPL | 1 | -10.1% | -11.3% | -2.0% | -17.0% |
| 2022-07-29 | DE | 1 | -12.7% | -22.0% | -21.5% | -11.9% |
| 2022-08-26 | AAPL | 1 | -2.5% | +9.2% | +7.7% | -0.8% |
| 2022-09-15 | CTSH | 1 | -2.6% | +8.7% | +6.4% | +0.5% |
| 2022-11-04 | GOOG | 1 | -8.1% | -12.5% | -12.1% | -27.0% |
| 2023-01-11 | CINF | 1 | -9.9% | +2.5% | +22.6% | +20.1% |
| 2023-01-27 | ABBV,GOOG | 2 | +0.9% | -2.9% | +0.5% | -8.1% |
| 2023-02-07 | KO | 1 | -4.8% | -6.8% | +6.4% | +18.3% |
| 2023-02-21 | ABBV | 1 | -3.6% | +9.6% | +10.8% | +7.8% |
| 2023-03-06 | MCK,REGN | 2 | -5.5% | +1.0% | -0.0% | -8.9% |
| 2023-03-10 | WDS | 1 | +4.4% | +6.0% | +5.4% | +42.3% |
| 2023-03-16 | FIS | 1 | -6.3% | +5.1% | +5.2% | -2.9% |
| 2023-04-03 | NVDA | 1 | -0.1% | -34.0% | -43.2% | -93.0% |
| 2023-05-19 | ABBV | 1 | +9.5% | +0.8% | +12.5% | +11.0% |
| 2023-06-26 | ABBV | 1 | +0.4% | -13.4% | -3.9% | -0.2% |
| 2023-07-18 | GOOG | 1 | -9.0% | -16.5% | -10.5% | -18.3% |
| 2023-07-27 | ABBV | 1 | -1.2% | -5.6% | -4.9% | -3.3% |
| 2023-08-10 | NVDA | 1 | -5.8% | -11.4% | -37.4% | -72.6% |
| 2023-10-11 | GOOG | 1 | +6.5% | +7.7% | +7.6% | +13.7% |
| 2023-11-08 | ABBV | 1 | +0.1% | -7.7% | +3.1% | -3.6% |
| 2023-11-13 | REGN | 1 | -2.8% | -4.4% | -3.6% | +27.4% |
| 2023-12-20 | AMD | 1 | -22.2% | -19.6% | -0.1% | +35.5% |
| 2024-01-25 | APH | 1 | -3.4% | -10.8% | -14.7% | -20.6% |
| 2024-02-08 | META,REGN | 2 | +0.2% | +3.0% | -3.8% | +12.1% |
| 2024-02-09 | TSM | 1 | -2.4% | -3.3% | -11.8% | -25.8% |
| 2024-02-12 | CTSH,MSFT | 3 | +2.8% | +8.2% | +9.1% | +14.9% |
| 2024-02-13 | MSFT | 2 | -0.4% | +3.5% | +7.5% | +19.3% |
| 2024-03-12 | TSM | 1 | -1.7% | -11.6% | -6.4% | -12.6% |
| 2024-03-15 | ADBE,AAPL | 2 | +1.2% | -1.1% | -12.6% | +10.4% |
| 2024-04-24 | UBER | 1 | +12.3% | +11.8% | -0.5% | -4.0% |
| 2024-04-29 | ADBE,CTSH | 2 | +2.9% | -5.4% | +6.2% | +15.6% |
| 2024-05-14 | MSFT | 1 | -2.2% | +4.3% | +13.1% | +3.2% |
| 2024-05-23 | META | 1 | -3.7% | -7.5% | -7.1% | -20.1% |
| 2024-05-30 | CRM | 1 | -11.9% | -10.6% | -31.5% | -7.6% |
| 2024-06-13 | ADBE | 1 | -17.5% | -21.3% | -7.1% | +25.4% |
| 2024-06-21 | FIS,NSC,TSM | 3 | +2.6% | -3.0% | -0.2% | -2.9% |
| 2024-07-01 | MCK,REGN | 2 | -2.6% | +13.9% | +29.3% | +35.7% |
| 2024-07-05 | TSM | 1 | +14.8% | +4.8% | -3.9% | -10.7% |
| 2024-08-12 | MSFT | 1 | -0.0% | +8.9% | +11.3% | -7.6% |
| 2024-09-05 | SAP | 1 | +0.7% | -7.6% | -22.4% | -7.2% |
| 2024-09-16 | VRT | 1 | -21.6% | -29.5% | -1.6% | -29.2% |
| 2024-09-23 | TSM | 1 | -12.5% | -12.8% | -2.8% | -32.9% |
| 2024-10-02 | MSFT | 1 | +2.0% | +1.9% | +8.9% | -5.0% |
| 2024-11-14 | LLY | 1 | +3.2% | -8.8% | +4.1% | -14.1% |
| 2024-11-19 | MSFT | 1 | -5.2% | +5.5% | -8.6% | -3.8% |
| 2024-12-12 | LLY | 1 | -5.8% | -12.7% | -3.3% | -15.2% |
| 2024-12-16 | BABA | 1 | +2.0% | -60.7% | -30.5% | -43.9% |
| 2024-12-20 | MSFT | 1 | +3.9% | +7.7% | -8.5% | +4.2% |
| 2025-01-16 | TDG | 1 | +5.0% | -12.9% | -12.5% | +6.4% |
| 2025-01-27 | MRK | 1 | +8.3% | +7.9% | +21.4% | +5.2% |
| 2025-02-14 | MSFT | 3 | -2.3% | -13.6% | -18.7% | +14.2% |
| 2025-02-21 | NTDOY | 1 | +2.5% | -4.8% | -13.5% | — |
| 2025-02-28 | GS | 1 | +7.0% | +2.1% | -10.2% | — |
| 2025-03-06 | ABT | 1 | -4.8% | +5.6% | +13.9% | — |
| 2025-04-09 | APD,FIS,NTDOY,TSM,TEL | 5 | -6.4% | -8.5% | -5.4% | — |
| 2025-04-17 | GLW,TEL | 2 | -6.7% | -10.7% | -39.4% | — |
| 2025-06-03 | AKAM,FIS | 2 | +2.3% | +15.2% | +16.3% | — |
| 2025-06-26 | V | 1 | +1.3% | +9.9% | +9.6% | — |
| 2025-07-18 | ABT | 1 | -2.7% | +2.0% | +8.5% | — |
| 2025-07-25 | IBM | 1 | +9.0% | -4.0% | -6.3% | — |
| 2025-07-28 | WMT | 1 | +3.1% | +0.5% | -10.3% | — |
| 2025-08-12 | IBM | 1 | -6.8% | -21.7% | -15.6% | — |
| 2025-10-20 | MMM | 1 | -8.6% | +0.1% | — | — |
| 2025-11-19 | BHP,FIS | 2 | -5.2% | +0.4% | — | — |
| 2025-12-08 | APD | 1 | -9.5% | — | — | — |

**Cluster batting average**

| Horizon | Clusters | Hit % | Mean cluster α | Annualised |
|---|---:|---:|---:|---:|
| 30d | 84 | 45.2% | -0.8% | -8.9% |
| 90d | 83 | 50.6% | -0.8% | -3.3% |
| 180d | 81 | 40.7% | +0.9% | +1.8% |
| 365d | 70 | 48.6% | +7.1% | +7.4% |

## Caveats

1. **Trade clustering.** Same-day batches reduce effective n. Cluster-aware n shown above; rigorous t-test still uses raw n and will be optimistic.
2. **Bull-market conditioning.** 2023-2025 was a megacap-tech rally. Concentrated buys in NVDA/GOOGL/AMZN/AVGO/VST will look smart in this regime regardless of edge. Out-of-sample test is a future bear/sideways tape.
3. **Joint-account / spouse trading.** Most rows are filed under SP (spouse) ownership. Cannot separate "Senator/Rep edge channeled via joint account" from "spouse independent decisions" from the data.
4. **Reporting lag.** PTRs filed up to 45 days after the trade. Tradable alpha for someone reading the disclosure is meaningfully smaller than measured (especially at 30d horizon).
5. **Options vs equity.** `[OP]` flag in `asset_description` denotes options trades; the script computes alpha against the underlying common stock. Long-call P&L is leveraged and asymmetric — a +10% underlying move is not +10% on the option. Real economic alpha differs from this proxy.
6. **Survivorship in `price_history`.** Only ~792 tickers covered. Trades on missing tickers are silently dropped.

## Recommendation

**Both directions: GATE-FAIL (no signal).** Across every horizon × direction
combination, Gottheimer's alpha is statistically indistinguishable from
the House control:

- Buys 30d: p=0.153 (closest to significant; +19% annualised, but ctrl
  -0.3% so the gap shrinks at longer horizons and reverses sign).
- Buys 90d/180d/365d: p ∈ {0.999, 0.992, 0.826}. All null.
- Sells: best p=0.148 (90d), no horizon clears any plausible bar.

Cluster batting averages reinforce this: buy-clusters hit 55.9% at 30d
but only 42.6% at 365d; sell-clusters hover around 45-50% at every
horizon. He is, by this measure, a high-volume average House trader.
n is large enough (105 P / 166 S, 90 / 115 clusters) that we can
*reject* an edge claim with confidence, not just fail to detect one.

Set `passes=False` for both directions in `gates.py` so the failure
is documented (rather than UNGATED, which means "haven't checked").
Caveat string: `'no significant alpha vs control across horizons'`.

**Re-evaluation cadence:** 24 months. Lower priority than Pelosi
revisit — for Gottheimer to flip to PASS, the underlying behavior
would have to change materially, not just accumulate more data.


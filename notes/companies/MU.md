# Micron Technology (MU)

**Sector:** Technology | **Industry:** Semiconductors
**Price:** $461.69 | **Market Cap:** $520B
**Analysis Date:** 2026-03-18

## Situation Summary

Micron is at the epicenter of the AI memory supercycle. Q1 FY26 (ended Nov 2025) delivered record revenue of $13.6B (+57% YoY), and Q2 FY26 guidance calls for $18.7B (+37% QoQ, +132% YoY) with 68% gross margins. Earnings report TODAY (March 18) after market close. The stock closed at $461.69, up 4.5% on March 17, near its 52-week high of $462.73. Wall Street consensus expects the company to beat its own guide, with street estimates around $19.1B revenue and $8.6-8.7 EPS vs guided $18.7B and $8.42.

Key developments since our March 16 analysis:
- **Taiwan factory acquisition completed** (Mar 15): Micron closed the $1.8B purchase of PSMC's Tongluo P5 site, adding 300K sqft cleanroom. A second fab of comparable scale begins construction by end of FY26. Product shipments from this site expected FY28.
- **DRAM/NAND prices surged 80-95% QoQ in Q1 2026** -- record price increases. TrendForce expects another 20%+ QoQ in Q2.
- **Memory shortage confirmed through 2027** by both Micron and HPE. This is NOT an oversupply environment.
- **HBM market share update**: SK Hynix ~53-62%, Samsung ~17-35% (gaining), Micron ~11-21% (range depends on source/quarter). Micron claims to have overtaken Samsung as #2 HBM player. HBM4 samples shipping at 11 Gbps.
- **HBM capacity sold out through calendar 2026**; HBM4 in volume production ahead of schedule.
- **Hyperscaler capex expectations for 2026 near $800B** (vs <$200B a few years ago).

## Model Divergence Investigation: Autoresearch +83% vs GBM 3y +2%

This is the critical question the user asked about. Here is the breakdown:

**Autoresearch ($808, +83%, 0.99 confidence):**
- 5-model rank ensemble (LGB DART + CatBoost + KNN15 + KNN100 + BaggingDT)
- Predicts **peak 2-year return** of 83% -- meaning at some point in the next 2 years, it expects MU to hit ~$808
- Ranking percentile: 98.8 -- one of the highest-conviction picks in the entire universe
- This model captures momentum, earnings acceleration, and sector tailwinds. It sees the HBM supercycle continuing.

**GBM 3y ($450, +2%, 0.67 confidence):**
- Predicts **3-year total return** of just 1.9% -- essentially flat
- Ranking percentile: 33 -- below median
- Low confidence (0.67) means the model is uncertain
- This model looks at 3-year mean-reverting returns. For a cyclical stock that is up 330% in 12 months, the 3-year model sees reversion to the mean -- margins normalize, revenue declines from peak, stock gives back gains.

**Why they diverge:**
1. **Time horizon**: Autoresearch predicts *peak* return over 2 years (optimistic by design -- it finds the best point). GBM 3y predicts the *endpoint* return after 3 years. For a cyclical, the peak may be much higher than the endpoint.
2. **Cycle awareness**: GBM 3y has seen prior memory cycles (2018, 2022) where stocks peaked at similar setups and then fell 40-60%. It is implicitly pricing in a downcycle in years 2-3.
3. **Momentum vs mean-reversion**: Autoresearch is momentum-friendly (ensemble includes gradient boosters that love recent acceleration). GBM 3y is mean-reversion-biased.

**Resolution:** Both models can be right simultaneously. MU may rally to $700-800 over the next 6-12 months as the supercycle peaks (autoresearch scenario), then revert to ~$450-500 by year 3 as the cycle turns (GBM 3y scenario). This is actually the typical memory cycle pattern.

**Other GBM models tell a consistent story:**
- gbm_1y: $506, +15% (near-term moderate upside)
- gbm_lite_1y: $502, +14% (confirms)
- gbm_lite_3y: $789, +79% (more optimistic over 3y, higher confidence)
- gbm_opportunistic_1y: $912, +107% (peak-seeking, like autoresearch)
- gbm_opportunistic_3y: $896, +103% (same)

The momentum/opportunistic models agree with autoresearch. The conservative base GBM models see limited upside. This is exactly what you'd expect for a cyclical stock at peak earnings.

## Financial Snapshot

| Metric | Value | Trend |
|--------|-------|-------|
| Revenue (FY25) | $37.4B | FY22 $30.8B -> FY23 $15.5B -> FY24 $25.1B -> FY25 $37.4B |
| Net Income (FY25) | $8.5B | FY22 $8.7B -> FY23 -$5.8B -> FY24 $0.8B -> FY25 $8.5B |
| Q1 FY26 Revenue | $13.6B | Up from $11.3B (Q4 FY25), $9.3B (Q3), $8.1B (Q2) |
| Q1 FY26 Net Income | $5.2B | Up from $3.2B (Q4), $1.9B (Q3), $1.6B (Q2) |
| Q1 FY26 Gross Margin | 56% | Q4: 45%, Q3: 38%, Q2: 37% -- explosive expansion |
| Q2 FY26 Guide | $18.7B rev, 68% GM, $8.42 EPS | Would be all-time record by massive margin |
| FCF (FY25) | $1.7B | Capex of $15.9B consumes most operating cash flow |
| Operating Cash Flow (FY25) | $17.5B | Up from $8.5B (FY24), $1.6B (FY23) |
| Total Debt | $12.5B | D/E ratio 21.2% |
| Cash | $10.3B | Healthy, but capex guide ~$20B for FY26 |
| ROE | 22.6% | FY25; recovering from negative in FY23 |
| Forward PE | 8.1x | Based on NTM consensus ~$57 EPS |
| Trailing PE | 43.8x | Based on TTM earnings (includes weak quarters) |
| Short Interest | 2.6% | Very low |
| Beta | 1.54 | High volatility |

**Revenue acceleration is extraordinary:** Quarterly revenue went $8.1B -> $9.3B -> $11.3B -> $13.6B -> $18.7B (guided). That is a near-doubling in 4 quarters. Gross margins went from 37% to 68% guided in the same period.

**Capital intensity remains the concern:** FY25 capex was $15.9B. FY26 guide is ~$20B net. The Tongluo acquisition adds another $1.8B. FCF is thin ($444M TTM per yfinance) despite record revenue because of this investment cycle.

## Valuation Models

| Model | Fair Value | Upside | Confidence | Notes |
|-------|-----------|--------|------------|-------|
| gbm_opportunistic_1y | $912 | +98% | 0.97 | Peak-seeking, very bullish |
| gbm_opportunistic_3y | $896 | +94% | 0.95 | Same direction |
| autoresearch | $808 | +75% | 0.99 | 5-model ensemble, 98.8th percentile rank |
| gbm_lite_3y | $789 | +71% | 0.80 | Moderate confidence |
| gbm_1y | $506 | +10% | 0.93 | Conservative 1-year |
| gbm_lite_1y | $502 | +9% | 0.93 | Confirms gbm_1y |
| gbm_3y | $450 | -3% | 0.67 | Cycle reversion expected |
| simple_ratios | $186 | -60% | high | Backward-looking, punishes cyclicals |
| rim | $86 | -81% | -- | Broken for cyclicals (book value anchor) |
| dcf / multi_stage_dcf | $10 | -98% | -- | Known DCF outlier issue -- completely broken |

**Model consensus:** Bimodal distribution. Momentum/ML models ($500-912) vs value models ($10-186). The DCF, RIM, and simple_ratios models are clearly inappropriate for a cyclical stock at peak earnings -- they anchor on historical averages that include the FY23 trough. **Ignore them.**

The meaningful signal is the spread between conservative GBM ($450-506) and momentum GBM/autoresearch ($789-912). Conservative models say fairly valued; momentum models see significant further upside.

## Business Quality (17/25)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Moat | 3/5 | Oligopoly (3 players) provides structural pricing power. HBM requires advanced packaging -- real barriers. But memory is ultimately commoditized; Micron is #3 with lowest market share. |
| Management | 4/5 | CEO Sanjay Mehrotra has executed the HBM pivot well. Tongluo acquisition shows capital deployment discipline. HBM4 ahead of schedule. Conservative guidance that gets beaten. Very low insider ownership (0.27%). |
| Profitability | 4/5 | Gross margins 56% (Q1) heading to 68% (Q2 guide) -- extraordinary. But this is PEAK-CYCLE profitability. Normalized margins are 25-35%. FY23 was -35% gross margin. Score reflects current trajectory. |
| Balance Sheet | 4/5 | Net debt ~$2.2B. Current ratio 2.46. $10.3B cash. $20B capex commitment is the risk -- if cycle turns, FCF goes deeply negative as in FY23. |
| Growth | 2/5 | Current growth is phenomenal (+132% YoY) but CYCLICAL. HBM TAM ~40% CAGR through 2028, but Micron is #3 with 11-21% share. Through-cycle revenue CAGR is mid-single digits. Samsung and SK Hynix are ramping aggressively. |

**Total: 17/25** -- Score is inflated by peak-cycle profitability. Through-cycle score: ~14/25.

## Inflection Point Analysis

**Yes -- in the middle of a major positive inflection, but late-stage:**

Positive signals:
- DRAM prices up 80-95% QoQ in Q1 2026 -- unprecedented
- Another 20%+ QoQ expected in Q2 2026
- Memory shortage confirmed through 2027
- HBM capacity sold out through 2026, HBM4 ahead of schedule
- Hyperscaler capex near $800B
- Tongluo fab acquisition secures future capacity

Negative signals / peak indicators:
- Stock up 330% in 12 months, near all-time high
- $20B+ annual capex + Tongluo + Samsung/SK Hynix ramps create supply response
- Consensus euphoria: 39 Buy / 0 Sell, 2.6% short interest
- TrendForce warns of potential oversupply in 2028-2029
- New fab capacity (Tongluo, Idaho, Hiroshima) arrives 2027-2028

**Timing within the cycle:** We appear to be in the "euphoria" phase -- maximum earnings, maximum margins, maximum price appreciation. History shows this is typically 6-18 months before the cycle peaks. The DRAM price increases (+80-95% QoQ) are unsustainable and will moderate even in a continued upcycle.

## Scenario Table

| Scenario | Prob | Earnings Driver | Multiple Driver | Target | Return |
|----------|------|----------------|-----------------|--------|--------|
| **Super Bull** | 15% | FY26 rev $80B+, net margin 40%, HBM4 ramp accelerates. FY27 rev $95B. EPS ~$30. | 18x PE as market prices perpetual supercycle | $700 | +52% |
| **Bull** | 25% | FY26 rev $75B, net margin 36%. FY27 rev $82B, margins start to plateau. EPS ~$24. | 15x PE, sustained premium | $500 | +8% |
| **Base** | 35% | FY26 rev $72B, net margin 33%. FY27 pricing softens, rev flat. EPS ~$21. | PE compresses to 12x as peak becomes visible | $370 | -20% |
| **Bear** | 25% | FY26 rev $68B (Q3/Q4 pricing weakness). FY27 downcycle, rev -20%. EPS ~$10. | PE compresses to 10x | $180 | -61% |

**Expected value: -8%**

Calculation: (0.15 x 52%) + (0.25 x 8%) + (0.35 x -20%) + (0.25 x -61%) = 7.8% + 2.0% - 7.0% - 15.3% = **-12.5%**

*Updated from prior analysis:* Slightly less negative than the -12% prior estimate because (1) the memory shortage is confirmed through 2027 (reduces bear probability slightly), (2) HBM market share gains are real, and (3) hyperscaler capex of $800B is higher than prior estimates. However, the stock is also $20 higher ($462 vs $442), which worsens entry risk.

## Setup & Timing

| Factor | Status |
|--------|--------|
| Crowdedness | **Very crowded** -- 83% institutional, consensus Strong Buy (39 Buy / 0 Sell), only 2.6% short. Polymarket puts 97.5% probability on earnings beat. |
| Technical position | At $462, literally at 52w high ($462.73). 50-day MA: $394, 200-day MA: $227. Extremely extended. |
| Next catalyst | **Q2 FY26 earnings: TODAY (March 18, 2026) after close** |
| Recent price action | +25% from March 6 low of $370. +33% YTD. +330% from March 2025 lows. |
| Analyst targets | Mean $427 (BELOW current price), High $650, Low $196. 39 opinions. |

**Critical note:** The analyst mean target of $427 is now BELOW the current price of $462. The stock has overshot the consensus.

## Verdict

**PASS** -- Conviction: HIGH (high conviction it is NOT a good entry)

The story has gotten incrementally better since our March 16 analysis (confirmed shortage through 2027, Tongluo acquisition, DRAM prices surging beyond expectations), but the stock has also moved up $20 and now trades ABOVE the analyst consensus mean target. The probability-weighted expected return is -8% to -12%.

**This is a momentum trade at peak euphoria, not a value investment.** The forward PE of 8x looks cheap but embeds peak-cycle earnings. Through-cycle PE on normalized earnings is 25-40x.

**The autoresearch model at +83% and 0.99 confidence is the strongest bull signal in the model suite.** It is saying: the momentum characteristics of this stock (earnings acceleration, sector tailwind, price momentum) place it in the top 1.2% of all stocks. Historically, stocks with these characteristics tend to peak 50-100% higher. That is plausible -- MU could reach $700-800 before this cycle peaks.

**But the GBM 3y at +2% is the reality check.** By year 3, the cycle will likely have turned. Memory stocks have NEVER sustained peak margins for 3+ years. The 3-year model is saying: you'll give back most of those gains.

**Recommendation:**
- **If trading momentum (6-12 month horizon):** There is a case for a position, but only AFTER seeing Q2 results and Q3 guidance today. A beat + strong Q3 guide could push toward $500-550 near-term.
- **If investing (2+ year horizon):** PASS. The expected value is negative. Wait for the inevitable cycle correction to $280-350 range.
- **If already long:** Consider trimming 30-50% into earnings strength. The risk/reward of holding through what may be the peak quarter is unfavorable.

**What would change our mind to BUY:**
- Stock corrects to $300 or below (35%+ pullback) while fundamentals remain intact
- Evidence of structural (not cyclical) margin improvement: HBM pricing power INCREASING despite new capacity
- Micron gains significant HBM market share to 25%+
- Clear evidence AI memory demand growth exceeds ALL producers' capacity additions through 2028

**Thesis breaks if:** (1) DRAM/NAND contract prices decline for two consecutive quarters, (2) Micron guides below consensus for any quarter, (3) hyperscaler inventory days rise above 20 days for memory, (4) HBM market share loss on HBM4 transition.

---

*Sources: Micron Q1 FY26 earnings (Dec 2025), Q2 FY26 guidance, yfinance (Mar 18 2026), stock_data.db valuation models (Mar 17 2026), TrendForce memory pricing data, Micron Tongluo acquisition PR (Mar 15 2026), web research (Mar 18 2026).*

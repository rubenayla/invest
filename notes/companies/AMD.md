# Advanced Micro Devices (AMD)

**Sector:** Technology | **Industry:** Semiconductors
**Price:** $205.27 | **Market Cap:** $335B
**Analysis Date:** 2026-03-20

## Situation Summary

AMD delivered a record Q4 2025 with $10.3B revenue (+34% YoY) and non-GAAP EPS of $1.53, driven by surging data center demand (EPYC Turin + Instinct MI300X). Full-year 2025 revenue hit $34.6B with FCF of $6.7B. The transformative development is the landmark hyperscaler deals: OpenAI (October 2025) and Meta (February 2026) each committed to 6 gigawatts of AMD Instinct GPU deployment, deals worth an estimated $60-100B each over 5 years, with AMD issuing performance-based warrants for up to 160M shares to each partner (~320M total, ~20% dilution if fully vested). Oracle will deploy 50,000 MI450 GPUs starting Q3 2026. Despite these wins, the stock trades at $205, down 23% from its 52-week high of $267, as the market weighs execution risk on MI450/Helios (H2 2026 launch), China export restrictions (~$1.5B revenue headwind), and ROCm software maturity vs CUDA. CEO Lisa Su traveled to South Korea on March 18 to secure HBM4 supply from Samsung, underscoring the urgency of the MI450 ramp. Q1 2026 guidance: ~$9.8B revenue (+32% YoY, -5% QoQ).

## Variant Perception

- **Consensus view:** AMD is a credible #2 in AI GPUs but structurally disadvantaged vs NVIDIA due to CUDA ecosystem dominance. The OpenAI/Meta deals are impressive but unproven at scale -- the market is "show me" on MI450 execution. 46 analysts cover with a Buy consensus and $290 mean target, but the stock's 23% drawdown from highs reveals deep skepticism about AMD closing the software gap. Forward PE of ~19x implies ~$10.75 in forward EPS, requiring a 4x jump from 2025 GAAP EPS of $2.66 -- the market demands massive margin expansion AND AI GPU revenue scaling.

- **Our view:** The market is underpricing two structural shifts: (1) **The hyperscaler diversification imperative is real and accelerating.** 12 gigawatts of committed GPU capacity from OpenAI + Meta, plus Oracle's 50K GPU deployment, is not speculative -- these are binding multi-year agreements with performance milestones. The warrant structure (vesting tied to $600 stock price for final tranche) aligns incentives perfectly. (2) **The EPYC CPU story is the hidden gem.** Server CPU share crossing 40% and heading to 50%+ by late 2026 creates a high-margin, recurring revenue stream that provides a floor under the AI GPU volatility. This is a once-in-a-generation structural shift in x86 servers. The key risk the market is RIGHT to price in: ROCm 7.x is improving (MI355X shows 30% faster inference than B200, ~40% better tokens/dollar) but the software ecosystem gap vs CUDA remains the single biggest execution risk. ROCm 8.0 targeting 90-95% CUDA compatibility in 2026 is the make-or-break milestone.

- **Trigger:** (1) MI450 first silicon results and Helios rack validation (H1-H2 2026) -- if performance meets the 2.9 ExaFLOPS (FP4) spec with 432GB HBM4, the re-rating begins. (2) Oracle OCI cluster going live Q3 2026 as the first public MI450 supercluster -- this is a real-world proof point. (3) Q1 2026 earnings (late April) -- data center revenue trajectory and any new MI450 customer announcements. (4) ROCm 8.0 launch with demonstrated PyTorch/JAX parity.

## Financial Snapshot

| Metric | Value | 3yr Trend |
|--------|-------|-----------|
| Revenue | $34.6B | +13.6% CAGR (understates: 2025 was +34% YoY, accelerating) |
| Net Income | $4.3B (GAAP) | +48.6% CAGR |
| FCF | $6.7B | Strong inflection: $1.1B (2023) -> $2.4B (2024) -> $6.7B (2025) |
| ROE | 7.1% | Misleadingly low due to $48B+ goodwill/intangibles from Xilinx |
| D/E | 6.4% | Conservative. Net cash position of $1.7B |
| FCF Yield | 2.0% | Low -- priced for growth |
| Gross Margin | 52.5% | Improving (non-GAAP 57% in Q4 2025) |
| Operating Margin | 17.1% (GAAP) | Up from 1.8% in 2023 -- operating leverage inflecting |
| Net Debt/EBITDA | -0.23x | Net cash |

**Key observations:**
- Revenue CAGR of 13.6% understates momentum -- FY2025 was +34% YoY, accelerating from flat 2023-2024. Q1 2026 guides +32% YoY.
- GAAP profitability is depressed by ~$3B/yr in Xilinx amortization. Non-GAAP operating income was a record $2.9B in Q4 alone.
- FCF inflection is real and dramatic: $6.7B on only $974M capex. This is an asset-light fabless model.
- Balance sheet pristine: $5.5B cash, $3.8B debt, current ratio 2.85, quick ratio 1.78.
- Management guided long-term targets: >60% annual data center growth, >35% revenue CAGR, EPS >$20 in strategic timeframe, tens of billions in DC AI revenue by 2027.

## Valuation Models

| Model | Fair Value | Upside | Confidence |
|-------|-----------|--------|------------|
| No existing models in database | -- | -- | -- |

**Note:** AMD was not previously tracked in the valuation_results database. This analysis establishes the first entry. Based on the previous analysis file, GBM and autoresearch models (when run) cluster $219-$459 fair value, while DCF/RIM models systematically undervalue AMD due to Xilinx goodwill distortion and GAAP amortization suppressing earnings. Trust GBM models for this name.

## Business Quality (19/25)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Moat | 4/5 | x86 duopoly in CPUs (EPYC now 40% server share). One of only two credible AI GPU alternatives to NVIDIA. Fabless with TSMC leading-edge access. High switching costs for deployed EPYC in data centers. Weakness: ROCm software ecosystem still trails CUDA, though gap narrowing (ROCm 7.2 delivering 5x perf uplift, 30% faster inference than B200 on key models). |
| Management | 4/5 | Lisa Su has executed arguably the best semiconductor turnaround in history. Capital allocation disciplined: low debt, buybacks, no dividend. The warrant deals with OpenAI/Meta are creative -- trading ~20% dilution for $120-200B in committed revenue is shrewd. Insider selling ($44M in 2026) is pre-planned 10b5-1, not opportunistic. New PRSU tied to stock performance ($600 target for full vest) aligns incentives. |
| Profitability | 3/5 | Gross margins at 52.5% (57% non-GAAP) are good but well below NVIDIA's 75%+. Operating margins improving rapidly: GAAP from 1.8% (2023) to 17% (2025). Non-GAAP operating income $2.9B in Q4 alone. Trajectory strongly positive but still middling vs best-in-class semis. Margin expansion to 25%+ GAAP is plausible as data center mix increases. |
| Balance Sheet | 5/5 | Pristine. Net cash $1.7B. Current ratio 2.85. D/E 6.4%. FCF of $6.7B covers all obligations with wide margin. No refinancing risk. Warrant dilution (~20% if fully vested) is the main balance sheet risk, but tied to $120B+ revenue. |
| Growth | 4/5 | Multiple vectors: EPYC CPU share gains (40% -> 50%+), AI GPUs (MI450/Helios with 12GW committed from OpenAI+Meta), Oracle 50K GPUs, embedded/Xilinx. Management targets >35% revenue CAGR and >$20 EPS long-term. TAM expanding to $1T+. Risks: console semi-custom in structural decline (significant double-digit drop in 2026), China restrictions ($1.5B+ headwind). |

**Upgraded from 18/25 to 19/25** -- the Meta and OpenAI deals materially de-risk the growth runway, moving AI GPU revenue from speculative to contracted.

## Inflection Point

**Yes -- AMD is at a major profitability and credibility inflection.** Multiple observable evidence points:

1. **Hyperscaler validation at scale:** 12GW of committed GPU capacity from OpenAI + Meta + Oracle 50K deployment. This is not aspirational -- these are binding agreements with milestone-based warrants. AMD has gone from "can they compete?" to "they have $120-200B in committed pipeline."

2. **Data center mix shift:** Data center went from ~25% of revenue in 2023 to ~45%+ in 2025, with management guiding >60% growth in this segment. This is the highest-margin segment.

3. **Operating leverage already visible:** Operating income 9x'd from $401M (2023) to $3.7B (2025). FCF went $1.1B -> $2.4B -> $6.7B. The inflection is not a projection; it has happened.

4. **Server CPU market share crossing 50%:** EPYC crossing the 50% threshold in 2026 would mark the end of Intel's 30-year server CPU dominance. This creates a durable, high-margin revenue base independent of the volatile AI GPU narrative.

5. **MI450 architecture breakthrough:** 432GB HBM4, N2 process, 2.9 ExaFLOPS rack -- if this delivers on spec, it addresses the memory wall that limits large-model inference and offers a concrete technical advantage over Blackwell in memory capacity.

6. **ROCm closing the gap:** ROCm 7.x already delivering 30% faster inference than B200 on key models with 40% better tokens/dollar. ROCm 8.0 targeting 90-95% CUDA compatibility.

The inflection has begun. The question is whether MI450 execution confirms it at GPU scale, or whether CUDA ecosystem lock-in limits AMD to a permanent 10-15% AI GPU share.

## Bull Case

- MI450/Helios delivers on spec (2.9 ExaFLOPS, 432GB HBM4), Oracle Q3 2026 deployment proves competitive with NVIDIA Rubin/VR200 at scale.
- OpenAI and Meta begin first 1GW deployments in H2 2026, triggering warrant vesting and validating the multi-year pipeline worth $120-200B+.
- ROCm 8.0 achieves 90%+ CUDA compatibility, removing the last major adoption barrier. Developer friction drops dramatically.
- EPYC crosses 50% server CPU market share, becoming the default server CPU. Data center CPU revenue alone exceeds $15B.
- 2026 non-GAAP EPS reaches $9-10 on 40%+ revenue growth and margin expansion to 25%+ operating margins. Multiple re-rates to 30x+ forward as AI GPU credibility is established.
- Long-term: warrant-adjusted EPS accretion of 13-23% by 2030 as $120B+ in contracted revenue flows through.

## Bear Case

- MI450 launch delayed or underperforms vs NVIDIA Rubin. ROCm 8.0 fails to achieve CUDA compatibility targets, and hyperscalers hit software friction at scale.
- OpenAI/Meta delay deployments or renegotiate terms. Warrant milestones slip, creating dilution overhang without corresponding revenue.
- China export restrictions tighten permanently. Loss of $2-3B annual TAM with no license approvals.
- NVIDIA cuts prices aggressively to defend share, compressing AMD's GPU margins below profitability threshold.
- Console semi-custom revenue collapses faster than expected, dragging total revenue growth below 20%.
- Intel Granite Rapids / Sierra Forest stages a comeback in servers, stalling EPYC share gains at ~45%.
- 20% warrant dilution (320M shares) materializes partially without full revenue trigger, diluting EPS for existing shareholders.

## Scenario Table

| Scenario | Prob | Earnings Driver | Multiple Driver | Target | Return |
|----------|------|----------------|-----------------|--------|--------|
| **Bull** | 30% | 2026 non-GAAP EPS ~$10.50 on 45%+ revenue growth, MI450 ramp begins, Meta/OpenAI 1GW milestones hit, EPYC >50% share | Re-rate to 30x forward as AI GPU credibility established via hyperscaler deployments | $310 | +51% |
| **Base** | 45% | 2026 non-GAAP EPS ~$8.50 on 30-35% revenue growth, EPYC gains continue, AI GPU grows solidly but MI450 ramp slower than hoped | Stable at 25x forward as contracted pipeline provides visibility | $210 | +2% |
| **Bear** | 25% | 2026 non-GAAP EPS ~$6.00 on China losses, MI450 delays/underperformance, semi-custom collapse, NVIDIA price war | De-rate to 20x as "perpetual #2" narrative hardens | $120 | -42% |

**Expected value: +6.0%** (0.30 x 51% + 0.45 x 2% + 0.25 x -42%)

**Thesis quality check:** The bull case is driven primarily by earnings growth (MI450 ramp + EPYC share) with multiple expansion as confirmation, not the primary driver. This is HIGHER QUALITY than a pure multiple-expansion thesis. The contracted pipeline from OpenAI/Meta provides visibility that did not exist 6 months ago.

**Thesis breaks if:** (1) MI450 first silicon results disappoint or Helios rack fails validation; (2) OpenAI or Meta delay or cancel 1GW deployments; (3) ROCm 8.0 fails to achieve meaningful CUDA compatibility; (4) Two consecutive quarters of data center revenue growth below 40% YoY.

## Setup & Timing

| Factor | Status |
|--------|--------|
| Crowdedness | **Moderately crowded.** 72% institutional ownership. Not a contrarian play, but not as consensus-long as NVIDIA. |
| Short interest | **Low at 2.1%.** No squeeze setup, no strong bear conviction. Declining from 2.4% recently. |
| Technical position | **Neutral-oversold.** Trading 23% below 52-week high ($267), near 50-day MA ($215), above 200-day MA ($192). Stabilized in $195-215 range for 3+ weeks after February selloff. |
| Next catalyst | **Q1 2026 earnings: late April 2026** (~5 weeks away). MI450 product updates at Computex (June). Oracle 50K deployment Q3 2026. |
| Recent price action | Bounced from $193 low (early March) to $205 currently. Up ~5% from trough but still 23% below highs. Not chasing a run-up. |

**Warrant dilution note:** The 320M potential warrant shares (~20% dilution) are NOT priced into the current share count. However, they vest only on milestone achievement tied to massive revenue ($120-200B), and the final tranche requires AMD stock to hit $600. This is EPS-accretive at scale but creates overhang uncertainty in the near term.

## Verdict

**WATCH** -- Conviction: MEDIUM-HIGH

AMD is at a genuine inflection point backed by the most significant hyperscaler commitments any NVIDIA challenger has ever secured. The 12GW pipeline from OpenAI + Meta, Oracle's 50K GPU deployment, EPYC approaching 50% server CPU share, and the MI450's 432GB HBM4 architecture represent a fundamentally stronger competitive position than existed even 6 months ago. The business quality score of 19/25 reflects a high-quality franchise.

However, at $205 the stock prices in substantial success. The forward PE of ~19x requires non-GAAP EPS to reach ~$10.75, which demands both MI450 ramp execution AND continued margin expansion. The expected value of +6% is positive but not compelling enough for a full-conviction BUY given the binary nature of the MI450 software/execution risk. The ROCm ecosystem gap vs CUDA remains the single biggest uncertainty -- hyperscalers have committed hardware but real-world software friction at scale is untested.

**Would upgrade to BUY on:** (1) Price pullback to $175-185, providing 15-20% margin of safety below base case; OR (2) MI450 first silicon/benchmark results confirming competitive performance vs NVIDIA Rubin; OR (3) ROCm 8.0 beta showing demonstrated PyTorch/JAX parity in independent testing; OR (4) Q1 2026 earnings showing data center revenue above $7B with new MI450 design wins beyond existing partners.

**Entry price if forced to buy today:** Scale in at $195-205 (current range), add aggressively below $180.
**Thesis-break signal:** MI450 delayed beyond Q4 2026, OR OpenAI/Meta delay 1GW milestones, OR data center growth decelerating below 35% YoY for two consecutive quarters.

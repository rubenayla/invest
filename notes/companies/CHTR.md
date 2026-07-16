# Charter Communications (CHTR)

**Sector:** Communication Services | **Industry:** Cable broadband (Spectrum brand), mobile (an MVNO — a mobile service resold over another carrier's network), video
**Price:** $131.24 (2026-07-15 close) | **Market Cap:** ~$18.2B | **Economic units:** 138.5M | **Net Debt:** $93.8B (4.15x trailing-twelve-month Adjusted EBITDA)
**Analysis Date:** 2026-07-16

**Standalone rating: WATCH** — genuinely cheap (4.96x EV/EBITDA, ~26% free-cash-flow yield on trailing-twelve-month free cash flow of $4.81B) but this is a *leveraged equity stub*: debt is 84% of enterprise value, and the entire market cap is worth 0.8 turns of EBITDA multiple. Three-year expected value ~**+39%**, but with a ~50% chance of losing money and a ~20% chance of near-total loss. Earnings on 2026-07-24 are a binary event — the last print took the stock down 25.5% in one day. Do not buy ahead of it. Entry becomes attractive **below ~$100**.

## Situation Summary

Charter is the second-largest US cable broadband operator (29.56M internet customers) trading at **$131.24, down 67% in twelve months** and near its three-year low of $125.54. The collapse is recent and specific: on **2026-04-24 the stock fell 25.5% in a single day** (from $242 to $180) on a Q1 print that showed −120,000 broadband subscribers and an EPS miss. It has ground down since, briefly popping 9.4% on 2026-06-29 when Bloomberg reported SpaceX partnership talks, then giving it all back.

The screen looks extraordinary: **4.96x EV/EBITDA**, ~3x forward earnings, **~26% free-cash-flow yield**, and a share count shrinking ~11% a year via buybacks. The reason it is this cheap is that the equity is a thin sliver on top of a very large debt stack, and the operating business is shrinking.

**Two pending transactions close together, expected 2H 2026:**
- **Cox** ($34.5B): the Federal Communications Commission cleared it on 2026-02-27 and the Department of Justice has cleared it too. Only the **California Public Utilities Commission (CPUC)** remains — two proposed decisions circulated 2026-07-09, both recommending approval, with a vote scheduled **2026-08-13**. The antitrust clearance under the Hart-Scott-Rodino Act (HSR) **expires 2026-09-15**; slipping past that forces a refiling and a fresh waiting period.
- **Liberty Broadband**: has **not** closed; will close contemporaneously with Cox.

## The Stub Math (this is the whole thesis)

Everything else in this note is secondary to this table.

| | |
|---|---|
| Market cap | **$18.2B** (16.2% of EV) |
| Net debt | **$93.8B** (83.8% of EV) |
| Enterprise value | **$112.0B** |
| Adjusted EBITDA (trailing twelve months) | **$22.58B** |
| EV/EBITDA | **4.96x** |
| Net leverage | **4.15x** (company-stated) |

The equity is worth zero at an EV/EBITDA of 4.15x. It trades at 4.96x. **The entire market capitalisation is 0.8 turns of multiple.**

**Equity value per unit = (Adj. EBITDA × multiple − net debt) / 138.5M units**

| Adj. EBITDA | 4.25x | 4.50x | 5.00x | 5.50x | 6.00x |
|---|---|---|---|---|---|
| $20.5B | wiped | wiped | $63 | $137 | $211 |
| $21.5B | wiped | $21 | $99 | $177 | $254 |
| **$22.58B (LTM)** | **$16** | **$57** | **$138** | **$220** | **$301** |
| $23.5B | $44 | $86 | $171 | $256 | $341 |
| $25.0B | $90 | $135 | $225 | $316 | $406 |

- Each **0.5x of multiple = $11.3B = $82/unit = 62% of the equity**.
- Each **1% of EBITDA (at 5x) = 6.2% of the equity**. A 5% EBITDA decline at a constant multiple removes **31%** of the equity.

This is why this repo's discounted-cash-flow (DCF) models return a *negative* fair value (−$275, −$390). That is not the usual DCF-outlier bug this repo sees — with 84% of enterprise value in debt, any model that discounts a declining cash-flow stream puts the equity underwater. The DCF is arguably the most honest model on this name; the machine-learning return models, which have no concept of leverage, are the least. (Full model table at the end of this note.)

**Share-count trap:** yfinance reports a market cap of $20.6B alongside a share count of 141M — figures that are mutually inconsistent (141M × $131.24 = $18.5B, not $20.6B; the $20.6B implies ~157M units). The correct economic count is **138,495,819** = 122,984,536 Class A shares + 15,511,283 Charter Holdings units held by Advance/Newhouse (A/N), the Newhouse family partnership that holds an exchangeable stake in Charter's operating subsidiary. Class B is a single share carrying votes but no economic value. Taking yfinance's $20.6B at face value **overstates Charter's equity value by 13%** and makes the stock look less cheap than it is.

## Variant Perception

- **Consensus view:** "A melting ice cube with 4.15x leverage. Broadband — the only thing that matters — is shrinking, fixed wireless and fiber are permanent substitutes, and the debt gets paid before equity holders see a cent. The free-cash-flow yield is a liquidation yield, not an earnings yield. Uninvestable."
- **Our view (partial pushback):** The subscriber panic is quantitatively overstated. Losses are **not accelerating** — they are a steady ~−115k/quarter bleed (~1.5%/yr) that has run nine quarters. And the free-cash-flow inflection is real and independently corroborated by all three rating agencies: capital spending falls from ~$11.7B (2025) to **under $8B by 2028** as the rural build-out and the DOCSIS 4.0 upgrade (the cable-industry standard that lets existing coaxial lines carry multi-gigabit, symmetrical speeds) both complete, roughly doubling free cash flow to **~$10B**. Against an $18.2B market cap, that is a ~55% free-cash-flow yield if EBITDA merely holds.
- **Why it is nonetheless not a buy here:** The offsets that kept revenue flat have run out. **Internet revenue has turned negative (−1.3% year over year)** — Charter no longer has the pricing power to offset falling volume. **The rural build that masks core losses ends in 2026**, removing the growth in homes passed that the flat-subscriber bull case mathematically requires. And EBITDA is already −2.2%. The bull case needs EBITDA to stop falling; the current trend says it won't. At 4.15x leverage you are not paid to be wrong.

## Financial Snapshot

| Metric | FY2025 | FY2024 | FY2023 | FY2022 | Trend |
|--------|--------|--------|--------|--------|-------|
| Revenue | $54.77B | $55.09B | $54.61B | $54.02B | Flat, turned **−0.6%** in 2025 |
| Adjusted EBITDA | $22.71B | $22.57B | — | — | +0.6%; **trailing twelve months to Q1 2026 = $22.58B, now below the FY2025 full year** |
| Operating Income | $13.32B | $13.24B | $12.51B | $12.24B | Flat |
| Net Income | $4.99B | $5.08B | $4.56B | $5.05B | Flat |
| Free Cash Flow | $5.00B | $4.26B | $3.32B | $5.55B | Rising; trailing twelve months $4.81B — **the capital-spending cliff drives it higher from here** |
| CapEx | $11.66B | $11.27B | $11.12B | $9.38B | **Peaking; guided <$8B by 2028** |
| Buybacks | $3.80B | $0.82B | $3.21B | $10.28B | 76% of FCF in 2025 |
| Total Debt | $94.3B | $95.8B | $98.2B | $97.6B | Flat; **held flat only because EBITDA was flat** |
| Interest Expense | $5.04B | $5.23B | $5.19B | $4.56B | Flat so far; refi step-up ahead |

**Q1 2026:** Revenue $13.6B (−1.0%), Adjusted EBITDA $5,637M (**−2.2%**), FCF $1,372M, buybacks $963M.

## Broadband: What the Trend Actually Says

The widely-quoted "−120k vs −59k, losses are accelerating" framing is **misleading**. Q1 2025's −59k was the best quarter in the series, and Q1 is seasonally Charter's strongest quarter.

| Quarter | Net adds (k) | | Quarter | Net adds (k) |
|---|---|---|---|---|
| Q1 2024 | −72 | | Q1 2025 | −59 |
| Q2 2024 | −149 | | Q2 2025 | −117 |
| Q3 2024 | −110 | | Q3 2025 | −109 |
| Q4 2024 | −177 | | Q4 2025 | −119 |
| | | | **Q1 2026** | **−120** |

FY2024 −508k, FY2025 −404k. **Trailing-twelve-month losses are −465k versus −495k the prior year — marginally better, not worse.** This is a persistent structural bleed of ~1.5%/yr, not a collapse. Craig Moffett, the telecom analyst at research firm MoffettNathanson, reads terminal cable penetration as landing near 47%, with subscribers going roughly *flat* rather than into freefall — a defensible view, though one to hold loosely: he forecast Charter at −22k subscribers for 2025 and the actual figure was −404k, so the same analyst has been badly miscalibrated on this exact metric (see bear case #7).

But three things make it worse than the headline:
1. **Posting −120k in a seasonally strong quarter** (vs −72k and −59k in prior Q1s) is a genuine underlying step down.
2. **It is an acquisition problem, not a churn problem.** Chief Executive Chris Winfrey on the Q1 2026 call: *"Our issue right now really is a top-of-funnel issue."* In other words existing customers are staying — Charter simply cannot win new ones. When households form or move, they don't choose Spectrum. Penetration fell 2.3 percentage points to 54.0%.
3. **The rural build is masking the core.** Q1 2026 total customer relationships were −163k *including* +41k from newly-built rural areas, implying the established footprint ran at roughly **−204k**. Winfrey says the rural build *"nearly completes in 2026"*, and the remaining federal subsidy programme (BEAD, the government's Broadband Equity, Access and Deployment fund) is worth only ~$230M to Charter, mostly in 2027-29. The flat-subscriber bull case depends on growth in homes passed offsetting the fall in penetration — and that growth in homes passed is about to stop.

**Versus Comcast:** Charter outperformed on subscribers in 2025 (−404k vs Comcast's −710k), but the two chose opposite poisons. Comcast bought subscriber improvement with price — its domestic broadband revenue fell **5.1%** on lower rates and residential connectivity EBITDA fell **6.0%**. Charter held price and lost subscribers, with EBITDA down only 2.2%. **Charter's EBITDA is actually holding up better than Comcast's.** Neither escaped; cable was 41% of US broadband gross adds in Q4 2025, its lowest share ever.

**Fixed wireless will not plateau on capacity.** Fixed wireless access (FWA) — home internet delivered over a mobile network, sold by T-Mobile, Verizon and AT&T — is the main share-taker alongside fiber. The bull hope is that it runs out of network capacity. It doesn't: T-Mobile *raised* its target to **15M subscribers by 2030** (from 12M by 2028) and stopped disclosing FWA metrics entirely in Q1 2026. Industry capacity headroom is ~32.4M subscribers against ~14.9M currently served. Verizon's FWA slowdown is a stated strategic shift toward fiber, not a capacity wall. The "FWA runs out of room" argument does not survive the sources.

## Bull Case

1. **The capex cliff is real and triply corroborated.** Capital spending falls from ~$11.7B (2025) → **<$8B by 2028** as rural expansion and the DOCSIS 4.0 network upgrade complete. Fitch independently projects free cash flow of ~$4.3B (2024) → **~$10B (2028)**; S&P projects free operating cash flow as a percentage of debt rising 4–5% → **8–9%** — both consistent. That is ~$10B of free cash flow against an $18.2B market cap.
2. **The bleed is slow and may be near terminal penetration.** ~−1.5%/yr, decelerating slightly on a trailing-twelve-month basis.
3. **Deleveraging.** Post-Cox leverage target **3.5–3.75x** within three years (tightened from 3.5–4.0x). Cox arrives levered at only **2.21x** against Charter's 4.15x, so it *de*-levers the combined entity — to ~3.93x on the company's own pro-forma figures (stated on a Q1 2025 basis; my post-Cox model below uses $111B of net debt against $28.0B of EBITDA, or ~3.96x, and ~4.2x if the preferred is counted as debt). Fitch has Charter on **Rating Watch Positive** for an upgrade — a "rising star" candidate to return to investment grade.
4. **No maturity wall.** 2026–27 maturities are ~$1.6B of a $94.3B stack (1.7%), 90% fixed, 12.5-year weighted average life. Bonds trade ~90c yielding 6.5–7.2% — a coupon/duration discount, not distress.
5. **Buybacks at 3x earnings** shrink the count ~11%/yr. The Cox unit count is *fixed*, so Charter's share-price collapse made the deal cheaper in dollar terms for existing holders.
6. **SpaceX optionality** (free): direct-to-cell talks could make mobile capex-light and add a growth vector.

## Bear Case (this is the one that matters)

1. **Pricing power is exhausted.** Internet revenue is **−1.3% year over year**, versus +2.8% growth as recently as Q2 2025. The standard bull argument for cable — the one this repo's Comcast note leans on, that revenue keeps rising even as subscriber counts fall, because price increases more than offset the losses — **no longer holds for Charter**. Volume has overwhelmed price.
2. **The rural offset ends in 2026.** The established footprint is already running at roughly −204k/quarter once newly-built rural areas are excluded. When growth in homes passed stops, the reported number gets worse with no lever left to pull.
3. **The refinancing step-up.** January 2026: $3.0B of *unsecured* notes issued at **7.000%/7.375%** to redeem $3.0B at 5.500%/5.125% — roughly a 190 basis-point step-up. That gap applies only to the **$27.3B unsecured slice** (29% of the stack); the **$55.4B secured** portion reprices far less (~+75bp), because Charter carries a split rating and its secured notes are investment grade. Blended, a full roll adds **~$1.0B/yr** of interest (~20% more than the current $5.04B) — not the $1.8B that naively applying 190bp to the whole $94.3B would imply. Slow, not a cliff: the 12.5-year maturity ladder spreads it over more than a decade. But it is a permanent grind against free cash flow.
4. **Leverage headroom is thin, and thinner than management's number suggests.** S&P downgrades above **4.5x**. On *management's* basis Charter sits at 4.15x — 0.35 turns of room, which an ~8% EBITDA decline would consume. But S&P counts the equipment-instalment-plan financing (customer handset loans, $1.6B) as debt where management doesn't, putting Charter nearer **4.22x** on S&P's own basis — about **0.28 turns, or a ~6% EBITDA decline**. Post-Cox S&P also counts the $6.0B preferred, widening the adjustment to ~0.26x. S&P expects adjusted leverage to remain at or slightly above its **4.0x upgrade trigger through 2027**. With EBITDA already at −2.2%, this is not comfortable margin.
5. **Cox is a weaker asset bought at a higher multiple.** Per S&P, Cox has above-average broadband revenue per user, which makes it *more* exposed to cheaper competition, and it has **worse subscriber losses than Charter**. Charter is paying **6.4x EBITDA** for it while its own *enterprise value* trades at ~5.0x — buying a weaker business for more than the market will pay for its own. Plus **$6.0B of 6.875% convertible preferred** struck at **$477.41** against a ~$131 share price — permanently out-of-the-money, so it behaves as perpetual debt (~$413M/yr), not equity.
6. **Mobile profitability is undisclosed.** 12.13M lines (+17.1%), but net adds decelerated hard (368k vs 507k) on telco iPhone subsidies, and Charter does not break out mobile EBITDA. Anyone claiming mobile is accretive is inferring, not citing.
7. **The recovery has been "next year" for two years.** Moffett forecast Charter at −22k subscribers in 2025 and +233k in 2026; the actual 2025 figure was −404k. Nine quarters of network upgrades, mobile bundling, rural builds and simplified pricing have not bent the curve. Winfrey now offers only: *"getting back to positive net additions is a game of inches."*

## Scenarios (3 years, to mid-2029, post-Cox)

Modelled on a pro-forma basis (i.e. as though Cox had already closed): EBITDA ~$28.0B, net debt ~$111B, 172.1M units (138.5M today + 33.6M Charter Holdings units issued to Cox), plus the $6.0B preferred treated as debt because it is far out-of-the-money. Value per unit = (EBITDA × multiple − net debt − $6.0B preferred) / units.

| Scenario | Prob | Adj. EBITDA | Multiple | Net debt | Units | Value/unit | Return |
|---|---|---|---|---|---|---|---|
| **Severe bear** — rural offset gone, core losses widen, EBITDA −4%/yr, capex stays high, market prices terminal decline | 20% | $24.8B | 4.25x | $110B | 172M | **~$0** | **−100%** |
| **Bear** — steady −115k/qtr bleed, EBITDA −2%/yr, capex cliff delivers, modest paydown | 30% | $26.4B | 4.75x | $103B | 168M | **$98** | **−25%** |
| **Base** — bleed persists but Cox synergies + capex cliff hold EBITDA ~flat; ~$10B/yr FCF split debt/buyback | 35% | $28.4B | 5.00x | $99B | 160M | **$231** | **+76%** |
| **Bull** — SpaceX deal makes mobile capex-light, subscribers stabilise, upgrade to investment grade, EBITDA +1.5%/yr | 15% | $30.1B | 5.75x | $94B | 152M | **$480** | **+266%** |

**Probability-weighted expected value: ~+39% over 3 years (~+11.6%/yr). Probability of loss ≈ 50%. Probability of near-total loss ≈ 20%.**

Eleven and a half percent a year is not adequate compensation for a one-in-five chance of a zero. The expected value is also unstable — it is dominated by tail assumptions, which is the signature of a stub.

**Entry price sensitivity** (same scenarios, terminal values $0 / $98 / $231 / $481):

| Entry | Expected value (3y) | Per year | Share of probability mass that loses money |
|---|---|---|---|
| $131.24 (now) | +39.0% | +11.6% | 50% |
| $115 | +58.6% | +16.6% | 50% |
| $105 | +73.7% | +20.2% | 50% |
| **$100** | **+82.4%** | **+22.2%** | 50% |
| $95 | +92.0% | +24.3% | **20%** |

**Entry: below ~$100.** At $100 the expected value exceeds +80% and the bear case is close to break-even (terminal $98, a −2% return), so the only scenario that loses real money is the severe bear at 20%. Note the strict probability of *any* loss stays at 50% until below $98 — at $95 it drops to 20%, because there the bear case turns positive. Break-even entry (expected value = 0) is **$182**.

## Verdict, Triggers, and What Would Change My Mind

**WATCH. Do not buy before the 2026-07-24 print.** Buying eight days ahead of an earnings release that moved this stock −25.5% last quarter, with no edge on the subscriber number, is a coin flip, not an investment. There is no cost to waiting: if Q2 is good the thesis improves and you pay up modestly for confirmation; if it is bad you avoid a −25% day.

**The falsifiable Q2 test — strip rural out of the headline.** If core net adds (total customer relationships minus rural additions) stay around −160k or worse while rural additions prop up the reported number, bear case #2 is confirmed and the name becomes a PASS.

**Turns constructive if (need most of these):**
- Net adds excluding rural improve materially, and management shows any evidence of fixing the customer-acquisition problem
- Internet revenue returns to flat or positive — the single most important line in the release
- Adjusted EBITDA returns to flat or positive growth (management guides "slight" 2026 growth)
- 2028 capital-spending guidance of under $8B reiterated *with* Cox included
- Cox closes cleanly (California PUC votes 2026-08-13, before the 2026-09-15 antitrust-clearance expiry)
- Price below ~$100

**Thesis is dead if:**
- EBITDA declines more than 3% year over year for two consecutive quarters
- Leverage exceeds 4.5x, S&P's downgrade trigger — a ~6% EBITDA fall does it on S&P's own adjusted basis (see bear case #4)
- 2028 capital-spending guidance is raised above ~$9B — the spending cliff *is* the bull case, and cable operators have deferred promised capital-spending declines before
- The internet-revenue decline steepens beyond about −3%
- Cox closing slips past 2026-09-15 and the antitrust clearance must be refiled

**Sizing note if it ever clears:** this is not a 10% position. At 4.15x leverage with a ~20% chance of a near-total loss, this repo's standard 15% single-name cap is the wrong reference point. Cap at ~3%.

## Charter versus Comcast — the comparison that decides this

This repo's note on Comcast (`notes/companies/CMCSA.md`) rates it **BUY LOW** on the same underlying thesis: cheap cable broadband, large cash returns, secular subscriber erosion. Charter is the *leveraged* expression of that identical bet, which makes "Charter or Comcast?" the question that actually matters here — not "Charter or nothing?":

| | CHTR | CMCSA |
|---|---|---|
| Net leverage | **4.15x** | ~2.5x |
| EV/EBITDA | 4.96x | ~4.8x |
| Equity as % of EV | **16%** | ~46% |
| EBITDA trend | −2.2% | −6.0% (residential connectivity) |
| Broadband revenue | −1.3% | −5.1% |

Charter's *operations* are holding up better than Comcast's — Comcast is discounting to hold subscribers, Charter is holding price. But Charter's balance sheet leaves no room to be wrong, and Comcast is diversified (mobile, Peacock, parks, and a pending split into two public companies).

**If you want this thesis, Comcast gives you nearly the same multiple (4.8x vs 4.96x) at ~60% of the leverage and roughly 2.8x the equity cushion** (46% of enterprise value vs 16%). Charter only wins if you have genuine confidence that broadband stabilises — and the evidence for that does not yet exist. Charter is the trade *after* the trend turns, not before.

## Model Outputs (all run 2026-07-16)

| Model | Fair Value | Upside | Confidence | Run Date |
|---|---|---|---|---|
| AutoResearch | $162.50 | +23.8% | 0.72 | 2026-07-16 |
| gbm_1y | $163.30 | +24.4% | 0.68 | 2026-07-16 |
| gbm_3y | $188.00 | +43.2% | 0.84 | 2026-07-16 |
| gbm_lite_1y | $174.50 | +32.9% | 0.86 | 2026-07-16 |
| gbm_lite_3y | $259.10 | +97.4% | 0.89 | 2026-07-16 |
| gbm_opportunistic_1y | $202.90 | +54.6% | 0.84 | 2026-07-16 |
| gbm_opportunistic_3y | $168.60 | +28.4% | 0.71 | 2026-07-16 |
| **GBM 6-model average** | — | **+46.9%** | — | 2026-07-16 |
| dcf | −$275.50 | −309.9% | 0.70 | 2026-07-16 |
| dcf_enhanced | −$389.60 | −396.9% | 0.70 | 2026-07-16 |

**Read these with care.** The gradient-boosted-machine (GBM) models — the repo's machine-learning return predictors — average +46.9%, which is exactly their known failure mode: a high-volatility, beaten-down name where they extrapolate mean reversion. They carry no representation of 4.15x leverage, a capital-spending cliff, or terminal decline. The discounted-cash-flow (DCF) models' negative fair value is *not* the usual outlier bug this repo sees — it is the honest arithmetic of an 84%-debt structure, where discounting a declining cash-flow stream leaves the equity underwater. **My scenario expected value of +39% sits between AutoResearch (+23.8%) and the GBM average (+46.9%), and I weight it above both because it is the only one that models the capital structure.**

Sell-side: mean target $214.35 (+63%), range **$120 to $413** — a 3.4x spread between low and high, which is itself the story. Consensus rating "hold" (17 analysts). Short interest 21.0M shares ≈ 17% of the Class A count.

## Macro Context (2026-07-16)

Repo macro screen reads **CAUTIOUS — keep dry powder** (score −2): S&P 500 within 0.5% of its 1-year high and +20.9% YoY, VIX 15.87 (calm). The 10-year Treasury at **4.55%, up 1.2ppt YoY**, is a direct headwind for a company refinancing a $94B stack into 7%+ unsecured coupons.

## Sources

- [Charter Q1 2026 10-Q](https://www.sec.gov/Archives/edgar/data/1091667/000109166726000028/chtr-20260331.htm) — share counts, leverage, buybacks
- [Charter Q1 2026 earnings release (8-K Ex-99.1)](https://www.sec.gov/Archives/edgar/data/1091667/000109166726000027/chtrex991earningsrelease33.htm) — subscriber series, Adj. EBITDA, FCF
- [Charter FY2025 10-K](https://www.sec.gov/Archives/edgar/data/1091667/000109166726000017/chtr-20251231.htm) — maturity schedule, A/N units, leverage targets
- [CCO Holdings Q1 2026 10-Q](https://www.sec.gov/Archives/edgar/data/1271833/000127183326000009/ccoh-20260331.htm) — split-rating debt structure
- [DEF 14A 2026](https://www.sec.gov/Archives/edgar/data/1091667/000114036126009220/ny20062718x1_def14a.htm) — as-if-exchanged share count, A/N 15,511,283 units
- [Q1 2026 earnings call transcript](https://www.fool.com/earnings/call-transcripts/2026/04/24/charter-chtr-q1-2026-earnings-call-transcript/) — top-of-funnel commentary, capex guidance
- [Cox investor deck](https://www.sec.gov/Archives/edgar/data/1091667/000114036125019410/ef20049175_ex99-2.htm) — pro-forma leverage 3.93x
- [S&P ratings affirmation, 2025-05-16](https://www.spglobal.com/ratings/en/regulatory/article/-/view/type/HTML/id/3371493) — BB+/Stable, 4.5x downgrade trigger, Cox assessment
- [Fitch Rating Watch Positive, 2025-05-19](https://www.investing.com/news/stock-market-news/fitch-puts-charter-communications-on-positive-rating-watch-93CH-4053766) — FCF $4.3B→$10B by 2028
- [Charter prices $3.0B senior unsecured notes, 2026-01-06](https://ir.charter.com/news-releases/news-release-details/charter-prices-30-billion-senior-unsecured-notes) — 7.000%/7.375% refi step-up
- [SpaceX–Charter mobile partnership talks, Bloomberg 2026-06-26](https://www.bloomberg.com/news/articles/2026-06-26/spacex-charter-discussed-mobile-phone-partnership-in-us)
- [T-Mobile FWA target raised to 15M by 2030](https://www.sec.gov/Archives/edgar/data/1283699/000119312526045679/d106287dex991.htm)
- [Big 3 have room for 32M FWA customers — Fierce, Dec 2025](https://www.fierce-network.com/broadband/big-3-now-have-room-32m-fwa-customers)
- [Moffett: cable broadband faces a flat future, not doomsday](https://www.lightreading.com/cable-technology/cable-broadband-faces-a-flat-future-not-doomsday)
- [CPUC judge proposes approving Charter-Cox merger, 2026-07-09](https://broadbandbreakfast.com/cpuc-judge-proposes-approving-charter-cox-merger/)

**Verification notes:** The 138,495,819 economic unit count is derived from two disclosed figures (122,984,536 Class A + 15,511,283 A/N units) — Charter does not publish an as-if-exchanged total at quarter-end. Charter has not disclosed what percentage of its footprint is overbuilt by competing fiber since Chief Financial Officer Jessica Fischer said "mid-to-high 50s" on 2025-03-10; the widely-cited "60% by end-2025" figure is **Comcast's**, and is routinely misattributed to Charter. Mobile EBITDA contribution is not disclosed in either the quarterly filing or the earnings call, so any claim that mobile is profitable is an inference, not a citation. Bond quotes are indicative and undated. A circulating "Fitch upgrade to BB+" result dates from **2016**, not 2025-26.

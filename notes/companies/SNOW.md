# Snowflake Inc. (SNOW)

**Sector:** Technology | **Industry:** Software - Application
**Price:** $165.34 (2026-05-21) | **Market Cap:** $57.3B
**Analysis Date:** 2026-05-21

## Business Primer

**What they do today.** Snowflake sells a cloud data platform — software that companies rent (it runs on top of Amazon, Microsoft, and Google's cloud servers) to store huge amounts of business data and run questions against it. Picture a giant, shared filing cabinet plus a search engine for a company's numbers: every sale, every click, every shipment, every sensor reading. A retailer dumps years of transaction records into Snowflake, then asks "which products sold best in rainy weeks in the Northeast?" and gets an answer in seconds. Customers pay only for what they use — every query that runs and every gigabyte stored is metered, like an electricity bill ("consumption-based" pricing). This is different from most software companies that charge a fixed yearly fee per user ("seats"). Almost all revenue is this product (compute + storage) usage; FY2026 (year ended Jan 31, 2026) product revenue was ~$4.5B of $4.68B total. Customers are large enterprises — Snowflake had 733 customers each paying over $1M/year, and 56 paying over $10M/year.

**Why customers choose them (the value proposition).** Before Snowflake, a company that wanted to analyze all its data had two bad options: (1) buy expensive on-premise data-warehouse hardware/software (Teradata, Oracle Exadata) that you had to size for peak load and that sat idle most of the time, or (2) stitch together open-source tools yourself, which needs a team of specialized engineers. Snowflake's key trick is that it splits storage from compute: your data sits cheaply in one place, and you spin up processing power only for the seconds you actually run a query, then it shuts off. So a month-end report that needs 100 servers for an hour costs you one hour, not a permanently-provisioned cluster. It also lets different teams query the same data at the same time without slowing each other down, and lets companies securely share live data with partners (a bank can give an auditor read-access without emailing spreadsheets). The concrete improvement: instead of a six-figure hardware purchase sized for your busiest day plus a database-administrator team, you get pay-per-second elasticity, near-zero maintenance, and queries that don't fight each other — at a cost that scales down when you're not using it. The newer pitch (Cortex AI) is "ask your data questions in plain English, and run AI models right where the data already lives" so you don't have to ship sensitive data out to a separate AI tool.

**Where they want to grow.** Three explicit bets. (1) **AI on top of the data** — Cortex AI, "Snowflake Intelligence" (plain-English querying, now in 2,500+ accounts, nearly doubling each quarter), and Cortex Code (4,400+ customers). Because pricing is usage-based, every AI query is incremental revenue on the same platform. (2) **New workloads beyond the warehouse** — the ~$600M acquisition of Observe (closed FY2026) pushes Snowflake into "observability" (monitoring whether your software is running correctly), a ~$50B market, with the product built on Snowflake so customer data stays in one place. (3) **Land-and-expand** — get a customer in cheaply, then grow usage as more teams adopt it; the proof is net revenue retention of 125% (existing customers spend 25% more year over year before counting new logos). Success in 3-5 years looks like product revenue roughly doubling past $9-10B with the AI workloads compounding on top of steady core growth, and GAAP profitability finally arriving as stock-based pay shrinks as a share of revenue.

**What could go wrong (business risks).** The biggest is **Databricks** — a private competitor at a similar ~$5B+ revenue scale but growing ~65% (vs Snowflake's ~29%), valued at ~$134B privately, widely expected to IPO in 2026. Databricks started from the AI/machine-learning and "data lake" side and is seen as better positioned for AI-heavy workloads, where the industry is shifting. If AI workloads become the main event and Databricks is the default there, Snowflake's growth could keep decelerating. Second, **AI products carry lower margins** than the core warehouse (management said so explicitly), so a faster AI mix can compress gross margin even as it adds revenue. Third, the **consumption model cuts both ways** — in a downturn customers can dial usage down instantly, so revenue is more sensitive to enterprise IT budgets than seat-based software. Fourth, **hyperscaler coopetition** — Snowflake runs on Amazon/Microsoft/Google's clouds, who each sell competing warehouses (Redshift, Synapse/Fabric, BigQuery) and could undercut on price.

**How to think about it.** Snowflake is the consumption-priced, data-warehouse-native challenger that grew up serving business analysts, now racing to become an AI platform before the AI-native challenger (Databricks) eats the high-growth part of the market. It is genuinely cash-generative (24% free-cash-flow margin) and net-cash, but still GAAP-unprofitable because of heavy stock-based pay, and it trades on revenue multiples, not earnings — so the whole debate is "does growth re-accelerate with AI, or keep fading toward 20%?"

## Situation Summary

Snowflake reports Q1 FY2027 (quarter ended Apr 30, 2026) on **May 27, 2026** — six days out — the single most important near-term event. The last print (Q4 FY2026, Feb 25, 2026) was a clean beat: product revenue +30% YoY to $1.23B, EPS $0.34 vs $0.27 expected, net revenue retention (NRR) steady at 125%, remaining performance obligations (RPO, booked-but-not-yet-recognized revenue) $9.8B up 42%, and FY2027 product-revenue guidance of ~$5.66B (+27%). The stock nonetheless sits at $165 — 41% below its 52-week high of $281 — caught in tech-multiple compression and an overhang from Databricks, the faster-growing private rival expected to file the largest enterprise-software IPO ever in 2026. Wall Street is broadly bullish (48 analysts, "buy"/"strong buy" consensus, mean target ~$230, range $110-$500), but targets are drifting both ways (Citi cut $280→$260 on May 18; Bank of America raised $195→$205 on May 19). The narrative tension: management is guiding to *deceleration* (27%) while RPO grows at 42% — a gap bulls read as conservatism.

## Variant Perception

- **Consensus view:** High-quality, cash-generative data-infrastructure company, but growth has faded from 70%+ to ~27% and is still decelerating; GAAP profits are years away; Databricks is winning the AI-workload narrative at ~2x the growth rate. Fairly-to-cheaply valued (~$230 mean target), a consensus long the market is reluctant to pay up for until the Databricks IPO comparison clears.
- **Our view:** Two things are underweighted. (1) **The 42% RPO growth vs 27% revenue-growth guide is the widest book-to-revenue gap in years** — booked business hasn't flowed into recognized revenue yet, and consumption ramps lag bookings, so the 27% guide is likely a floor, not a ceiling. (2) **AI adds revenue without adding seats** — Snowflake Intelligence nearly doubling quarter-over-quarter and 9,100+ accounts using AI means usage (the metered thing) is compounding on a platform where every incremental query is margin-positive cash. The market prices SNOW as a 20-something-percent grower fading to 20%; the booking signal and AI-usage curve argue 27-30%+ holds longer than feared.
- **Trigger:** **Q1 FY2027 earnings on May 27, 2026.** A product-revenue beat above the $1.262-1.267B guide (toward 30%) plus NRR holding/ticking up flips the story from "decel" to "AI re-acceleration." Secondary trigger: the **Databricks IPO in 2026**, forcing a public side-by-side that could re-rate SNOW on its ~2x valuation discount — or expose it, depending on the growth gap shown.

## Financial Snapshot

| Metric | Value | 3yr Trend |
|--------|-------|-----------|
| Revenue | $4.68B (FY26) | +31% CAGR (2.07→4.68B) |
| Net Income | -$1.33B (FY26) | Persistent loss, SBC-driven |
| FCF | $1.12B (FY26) | +31% CAGR, consistently positive (0.50→0.75→0.88→1.12B) |
| FCF Margin | 23.9% | Expanding |
| Gross Margin | 67% (GAAP) / 75.8% (non-GAAP product) | Stable/expanding |
| Operating Margin | 10.5% non-GAAP (FY26) | +400bps YoY; guided 12.5% FY27 |
| ROE | -54% | Negative (GAAP losses + buybacks shrinking equity) |
| D/E | 1.42x | Elevated (convertible debt) but $4.0B cash+STI = net cash -$1.3B |
| FCF Yield | 1.95% | Low (growth multiple) |
| P/S (TTM) | 12.2x | Compressed from 25x+ at peak |
| Forward P/E | 68x | High (early-profitability) |
| NRR | 125% | Stable YoY |
| RPO | $9.8B | +42% YoY |

**Key observation:** GAAP losses are misleading — driven by stock-based compensation (SBC), which is *falling* as a share of revenue (41%→34%→guided 27%). On cash, Snowflake throws off ~$1.12B FCF (24% margin) and is net-cash. The Iron-Rule check confirms revenue, FCF, and margins are all genuinely *up* over 3 years; the only "declining" trends are the SBC ratio (good) and the revenue *growth rate* (29% off a far larger base — law of large numbers, not deterioration).

## Valuation Models

Models run 2026-05-18 at `current_price=$157.47`; live price is **$165.34** (+5.0%). Upside % below is **recalculated against the live price** (GBM fair values are absolute).

| Model | Fair Value | Upside (vs $165.34) | Confidence | Run Date |
|-------|-----------|--------|------------|----------|
| gbm_lite_3y | $337 | +103.9% | 0.94 | 2026-05-18 |
| gbm_opportunistic_1y | $314 | +89.8% | 0.95 | 2026-05-18 |
| gbm_3y | $270 | +63.5% | 0.94 | 2026-05-18 |
| autoresearch | $225 | +36.0% | 0.94 | 2026-05-18 |
| gbm_lite_1y | $220 | +32.8% | 0.94 | 2026-05-18 |
| gbm_opportunistic_3y | $211 | +27.3% | 0.72 | 2026-05-18 |
| gbm_1y | $201 | +21.6% | 0.86 | 2026-05-18 |
| dcf_enhanced | $125 | -24.4% | 0.70 | 2026-05-18 |
| dcf | $88 | -46.8% | 0.70 | 2026-05-18 |
| multi_stage_dcf | $59 | -64.1% | 0.70 | 2026-05-18 |
| simple_ratios | $50 | -69.7% | 0.70 | 2026-05-18 |
| rim / growth_dcf | N/A | — | — | 2026-05-18 |

*Models older than 7 days may use stale prices — these are 3 days old, prices recalculated above.*

**Model consensus:** Sharp bimodal split. The GBM family and autoresearch (most reliable per project history) cluster at **$201-$337 fair value (+22% to +104%)**, all high-confidence. The DCF/ratio family produces $50-$125 (-25% to -70%) — the known DCF bias against high-SBC, pre-GAAP-profitability names: discounting negative GAAP earnings massively understates a company generating $1.1B cash FCF. Analyst mean target ~$230 sits inside the GBM range. Trusting the GBM/autoresearch cohort, **center-of-mass fair value ~$230-250, implying ~40-50% upside** — though wide dispersion warrants the more conservative scenario-EV below.

## Business Quality (18/25)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Moat | 3/5 | Real switching costs (data gravity, SQL workloads, governance config) and data-sharing network effects, but the moat is *contested* — Databricks growing ~2x faster on the AI side, and Amazon/Microsoft/Google sell competing warehouses they could subsidize. Not a durable monopoly. |
| Management | 4/5 | Strong execution under CEO Sridhar Ramaswamy: NRR held at 125%, beat the last 4+ quarters, SBC discipline (41%→27% of revenue), disciplined ~$600M Observe tuck-in, 200-person reduction-in-force in Q4 showing cost focus. Transparent on lower AI margins. Heavy SBC dilution is the knock. |
| Profitability | 3/5 | 24% FCF margin and 75.8% non-GAAP product gross margin are excellent; but GAAP still deeply negative (-$1.33B), ROE -54%. Non-GAAP operating margin only 10.5% and AI mix is dilutive to gross margin. Genuine cash engine, immature GAAP profitability. |
| Balance Sheet | 4/5 | Net cash (-$1.3B net debt: $4.0B cash+short-term investments vs $2.7B mostly-convertible debt), current ratio 1.3, $1.1B annual FCF self-funds. D/E optics elevated by convertibles only. Solid. |
| Growth | 4/5 | 29-31% growth at $4.7B scale, RPO +42%, $50B observability TAM via Observe, AI usage compounding on a consumption model, customers >$10M up 56%. Runway is large; drags are the law of large numbers and Databricks taking the fastest-growing slice. |

**Total: 18/25** — Above the 15 yellow-flag line. Quality is real; the contested moat and GAAP-profitability gap keep it out of the 20+ tier.

## Inflection Point

**Partial / approaching, not yet confirmed.** Evidence *for*: (1) the RPO-to-revenue gap (42% vs 27%) signals booked demand not yet recognized — a forward-revenue tailwind; (2) AI usage (Snowflake Intelligence nearly doubling QoQ, 9,100+ AI accounts, 7 nine-figure contracts vs 2 a year ago) is an observable new-demand curve on a metered model; (3) SBC ratio falling toward 27% plus operating margin +400bps is a profitability inflection in progress. Evidence *against* / unconfirmed: growth is still guided *down* (27% < 30%), and the AI re-acceleration is a thesis, not yet a printed number. The May 27 earnings is precisely the read on whether the inflection is real — a "wait for observable evidence at the catalyst" setup rather than a confirmed turn.

## Bull Case

- Q1 product revenue beats the $1.262-1.267B guide toward 30%, and the 42% RPO growth starts converting to recognized revenue — narrative flips from deceleration to AI-driven re-acceleration.
- AI usage compounds on the consumption model: Snowflake Intelligence and Cortex add metered, margin-positive revenue without selling new seats; 9,100+ AI accounts is an early read on a multi-year usage ramp.
- SBC falling to 27% of revenue + operating margin to 12.5% drives a GAAP-profitability inflection, letting the stock be valued on earnings, not just sales.
- Databricks IPO frames SNOW as the cheaper, cash-generative public way to own the data-platform theme at a ~2x valuation discount; re-rate toward ~15x P/S.

## Bear Case

- Databricks IPOs and showcases ~65% growth vs Snowflake's ~27%; investors rotate to the faster horse and SNOW de-rates on the growth gap, not the discount.
- Consumption model bites: an enterprise-IT pullback lets customers dial usage down instantly, and Q1 prints *below* the 27% guide with NRR slipping under 125%.
- **Under-covered disclosed risk (from the Q4 call, not the headlines):** management explicitly said the **new AI products carry lower gross margins** than the core warehouse and are only being offset by "more efficiencies in the core business." A faster AI mix could compress gross margin even as it grows revenue — the AI growth story and the margin story are partly in tension, which the bullish AI narrative glosses over. Relatedly, the Observe acquisition is a **150bps FCF-margin headwind** in FY27 (FCF margin guided *down* 25.5%→23%) — a detail buried under the AI-momentum coverage.
- Hyperscalers (Amazon Redshift, Microsoft Fabric, Google BigQuery) undercut on price within their own clouds, where Snowflake pays them for compute.

## Scenario Table

| Scenario | Prob | Earnings Driver | Multiple Driver | Target | Return |
|----------|------|----------------|-----------------|--------|--------|
| Bull | 25% | Q1 beats toward 30%, RPO converts, AI usage re-accelerates, FY27 guide raised | Re-rate to ~15x P/S as decel fear lifts; Databricks-IPO discount narrows | $279 | +69% |
| Base | 50% | Q1 in line ~27%, FY27 held at $5.66B, NRR ~125%, FCF margin 23%, margins on track | Stable ~13-14x P/S; drift to analyst-mean territory | $215 | +30% |
| Bear | 25% | Q1 below 27% / NRR slips; Databricks IPO steals mindshare; AI margin dilution flagged | De-rate to ~9x P/S on growth-gap + margin worry | $121 | -27% |

**Expected value: +25.5%**
**Thesis breaks if:** Q1 product revenue growth prints **below 25%** *and* NRR falls below 122%, confirming the consumption base is eroding rather than re-accelerating — the bull "RPO converts / AI re-accelerates" thesis is then falsified and the "Databricks-is-winning" bear case is the right read.

## Setup & Timing

| Factor | Status |
|--------|--------|
| Crowdedness | Moderately crowded — 76% institutional, "buy/strong-buy" consensus (48 analysts), but the multiple has compressed to 12x P/S (cheapest since IPO) — a *de-rated* consensus long, not an extended one |
| Short interest | 5.15% of float — modest; not a squeeze setup, mild consensus skepticism |
| Technical position | Neutral-to-recovering — $165 vs 50d avg $153 (above) but 200d $203 (below); 41% off 52w high ($281), 40% above 52w low ($118) |
| Next catalyst | **Q1 FY2027 earnings — 2026-05-27 (6 days)** |
| Recent price action | Bounced off ~$118 lows toward $165; has NOT run ahead of the catalyst (still well below mean target and 200d avg) |

**Read:** Uncrowded *on valuation* (de-rated), a hard dateable catalyst 6 days out, observable-but-unconfirmed inflection evidence, and the stock has not pre-run the print. Close to the "favor buying now" profile — except the catalyst is binary and 6 days away, so the real decision is "own it *into* the May 27 print, or wait to see the number."

## Verdict

**WATCH (lean BUY into/after the print)** — Conviction: **MEDIUM**

The variant perception is clear and testable: the 42% RPO vs 27% revenue-guide gap plus compounding metered AI usage argue growth holds higher and longer than the "fading to 20%" consensus, on a stock de-rated to its cheapest P/S since IPO, with the most-reliable models (GBM/autoresearch) clustering at +22% to +64% and analyst mean ~+40%. Quality is solid (18/25), it's net-cash and generates $1.1B FCF, and scenario EV is +25.5%. What holds it at WATCH rather than BUY is that the entire thesis hinges on a **binary catalyst 6 days out (May 27)** and a contested moat against a faster-growing Databricks about to go public — both the inflection and the competitive verdict get materially clearer within a week, so paying up blind into the print is poor risk discipline.

**If WATCH → upgrade to BUY on:** (a) Q1 product revenue ≥28% growth with NRR ≥125% on May 27 (confirms re-acceleration), buy on the print even if it gaps up toward ~$190; OR (b) absent a strong print, accumulate on weakness toward **$130-140** (near the GBM-1y floor and well under the fair-value cluster), where risk/reward skews favorable even in the base case.
**Thesis-break / avoid level:** Q1 growth <25% with NRR <122% — stand aside; the "Databricks-wins" bear case is then the base case.

<!-- Do NOT add a "Position Context" / "Personal Position" / "My Holding"
     section here. The public file is generic research only. Personal
     position size, cost basis, P&L, and share counts go to
     ~/vault/finance/notes/positions/{TICKER}.md (or are tracked in
     portfolio.md / journal/transactions/). See the Public-vs-private
     content rule in STEP 8 above. -->

# Snowflake Inc. (SNOW)

**Sector:** Technology | **Industry:** Software - Application
**Price:** ~$238 (2026-05-28, pre-market) | **Market Cap:** ~$82B
**Analysis Date:** 2026-05-28

> **Price note:** The May 27 regular-session *close* was $175.26 — set **before** Q1 FY2027 earnings, which were released after the bell. The stock gapped up ~36% in extended/pre-market trading to ~$238 on the blowout. All valuation below uses the live ~$238, not the stale $175 close. (DB/yfinance daily series still shows the $175.26 close; do not anchor on it.)

## Business Primer

**What they do today.** Snowflake sells a cloud data platform — software companies rent (it runs on top of Amazon, Microsoft, and Google's cloud servers) to store huge amounts of business data and run questions against it. Picture a giant shared filing cabinet plus a search engine for a company's numbers: every sale, click, shipment, sensor reading. A retailer dumps years of transactions into Snowflake, then asks "which products sold best in rainy weeks in the Northeast?" and gets an answer in seconds. Customers pay only for what they use — every query and every gigabyte stored is metered, like an electricity bill ("consumption-based" pricing), unlike most software that charges a fixed yearly fee per user ("seats"). Almost all revenue is this usage: FY2026 product revenue was ~$4.5B of $4.68B total. Customers are large enterprises — 779 each pay over $1M/year.

**Why customers choose them (the value proposition).** Before Snowflake, analyzing all your data meant two bad options: (1) buy expensive on-premise data-warehouse hardware (Teradata, Oracle Exadata) sized for peak load that sat idle most of the time, or (2) stitch together open-source tools yourself, needing a team of specialized engineers. Snowflake's key trick is splitting storage from compute: your data sits cheaply in one place, and you spin up processing power only for the seconds a query actually runs, then it shuts off. A month-end report that needs 100 servers for an hour costs you one hour, not a permanent cluster. Different teams query the same data simultaneously without slowing each other, and companies share live data with partners securely (a bank gives an auditor read-access without emailing spreadsheets). Concrete improvement: instead of a six-figure hardware purchase plus a database-administrator team, you get pay-per-second elasticity, near-zero maintenance, and queries that don't fight each other, at a cost that scales down when idle. The newer pitch (Cortex AI) is "ask your data questions in plain English, and run AI models right where the data already lives" so you don't ship sensitive data to a separate AI tool.

**Where they want to grow.** Three explicit bets. (1) **AI on top of the data** — Cortex AI, "Snowflake Intelligence" (plain-English querying, accounts more than doubled QoQ this quarter), and **Cortex Code / "CoCo"** (7,100+ accounts, now management's largest single driver to the raised forecast). Because pricing is usage-based, every AI query is incremental, margin-positive revenue on the same platform — a "flywheel" where AI workloads pull through more core consumption. (2) **Agentic workflows** — the new **Natoma acquisition** extends Snowflake's "agentic control plane" so users can send emails, summarize Slack, check calendars, and open Jira tickets from inside Snowflake Intelligence, in a governed environment. (3) **Land-and-expand** — get a customer in cheaply, grow usage as more teams adopt; net revenue retention is 126% (existing customers spend 26% more YoY before new logos). Success in 3-5 years looks like product revenue roughly doubling past $9-10B with AI compounding on steady core growth, and GAAP profitability arriving as stock-based pay shrinks as a share of revenue.

**What could go wrong (business risks).** The biggest is **Databricks** — a private rival at a ~$5.4B revenue run-rate growing ~65% (vs Snowflake's 34%), valued at ~$134B privately, widely expected to IPO. Databricks grew up on the AI/machine-learning and "data lake" side and reportedly wins ~70% of incremental AI/ML budget in head-to-head bake-offs, with $1B+ AI revenue run-rate vs Snowflake's ~$100M. If AI workloads become the main event and Databricks is the default there, Snowflake's re-acceleration could stall. Second, **AI products carry lower gross margins** than the core warehouse (management said so explicitly) — a faster AI mix can compress gross margin even as it adds revenue. Third, the **consumption model cuts both ways** — in a downturn customers dial usage down instantly, so revenue is more budget-sensitive than seat software. Fourth, **hyperscaler coopetition** — Snowflake runs on Amazon/Microsoft/Google clouds, who each sell competing warehouses (Redshift, Fabric, BigQuery) and could undercut on price.

**How to think about it.** Snowflake is the consumption-priced, data-warehouse-native incumbent that just proved its AI products (CoCo, Intelligence) can *re-accelerate* core growth rather than merely defend it — the bull thesis the May 21 note bet on. The debate has now shifted from "is growth fading to 20%?" (answered: no, it re-accelerated to 34%) to "is a 34%-growth, ~14x-sales platform fairly priced after a 36% gap-up, with Databricks still winning the pure-AI slice?"

## Situation Summary

Snowflake reported **Q1 FY2027 (quarter ended Apr 30, 2026) after the close on May 27** — a blowout that sent the stock up ~36% to ~$238 pre-market. Product revenue grew **34% YoY to $1.334B** (accelerating from 30% the prior quarter, vs the ~27% the company had guided), total revenue +33% to $1.391B, NRR ticked up to **126%**, RPO $9.21B (+38%), and non-GAAP operating margin expanded ~300bps to 11.9%. Management **raised** FY2027 guidance to **$5.84B product revenue (+31%, from $5.66B/+27%)** and operating margin to **13.5% (from 12.5%)**. Two strategic items landed alongside: a **new five-year, $6B AWS agreement** (more than double the prior deal) and the **Natoma acquisition** (agentic control plane). Management explicitly credited **AI products (CoCo) as the largest driver of the raised forecast** and now calls AI "a significant revenue engine." The May-21 variant thesis — that the 42% RPO vs 27% guide gap and compounding metered AI usage meant growth holds higher/longer than the "fading to 20%" consensus — **played out and the market has now priced it in.**

## Variant Perception

- **Consensus view (post-print):** The re-acceleration debate is *settled in the bulls' favor* — AI is monetizing, growth re-accelerated to 34%, guidance raised, margins expanding. Consensus has flipped to "AI flywheel is real," analyst targets are being marked up from the ~$229 mean, and the stock has gapped to ~$238. The remaining bear is valuation (back to ~14x forward sales) and the Databricks AI-share gap.
- **Our view:** The prior edge has **largely closed**. The variant call (growth holds higher/longer) was correct and is now in the price — at ~$238 the stock trades roughly *at* the most-reliable models' fair-value cluster ($230-250) and *above* the prior analyst mean. The only remaining differentiated angle is mildly contrarian *and* cautious: a single quarter of AI-driven re-acceleration may partly reflect **launch-driven pull-forward** (CoCo/Intelligence launched Feb 5; "more than doubled QoQ" growth rates decelerate fast off a tiny base), and the AI gross-margin drag is still ahead. Net: edge is thin both ways near $238. **Honest read: there is no strong variant perception left at this price — the asymmetry that justified owning it into the print is gone.**
- **Trigger:** Now backward-looking — the May 27 print was the trigger and it fired. Forward catalysts that could *re-open* a gap: (a) the **Databricks IPO**, which sets a public AI-growth benchmark that either flatters SNOW's discount or exposes its AI-share deficit; (b) **Q2 FY2027 earnings (~late Aug 2026)** — whether 34% growth is durable or fades as the launch bump normalizes.

## Financial Snapshot

| Metric | Value | 3yr Trend |
|--------|-------|-----------|
| Revenue (FY26) | $4.68B | +31% CAGR (2.07→4.68B) |
| Q1 FY27 product rev | $1.334B | +34% YoY (re-accelerating from 30%) |
| Net Income (FY26) | -$1.33B | Persistent GAAP loss, SBC-driven |
| FCF (FY26) | $1.12B | +31% CAGR, consistently positive |
| FCF Margin | ~24% (FY26) / 23% guided FY27 | High; ~150bps Observe drag |
| Gross Margin | 67% GAAP / 75.1% non-GAAP product | Stable |
| Op Margin | 11.9% non-GAAP (Q1) | +300bps YoY; FY27 guide 13.5% |
| ROE | -54% | Negative (GAAP losses + buybacks) |
| D/E | 1.42x | Convertibles; net-cash ~-$1.3B net debt |
| NRR | 126% | Ticked up from 125% |
| RPO | $9.21B | +38% YoY |
| SBC (Q1) | $433.7M | ~31% of revenue — still elevated |
| Forward P/S (at ~$238) | ~14x | Re-rated up from ~12x (cheapest-since-IPO) trough |

**Key observation:** GAAP loss remains misleading — driven by stock-based compensation (~31% of revenue), which is falling as a share of revenue over time. On cash, Snowflake generates >$1.1B FCF and is net-cash. The Iron-Rule check confirms revenue, FCF, margins, *and now the growth rate* are all up. The only adverse trend is the multiple, which has re-expanded from the trough back to ~14x sales after the gap-up.

## Valuation Models

**Local Postgres (port 5433) was offline at analysis time — could not pull the stored model rows.** The prior run (2026-05-18) is reproduced for reference; **upside % recalculated against the live ~$238**, which materially compresses every GBM's implied upside vs the $157-165 base those models used.

| Model | Fair Value | Upside (vs ~$238) | Confidence | Run Date |
|-------|-----------|--------|------------|----------|
| gbm_lite_3y | $337 | +42% | 0.94 | 2026-05-18 |
| gbm_opportunistic_1y | $314 | +32% | 0.95 | 2026-05-18 |
| gbm_3y | $270 | +13% | 0.94 | 2026-05-18 |
| autoresearch | $225 | -5% | 0.94 | 2026-05-18 |
| gbm_lite_1y | $220 | -8% | 0.94 | 2026-05-18 |
| gbm_opportunistic_3y | $211 | -11% | 0.72 | 2026-05-18 |
| gbm_1y | $201 | -16% | 0.86 | 2026-05-18 |
| dcf_enhanced | $125 | -47% | 0.70 | 2026-05-18 |
| dcf / multi_stage_dcf / simple_ratios | $50-88 | -63% to -79% | 0.70 | 2026-05-18 |

**Model consensus:** These fair values **predate the beat-and-raise**, so the GBM absolutes are likely stale-low (they'll mark up on the new, higher revenue base when re-run). But mechanically against today's ~$238: the 1-year GBMs and autoresearch now sit *at or below* the price (-16% to -5%), while only the multi-year GBMs show double-digit upside (+13% to +42%). The DCF family stays deeply negative (the known anti-SBC, pre-GAAP-profit bias). **Takeaway:** the easy gap between price and fair value that existed at $157-165 has closed; at $238 the stock is roughly *at* fair value on the near-term models and only cheap on the 3-year GBMs. Re-run the models post-earnings before trusting any single number.

## Business Quality (19/25)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Moat | 3/5 | Real switching costs (data gravity, SQL workloads, governance) and data-sharing network effects, reinforced by the $6B AWS deal and CoCo's multi-platform reach. Still *contested* — Databricks wins ~70% of incremental AI/ML budget and ~$1B+ AI run-rate vs SNOW's ~$100M. Not a monopoly. |
| Management | 4/5 | Strong execution under CEO Sridhar Ramaswamy: re-accelerated growth to 34%, raised guidance, NRR up to 126%, SBC discipline, disciplined tuck-ins (Observe, Natoma), transparent on lower AI margins. Heavy SBC dilution is the knock. |
| Profitability | 3/5 | 75.1% non-GAAP product gross margin and ~24% FCF margin are excellent; but GAAP still deeply negative, SBC ~31% of revenue, op margin only ~12%. Genuine cash engine, immature GAAP profitability. |
| Balance Sheet | 4/5 | Net cash (~-$1.3B net debt), current ratio 1.3, >$1.1B annual FCF self-funds. D/E optics elevated by convertibles only. Solid. |
| Growth | 5/5 | 34% at $5.8B-run-rate scale with growth *re-accelerating*, RPO +38%, NRR 126%, AI a confirmed revenue engine, $6B AWS deal, $50B observability TAM via Observe. Best-in-class for the scale. Drag: Databricks owns the fastest-growing AI slice. |

**Total: 19/25** (was 18) — Growth upgraded to 5/5 on confirmed re-acceleration. The contested AI moat and GAAP-profitability gap keep it out of the 20+ tier.

## Inflection Point

**Confirmed (this print).** The May-21 note flagged this as "partial/approaching, not yet confirmed" pending the catalyst. May 27 confirmed it: growth re-accelerated (30%→34%), guidance raised both on revenue and margin, AI moved from "thesis" to "largest driver of the forecast increase," and operating margin expanded ~300bps. The profitability inflection (SBC ratio falling, op margin rising) is in motion. The catch for *new* investors: an inflection that is now *recognized and priced* is no longer an edge — the time to act on it was into the print at $135-165, which is exactly what the prior note's BUY-trigger called.

## Bull Case

- AI flywheel proves durable: CoCo (7,100+ accounts) and Snowflake Intelligence keep pulling through core consumption, growth holds 32-35% through FY2027, and the raised guide ($5.84B) proves conservative *again*.
- $6B AWS deal + Natoma agentic capabilities deepen the platform and lower delivery cost, supporting both growth and the margin-expansion path (op margin 13.5%→mid-teens+).
- NRR re-expansion (125%→126%) signals existing customers are spending more on AI workloads — the highest-quality, lowest-CAC growth.
- GAAP profitability inflection lets the stock eventually be valued on earnings, not just sales; net-cash, $1.1B+ FCF de-risks the balance sheet.

## Bear Case

- **At ~$238 the stock has re-rated to ~14x forward sales — the cheap entry is gone.** Most upside is captured; you're now paying full freight for a story the market already believes.
- **Launch pull-forward risk (under-covered):** the AI re-acceleration leans on products launched Feb 5; "more than doubled QoQ" growth rates collapse fast off small bases. If Q2 (late Aug) shows the bump normalizing back toward high-20s, the multiple de-rates hard from 14x.
- **AI gross-margin dilution (disclosed, under-covered):** management has repeatedly said AI products carry *lower* gross margins than the core warehouse, offset only by core efficiencies. A faster AI mix can pressure the 75% product gross margin even as revenue grows — the AI growth story and the margin story are partly in tension.
- Databricks IPOs showcasing ~65% growth and $1B+ AI revenue vs SNOW's ~$100M AI run-rate; investors rotate to the faster horse on the AI-share gap.
- Consumption model bites in any enterprise-IT pullback — usage (the metered thing) drops instantly, unlike seat-based software.

## Scenario Table

*(Base price ~$238; forward P/S ~14x on the raised $5.84B FY27 product-revenue guide.)*

| Scenario | Prob | Earnings Driver | Multiple Driver | Target | Return |
|----------|------|----------------|-----------------|--------|--------|
| Bull | 25% | AI flywheel durable, growth holds 33-35% through FY27, guide raised again, op margin beats toward mid-teens | Re-rate to ~16-17x sales on sustained re-acceleration | $300 | +26% |
| Base | 50% | Growth moderates to guided ~31%, NRR ~125%, margins on track, AI contributes but Databricks keeps AI-budget lead | Multiple holds ~14x | $250 | +5% |
| Bear | 25% | H2 growth fades toward 26-28% as launch bump normalizes; AI margin dilution shows; Databricks IPO steals mindshare | De-rate to ~10x sales | $175 | -26% |

**Expected value: +2.5%**
**Thesis breaks if:** Q2 FY2027 (late Aug) product-revenue growth decelerates below ~28% with NRR slipping under 124% — confirming the Q1 re-acceleration was a launch-driven, one-quarter pull-forward rather than a durable flywheel.

## Setup & Timing

| Factor | Status |
|--------|--------|
| Crowdedness | Now a *winning, recognized* long — sentiment flipped bullish post-print; the de-rated-contrarian setup that existed at $157-165 is gone |
| Short interest | 5.15% of float (pre-print) — modest; will likely fall as shorts cover the gap-up |
| Technical position | Gapped ~36% to ~$238; now *above* the prior $229 analyst mean and 200d avg, mid-way to the $281 52w high. Extended short-term after a one-day spike |
| Next catalyst | **Q2 FY2027 earnings ~late Aug 2026**; **Databricks IPO** (date TBD, 2026) |
| Recent price action | +36% in a single session on the beat-and-raise — has now *over-run* into the catalyst; chasing the gap is poor entry discipline |

**Read:** The favorable "own it into the print" setup the prior note identified has fully resolved — the catalyst fired, the thesis was right, and the stock captured ~36% in a day. New money is now *chasing a gap-up* into a fully-priced, technically-extended name. That argues for patience, not pursuit.

## Verdict

**WATCH (no new buys at ~$238) — Conviction: MEDIUM**

*(was WATCH / lean-BUY into the print on 2026-05-21 — the BUY-into-the-print trigger fired on the May 27 beat-and-raise and worked; the thesis is now realized and priced.)*

The May-21 variant perception was correct: growth re-accelerated to 34% (not "faded to 20%"), NRR rose to 126%, and guidance was raised — exactly the "AI re-acceleration" outcome the note bet on, and the stock gapped ~36% to ~$238. **The edge is now spent.** At ~$238 the stock trades at the most-reliable models' fair-value cluster ($230-250), above the prior analyst mean, at ~14x forward sales — no longer the cheapest-since-IPO bargain. Scenario EV is only **+2.5%** with a symmetric ±26% bull/bear, and the residual risk (launch-pull-forward, AI gross-margin dilution, Databricks' AI-share lead) is real. Quality is genuine (19/25, net-cash, $1.1B+ FCF), but quality at fair value is a *hold*, not a *buy*.

**Existing holders:** Hold / ride the momentum; consider trimming a partial slice into the spike to lock the catalyst gain, especially if position is oversized. The durability question gets answered at Q2 (late Aug).
**New money — would upgrade to BUY on:** a pullback toward **$180-200** (gives back part of the gap, restores a margin of safety against the ~$230-250 fair-value cluster) **with** Q2 confirming growth holds ≥30% and NRR ≥125%. Absent that, **PASS at ~$238** — don't chase a 36% one-day gap.
**Thesis-break / avoid level:** Q2 growth <28% with NRR <124% — the re-acceleration was a one-quarter launch bump; stand aside.

<!-- Do NOT add a "Position Context" / "Personal Position" / "My Holding"
     section here. The public file is generic research only. Personal
     position size, cost basis, P&L, and share counts go to
     ~/vault/finance/notes/positions/{TICKER}.md (or are tracked in
     portfolio.md / journal/transactions/). See the Public-vs-private
     content rule in STEP 8 above. -->

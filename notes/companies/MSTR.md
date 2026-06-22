# Strategy Inc (MSTR)

**Sector:** Technology | **Industry:** Software - Application (de facto: leveraged bitcoin holding company)
**Price:** $112.53 (2026-06-22) | **Market Cap:** ~$40B
**Analysis Date:** 2026-06-22

## Business Primer

**What they do today.** Strategy (formerly MicroStrategy) is two things bolted together. The small, original part is an enterprise software business — it sells "business intelligence" tools (dashboards and analytics that let a company chart its sales, inventory, etc.) to corporate customers, generating ~$480M of annual revenue. The big part, and the only one the market cares about, is a **bitcoin holding vehicle**: the company borrows money and sells stock to buy and hold bitcoin. As of early May 2026 it held **818,334 BTC** acquired for ~$61.8B (average cost **$75,537/coin**). The stock is, in practice, a leveraged way to own that pile of bitcoin through a Nasdaq-listed share.

**Why investors choose them (the value proposition).** A retail investor who wants leveraged bitcoin exposure inside a normal brokerage or retirement account can't easily borrow to buy bitcoin. MSTR does the leveraging for them: it issues low-coupon convertible bonds and preferred stock, uses the cash to buy bitcoin, and the common shareholder gets amplified exposure to bitcoin's price moves (the stock's beta is ~3.5). For years the trick that made it *better* than just owning bitcoin was the **mNAV premium** (modified net asset value premium): the stock traded at 2–4× the value of the bitcoin it held, so management could sell new shares at that premium, buy more bitcoin, and *increase bitcoin-per-share* for existing holders — "accretive dilution." That self-reinforcing loop ("the flywheel") was the entire edge.

**Where they want to grow.** Management's stated goal was to keep growing both total bitcoin held and **bitcoin per share**, funded by an alphabet soup of perpetual preferred securities — STRK, STRF, STRD, STRC, STRE (each a different seniority/coupon slice sold to yield-hungry investors) — plus convertible notes and at-the-market (ATM) common stock sales. Success in their telling: ride toward 1,000,000+ BTC and become the dominant, most-liquid public bitcoin proxy with index (S&P/Nasdaq) inclusion.

**What could go wrong (business risks).** The flywheel only spins **above 1.0× mNAV**. Below parity, selling stock to buy bitcoin *dilutes* bitcoin-per-share instead of growing it, so the growth engine stops. Meanwhile the financing stack creates fixed cash obligations — roughly **$800–900M/year** of preferred dividends plus convertible-note interest — that the tiny, barely-breakeven software business cannot cover. If bitcoin falls and stays down, the company must fund those payments by **selling bitcoin** or issuing equity at a discount, both of which shrink bitcoin-per-share and can feed a reflexive downward spiral. The software business itself is stagnant and structurally irrelevant.

**How to think about it.** This is not a software company and not really an operating business — it's a **closed-end leveraged bitcoin fund with a permanent financing overhang**, currently trading at a *discount* to the bitcoin it holds. Value it as bitcoin exposure minus senior claims minus the cost of carrying the preferred stack, not on revenue/earnings multiples.

## Situation Summary
The regime has flipped. Bitcoin (~$64k as of 2026-06-21) now trades **below Strategy's $75,537 average cost basis** — the company is underwater on its hoard — and MSTR's mNAV has collapsed from ~2.5× (Dec 2024) and ~1.16× (spring 2026) to **0.74× basic / 0.80× diluted (June 15, 2026)**, i.e. the stock trades at roughly an **18–20% discount** to the dollar value of its bitcoin. On the Q1 2026 call (reported May 5), management formally **abandoned the "never sell bitcoin" pledge** ("We will sell Bitcoin when it's advantageous"), and in late May actually **sold 32 BTC for ~$2.5M to fund the STRC preferred dividend** — a symbolic crossing of the Rubicon. Despite all this, Wall Street still rates it "Strong Buy" with a mean target near $350–460, a striking disconnect from the structural reality. (This analysis is primary-source + market-data based; no quantitative models exist for MSTR — see Valuation Models below.)

## Variant Perception
- **Consensus view:** Two camps. Sell-side analysts (13 opinions, "strong buy," mean target ~$351) still treat it as a bitcoin call option with 200%+ upside. Crypto-twitter increasingly sees a "death spiral" — discount to NAV + broken pledge + forced selling.
- **Our view:** Neither camp has an *edge* here, and neither do we. At 0.80× diluted mNAV you are buying bitcoin for ~80 cents on the dollar *with* embedded leverage — superficially attractive. But the discount is **structurally deserved, not a free lunch**: senior preferred ($10.3B) and converts ($8.25B) sit ahead of common; ~$800–900M of annual fixed obligations must be met by a company with negligible operating cash flow; and below 1.0× mNAV every financing action (equity sale or bitcoin sale) *erodes* bitcoin-per-share. The honest conclusion: **there is no fundamental edge** — MSTR's return is ~entirely a leveraged bet on bitcoin's direction, now with negative carry. The "discount will close" thesis is weak because the discount can persist or widen for as long as bitcoin is below cost.
- **Trigger:** Re-rating up requires bitcoin reclaiming ~$75k+ (back above cost basis) so the flywheel can restart; re-rating down requires bitcoin breaking ~$50k, which would intensify forced selling and put STRC dividend coverage in question. Next scheduled event: **Q2 2026 earnings (~early Aug 2026)**.

## Financial Snapshot

| Metric | Value | 3yr Trend |
|--------|-------|-----------|
| Revenue (software) | ~$0.48B (FY25) | Flat (~+12% YoY Q1, off a tiny base) |
| Net Income | -$3.85B (FY25) | Deeply negative — bitcoin mark-to-market (ASU 2023-08 fair-value accounting) drives huge swings |
| Operating Income | -$41M (FY25) | Negative; software ~breakeven |
| Operating Cash Flow | -$67M (FY25) | Negative — cannot self-fund obligations |
| Stockholders Equity | $51.0B | Up (bitcoin carried at fair value) |
| Total Debt | $8.24B (converts) + ~$10.3B preferred | Rising |
| BTC held | 818,334 (avg cost $75,537) | Up ~22% YTD 2026 |
| mNAV (diluted) | 0.80× (June 15) | Collapsed from 2.5× → 1.16× → <1.0× |

*Caveat: net income is dominated by non-cash bitcoin remeasurement under fair-value accounting — ignore the P&L, watch bitcoin price and the financing stack.*

## Valuation Models

| Model | Fair Value | Upside | Confidence | Run Date |
|-------|-----------|--------|------------|----------|
| llm_deep_analysis | $138.41 | +23.0% | 0.50 (LOW) | 2026-06-22 |

**Model consensus:** No quantitative models (DCF/RIM/GBM) have ever been run on MSTR — it is outside the standard screening universe and those models are in any case **meaningless** here: there is no durable earnings stream to discount. Fair value ≈ bitcoin holdings × price − senior claims − capitalized cost of preferred carry, then a market-set premium/discount on top. The only DB row is this deep-analysis EV (+23%, low confidence). Sell-side targets (~$351 mean, $163 low / $570 high) embed bitcoin price assumptions far above today's and a re-rating back to a premium.

## Business Quality (8/25)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Moat | 1/5 | Software business is irrelevant/stagnant. The only "moat" is being the largest, most-liquid public bitcoin proxy with index inclusion — and a wave of copycat bitcoin/crypto treasury companies (BMNR, Strive, etc.) is eroding even that scarcity. |
| Management | 2/5 | Saylor is a skilled capital-markets engineer, but just **broke the central "never sell BTC" pledge**, diluted heavily *above $90k* only to trade at a discount now, and runs a promotional, reflexivity-dependent model with a complex conflicted capital stack. |
| Profitability | 1/5 | Operating income negative, operating cash flow negative; software FCF negligible vs. $800–900M annual fixed obligations. |
| Balance Sheet | 2/5 | $8.25B converts + ~$10.3B preferred against ~breakeven cash generation. A $2.25B USD reserve gives ~2.5 years of STRC coverage — not imminent insolvency, but structurally fragile and dependent on bitcoin price and open capital markets. |
| Growth | 2/5 | The bitcoin-per-share growth engine **broke below 1.0× mNAV**. Can still raise total BTC via senior preferred/debt, but each raise now adds fixed claims ahead of common. |

*An 8/25 reflects that this is a poor *business*; it is more fairly judged as a leveraged fund, where the relevant question is discount/leverage/carry, not business quality.*

## Inflection Point
Yes — but a **negative** one that has already begun, not a turnaround to buy into. The observable evidence: (1) mNAV crossed below 1.0× (the flywheel-killing threshold), (2) bitcoin fell below cost basis, (3) management broke the never-sell pledge and *actually sold* BTC to fund a dividend, (4) STRC preferred trades below par and new issuance was halted. These are markers of the model downshifting from "accretive growth machine" to "leveraged holder defending a financing stack." A *positive* inflection would require bitcoin back above ~$75k and mNAV re-stabilizing >0.9× — not yet in evidence.

## Bull Case
- **Discount + leverage convexity:** buying bitcoin at ~0.80× through a leveraged vehicle; if bitcoin rallies to $90k+ and mNAV re-rates to ≥1.1×, the common gets a double kick (asset up *and* discount closing) → triple-digit upside.
- **Bitcoin is cyclically oversold** post-Fed; a dovish pivot or risk-on rotation could send BTC back above cost basis and restart the flywheel and ATM accretion.
- **$2.25B USD reserve** buys ~2.5 years of preferred-dividend coverage — no forced-liquidation cliff in the near term; time for bitcoin to recover.
- **Index inclusion / liquidity** keeps a structural bid from passive flows that pure bitcoin lacks.

## Bear Case
- **Reflexive financing trap:** below 1.0× mNAV, funding the $800–900M/yr obligations by selling stock *or* bitcoin both shrink bitcoin-per-share → discount widens → cheaper equity → more selling. Self-reinforcing downward.
- **Bitcoin below cost basis ($75,537):** every dividend-funding BTC sale now locks in losses, accelerating per-share bitcoin erosion.
- **Broken pledge = lost narrative premium:** the "never sell" promise was load-bearing for the cult-like premium; abandoning it structurally re-rates the multiple down, possibly permanently.
- **Under-covered primary-source risk (Q1 call / filings):** management explicitly reframed the goal as *bitcoin-per-share*, not total BTC, and stood up a finite $2.25B reserve with a hard ~2.5-year coverage horizon. Headlines focus on the discount; the under-covered point is that **STRC dividend sustainability is now openly reserve- and bitcoin-price-dependent**, and STRC already trades below par with new issuance halted — a quiet signal the preferred channel is stressed.
- **Senior claims subordinate the common:** $18.5B of converts + preferred sit ahead; in a deep bitcoin drawdown the common absorbs losses first.

## Scenario Table

| Scenario | Prob | Earnings Driver | Multiple Driver | Target | Return |
|----------|------|----------------|-----------------|--------|--------|
| Bull | 30% | Bitcoin recovers to $90k+ (2027), BTC-per-share holds; reserve untouched | mNAV re-rates 0.80×→1.1×; flywheel restarts | ~$250 | +120% |
| Base | 40% | Bitcoin chops $55–70k; modest dividend-funded BTC sales erode per-share holdings | mNAV stuck 0.8–0.9× | ~$118 | +5% |
| Bear | 30% | Bitcoin breaks <$50k; forced selling accelerates; STRC coverage questioned / dividend reset | mNAV widens to ~0.6×; narrative premium gone | ~$55 | -51% |

**Expected value: +23%** — but this is a **low-quality EV**: it is dominated by an unforecastable asset (bitcoin) plus an embedded leverage/discount bet, with enormous variance (beta ~3.5). The positive expectation is essentially "I think bitcoin goes up," not a genuine company-specific edge.

**Thesis breaks if:** bitcoin sustains below ~$50k (forces accelerating BTC sales and puts the STRC dividend at risk) **or** mNAV stays <0.85× while the company keeps issuing/selling to fund dividends (confirms per-share bitcoin erosion is permanent).

## Setup & Timing

| Factor | Status |
|--------|--------|
| Crowdedness | Heavily owned (institutions ~64%); high retail/options crowding; short interest elevated |
| Short interest | ~11.4% of float |
| Technical position | Weak — down with bitcoin; below cost basis; near lower end of range, but no base yet |
| Next catalyst | Q2 2026 earnings ~early Aug 2026; otherwise bitcoin price daily; monthly STRC dividend dates |
| Recent price action | Tracking bitcoin lower; discount to NAV persistent for weeks |

## Verdict

**WATCH (lean PASS)** — Conviction: **LOW**

There is **no fundamental edge** here: MSTR is a leveraged bitcoin proxy whose famed "accretive dilution" flywheel has structurally broken below 1.0× mNAV, with bitcoin underwater against cost basis and ~$800–900M of annual fixed obligations the operating business cannot cover. The ~20% discount to bitcoin NAV looks like a bargain but is rationally deserved given the senior-claim overhang and the now-confirmed need to sell bitcoin to pay preferred dividends. The scenario EV is mildly positive (+23%) but is just a high-variance bitcoin direction bet with negative carry — not something to own for company-specific reasons. For a fundamental portfolio this is effectively a **PASS**; only justified as a *deliberately sized, leveraged bitcoin position* by someone who wants exactly that exposure and accepts the financing-spiral tail risk.

**If WATCH:** Would upgrade toward BUY only if **bitcoin reclaims ~$75k (cost basis) AND mNAV stabilizes ≥0.9×** (flywheel can restart) — or, contrarian-deep-value, if the discount blows out to **<0.6× mNAV while the $2.25B reserve and STRC dividend coverage remain intact** (paying ~60c for $1 of bitcoin with runway). Avoid adding while mNAV is between 0.8–0.95× and bitcoin is below cost — that is the dead zone where per-share bitcoin quietly bleeds.

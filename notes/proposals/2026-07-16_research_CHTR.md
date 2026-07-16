# CHTR (Charter Communications) — first note, 2026-07-16

**Verdict: WATCH.** Price $131.24 (2026-07-15 close). Full note: `notes/companies/CHTR.md`.

**Why this is on your desk despite being a WATCH:** Charter is down **67% in twelve months** and screens as one of the cheapest large-caps anywhere — 4.96x EV/EBITDA, ~3x forward earnings, **~26% free-cash-flow yield**, share count shrinking ~11%/yr. It looks like an obvious bargain. It mostly isn't, yet, and the reason is not visible on a screen. There is also a **binary catalyst in 8 days** (Q2 earnings, 2026-07-24) and a **merger vote on 2026-08-13**.

## The one thing to understand

Charter's equity is a **leveraged stub**. Net debt is $93.8B against an $18.2B market cap — **84% of enterprise value is debt**.

- It trades at **4.96x** EV/EBITDA. The equity is worth **zero at 4.15x**.
- **The entire market capitalisation is 0.8 turns of EBITDA multiple.**
- Each **0.5x of multiple = 62% of the equity**. A **5% EBITDA decline at a constant multiple removes 31%** of it.

This is why the repo's DCF models return a *negative* fair value (−$275, −$390). That is not the usual DCF-outlier bug — with 84% of enterprise value in debt, any model discounting a declining cash-flow stream puts the equity underwater. Conversely the GBM models' +46.9% average is their known failure mode: a high-volatility, beaten-down name where they extrapolate mean reversion, with no representation of leverage.

**Data trap worth knowing:** yfinance reports Charter's market cap as $20.6B and its share count as 141M — mutually inconsistent, and both wrong. The correct economic count is **138,495,819** (122,984,536 Class A + 15,511,283 Advance/Newhouse units). Taking yfinance's number overstates the equity by 13%.

## What I got wrong on the way in (and the correction)

I started with "broadband losses are accelerating (−120k vs −59k)" — the market's framing. **That is misleading.** The full series shows a *steady* ~−115k/quarter bleed for nine quarters; trailing-twelve-month losses are −465k vs −495k the prior year, i.e. marginally *better*. Q1 2025's −59k was the best quarter in the series, so the year-over-year comparison flatters the deterioration.

I also assumed a refinancing crisis. **There isn't one**: 2026-27 maturities are ~$1.6B of a $94.3B stack (1.7%), 90% fixed, 12.5-year average life, bonds at ~90c yielding 6.5–7.2% (not distressed), and Fitch has Charter on watch for an **upgrade**.

**The real bear case is narrower and better:** the offsets have run out.
1. **Internet revenue has turned negative (−1.3% y/y)**, versus +2.8% growth as recently as Q2 2025. Pricing no longer offsets volume. The Comcast bull argument in `notes/companies/CMCSA.md` — "revenue still rises even as units fall" — **no longer holds for Charter**.
2. **The rural build that masks core losses ends in 2026.** Core footprint is already ~−204k/quarter excluding rural additions. The flat-subscriber bull case mathematically requires growth in homes passed, and that growth is about to stop.
3. **Thin leverage headroom** before S&P's 4.5x downgrade trigger: 0.35 turns on management's basis (an ~8% EBITDA fall), but nearer 0.28 turns (~6%) on S&P's own basis, since S&P counts the $1.6B of customer handset-loan financing as debt and management doesn't. EBITDA is already −2.2%.
4. **Cox is a weaker asset at a higher multiple** — S&P says it has worse subscriber losses than Charter, and Charter is paying 6.4x for it while its own *enterprise value* trades at ~5.0x.

**The real bull case is also better than I expected, and triply corroborated:** capital spending falls from ~$11.7B (2025) to **under $8B by 2028** as the rural build and DOCSIS 4.0 upgrade complete. Fitch independently projects free cash flow of ~$4.3B (2024) → **~$10B (2028)**; S&P projects free operating cash flow/debt rising from 4–5% to 8–9%. That is ~$10B of free cash flow against an $18.2B market cap — if EBITDA merely holds.

So: a genuine ~55% free-cash-flow yield in 2028 *if* the business stops shrinking, and a zero *if* it shrinks a bit faster. That is the whole trade.

## Scenarios (3y, post-Cox)

| Scenario | Prob | Value/unit | Return |
|---|---|---|---|
| Severe bear — rural offset gone, EBITDA −4%/yr, multiple 4.25x | 20% | ~$0 | **−100%** |
| Bear — steady bleed, EBITDA −2%/yr | 30% | $98 | −25% |
| Base — EBITDA ~flat, capex cliff delivers, ~$10B/yr FCF | 35% | $231 | +76% |
| Bull — subs stabilise, SpaceX, investment-grade upgrade | 15% | $480 | +266% |

**Expected value ~+39% over 3 years (~+11.6%/yr). Probability of loss ≈ 50%. Probability of near-total loss ≈ 20%.**

Eleven and a half percent a year is not adequate payment for a one-in-five chance of a zero.

## Actions

1. **Do not buy before 2026-07-24.** The last print moved this stock **−25.5% in one day**. Buying eight days ahead of it with no edge on the subscriber number is a coin flip. Waiting costs nothing.
2. **The falsifiable Q2 test — strip rural out of the headline.** If core net adds (total customer relationships minus rural additions) stay around −160k or worse while rural props up the reported figure, the bear case is confirmed and this becomes a PASS. Also watch whether internet revenue is still negative.
3. **Entry below ~$100** — there the expected value exceeds +80% and the bear case is roughly break-even (terminal $98, a −2% return), leaving only the 20% severe-bear scenario losing real money. Break-even entry (expected value = 0) is $182.
4. **Size at ~3% if it ever clears**, not the repo's 15% single-name cap. A 20% wipeout tail makes that cap the wrong reference.

## The more useful comparison: you already own this thesis via CMCSA

`notes/companies/CMCSA.md` rates Comcast **BUY LOW** on the same underlying bet. Charter is the *leveraged* version of it:

| | CHTR | CMCSA |
|---|---|---|
| Net leverage | **4.15x** | ~2.5x |
| EV/EBITDA | 4.96x | ~4.8x |
| Equity as % of EV | **16%** | ~46% |
| EBITDA trend | −2.2% | −6.0% (residential connectivity) |
| Broadband revenue | −1.3% | −5.1% |

Charter's *operations* are actually holding up better — Comcast is discounting to hold subscribers (broadband revenue −5.1%, connectivity EBITDA −6.0%), Charter is holding price and losing subscribers instead. But Comcast's balance sheet leaves room to be wrong and Charter's does not.

**At nearly the same multiple (4.8x vs 4.96x), Comcast gives you this thesis at ~60% of the leverage and ~2.8x the equity cushion (46% of enterprise value vs 16%).** CHTR only wins if you have real confidence broadband stabilises — and that evidence does not exist yet. Charter is the trade *after* the trend turns, not before. Given the macro screen currently reads CAUTIOUS (S&P within 0.5% of its high, 10-year at 4.55% and rising), there is no urgency.

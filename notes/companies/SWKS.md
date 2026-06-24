# SWKS — Skyworks Solutions

**Price:** $73.44 (2026-06-23)
**Rating:** WATCH (lean PASS) — cheap on multiples but structurally declining; a value-trap until revenue stabilizes
**First look:** 2026-06-23

Skyworks makes radio-frequency (RF) front-end chips — power amplifiers, filters, switches — that
sit between a phone's modem and its antennas. It screens as deep value (~14x forward earnings,
3.9% dividend yield, net cash) but the business has been shrinking for three straight years, and
the cheap multiple looks deserved rather than a mispricing.

## Why it's on the radar
- Down ~19% from its 52-week high ($90.90), trading at $73.44 vs a $52–91 range.
- Forward P/E ~14x, ~3.9% dividend yield, ~6% free-cash-flow yield, net cash (~$1.42B cash vs
  ~$1.19B debt). Surface metrics of a bargain.
- Consensus is lukewarm: mean target ~$73 (≈ flat), "hold."

## The bear case (lead with it — this is the crux)
1. **Structural revenue decline, not a cyclical dip.** Revenue has fallen every year:
   FY22 $5.49B → FY23 $4.77B → FY24 $4.18B → FY25 $4.09B. Net income collapsed alongside:
   $1.28B → $983M → $596M → $477M. Gross margin compressed from ~50% historically to ~41%.
2. **Apple concentration is the whole story.** Roughly two-thirds of revenue comes from its
   single largest customer (Apple). Apple is methodically reducing supplier dependence —
   bringing its modem in-house (the C1 in the iPhone 16e) and dual-sourcing RF content with
   Qorvo. Skyworks has reportedly lost socket/content share in recent iPhone cycles. Every
   point of content loss at a customer that large is a direct, hard-to-replace hole.
3. **Dividend payout ratio >1 on GAAP earnings (~1.18).** Free cash flow (~$688M) still covers
   the ~$440M dividend, but the margin of safety is thinning as earnings fall. A cheap yield
   that the business is growing into the wrong direction is a warning, not a reward.
4. **The "Broad Markets" growth hope (~40% of revenue: IoT, auto, infrastructure) is real but
   slow** — not yet large or fast enough to offset Mobile's decline.

The repo's DCF family agrees: `dcf` $20.92, `multi_stage_dcf` $24.58, `dcf_enhanced` $38.25 —
all well below price, because they extrapolate the declining cash flows. That's the value-trap
signal.

## The bull case (what would have to go right)
- **Apple destocking/content loss is mostly behind it** and Mobile revenue stabilizes near
  $4B; the multiple stops compressing.
- **Broad Markets inflects** — auto RF, edge-AI device content, and IoT grow into the majority
  of revenue, unwinding the Apple-concentration discount.
- **Capital return does the work**: 6% FCF yield funds buybacks that shrink the share count
  while you collect ~4%. At 14x a stabilized ~$5.20 non-GAAP EPS with a re-rating to 17x,
  you get a respectable return without heroic growth.
- Ratio/RIM models lean this way: `simple_ratios` $107.99, `rim` $137.67, neural `autoresearch`
  $94.55 — all above price on book value, dividend, and trough multiples.

## Model snapshot (all run 2026-06-23, model px $76.18)
| Model | Fair Value | vs px | Read |
|---|---|---|---|
| dcf | $20.92 | −73% | declining FCF |
| multi_stage_dcf | $24.58 | −68% | declining FCF |
| dcf_enhanced | $38.25 | −50% | declining FCF |
| growth_dcf | $70.13 | −8% | ≈ flat |
| gbm_3y | $80.92 | +6% | muted |
| gbm_opportunistic_3y | $77.64 | +2% | muted |
| gbm_1y | $94.73 | +24% | trough bounce |
| gbm_lite_3y | $117.09 | +54% | outlier-high |
| autoresearch (neural) | $94.55 | +24% | trough-multiple |
| simple_ratios | $107.99 | +42% | cheap multiple |
| rim | $137.67 | +81% | book + dividend |

The spread is the thesis: cash-flow models say "earnings are falling, worth $20–38"; multiple
models say "cheap, worth $100+." The **GBM 3-year models — the repo's most reliable for return
prediction — sit at +2% to +6%**, corroborating a muted, value-trap-leaning outcome rather than
a bargain.

## Scenario table (~2–3 year horizon, from $73.44, price only; add ~4%/yr dividend)
| Scenario | Prob | What happens | Target | Price return |
|---|---|---|---|---|
| Bear | 40% | Apple content keeps eroding, Mobile sub-$3.8B, EPS to ~$4, stuck at ~11x | $52 | −29% |
| Base | 40% | Revenue stabilizes ~$4.0–4.2B, EPS ~$5.20, modest re-rate to ~14x | $80 | +9% |
| Bull | 20% | Broad Markets inflects, content holds, buybacks + re-rate to ~17x on ~$5.80 | $98 | +33% |

**Probability-weighted price return ≈ −1%.** Adding the ~4%/yr dividend over the horizon nets a
low-single-digit total expected return with a fat left tail. Risk/reward is unattractive at
$73 — you are not paid enough to own the Apple-content-erosion risk.

## Entry / exit
- **Entry interest:** sub-$55 (near the 52-week low). At ~$52, the dividend yield pushes past
  ~5.5% and you'd be buying genuine distress pricing where the bear case is largely in the
  quote — *and only if* a quarter or two shows Mobile revenue flattening and Broad Markets
  growth accelerating.
- **Thesis-break (avoid / abandon):** another iPhone cycle with visible content loss, Broad
  Markets growth stalling below mid-single digits, or FCF dipping below the dividend. Any of
  these confirms value trap.
- **What would change my mind to a buy:** two consecutive quarters of year-over-year revenue
  growth (stabilization confirmed), Broad Markets crossing ~50% of revenue, or a credible
  design-win pipeline that de-risks the Apple concentration.

## Bottom line
Cheap for a reason. The 14x multiple and 3.9% yield are real, but they sit on a business whose
revenue and earnings have fallen three years running because its largest customer is designing
it out. The DCF models and the GBM 3-year consensus both point to muted-or-negative outcomes;
the optical cheapness is doing the persuading, and that's exactly how value traps recruit. Pass
at $73; revisit near $52–55 only with evidence of stabilization.

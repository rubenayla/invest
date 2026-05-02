# Kelly Position Sizing — How to Use It Correctly

This is the canonical reference for what Kelly is, what it tells you, and how to apply it in real portfolio decisions in this repo. The math lives in [`trading-formulas.md`](trading-formulas.md); this doc is about **interpretation and use**.

## What Kelly is

Kelly is a **single-bet sizing formula**. Given a bet with known win probability `p` and win/loss ratio `b`, Kelly returns the fraction `f* = (pb − q) / b` of capital that maximizes long-run geometric growth. That's it.

In our system, `run_position_sizer.py` runs Kelly **independently per stock**:
- `p` is derived from **trust-weighted** agreement among the committee. Each model's stored confidence is multiplied by a per-model trust weight before the bullish-fraction is computed.
- `b` is `consensus_upside / historical_VaR(5%)` — model-implied upside divided by real-world downside.
- The raw Kelly is then halved (default α = 0.5, "half-Kelly") for noise tolerance.
- Caps are applied: 15% per single position, 35% per sector.

### Trusted-model committee (highest → lowest trust)

| Model | Trust weight | Coverage | What it is |
|---|---|---|---|
| `llm_deep_analysis` | **3.0** | sparse (~200) | Structured Claude deep dive: variant perception, scenarios, primary-source reading. Highest trust where present, but a feedback-loop risk exists since this is Claude's own output. |
| `autoresearch` | 2.0 | ~760 | LLM-driven fair value across the universe. Calibrated, broad coverage. |
| `gbm_3y` | 1.0 | ~760 | Standard GBM, the calibrated baseline. |
| `gbm_opportunistic_3y` | 1.0 | ~760 | Peak-return-in-window target. |
| `gbm_lite_3y` | 0.7 | ~760 | Limited-history variant — flagged overoptimistic. |

Weights are relative; only ratios matter. When `llm_deep_analysis` exists for a ticker it dominates the committee but does not override an obviously-disagreeing ML quartet. When it doesn't exist, the sizer falls back to autoresearch + 3 GBMs as before.

Each stock gets its own answer as if that bet were the only thing you'd do.

## What Kelly is good for

### 1. Ranking two specific bets against each other

The valid use case. "Is PNG.V a better marginal dollar than topping up TSLA?" → run Kelly on both, compare:
- Confidence-weighted return
- Win probability `p` (model agreement)
- Number of bulls (e.g. 4/4 vs 3/4)
- Volatility and historical max drawdown

Higher Kelly return + higher agreement + comparable vol = better marginal bet. This is meaningful comparison.

### 2. Capping concentration on a single name

Kelly's 15% per-position cap is a **ceiling**, not a target. If a name's raw Kelly is 84% (as PNG.V was on 2026-05-01), the cap stops you from over-betting on noisy estimates. That's the feature.

### 3. Edge sanity check

If Kelly comes back negative or zero ("no edge"), the trusted models don't have a strong opinion either way. That's a useful "don't add capital here" signal — though it does **not** mean "sell what you already own."

## How to actually use the output

When the user asks **"should I buy X?"** or **"should I add to Y?"**:

1. **Run Kelly on the candidate(s) only.** Don't sweep the whole portfolio looking for "gaps."
2. **Pull live price, 52-week range, and analyst PTs** for each candidate. Kelly is price-blind to extension. If the stock is within 5% of its 52w high or above analyst mean PT, flag it — that's not what Kelly evaluated.
3. **Compare candidates' Kelly outputs head-to-head.** Better return, higher confidence, more agreement, lower vol — pick the winner of those criteria.
4. **Treat the Kelly cap as a ceiling for discretionary sizing**, not a target. New names with thin model history or binary catalysts should be sized well below the cap (e.g., 3-5% starter on a brand-new ticker that hits the 15% cap).
5. **Cash deployment ≠ portfolio rebalance.** "I have $6,500 cash to put to work" and "Kelly says rebalance my whole portfolio" are different questions. The first is a single-decision question with the cash as the constraint. The second requires a rotation plan, tax-loss analysis, and conviction review on the names being trimmed.

## Worked example: "buy PNG.V instead of topping up existing names?"

**Wrong way (what was done on 2026-05-02):**
- Ran Kelly on all 13 portfolio tickers + PNG.V.
- Read each stock's per-position target % from the output.
- Computed `gap = target_% − current_%` for each.
- Recommended the biggest gaps (PNG.V at 15pp, STLD at 12pp).
- Suggested rotating from "no-edge" names (MOH, GOOG, FSLR) to fill them.

Why this was wrong:
- The per-stock targets in `--portfolio` mode are normalized within a clean-sheet $50k allocation. They assume you're starting from cash, not from your real portfolio.
- Five names hit the 15% cap → the implicit recommendation was "concentrate 75% of capital in 5 names," which is not what the user asked.
- "No edge" was treated as "sell" — it isn't. It means the trusted models don't have a directional opinion on those names. The user may still hold them for reasons outside the model's view.
- I recommended STLD without checking it was at its 52-week high.

**Right way:**
- Compare PNG.V vs the user's existing top-picks individually.
- For each, look at: Kelly return, p, # bulls, vol, current price vs 52w high, analyst mean PT vs current.
- Decide: which name has the best risk-adjusted entry given the cash on hand?
- Size the buy at a level appropriate for the name's model maturity and catalyst structure — not the Kelly cap.

## Quick reference: when NOT to lean on Kelly alone

Kelly is the right tool for sizing a bet you've already decided to make. It's the wrong tool for:

- **Choosing what to sell.** "No edge per Kelly" ≠ "sell." Kelly only sees the trusted models — it doesn't see your tax basis, conviction, holding period, or fundamental view.
- **Setting an entry price.** Kelly doesn't know about chart extension, support/resistance, or recent run-ups. Always check price vs 52w range and analyst PT before pulling the trigger.
- **Recommending allocations across the whole portfolio in one pass.** It'll happily max-cap several names, leaving zero room for diversification or new positions you haven't shown it yet.
- **Sizing brand-new names with thin model history.** PNG.V had 6 fundamental snapshots when first scored — the GBM models were extrapolating. Discretionary cap should be much lower than the system's 15% on new tickers.

Cross-references:
- Math: [`trading-formulas.md`](trading-formulas.md)
- Code: `src/invest/sizing/kelly.py`, `scripts/run_position_sizer.py`
- Trusted models: `gbm_3y`, `gbm_lite_3y`, `gbm_opportunistic_3y`, `autoresearch`
- Incident that prompted this doc: 2026-05-02 entry in `.agents/error-log.md`

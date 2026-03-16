---
name: size
description: Kelly Criterion position sizing. Use when user says "size", "kelly", "how much to buy", "position size", "how many shares", "build portfolio", or "allocate".
argument-hint: "TICKER [...] [--portfolio --budget N] [--portfolio-value N] [--fraction 0.5] [--verbose]"
---

# Position Sizer (Kelly Criterion)

Calculate how much to buy based on model consensus, historical volatility, and risk limits.

## Steps

1. **Read portfolio context** from `notes/portfolio/portfolio.md` to get current portfolio value and holdings
2. **Run the position sizer**:
   - **Specific tickers**: `uv run python scripts/run_position_sizer.py TICKERS --portfolio-value VALUE --verbose`
   - **Build full portfolio**: `uv run python scripts/run_position_sizer.py --portfolio --budget AMOUNT --max-positions N --verbose`

   Portfolio mode scans all ~700 stocks in DB, ranks by risk-adjusted Kelly score, enforces sector caps, and proposes an allocation. Pass through any user-specified flags.

3. **Interpret and present results:**
   - If Kelly says "no_edge" — tell the user the models don't see enough upside to justify a position
   - If models disagree (some bull, some bear) — highlight the divergence and which models disagree
   - If risk flags fire — explain why (high volatility, sector concentration, etc.)
   - Give a clear recommendation: "Buy X shares of TICKER at ~$PRICE = $AMOUNT"

## Key concepts for the user

- **Half-Kelly (default)**: Gives ~75% of max theoretical growth with ~50% of the volatility
- **p**: Weighted fraction of models predicting upside (higher = more consensus)
- **b**: Upside/downside ratio (how much you gain vs lose)
- **Edge**: p * b - q. Must be positive to trade. Higher = stronger signal
- **Flags**: "thin_edge" means edge exists but is small. "no_edge" means don't trade.

## Important

- Always use `uv run python` for all commands
- The sizer reads from `valuation_results` table — models must be up to date. If data is stale, suggest running `/update` first
- Portfolio value should reflect actual investable cash, not total net worth
- The sizer caps at 15% per position and 35% per sector by default

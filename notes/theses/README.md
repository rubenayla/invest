# Investment Theses

Macro-level investment theses and sector/commodity analyses. Unlike individual stock watchlist items, these are thematic bets on broader trends.

## Active Theses

| Thesis | Status | Verdict | Last Updated |
|--------|--------|---------|--------------|
| [Copper](copper-thesis.md) | Researched | Cautiously Bullish | 2026-01-31 |
| [Power](power-thesis.md) | Researched | Bullish but Entry-Selective | 2026-02-09 |
| [Argentina ETF](argentina-thesis.md) | Researched | Speculative Bullish | 2026-01-31 |
| [AI Disruption "Hit List"](ai-disruption-thesis.md) | Researched | Actionable — Selective Shorts + Avoid | 2026-02-25 |
| [BTC Miners as AI Datacenter Infrastructure](btc-miners-ai-datacenter-thesis.md) | Researched | Cautiously Bullish — Stock Selection Critical | 2026-03-07 |

## Thesis Structure

Each thesis is a single `*-thesis.md` file in this folder. If we ever need supporting material (data, charts), prefer adding it inline unless it becomes unwieldy.

## How to Use

1. **Research phase**: Create folder, compile analysis
2. **Decision**: Document verdict and position sizing
3. **Monitoring**: Track key indicators, update as needed
4. **Exit**: Document reasoning when closing thesis

## Polymarket Probability Anchoring

Use [Polymarket](https://polymarket.com) prediction market prices to anchor scenario probabilities in thesis evaluation. Instead of guessing P(event), check if a liquid market exists.

**Lookup tool**: `uv run python scripts/polymarket_lookup.py "<keywords>"`

Examples:
```bash
uv run python scripts/polymarket_lookup.py "fed"           # rate decisions
uv run python scripts/polymarket_lookup.py "bitcoin"        # crypto price targets
uv run python scripts/polymarket_lookup.py "recession"      # macro outlook
uv run python scripts/polymarket_lookup.py "fed" --json     # machine-readable output
```

**How to use in scenario tables**: replace subjective probability with Polymarket price where a relevant, liquid (>$100K volume) contract exists. Flag when your prior diverges significantly from the market.

**Caveats**: coverage is uneven (strong on US politics, crypto, Fed; weaker on commodities, sector-specific events). Low-liquidity contracts (<$10K) are noisy — treat as directional only.

## Difference from Watchlist

| Theses | Watchlist |
|--------|-----------|
| Macro/sector bets | Individual stocks |
| Multiple instruments | Single ticker |
| Longer time horizon | Variable |
| Thematic catalyst | Company-specific |

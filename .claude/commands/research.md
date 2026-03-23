# research TICKER — Deep dive on one company

Full investment research: news, variant perception, financials, scenarios, verdict.
Saves to `notes/companies/TICKER.md` and `valuation_results` DB (model: `llm_deep_analysis`).

---

## STEP 0: Research the Situation (NEWS & NARRATIVE)

**This step comes FIRST. Before touching any numbers, understand what's actually happening.**

Use web search to find:
1. **Recent news** (last 30-90 days): earnings surprises, guidance changes, management turnover, M&A, lawsuits, regulatory actions, activist investors
2. **The market narrative**: What does Wall Street currently believe about this stock? Is it a "consensus long" or contrarian?
3. **Sector context**: How is the industry doing? Tariffs, regulation, interest rate sensitivity, competitive shifts?
4. **Upcoming events**: Next earnings date, FDA decisions, contract renewals, product launches, analyst days — anything dateable in the next 6 months

**Output a 3-5 sentence "Situation Summary"** — what's the story right now?

---

## STEP 1: Variant Perception (THE MOST IMPORTANT STEP)

Before doing any valuation, answer Steinhardt's 4 questions:

1. **The Idea**: What is the specific investment opportunity?
2. **The Consensus View**: What does the market currently believe? (Check analyst ratings, short interest, institutional ownership, recent price action)
3. **Your Variant Perception**: Where specifically does your view differ from consensus, and WHY? What do you see that the market doesn't?
4. **The Trigger Event**: What specific, dateable catalyst will force the market to re-rate?

**If you cannot articulate a variant perception, there is no edge. Say so honestly.**

Reverse-engineer what the current price implies about future earnings/growth. Compare that to what you think will actually happen. The gap IS the opportunity.

---

## STEP 2: Gather Model Data (Database)

Query the PostgreSQL database for ALL valuation models (use `invest.data.db.get_connection()`):

```sql
SELECT model_name, fair_value, current_price, upside_pct, confidence, timestamp
FROM valuation_results
WHERE ticker = '{TICKER}'
ORDER BY upside_pct DESC;
```

Record: which models are bullish vs bearish. Note extreme divergences (>50pp spread).
Flag stale data (>30 days old). Known biases: DCF overvalues cyclicals at peak earnings, RIM undervalues asset-light companies. GBM and autoresearch are most reliable for return predictions.

---

## STEP 3: Pull Live Financials (yfinance)

```python
import yfinance as yf
t = yf.Ticker('{TICKER}')

# Income statement (3-5 year trend)
print(t.income_stmt.loc[['Total Revenue', 'Net Income', 'EBITDA', 'Operating Income']])

# Balance sheet
print(t.balance_sheet.loc[['Total Assets', 'Total Debt', 'Stockholders Equity', 'Cash And Cash Equivalents']])

# Cash flow
print(t.cashflow.loc[['Operating Cash Flow', 'Free Cash Flow', 'Capital Expenditure']])

# Key ratios
info = t.info
for k in ['trailingPE', 'forwardPE', 'priceToBook', 'priceToSalesTrailing12Months',
           'debtToEquity', 'returnOnEquity', 'returnOnAssets', 'profitMargins',
           'operatingMargins', 'grossMargins', 'dividendYield', 'payoutRatio',
           'beta', 'marketCap', 'enterpriseValue', 'currentRatio', 'quickRatio',
           'revenueGrowth', 'earningsGrowth', 'sector', 'industry',
           'shortPercentOfFloat', 'heldPercentInsiders', 'heldPercentInstitutions',
           'targetMeanPrice', 'targetLowPrice', 'targetHighPrice', 'numberOfAnalystOpinions',
           'recommendationKey']:
    print(f"{k}: {info.get(k, 'N/A')}")
```

**THE IRON RULE**: Before claiming any trend ("declining revenue", "improving margins"), verify with the actual data. Check 3-5 year trends.

Calculate: Revenue CAGR (3yr), Earnings CAGR (3yr), FCF yield (FCF/market cap), Net debt/EBITDA.

---

## STEP 4: Business Quality Assessment

Score each dimension 1-5 with specific evidence:

| Dimension | What to assess |
|-----------|---------------|
| **Moat (1-5)** | Pricing power, switching costs, network effects, scale advantages, brand. Is it DURABLE? |
| **Management (1-5)** | Capital allocation track record (ROIC vs WACC), M&A history, insider buying/selling, forecasting accuracy, transparency in bad times (Fisher point #14) |
| **Profitability (1-5)** | Margins vs peers, ROE sustainability, capital intensity, margin trajectory |
| **Balance Sheet (1-5)** | Leverage appropriate for industry, interest coverage, debt maturity profile, cash generation vs obligations |
| **Growth Runway (1-5)** | TAM expansion, new products/markets, organic vs acquired growth, law of large numbers risk |

**Total: X/25** — Below 15 is a yellow flag. Below 10 is a red flag.

---

## STEP 5: Inflection Point Check

Is this company at or near a fundamental inflection? The best investments come at turning points. Check for:

- **Turnaround**: Recovering from setbacks with identifiable, correctable causes?
- **Hidden segment growth**: Fast-growing product/segment masked by larger flat business?
- **Demand breakthrough**: New distribution, geographic expansion, regulatory approval?
- **Profitability inflection**: Crossing into strong profitability as operating leverage kicks in?
- **Corporate event**: Spin-off, activist involvement, new management with a clear plan?

**Timing principle**: Don't try to buy absolute bottoms. Look for OBSERVABLE EVIDENCE that the inflection has begun. Enter after initial recovery starts — you trade some upside for dramatically reduced value-trap risk.

If no inflection is evident, the stock needs to be cheap enough on a static basis to justify buying into a "more of the same" scenario.

---

## STEP 6: Scenario Table (TIED TO REAL EVENTS)

Each scenario must be driven by specific, identifiable conditions — not generic "things go well/badly."

For each scenario, decompose the return into **earnings growth** + **multiple change**:

| Scenario | Prob | Earnings Driver | Multiple Driver | Target | Return |
|----------|------|----------------|-----------------|--------|--------|
| **Bull** | X% | {specific: revenue acceleration from X, margin expansion from Y} | {re-rating because Z} | $X | +X% |
| **Base** | X% | {specific: continuation of current trends} | {stable multiple} | $X | +X% |
| **Bear** | X% | {specific: what goes wrong — loss of customer, margin compression from X} | {de-rating because Y} | $X | -X% |

**Expected value** = sum(probability x return)

**Thesis quality check**: If your upside depends entirely on multiple expansion (not earnings growth), the thesis is LOW QUALITY. Flag it.

**Pre-mortem**: What specific condition would break your thesis entirely? Define the "I was wrong" signal upfront.

---

## STEP 7: Setup & Timing Assessment

Even a great company is a bad buy at the wrong price/time. Check:

| Factor | Check | Status |
|--------|-------|--------|
| **Crowdedness** | Is it a consensus hedge fund long? (Check top holders) | Crowded / Uncrowded |
| **Short interest** | High = squeeze potential but also consensus negative | X% |
| **Technical position** | RSI, distance from 52w high/low, relative performance vs sector | Oversold / Neutral / Overbought |
| **Catalyst proximity** | Is there a dateable catalyst in 0-6 months? | Yes (date) / No |
| **Recent price action** | Has it already run 10%+ ahead of the catalyst? | |

**Favor buying now when**: uncrowded, near-term catalyst, observable inflection evidence, stock hasn't run yet.
**Favor waiting when**: crowded, catalyst is 6+ months out, technically overbought, already appreciated significantly.

---

## STEP 8: Final Verdict

| Criterion | Assessment |
|-----------|-----------|
| **Variant Perception?** | Clear / Weak / None — what do you see that the market doesn't? |
| **Undervalued?** | Model consensus direction and magnitude |
| **Quality?** | Business quality score (X/25) |
| **Inflection?** | Is there an identifiable turning point? |
| **Catalyst?** | Specific dateable event within 6 months? |
| **Risk/Reward?** | Expected value from scenario table |
| **Setup?** | Entry timing favorable? |
| **Conviction** | HIGH / MEDIUM / LOW |

**Final verdict**: BUY / WATCH / PASS — with clear rationale

**If BUY**: At what price? Full position or scale in? What's the thesis-break signal?
**If WATCH**: What would change your mind? What price/event triggers a BUY?
**If PASS**: Why? Is it permanently uninvestable or just wrong timing?

---

## OUTPUT FORMAT

**Save to `notes/companies/{TICKER}.md`** — this is the SINGLE source of truth for each company's analysis.
If the file already exists, OVERWRITE it with the new analysis (the old version is in git history).
If the ticker has supplementary files, they live in `notes/companies/{TICKER}/` (subdirectory) — don't touch those.

Template:

```markdown
# {Company Name} ({TICKER})

**Sector:** {sector} | **Industry:** {industry}
**Price:** ${price} | **Market Cap:** ${cap}
**Analysis Date:** {YYYY-MM-DD}

## Situation Summary
{3-5 sentences: what's happening with this company RIGHT NOW. Recent news, narrative, sector dynamics.}

## Variant Perception
- **Consensus view:** {what the market believes}
- **Our view:** {where we differ and why}
- **Trigger:** {what event forces re-rating}

## Financial Snapshot

| Metric | Value | 3yr Trend |
|--------|-------|-----------|
| Revenue | $XB | {CAGR}% |
| Net Income | $XB | {CAGR}% |
| FCF | $XB | {trend} |
| ROE | X% | {trend} |
| D/E | X | {trend} |
| FCF Yield | X% | |

## Valuation Models

| Model | Fair Value | Upside | Confidence |
|-------|-----------|--------|------------|
| ... | ... | ... | ... |

**Model consensus:** {summary — which models agree/disagree and why}

## Business Quality (X/25)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Moat | /5 | {specific evidence} |
| Management | /5 | {capital allocation, insider activity, transparency} |
| Profitability | /5 | {margins vs peers, trajectory} |
| Balance Sheet | /5 | {leverage, coverage, trajectory} |
| Growth | /5 | {runway, organic vs acquired} |

## Inflection Point
{Is there one? What evidence? Or is this a static value play?}

## Bull Case
{3-5 bullets — specific, not generic}

## Bear Case
{3-5 bullets — what actually kills the thesis}

## Scenario Table

| Scenario | Prob | Earnings Driver | Multiple Driver | Target | Return |
|----------|------|----------------|-----------------|--------|--------|
| Bull | X% | {specific} | {specific} | $X | +X% |
| Base | X% | {specific} | {specific} | $X | +X% |
| Bear | X% | {specific} | {specific} | $X | -X% |

**Expected value: +X%**
**Thesis breaks if:** {specific condition}

## Setup & Timing

| Factor | Status |
|--------|--------|
| Crowdedness | |
| Short interest | |
| Technical position | |
| Next catalyst | {date} |
| Recent price action | |

## Verdict

**{BUY / WATCH / PASS}** — Conviction: {HIGH/MEDIUM/LOW}

{2-3 sentence rationale linking variant perception, quality, catalyst, and setup}

**If BUY:** Entry at $X, scale-in plan, thesis-break at $X
**If WATCH:** Would upgrade on {specific condition}
```

---

## STEP 9: Save to Database

After writing the .md file, save the structured results to the valuation database.
Run this Python script with the actual values from your analysis:

```python
uv run python -c "
import json
from datetime import datetime
from invest.data.db import get_connection

conn = get_connection()
cur = conn.cursor()

# Map conviction to confidence score
conviction_map = {'HIGH': 0.9, 'MEDIUM': 0.7, 'LOW': 0.5}

# --- FILL THESE FROM YOUR ANALYSIS ---
ticker = '{TICKER}'
current_price = {CURRENT_PRICE}
verdict = '{BUY/WATCH/PASS}'
conviction = '{HIGH/MEDIUM/LOW}'
expected_value_pct = {EXPECTED_VALUE}  # e.g. 36.0 for +36%
quality_score = {QUALITY_SCORE}  # out of 25
entry_price = {ENTRY_PRICE}  # your recommended buy price
thesis_break_price = {THESIS_BREAK_PRICE}  # price where thesis is wrong

# Scenario table values
bull = {'prob': {BULL_PROB}, 'target': {BULL_TARGET}, 'return_pct': {BULL_RETURN}}
base = {'prob': {BASE_PROB}, 'target': {BASE_TARGET}, 'return_pct': {BASE_RETURN}}
bear = {'prob': {BEAR_PROB}, 'target': {BEAR_TARGET}, 'return_pct': {BEAR_RETURN}}

variant_perception = '{ONE_LINE_VARIANT_PERCEPTION}'
# --- END FILL ---

fair_value = current_price * (1 + expected_value_pct / 100)
confidence = conviction_map.get(conviction, 0.5)
suitable = verdict == 'BUY'

details = {
    'verdict': verdict,
    'conviction': conviction,
    'quality_score': quality_score,
    'expected_value_pct': expected_value_pct,
    'entry_price': entry_price,
    'thesis_break_price': thesis_break_price,
    'variant_perception': variant_perception,
    'scenarios': {'bull': bull, 'base': base, 'bear': bear},
}

cur.execute('''INSERT INTO valuation_results
    (ticker, model_name, timestamp, fair_value, current_price, upside_pct, suitable, confidence, details_json)
    VALUES (%s, 'llm_deep_analysis', %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (ticker, model_name) DO UPDATE SET
    timestamp=EXCLUDED.timestamp, fair_value=EXCLUDED.fair_value, current_price=EXCLUDED.current_price,
    upside_pct=EXCLUDED.upside_pct, suitable=EXCLUDED.suitable, confidence=EXCLUDED.confidence,
    details_json=EXCLUDED.details_json''',
    (ticker, datetime.now().isoformat(), fair_value, current_price,
     expected_value_pct, suitable, confidence, json.dumps(details)))
conn.commit()
conn.close()
print(f'Saved {ticker} llm_deep_analysis: verdict={verdict}, EV={expected_value_pct}%, confidence={confidence}')
"
```

**This step is MANDATORY.** Every deep analysis must be persisted to the database so the dashboard and other tools can access it.

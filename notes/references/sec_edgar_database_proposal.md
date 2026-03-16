# SEC EDGAR Database Integration Proposal

## Executive Summary

**Source**: SEC EDGAR companyfacts.zip (1.2 GB, 10,000+ companies)
**Coverage**: 2006-2025 (19 years) ✓ **EXCEEDS our requirement (17 years)**
**Data Quality**: Official SEC filings - highest quality available
**Cost**: $0 - completely free
**Status**: Data downloaded and analyzed

---

## Data Format Analysis

### File Structure
```
companyfacts.zip
├── CIK0000320193.json  (Apple - 3.4 MB)
├── CIK0000789019.json  (Microsoft - 4.4 MB)
└── ... (~10,000 company files)
```

### JSON Structure (Per Company)
```json
{
  "cik": 320193,
  "entityName": "Apple Inc.",
  "facts": {
    "us-gaap": {
      "Assets": {
        "label": "Assets",
        "description": "...",
        "units": {
          "USD": [
            {
              "end": "2025-06-28",
              "val": 364980000000,
              "accn": "0000320193-25-000077",
              "fy": 2025,
              "fp": "Q3",
              "form": "10-Q",
              "filed": "2025-08-01",
              "frame": "CY2025Q2"
            },
            // ... hundreds of historical datapoints
          ]
        }
      },
      // ... hundreds of XBRL tags
    }
  }
}
```

### Historical Depth (Apple Example)
| Metric | Datapoints | Earliest | Latest | Years |
|--------|-----------|----------|--------|-------|
| Assets | 138 | 2008-09-27 | 2025-06-28 | 17 |
| NetIncomeLoss | 325 | 2007-09-29 | 2025-06-28 | 18 |
| StockholdersEquity | 244 | 2006-09-30 | 2025-06-28 | 19 |
| Cash | 220 | 2006-09-30 | 2025-06-28 | 19 |

**Conclusion**: We have 19 years of quarterly fundamental data ✓

---

## Available Financial Metrics

### Income Statement
- ✓ Revenues / RevenueFromContractWithCustomerExcludingAssessedTax
- ✓ GrossProfit
- ✓ OperatingIncomeLoss
- ✓ NetIncomeLoss
- ✓ EarningsPerShareBasic
- ✓ EarningsPerShareDiluted

### Balance Sheet
- ✓ Assets / AssetsCurrent
- ✓ Liabilities / LiabilitiesCurrent / LiabilitiesNoncurrent
- ✓ StockholdersEquity
- ✓ CashAndCashEquivalentsAtCarryingValue
- ✓ LongTermDebt / ShortTermBorrowings
- ✓ CommonStockSharesOutstanding

### Cash Flow
- ✓ NetCashProvidedByUsedInOperatingActivities
- ✓ NetCashProvidedByUsedInInvestingActivities
- ✓ NetCashProvidedByUsedInFinancingActivities

**From these we can calculate ALL ratios we need:**
- PE Ratio = Price / EPS
- PB Ratio = Price / Book Value Per Share
- PS Ratio = Price / Revenue Per Share
- Profit Margin = Net Income / Revenue
- Operating Margin = Operating Income / Revenue
- ROE = Net Income / Stockholders Equity
- Revenue Growth = YoY change
- Earnings Growth = YoY change
- Debt-to-Equity = Total Debt / Stockholders Equity
- Current Ratio = Current Assets / Current Liabilities
- FCF Yield = Free Cash Flow / Market Cap
- OCF Yield = Operating Cash Flow / Market Cap

---

## Database Schema - NO CHANGES NEEDED! ✓

**Good News**: Our existing `snapshots` table already has all the fields we need!

Current schema:
```sql
CREATE TABLE snapshots (
    id INTEGER PRIMARY KEY,
    asset_id INTEGER NOT NULL,
    snapshot_date DATE NOT NULL,

    -- Fundamental ratios (currently NULL - we'll populate these)
    pe_ratio REAL,
    pb_ratio REAL,
    ps_ratio REAL,
    profit_margins REAL,
    operating_margins REAL,
    return_on_equity REAL,
    revenue_growth REAL,
    earnings_growth REAL,
    debt_to_equity REAL,
    current_ratio REAL,

    -- Per-share metrics
    trailing_eps REAL,
    book_value REAL,
    revenue_per_share REAL,

    -- Cash flow metrics
    free_cashflow REAL,
    operating_cashflow REAL,

    -- Company size
    market_cap REAL,

    -- Macro indicators (already populated)
    vix REAL,
    treasury_10y REAL,
    dollar_index REAL,
    oil_price REAL,
    gold_price REAL,

    FOREIGN KEY (asset_id) REFERENCES assets(id)
);
```

**Schema Changes Required**: **NONE** ✓

All fields already exist. We just need to populate the NULL values.

---

## Implementation Plan

### Phase 1: Full Extraction (1-2 days)
```bash
# 1. Extract full ZIP (10,000+ companies)
cd /Users/rubenayla/repos/invest/data/sec_edgar/raw
unzip companyfacts.zip -d companyfacts/

# 2. Make backup read-only
chmod -R 444 companyfacts/

# 3. Extract our 358 tickers
python data/sec_edgar/scripts/extract_our_tickers.py
```

### Phase 2: Calculate Ratios (1-2 days)
```python
# For each stock and each snapshot date:
# 1. Find closest SEC filing date (quarterly report)
# 2. Extract raw financials (revenue, earnings, assets, etc.)
# 3. Get price from price_history for that date
# 4. Calculate all ratios
# 5. Handle missing data gracefully
```

### Phase 3: Database Population (1 day)
```sql
-- For each snapshot:
UPDATE snapshots
SET
    pe_ratio = ?,
    pb_ratio = ?,
    ps_ratio = ?,
    profit_margins = ?,
    operating_margins = ?,
    return_on_equity = ?,
    revenue_growth = ?,
    earnings_growth = ?,
    debt_to_equity = ?,
    current_ratio = ?,
    trailing_eps = ?,
    book_value = ?,
    revenue_per_share = ?,
    free_cashflow = ?,
    operating_cashflow = ?,
    market_cap = ?
WHERE id = ?;
```

### Phase 4: Data Quality Verification (1 day)
- Check coverage: How many snapshots now have data?
- Check for outliers (PE > 1000, negative margins where unexpected)
- Compare with current_stock_data for recent quarters
- Verify growth rate calculations are correct

### Phase 5: Update Neural Network Training (2-3 days)
- Modify `train_single_horizon.py` to use fundamental features
- Update temporal features to include fundamental ratios per snapshot
- Update static features to include latest fundamentals
- Retrain all models (1m, 3m, 6m, 1y, 2y, 3y)
- Evaluate performance improvement

**Total Time**: 7-10 days
**Total Cost**: $0

---

## Data Mapping Strategy

### Quarterly Filing Dates → Semi-Annual Snapshots

Our snapshots are semi-annual (~every 6 months).
SEC filings are quarterly (every 3 months).

**Mapping approach**:
```
Snapshot Date: 2020-01-03
  ↓
Find SEC filing closest to this date (within ±3 months)
  ↓
SEC filing: 2019-12-31 (10-K or 10-Q)
  ↓
Extract fundamentals from this filing
  ↓
Calculate ratios using price from price_history on 2020-01-03
```

**Logic**:
```python
def find_closest_filing(snapshot_date, sec_datapoints):
    # Find filing within ±90 days
    tolerance = 90 days
    closest = min(sec_datapoints,
                  key=lambda dp: abs(dp['end'] - snapshot_date))
    if abs(closest['end'] - snapshot_date) <= tolerance:
        return closest
    return None
```

---

## Handling Data Quality Issues

### Issue 1: Different XBRL Tags Across Companies
**Problem**: Companies may use different tags for the same metric
- Some use `Revenues`
- Others use `RevenueFromContractWithCustomerExcludingAssessedTax`
- Others use `SalesRevenueNet`

**Solution**: Try multiple tag variants in order of preference
```python
REVENUE_TAGS = [
    'Revenues',
    'RevenueFromContractWithCustomerExcludingAssessedTax',
    'SalesRevenueNet',
    'RevenueFromContractWithCustomerIncludingAssessedTax'
]

for tag in REVENUE_TAGS:
    if tag in company_facts['us-gaap']:
        revenue_data = company_facts['us-gaap'][tag]
        break
```

### Issue 2: Missing Datapoints
**Problem**: Not all companies file all metrics for all quarters

**Solution**:
- Mark snapshots with insufficient data as NULL
- Track coverage statistics
- Accept that some snapshots won't have complete fundamental data

### Issue 3: Outliers and Errors
**Problem**: Calculation errors, data entry mistakes

**Solution**:
- Cap extreme values (PE ratio: [-50, 100], PB ratio: [0, 20])
- Flag suspicious values for manual review
- Keep raw SEC data for verification

---

## Expected Outcomes

### Coverage Estimate

Current status:
- Snapshots table: 15,003 snapshots from 358 stocks
- Currently: 0 snapshots with fundamental data

After population:
- **Best case**: 12,000-13,000 snapshots with complete fundamental data (~80-85%)
- **Realistic**: 10,000-11,000 snapshots with complete fundamental data (~65-75%)
- **Worst case**: 8,000-9,000 snapshots with partial fundamental data (~55-60%)

**Why not 100%?**
- Some companies may not have filed for older periods
- XBRL tagging inconsistencies
- Companies that went public recently
- Missing or incomplete filings

### Neural Network Performance

**Current models** (without fundamentals):
- Features: Price momentum + Macro indicators + Sector
- 1y model: 78.64% hit rate, 44.2% correlation

**Expected with fundamentals**:
- Features: Price momentum + Macro + Sector + **Fundamentals**
- Expected improvement: +5-15% hit rate, +10-20% correlation
- Why: Fundamentals provide company quality signals that price alone misses

**Temporal advantage**:
- Current: Only most recent fundamentals as static features
- Proposed: Fundamental evolution over 4 snapshots (2 years) in temporal sequence
- LSTM can learn patterns like "improving margins → price increase"

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Data extraction fails | High | Low | Test with 5 stocks first |
| XBRL tag inconsistencies | Medium | High | Use multiple tag fallbacks |
| < 50% coverage | High | Low | Check 10 sample stocks first |
| Ratio calculation errors | Medium | Medium | Extensive unit tests |
| Model performance degrades | High | Very Low | Keep old models as baseline |
| 7-10 day implementation time | Low | High | Worth it for free, complete data |

---

## Recommendation

**PROCEED WITH SEC EDGAR INTEGRATION**

**Reasons**:
1. ✓ **Free** - $0 vs $180-850/year for paid services
2. ✓ **Complete** - 19 years vs 5-20 years from paid services
3. ✓ **Official** - Highest quality data available
4. ✓ **No schema changes** - Existing database structure is perfect
5. ✓ **Expected improvement** - Neural networks should perform significantly better with fundamentals

**Next Steps**:
1. Create proof-of-concept script to extract 5 stocks
2. Verify data quality and coverage
3. If good → proceed with full extraction
4. If poor → reconsider paid API options

Would you like me to create the proof-of-concept extraction script?

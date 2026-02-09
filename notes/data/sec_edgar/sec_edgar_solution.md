# SEC EDGAR - FREE Open-Source Fundamental Data Solution ⭐⭐⭐

## THE ANSWER: Yes, There IS an Open-Source Bank of Data!

**SEC EDGAR (Securities and Exchange Commission - Electronic Data Gathering, Analysis, and Retrieval)**

All publicly-traded US companies are **required by law** to file their financial statements with the SEC. This data is **100% free and public**.

---

## What SEC EDGAR Provides

### Data Coverage
- **ALL US publicly-traded companies** (10,000+ tickers)
- **Historical depth**: Complete filing history since companies went public (often 20-30+ years!)
- **Frequency**: Quarterly (10-Q) and Annual (10-K) reports
- **Format**: XBRL (eXtensible Business Reporting Language) - structured, machine-readable

### Financial Statements
- Income Statements (Profit & Loss)
- Balance Sheets
- Cash Flow Statements
- Statement of Changes in Equity
- **All line items**: Revenue, expenses, assets, liabilities, cash flows, etc.

### From These We Can Calculate
- PE ratio (Price / EPS)
- PB ratio (Price / Book Value)
- PS ratio (Price / Revenue)
- Profit margins
- Operating margins
- ROE (Return on Equity)
- Revenue growth
- Earnings growth
- Debt-to-equity
- Current ratio
- Free cash flow
- **Everything we need!**

---

## How to Access It (100% FREE)

### Option 1: Bulk Download (FASTEST)
**companyfacts.zip** - All company XBRL data in one ZIP file
- **URL**: https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip
- **Size**: Large (several GB)
- **Updated**: Nightly
- **Format**: JSON files (one per company with all historical filings)
- **Cost**: FREE
- **Rate limit**: None for bulk download

### Option 2: SEC EDGAR API
**Official RESTful API**
- **Endpoint**: https://data.sec.gov/api/xbrl/companyfacts/CIK{######}.json
- **Cost**: FREE
- **Authentication**: None required (no API key!)
- **Rate limit**: 10 requests/second
- **Historical depth**: Complete filing history

### Option 3: Financial Statement Data Sets (Quarterly ZIP Files)
**URL**: https://www.sec.gov/data-research/sec-markets-data/financial-statement-data-sets
- Pre-processed quarterly datasets
- Updated quarterly
- CSV/TSV format
- All companies combined

---

## Python Libraries for Parsing SEC EDGAR

### 1. edgartools (RECOMMENDED) ⭐
**GitHub**: https://github.com/dgunning/edgartools
**Install**: `uv add edgartools`

**Features**:
- Simple API (3 lines of code)
- Access Balance Sheets, Income Statements, Cash Flows
- XBRL tag or common name lookup
- Handles quarterly and annual data
- Built-in caching

**Example**:
```python
from edgar import Company

# Get company
apple = Company('AAPL')

# Get quarterly income statement
income = apple.income_statement(periods=8, annual=False)  # Last 8 quarters

# Get balance sheet
balance = apple.balance_sheet(periods=8, annual=False)

# Get cash flow
cashflow = apple.cash_flow(periods=8, annual=False)
```

### 2. sec-edgar-financials
**GitHub**: https://github.com/farhadab/sec-edgar-financials
- Parses SGML to JSON
- Quarterly & annual data
- Good for batch processing

### 3. Direct companyfacts.zip Parsing
- Download bulk ZIP
- Extract JSON files
- Parse with standard Python JSON library
- Most flexible but requires more coding

---

## Data Structure Example

From companyfacts.zip, each company has a JSON file like:
```json
{
  "cik": 320193,
  "entityName": "Apple Inc.",
  "facts": {
    "us-gaap": {
      "Revenues": {
        "label": "Revenues",
        "units": {
          "USD": [
            {
              "end": "2023-09-30",
              "val": 383285000000,
              "form": "10-K",
              "fy": 2023,
              "frame": "CY2023"
            },
            {
              "end": "2023-06-30",
              "val": 81797000000,
              "form": "10-Q",
              "fy": 2023,
              "fp": "Q3",
              "frame": "CY2023Q3"
            }
            // ... historical quarters going back 20+ years
          ]
        }
      },
      "Assets": { ... },
      "Liabilities": { ... },
      // ... hundreds of XBRL tags
    }
  }
}
```

---

## Implementation Plan

### Phase 1: Test with edgartools (1-2 hours)
1. Install: `uv add edgartools`
2. Test with 5 stocks to verify data quality
3. Check historical depth (should be 10-20+ years)
4. Verify we can extract all needed ratios

### Phase 2: Batch Download (1 day)
1. Download companyfacts.zip (~5-10 GB)
2. Extract JSON files
3. Parse for our 358 tickers
4. Extract quarterly data matching our snapshot dates (semi-annual)

### Phase 3: Calculate Ratios (1 day)
1. Extract raw financial data (revenue, earnings, assets, liabilities, etc.)
2. Match to price_history for calculating ratios (PE = Price / EPS)
3. Calculate all fundamental ratios:
   - Valuation: PE, PB, PS
   - Profitability: Profit margin, Operating margin, ROE
   - Growth: Revenue growth, Earnings growth
   - Financial health: Debt-to-equity, Current ratio
   - Cash flow: FCF yield, OCF yield

### Phase 4: Populate Database (1 day)
1. Map SEC filing dates to nearest snapshot dates
2. INSERT/UPDATE snapshots table with calculated ratios
3. Verify data quality (check for outliers, NULL values)

### Phase 5: Retrain Models (2-3 days)
1. Update training scripts to use fundamental features
2. Retrain all horizons (1m, 3m, 6m, 1y, 2y, 3y)
3. Evaluate improvement in prediction accuracy

**Total estimated time**: 5-7 days
**Total cost**: $0

---

## Advantages of SEC EDGAR

✅ **100% FREE** - No cost, ever
✅ **Complete historical data** - 20-30+ years for most companies
✅ **Official source** - Direct from SEC, highest quality
✅ **No rate limits** (for bulk download)
✅ **No API keys** required
✅ **Open source** - Multiple Python libraries available
✅ **Updated regularly** - Companies must file quarterly
✅ **Covers all our stocks** - All US publicly-traded companies
✅ **More data than we need** - Can get ALL financial line items, not just ratios

## Disadvantages

❌ **Requires parsing** - More complex than paid APIs (but libraries help!)
❌ **XBRL complexity** - Different companies use different tags
❌ **Data cleaning needed** - May have reporting differences across companies
❌ **Implementation time** - ~5-7 days vs instant API access
❌ **Large files** - companyfacts.zip is several GB

---

## RECOMMENDATION

**Use SEC EDGAR via edgartools library**

This is the **BEST solution** because:
1. Completely free (saves $15-71/month)
2. Most comprehensive data (20-30+ years vs 5-20 years from paid services)
3. Official source (highest quality)
4. Open source (no vendor lock-in)
5. Good Python libraries available (edgartools makes it easy)

The only cost is implementation time (~5-7 days), but you save hundreds of dollars per year and get better data.

**Next step**: Test edgartools with a few stocks to verify it works for our use case.

Would you like me to implement a proof-of-concept?

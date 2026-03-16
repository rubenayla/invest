# YFinance Historical Fundamental Data - LIMITS

## What YFinance Actually Provides

### Frequency
- **Quarterly data**: Financial statements reported every 3 months
- **Annual data**: Financial statements reported every year

### Historical Depth (CRITICAL LIMITATION)
Tested with AAPL on 2025-10-10:
- **Quarterly financials**: Only 5 quarters (~1.25 years)
  - Most recent dates: 2025-06-30, 2025-03-31, 2024-12-31, 2024-09-30, 2024-06-30
- **Annual financials**: Only 4 years

### What This Means
**YFinance CANNOT provide historical fundamentals for our snapshots table.**

Our snapshots span:
- **2006 to 2025** (19 years)
- **15,003 snapshots**
- **Semi-annual frequency** (~every 6 months)

YFinance only provides:
- **2024-2025** (1.25 years of quarterly data)
- **5 quarterly periods**

**We can only populate the MOST RECENT snapshots (~5 quarters = 2-3 snapshots per stock).**

## What Data Does YFinance Historical Provide?

From quarterly/annual financials, balance sheets, and cash flows:

**Income Statement**:
- Total Revenue
- Gross Profit
- Operating Income
- Net Income
- EPS (Earnings Per Share)

**Balance Sheet**:
- Total Assets
- Total Liabilities
- Stockholders Equity
- Total Debt
- Cash and Cash Equivalents

**Cash Flow**:
- Operating Cash Flow
- Free Cash Flow
- Capital Expenditures

**From these we can CALCULATE**:
- PE Ratio = Price / EPS
- PB Ratio = Price / Book Value Per Share
- PS Ratio = Price / Revenue Per Share
- Profit Margin = Net Income / Revenue
- Operating Margin = Operating Income / Revenue
- ROE = Net Income / Stockholders Equity
- Debt-to-Equity = Total Debt / Stockholders Equity
- Revenue Growth = (Revenue_current - Revenue_previous) / Revenue_previous
- Earnings Growth = (Earnings_current - Earnings_previous) / Earnings_previous

## THE FUNDAMENTAL PROBLEM

**We cannot train neural networks with historical fundamentals because:**

1. Our snapshots go back 19 years (2006-2025)
2. YFinance only provides 1.25 years of quarterly fundamentals
3. **We cannot populate 99% of our historical snapshots**

## REVISED OPTIONS

### Option 1: Train with Recent Data Only (2024-2025)
**Approach**: Only use snapshots from 2024-2025 where we can fetch fundamentals
**Problem**: Only ~2-3 snapshots per stock = insufficient training data

### Option 2: Train Without Fundamentals (ONLY REALISTIC OPTION)
**Approach**: Accept that neural networks use only:
- Price momentum (returns, volatility, volume)
- Macro indicators (VIX, rates, commodities)
- Sector

**Reality**: This is what we MUST do because historical fundamental data is not available at sufficient depth.

### Option 3: Use Alternative Data Source
**Approach**: Find a paid API that provides 10+ years of historical quarterly fundamentals
**Problem**: Expensive, requires subscription (Alpha Vantage Premium, Financial Modeling Prep, etc.)

## CONCLUSION

**YFinance does NOT provide sufficient historical fundamental data to train our neural networks.**

The neural networks MUST be trained with:
- Price momentum + Macro indicators + Sector only

This is a **data availability constraint**, not a design choice.

The disagreement between traditional models and neural networks is explained:
- Traditional models use current fundamentals
- Neural networks cannot use fundamentals due to lack of historical data

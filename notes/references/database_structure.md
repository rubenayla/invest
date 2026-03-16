# Database Structure - Actual Findings

## Snapshots Table Structure

### Temporal Resolution
**Semi-annual**: ~6 months between snapshots (average 46 days, but that's skewed by duplicates)

**Actual unique snapshots per stock**: 36 dates over 17 years (2006-2023)
- Total records: 138 per stock
- **Bug detected**: 4 duplicate records per snapshot date (same data, different IDs)
- True frequency: 17 years / 36 snapshots = **one snapshot every ~6 months**

### What Each Snapshot Contains

**Macro indicators** (populated with real data):
- VIX
- Treasury 10Y yield
- Dollar Index
- Oil price
- Gold price

**Fundamental ratios** (ALL NULL - no data):
- pe_ratio
- pb_ratio
- ps_ratio
- profit_margins
- operating_margins
- return_on_equity
- revenue_growth
- earnings_growth
- debt_to_equity
- current_ratio
- trailing_eps
- book_value
- free_cashflow
- operating_cashflow
- market_cap

**Metadata**:
- snapshot_date
- asset_id (links to assets table for ticker/sector)

## Price History Table (Higher Temporal Resolution)

**Frequency**: DAILY (every trading day)

**Records**: 34.9 million daily OHLCV records
- Each snapshot has ~500-750 days of price history linked to it
- Goes back to 2004 (earlier than snapshots)

**What it contains**:
- date
- open
- high
- low
- close
- volume
- adjusted_close
- snapshot_id (links to snapshots)

## Data Alignment

```
Snapshots:     [Jan 2006]---6mo---[Jul 2006]---6mo---[Jan 2007]---6mo---[Jul 2007]
               Semi-annual points with macro data

Price History: •••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
               Daily OHLCV data for every trading day
```

Each snapshot has price history **up to that snapshot date**.

## Answer to Your Question

**Do snapshots contain data with higher temporal resolution than quarterly?**

**NO** - Snapshots themselves are LOWER resolution than quarterly:
- Snapshots: Every 6 months (semi-annual)
- Quarterly: Every 3 months

**But price_history has MUCH HIGHER resolution**:
- Daily prices (every trading day)
- Linked to each snapshot

## Training Data Available

For neural network training, we have:

**Semi-annual (from snapshots)**:
- Macro indicators ✓
- Fundamentals ✗ (all NULL)

**Daily (from price_history)**:
- OHLCV prices ✓
- From these we calculate: returns, volatility, volume trends ✓

## The Gap

YFinance provides quarterly fundamentals (every 3 months), but:
- Our snapshots are semi-annual (every 6 months) - so quarterly would be MORE frequent, which is fine
- Problem: YFinance only provides 5 quarters (1.25 years), we need 70+ quarters (17 years)

**Quarterly frequency would be BETTER than our semi-annual snapshots.**
**The problem is DEPTH (only 5 quarters available), not FREQUENCY.**

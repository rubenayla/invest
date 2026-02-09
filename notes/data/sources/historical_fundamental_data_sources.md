# Historical Fundamental Data Sources - Comparison

## Requirements
- **Historical depth**: 17+ years (2006-2025) to match our snapshots
- **Frequency**: Quarterly or annual financial statements
- **Coverage**: US stocks (358 tickers)
- **Data types**: Income statements, balance sheets, cash flows
- **From these**: Calculate PE, PB, margins, ROE, growth rates, etc.

---

## FREE Options

### 1. SimFin (BEST FREE OPTION) ⭐
**Historical Depth**: 5 years (free tier)
**Coverage**: 5,000 US stocks
**Data Types**:
- Quarterly & annual financials
- Balance sheets
- Income statements
- Cash flows
- 80+ calculated indicators

**API Access**:
- Python library available
- Bulk download
- 500 high-speed credits/month
- 2 API calls/second
- **12-month delay on free data**

**Pros**:
- ✓ Free forever
- ✓ Python library (`simfin` package)
- ✓ Well-documented API
- ✓ Bulk downloads available
- ✓ 5 years is enough for recent training

**Cons**:
- ✗ Only 5 years (need 17 years for full history)
- ✗ 12-month data delay
- ✗ Can't train on 2006-2018 period

**Verdict**: Good for testing, insufficient for full historical training

---

### 2. Alpha Vantage
**Historical Depth**: 5 years ONLY
**Coverage**: Most US stocks
**Data Types**:
- Annual & quarterly income statements
- Balance sheets
- Cash flows

**API Access**:
- Free API key
- 25 requests/day (severe limitation!)
- 5 requests/minute

**Pros**:
- ✓ Completely free
- ✓ Easy to use
- ✓ JSON format

**Cons**:
- ✗ ONLY 5 years of historical data
- ✗ Very limited rate (25 requests/day for 358 stocks = 15 days to fetch all!)
- ✗ Can't get data before 2019

**Verdict**: Too limited for our needs

---

### 3. YFinance (Current)
**Historical Depth**: 1.25 years (5 quarters)
**Coverage**: Most stocks
**Data Types**: Quarterly & annual financials

**Pros**:
- ✓ Already using it
- ✓ No API key needed
- ✓ Good for current data

**Cons**:
- ✗ Only 5 quarters = 1.25 years
- ✗ Completely insufficient

**Verdict**: Not viable

---

### 4. Financial Modeling Prep (FMP) - Free Tier
**Historical Depth**: Up to 30 years (!)
**Coverage**: Most US stocks
**Data Types**: All financial statements

**API Access**:
- **250 total requests** (not per month - TOTAL!)
- After 250 requests, must upgrade

**Pros**:
- ✓ 30 years of historical data available
- ✓ Excellent data quality
- ✓ Good documentation

**Cons**:
- ✗ Only 250 total API calls before requiring paid plan
- ✗ 358 stocks × multiple endpoints = would exhaust immediately
- ✗ Not really "free" for our use case

**Verdict**: Free tier is a trap - insufficient quota

---

## PAID Options (Reasonable Cost)

### 1. SimFin START - $15/month ⭐⭐⭐ RECOMMENDED
**Historical Depth**: 10 years
**Coverage**: 5,000 US stocks
**Data Types**: All fundamentals

**API Access**:
- Python API
- 5,000 high-speed credits/month
- Bulk downloads
- Excel plugin

**Cost**: $180/year (if paid annually)

**Pros**:
- ✓ Affordable ($15/month)
- ✓ 10 years of history (2015-2025)
- ✓ Good enough for training (covers recent market regimes)
- ✓ No data delay
- ✓ Python library

**Cons**:
- ✗ Missing 2006-2014 data (9 years)
- ✗ Can't train on pre-2008 crisis period

**Verdict**: BEST VALUE - good balance of cost vs coverage

---

### 2. SimFin BASIC - $35/month
**Historical Depth**: 15 years (2010-2025)
**Coverage**: 5,000 US stocks
**Data Types**: All fundamentals + premium datasets

**API Access**:
- 15,000 high-speed credits/month
- 5 calls/second
- Premium bulk datasets
- Email support

**Cost**: $420/year

**Pros**:
- ✓ 15 years (covers 2008 crisis!)
- ✓ Premium datasets
- ✓ Higher API limits

**Cons**:
- ✗ Still missing 2006-2009
- ✗ More expensive

**Verdict**: Good option if you want 2008 crisis in training data

---

### 3. SimFin PRO - $71/month
**Historical Depth**: 20+ years (2003-2025)
**Coverage**: 5,000 US stocks
**Data Types**: Complete historical fundamentals

**API Access**:
- 30,000 high-speed credits/month
- 20 calls/second
- Phone support

**Cost**: $852/year

**Pros**:
- ✓ FULL 20+ years (exceeds our 17-year requirement!)
- ✓ Covers all market regimes (dot-com bubble, 2008 crisis, COVID, etc.)
- ✓ Complete historical training data

**Cons**:
- ✗ Most expensive
- ✗ May be overkill for our needs

**Verdict**: Complete solution if you want maximum historical depth

---

### 4. Financial Modeling Prep - Starter - $19.99/month
**Historical Depth**: 30 years
**Coverage**: Most US stocks
**Data Types**: All financials

**API Access**:
- 250 requests/day
- 10 requests/second
- Good documentation

**Cost**: $240/year

**Pros**:
- ✓ 30 years of historical data
- ✓ Reasonable daily limit

**Cons**:
- ✗ 250 requests/day for 358 stocks × 3 endpoints (income, balance, cashflow) = ~5 days to fetch
- ✗ Need to manage rate limits carefully

**Verdict**: Comparable to SimFin START, but less focused on fundamentals

---

### 5. EOD Historical Data (EODHD) - All-World - $19.99/month
**Historical Depth**: 20+ years for quarterly & annual data
**Coverage**: 11,000+ US tickers (NYSE, NASDAQ, ARCA)
**Data Types**: All financial statements

**API Access**:
- 100,000 requests/day
- 20 requests/second

**Cost**: $240/year

**Pros**:
- ✓ 20 years of data
- ✓ Very high API limits
- ✓ Excellent coverage
- ✓ Good value

**Cons**:
- ✗ Less focused on fundamentals than SimFin
- ✗ API documentation quality varies

**Verdict**: Strong alternative to SimFin

---

## MY RECOMMENDATION

### For Budget-Conscious ($15-20/month)
**SimFin START - $15/month**
- 10 years of history (2015-2025)
- Covers recent market regimes (COVID, Fed tightening, etc.)
- Best value for money
- **Good enough for neural network training**

### For Complete Historical Coverage ($71/month)
**SimFin PRO - $71/month**
- 20+ years (2003-2025)
- Covers ALL market regimes
- Complete training data for your 17-year requirement
- Worth it if you want maximum model performance

### Free Testing Strategy
1. Start with **SimFin FREE** (5 years)
2. Train model on 2020-2025 data
3. Evaluate if fundamentals improve predictions
4. If yes → upgrade to SimFin START or PRO
5. If no → save money, stick with price momentum + macro

---

## IMPLEMENTATION PLAN

If you choose SimFin START ($15/month):

1. **Sign up**: Get API key from simfin.com
2. **Install**: `uv add simfin`
3. **Fetch**: Write script to fetch quarterly fundamentals for 358 stocks
4. **Calculate**: Compute PE, PB, margins, ROE, growth rates
5. **Populate**: Insert into snapshots table (matching dates)
6. **Train**: Retrain neural networks with fundamentals
7. **Evaluate**: Compare performance vs price-only models

**Estimated time**: 1-2 days for implementation
**Data volume**: ~40,000 quarterly records (358 stocks × 40 quarters × 3 statements)

Would you like me to implement the SimFin integration?

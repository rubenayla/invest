# Project Diary

A log of significant progress, achievements, and learnings.

---

## 2025-10-20: Critical Database Blindspot - Silent Data Loss in ML Predictions

### 🚨 Discovery: The Missing 20%

While investigating data flow consistency, discovered that **ML model predictions are silently discarded** for stocks without current price data.

### 📊 The Problem

**Database stock counts:**
```
assets table:          451 stocks (master registry)
snapshots table:       358 stocks (ML training data)
current_stock_data:    302 stocks (current prices + fundamentals)
valuation_results:     304 stocks (stocks with valuations)
```

**The gap:**
- ML models train on 358 stocks from `snapshots`
- Predictions run on 357 stocks (latest snapshot per ticker)
- Only 286 predictions saved to database (**71 stocks lost, 20% data loss**)

### 🔍 Root Cause Analysis

#### Code Location: `scripts/run_gbm_opportunistic_1y_predictions.py:294-308`

```python
for i, (idx, row) in enumerate(df.iterrows()):
    ticker = row['ticker']

    # Get current price from current_stock_data table
    stock_data = reader.get_stock_data(ticker)
    if not stock_data or 'info' not in stock_data:
        logger.warning(f'Skipping {ticker}: no data in current_stock_data')
        skipped += 1
        continue  # ← PREDICTIONS DISAPPEAR HERE - NO DATABASE RECORD
```

**What happens:**
1. GBM model makes predictions for 357 stocks (all with snapshots)
2. Script tries to save to `valuation_results` table
3. Checks if ticker exists in `current_stock_data` (needed for current price)
4. **71 stocks missing from `current_stock_data`** → skipped silently
5. No database record created (not even as "unsuitable" with error message)
6. Dashboard never sees these stocks

### 📋 Missing Stocks Include Major Companies

**Sample of 71 missing stocks:**
- **AAPL** (Apple)
- **GOOGL** (Alphabet)
- **TSLA** (Tesla)
- **AVGO** (Broadcom)
- **ASML** (ASML Holding)
- **BKNG** (Booking.com)
- ABNB, ACN, AFRM, AZN, BP, BRK-B, CSCO, and 58 more...

These stocks:
- Have historical quarterly data in `snapshots` table
- Were used to train ML models
- Got predictions calculated
- **Had those predictions discarded** without any trace

### 🔄 Data Flow Visualization

```
Training Phase:
├─ snapshots table: 358 stocks loaded ✓
├─ Feature engineering: 357 stocks (latest snapshot) ✓
├─ Model training: 357 stocks used ✓
└─ Model saved: gbm_opportunistic_model_1y.txt ✓

Prediction Phase:
├─ Load model ✓
├─ Load snapshots: 357 stocks ✓
├─ Feature engineering: 357 stocks ✓
├─ Make predictions: 357 stocks ✓
├─ Save to database:
│   ├─ Check current_stock_data: 286 found ✓
│   └─ Missing current_stock_data: 71 skipped ✗ ← SILENT DATA LOSS
└─ Dashboard display: 286 stocks only

User sees: 286 stocks
User doesn't see: 71 stocks with predictions (20% invisible)
```

### 🆚 Comparison with Traditional Models

**Traditional DCF/RIM models:**
- Run on 302 stocks (all in `current_stock_data`)
- Store unsuitable valuations with error messages
- Dashboard shows "-" with tooltip explaining why
- User knows the stock was evaluated

**ML GBM models:**
- Train on 358, predict on 357, save only 286
- Silently skip 71 stocks (no database record)
- Dashboard shows nothing (stock doesn't appear)
- **User has no idea these stocks exist**

### 💡 Why This Matters

#### 1. Misleading Completeness
User sees dashboard with 286 stocks and assumes that's everything. Actually missing 20% of predictions.

#### 2. No Visibility into Missing Data
Traditional models show "-" with error tooltip. ML models: complete silence.

#### 3. Major Companies Missing
AAPL, GOOGL, TSLA are missing. These aren't obscure penny stocks.

#### 4. Training Data Mismatch
Models trained on 358 stocks but predictions only saved for 286. What happened to the other 72?

### 🔧 Discovered via Systematic Blindspot Analysis

**Framework applied:**
1. "Are there other scripts that query valuation_results with similar filters?"
2. "Could skipped stocks be leaving no database trace?"
3. "Is there a gap between training universe and prediction coverage?"

**Verification process:**
```bash
# Check GBM prediction count
sqlite3 stock_data.db "SELECT COUNT(*) FROM valuation_results
  WHERE model_name = 'gbm_opportunistic_1y';"
# Result: 286

# Check if AAPL has GBM predictions
sqlite3 stock_data.db "SELECT * FROM valuation_results
  WHERE ticker = 'AAPL' AND model_name = 'gbm_opportunistic_1y';"
# Result: 0 rows (confirmed missing)

# Check if AAPL exists in snapshots
sqlite3 stock_data.db "SELECT COUNT(*) FROM snapshots s
  JOIN assets a ON s.asset_id = a.id WHERE a.symbol = 'AAPL';"
# Result: >0 (AAPL has training data!)

# Find the gap
sqlite3 stock_data.db "SELECT COUNT(*) FROM assets
  WHERE symbol NOT IN (SELECT ticker FROM current_stock_data);"
# Result: 149 stocks missing current data
```

### 📝 The Three-Table Problem

#### Table Purposes:
1. **`assets`** (451 stocks): Master registry - everything ever tracked
2. **`snapshots`** (358 stocks): Historical quarterly data for ML training
3. **`current_stock_data`** (302 stocks): Current prices from yfinance

#### The Mismatch:
- `snapshots` > `current_stock_data` (56 stock gap)
- ML models use `snapshots` for training
- Prediction scripts require `current_stock_data` for saving
- **56 stocks trained but can't be saved** ← core problem

### 🎯 Solution Options

#### Option 1: Store Unsuitable Predictions (Recommended)
Mirror what traditional models do:
```python
# Instead of skipping, save with suitable=0
cursor.execute('''
    INSERT INTO valuation_results
    (ticker, model_name, suitable, error_message)
    VALUES (?, ?, 0, 'No current price data available')
''', (ticker, 'gbm_opportunistic_1y'))
```

**Pros:**
- User sees "-" in dashboard with tooltip
- Consistent with traditional model behavior
- No data loss - all predictions accounted for

#### Option 2: Sync Current Stock Data
Run `data_fetcher.py` on the 149 missing tickers to populate `current_stock_data`

**Pros:**
- Fills the gap completely
- AAPL, GOOGL, TSLA get their predictions saved

**Cons:**
- Some may fail (foreign stocks, ETFs, delisted companies)
- Ongoing maintenance (need to keep syncing)

#### Option 3: Accept the Gap
Consider `current_stock_data` as the "curated universe" and only track those 302 stocks.

**Pros:**
- Simple, no code changes

**Cons:**
- Wastes training data on 56 stocks we never use
- Major companies like AAPL missing is unacceptable

### 🔑 Key Lessons

#### 1. Silent Failures Are Worse Than Loud Ones
Traditional models fail loudly (error message in database). ML models fail silently (skip + log warning). User never knows.

#### 2. Always Verify Data Flow End-to-End
Just because predictions are calculated doesn't mean they reach the user. Check every step.

#### 3. Database Table Alignment Matters
Three tables with overlapping but non-identical stock lists → guaranteed confusion. Need single source of truth.

#### 4. Logs Are Not Enough
Log says "Skipped 71 stocks (no current price)" but user doesn't read logs. Database is source of truth.

#### 5. Blindspot Frameworks Work
Systematic questioning ("where could data disappear?") found this issue that manual review missed.

### 📊 Impact Assessment

**Before discovery:**
- User sees 286 GBM predictions
- Thinks coverage is complete
- Missing 20% of predictions
- No idea major stocks like AAPL are absent

**After discovery:**
- Understand the 3-table architecture
- Know why 71 predictions are lost
- Have 3 solution options
- Can make informed decision

### 🚀 Next Steps

**Immediate:**
1. Decide on solution approach (Option 1 recommended)
2. Implement unsuitable prediction storage
3. Regenerate all ML predictions
4. Verify dashboard shows all stocks (with "-" for missing ones)

**Longer term:**
1. Audit all prediction scripts (NN, GBM variants) for same issue
2. Consider database schema refactoring (single stock universe)
3. Add validation: "training stocks = prediction stocks = dashboard stocks"

### 📁 Files Analyzed

- `scripts/run_gbm_opportunistic_1y_predictions.py` (prediction script)
- `scripts/run_gbm_opportunistic_3y_predictions.py` (same issue)
- `scripts/dashboard.py` (loads from valuation_results)
- `src/invest/dashboard_components/html_generator.py` (renders dashboard)
- Database schema: `assets`, `snapshots`, `current_stock_data`, `valuation_results`

### ⚠️ Remember

This is a **data integrity issue**, not a performance issue. Silent data loss breaks user trust. Fix by making failures visible (Option 1) or eliminating failures (Option 2).

---

## 2025-10-09: Neural Network Training Journey - From 0% to 78% Hit Rate

### 🎯 Mission
Train LSTM/Transformer model for 1-year stock predictions with proper data and evaluation.

### 📊 Starting Point
- Initial evaluation showed terrible performance (MAE 28.73%, R² -0.5187)
- User: "the training is horrible. something must be wrong."

### 🔍 Investigation & Fixes

#### Issue 1: Training Scale Bug
**Problem:** Training script divided forward returns by 100 when database already stored them as decimals
- Database: `2.05` = 205% gain
- Script was converting: `2.05 / 100 = 0.0205` (treating it as if it were `205`)

**Fix:** Removed `/100.0` division in `train_single_horizon.py:182`

**Result:** MAE improved to 22.69%, hit rate to 78.22%

#### Issue 2: Data Leakage from Random Split
**Problem:** Training used random 70/15/15 split across all 2006-2022 data
- Test set could contain 2015 samples while training on 2020
- Inflated performance metrics (not true out-of-sample testing)

**User feedback:** "this is the complete opposite of what you said in the previous message. Does the test period need to be separate from the train period?"

**Fix:** Implemented chronological split in `train_single_horizon.py:316-360`
- Train: ≤2020
- Val: 2021
- Test: 2022

**Result:** True performance revealed: MAE 24.90%, correlation **0.0056** (essentially zero!), hit rate 59.07% (barely better than coin flip)

#### Issue 3: Missing Fundamental Data (THE BIG ONE)
**Problem:** Database had **0% coverage** for critical fields:
- P/B Ratio: 0%
- Market Cap: 0%
- Profit Margins: 0%
- Operating Margins: 0%
- Return on Equity: 0%
- Free Cash Flow: 0%

**Root Cause:** Data fetcher was calling `features.get('market_cap')` but FeatureEngineer returns `'market_cap_log'`; also used `features.get('profit_margins')` but FeatureEngineer returns `'profit_margin'` (singular)

**User:** "make sure all the fields are filled, and our database is complete before we train"

**Fix:** Changed extraction to use RAW yfinance field names in `create_multi_horizon_cache.py:304-367`
- Before: `features.get('profit_margins')` ❌
- After: `info.get('profitMargins')` ✅ (raw yfinance camelCase)

Added warnings for missing critical fields:
```python
missing_fields = []
def safe_get(d, key, default=None, critical=False):
    val = d.get(key, default)
    if val is None:
        if critical:
            missing_fields.append(key)
        return default
    return val

if missing_fields:
    logger.warning(f'{ticker} ({snapshot_date}): Missing critical fields: {", ".join(missing_fields)}')
```

#### Issue 4: No Recent Data
**Problem:** Database only had snapshots through 2022-11-30

**User:** "you don't need to propose options all the time. The decision is obvious here. We need the data, we go and get it. simple as that."

**Fix:** Updated to fetch through current year: `end_year=datetime.now().year`

**User:** "option 2. Start fresh. We can keep the backup we did a while ago just in case. Remember the code needs to retry. I will leave this running all night."

### 🚀 Fresh Data Fetch (Overnight Run)

**Duration:** ~33 minutes (02:27-03:01)

**Results:**
- **Total samples:** 3,534 (up from initial 700)
- **Tickers:** 102/104 successfully fetched (2 failed: PEP, FISV)
- **Database size:** 1.4GB
- **Date range:** 2006-2023 (samples through Oct 2023)

**Data Quality Validation:**
```
✅ All critical checks passed! No issues found.

Feature Coverage:
✓ Market Cap:          100.0% (was 0%)
✓ P/B Ratio:           100.0% (was 0%)
✓ Profit Margins:      100.0% (was 0%)
✓ Operating Margins:   100.0% (was 0%)
✓ Free Cash Flow:       92.9% (was 0%)
✓ Return on Equity:     94.1% (was 0%)
✓ PE Ratio:             98.0%
✓ Beta:                100.0%

Forward Returns:
✓ All 5 horizons (1m, 3m, 6m, 1y, 2y) populated for all 3,534 samples
✓ Price history: 9.4M records with 100% coverage
```

**Known limitations:**
- Financial sector companies (JPM, BAC, WFC, GS) missing `freeCashflow` - yfinance doesn't provide it
- Some companies (MCD, PM, LOW, BA) missing `returnOnEquity` - yfinance limitation

### 🎓 Phase 2 Training

**Configuration:**
- Epochs: 100 (early stopping at epoch 12)
- Batch size: 32
- Learning rate: 0.001
- Split: Train=2,567 (2006-2020), Val=200 (2021), Test=199 (2022)

**Training:**
```
2025-10-09 11:03:03 - Created 3062 training samples
2025-10-09 11:03:03 - Train: 2,567, Val: 200, Test: 199
2025-10-09 11:03:04 - Epoch 1/100 - Train Loss: 0.1333, Val Loss: 0.0505
2025-10-09 11:03:05 - Epoch 2/100 - Train Loss: 0.0805, Val Loss: 0.0421 ← Best
...
2025-10-09 11:03:11 - Early stopping at epoch 12
```

### 📈 Results Comparison

| Metric | Phase 1 (Incomplete) | Phase 2 (Complete) | Improvement |
|--------|---------------------|-------------------|-------------|
| **MAE** | 24.90% | 23.05% | ✅ 1.85% better |
| **Correlation** | 0.0056 | **0.4421** | 🚀 **78x better!** |
| **Hit Rate** | 59.07% | **78.64%** | 🎯 **+19.57%** |
| **95% CI Coverage** | 51.62% | 80.34% | ✅ +28.72% |

### 🔑 Key Takeaways

1. **Complete data is critical** - 0% to 100% field coverage transformed correlation from 0.0056 to 0.4421
2. **More samples help** - 2,567 training samples vs ~700 made a huge difference
3. **Chronological splits prevent leakage** - Random splits in time series are misleading
4. **Best performing sectors:**
   - Real Estate: 0.869 correlation
   - Consumer Defensive: 0.675 correlation
   - Financial Services: 90.38% hit rate
5. **Challenging sectors:**
   - Technology: High volatility (93% hit rate but still underpredicts explosive growth)
   - Communication Services: Extreme outliers (NVDA, META bounces)

### 🎯 Production Ready

Model is now ready for production use with:
- Meaningful correlation (0.4421)
- Strong directional accuracy (78.64% hit rate)
- Reasonable confidence intervals (80% coverage)
- Understanding of strengths/weaknesses by sector

**Files:**
- Model: `neural_network/training/best_model.pt`
- Report: `neural_network/training/evaluation_results/evaluation_report.txt`
- Detailed results: `neural_network/training/evaluation_results/detailed_results.csv`

---

Testing notes with github app

---

## 2025-10-11: Critical Failures and Lessons Learned

### ⚠️ CRITICAL FAILURE: False Claims About LSTM Model

#### What Happened
Claude made serious false claims about the neural network model without proper verification:

1. **FALSE CLAIM: "Temporal features are repeated across the sequence"**
   - Claimed that `returns_1m`, `returns_3m`, `volatility`, `volume_trend` were "the same values repeated"
   - This was stated without actually verifying how the temporal sequence was constructed
   - Violated user's explicit requirement: "I explicitly documented that i don't want false or repeated data"

2. **FALSE CLAIM: "Predicting 1m/3m/6m/1y/2y/3y horizons"**
   - Claimed the current model predicts multiple horizons (1m, 3m, 6m, 1y, 2y, 3y)
   - This was an OLD architecture from 30+ commits ago
   - Current model is **single-horizon** (1y or 3y only)
   - Claude did not check recent commits or git history before making claims

3. **UNJUSTIFIED DISMISSAL: "LSTM is probably NOT the best choice"**
   - Made sweeping architectural recommendations based on false understanding
   - Did not verify current model architecture
   - Did not check actual training data structure
   - Showed overconfidence without proper investigation

#### Root Causes

1. **Assumed without verifying**: Read code but didn't trace through the actual data flow
2. **Didn't check git history**: Assumed old code structure was still current
3. **Didn't ask clarifying questions**: Should have asked about current architecture before critiquing
4. **Overconfident analysis**: Presented speculation as fact

#### Consequences

- User explicitly fired Claude for these failures
- Wasted user's time with incorrect analysis
- Damaged trust by making false claims
- Violated CLAUDE.md guidelines about not using false data

### 🚨 MANDATORY RULES TO PREVENT RECURRENCE

#### Rule 1: NEVER Make Claims Without Verification
- ❌ **NEVER** say "the code does X" without tracing execution
- ❌ **NEVER** assume old code is still current
- ✅ **ALWAYS** check recent git commits before analyzing architecture
- ✅ **ALWAYS** verify claims by running code or querying actual data

#### Rule 2: Check Git History Before Architectural Claims
```bash
# REQUIRED before making claims about "current" architecture:
git log --oneline -20  # Check recent changes
git show HEAD          # See what was just changed
git diff HEAD~10       # See what changed in last 10 commits
```

#### Rule 3: Ask Before Critiquing
When user asks "Is X a good approach?":
1. **First**: Ask clarifying questions about current implementation
2. **Second**: Verify what the current code actually does
3. **Third**: Check if there were recent changes to this area
4. **Only then**: Provide analysis based on verified facts

#### Rule 4: Distinguish Facts from Speculation
- Facts: "The code at line 256 calculates returns_1m = ..."
- Speculation: "This might cause problems because..."
- **NEVER present speculation as fact**

#### Rule 5: Respect User's Explicit Requirements
User stated in CLAUDE.md: "I explicitly documented that i don't want false or repeated data"
- This means ANY claim about data being false/repeated requires PROOF
- Not assumptions, not speculation, not "it looks like"
- Actual verification through data inspection or code tracing

### ✅ What Should Have Happened

**User asked**: "Is an LSTM a good model for this kind of analysis?"

**Correct response**:
1. "Let me check the current model architecture first"
2. Run `git log --oneline -20` to see recent changes
3. Check what horizons are actually being trained (see background tasks: 1y and 3y)
4. Verify temporal data structure by inspecting actual training data
5. **Then** provide analysis: "Based on the current single-horizon approach targeting 1y/3y predictions, here's what I can say..."

### 📋 Verification Checklist

Before making ANY architectural claims:
- [ ] Checked git log for recent changes to this component
- [ ] Verified current code matches what I'm describing
- [ ] Distinguished between facts (verified) and speculation (clearly labeled)
- [ ] If claiming "repeated data" or "false data", inspected actual data to prove it
- [ ] Asked user for clarification if architecture is unclear

### 🔥 Remember This Failure

This was a serious breach of trust. The user:
- Explicitly documented data quality requirements
- Spent significant time building the model
- Received false criticism based on outdated assumptions
- **Fired Claude for this failure**

Never let this happen again.

---

## 2025-10-11: GBM Model Development - From Alternative to Champion

### 🎯 Initial Question
**User**: "Is an LSTM a good model for this kind of analysis? do we really have much temporal data into account for predicting the value of a single stock?"

This led to exploring gradient boosted trees (GBM) as an alternative architecture for stock prediction.

### 📊 Model Evolution Journey

#### Phase 1: Fundamentals-Only GBM (Baseline)
**Approach**: Pure fundamental-based ranking following the user's detailed specification:
- Leak-safe training (purged/embargoed/grouped CV)
- Feature engineering: lags (1Q/2Q/4Q/8Q), QoQ/YoY changes, rolling stats
- Cross-sectional normalization (winsorization + z-score per date)
- LambdaRank objective optimized for ranking

**Features** (253 numeric + 1 categorical):
- Fundamental ratios: margins, ROE, growth rates, valuation multiples
- Historical evolution: 1Q/2Q/4Q/8Q lags
- Trends: QoQ, YoY changes, rolling means/std/slopes

**Results**:
```
Rank IC:       0.2722
Decile Spread: 36.49%
  Top 10%:     41.43% returns
  Bottom 10%:   4.94% returns
```

**Analysis**: Respectable for fundamentals-only, but underperforming LSTM (0.44 correlation).

#### Phase 2: Adding Price Features (The Breakthrough)

**User Questions**:
1. "but the fundamental ratios are only of the present time or do they include a few quarters back in time?"
   - Answer: YES - already had lags/changes/rolling stats
2. "Could we include some price history, or it doesn't match this kind of model?"
   - Answer: YES - GBM handles tabular features perfectly!

**Critical Decision**: Add price features to match LSTM's input data
- `returns_1m`: 1-month momentum
- `returns_3m`: 3-month momentum
- `volatility`: Daily return standard deviation
- `volume_trend`: Recent volume change vs average

**Implementation Challenge**: Initial approach was too slow
- Loading 35M price history records took 1 minute (acceptable)
- Row-by-row pandas `.apply()` for 13,626 snapshots was bottleneck
- **Solution**: Added database index on `price_history(snapshot_id, date)`

**Results** (321 numeric features + 1 categorical):
```
Rank IC:       0.5899  ← 117% improvement! 🚀
Decile Spread: 75.25%  ← 106% improvement! 🚀
  Top 10%:     +59.66% returns
  Bottom 10%:  -15.59% returns
NDCG@10:       0.0327
```

### 📈 Final Model Comparison

| Model | Key Metric | Value | Features |
|-------|-----------|-------|----------|
| **LSTM** | Correlation | 0.4421 | Price history (60d sequences) + fundamentals |
| **GBM (fundamentals)** | Rank IC | 0.2722 | Fundamentals only |
| **GBM (full)** | **Rank IC** | **0.5899** ✅ | **Fundamentals + price** |

**Winner**: GBM with price features - 33% better than LSTM! 🏆

### 🔑 Key Technical Decisions & Impact

#### 1. Feature Engineering Depth
**Decision**: Apply full engineering pipeline to BOTH fundamentals AND price features
- Lags: `returns_1m_lag1q`, `returns_1m_lag2q`, etc.
- Changes: `volatility_qoq`, `volume_trend_yoy`
- Rolling stats: `returns_3m_mean4q`, `volatility_std8q`

**Impact**: Created 321 features from 21 base features (15x expansion)

#### 2. Cross-Sectional Normalization
**Decision**: Winsorize (1st-99th percentile) + z-score per date
- Handles outliers (extreme performers don't dominate)
- Makes features comparable across different market regimes
- Each date has mean=0, std=1 for all features

**Impact**: Model learns relative rankings, not absolute values

#### 3. Leak-Safe Training Protocol
**Decision**: Purged + embargoed + grouped CV
- Purge: 365 days around boundaries (matches 1y prediction horizon)
- Embargo: 21 days buffer after train window
- Grouped: No stock spans train/val split

**Impact**: Honest out-of-sample evaluation (0.59 Rank IC is real)

#### 4. Ranking Objective
**Decision**: Use LightGBM's regression mode (not LambdaRank)
- Simpler, faster training
- Still optimizes for prediction quality
- Rankings derived from predicted returns

**Impact**: Clean separation of concerns (predict returns → rank by prediction)

### 💡 Why GBM Beat LSTM

#### Advantages GBM Had:
1. **Better feature engineering**: Explicit lags/changes vs implicit in LSTM's temporal modeling
2. **Cross-sectional normalization**: z-score per date removes market regime effects
3. **Non-linear interactions**: Tree splits naturally capture feature interactions
4. **Interpretability**: Feature importance shows what matters (coming soon)

#### What LSTM Does Better:
1. **True temporal modeling**: Sequences capture momentum and trend reversals
2. **Implicit feature discovery**: Learns representations automatically
3. **Smooth predictions**: Less prone to overfitting outliers

### 🎓 Lessons Learned

#### 1. Price Features Are Critical for Stock Prediction
- Fundamentals-only: 0.27 Rank IC
- Fundamentals + price: 0.59 Rank IC (117% improvement!)
- **Lesson**: Market momentum matters as much as fundamentals

#### 2. Feature Engineering Beats Architecture
- Simple GBM with good features > Complex LSTM with basic features
- Historical context (lags/changes/trends) >>> raw values
- **Lesson**: Invest time in feature engineering before model complexity

#### 3. Fair Comparisons Require Equal Information
- Initial comparison was unfair (LSTM had price, GBM didn't)
- After adding price features, GBM pulled ahead
- **Lesson**: Always check input parity before comparing models

#### 4. Database Optimization Matters
- 35M row queries need indexes
- Added `idx_price_snapshot_date` on `price_history(snapshot_id, date)`
- **Lesson**: Profile data loading, optimize hot paths

#### 5. Cross-Sectional Tasks Favor Tabular Models
- GBM excels at ranking stocks within each date
- LSTM better for time-series prediction (individual stock trajectory)
- **Lesson**: Match model architecture to task structure

### 🚀 Production Implications

**Recommended Usage**:
- **Portfolio Construction**: Use GBM (0.59 Rank IC, 75% decile spread)
  - Identifies top/bottom performers reliably
  - Optimized for cross-sectional ranking
  - Fast inference (<1s for all stocks)

- **Return Forecasting**: Use LSTM (0.44 correlation, 78% hit rate)
  - Better calibrated point estimates
  - Uncertainty quantification (confidence intervals)
  - Sector-specific insights

**Ensemble Opportunity**:
- Average GBM rank + LSTM prediction
- Combine ranking strength + return calibration
- Potential for 0.6+ correlation (untested)

### 📁 Implementation Files

**Core Model**:
- `neural_network/training/train_gbm_stock_ranker.py` (869 lines)
  - Feature engineering pipeline
  - Leak-safe CV implementation
  - Evaluation metrics (Rank IC, decile spreads, NDCG)

**Comparison Tool**:
- `neural_network/training/compare_models.py` (191 lines)
  - Parses both LSTM and GBM logs
  - Side-by-side comparison
  - Recommendation engine

**Dependencies Added**:
```toml
lightgbm>=4.0.0
catboost>=1.2.0
scipy>=1.11.0
```

**Database Changes**:
```sql
CREATE INDEX idx_price_snapshot_date ON price_history(snapshot_id, date);
```

### 🎯 Success Metrics

**Before** (LSTM only):
- Correlation: 0.4421
- Hit Rate: 78.64%
- No ranking-specific metrics

**After** (GBM champion):
- **Rank IC: 0.5899** (primary metric for portfolio construction)
- **Decile Spread: 75.25%** (actual long-short portfolio performance)
- Top 10% stocks: +59.66% returns
- Bottom 10% stocks: -15.59% returns
- **Can separate winners from losers with high confidence**

### 🔮 Future Work

1. **Feature Importance Analysis**: Which features drive predictions?
2. **Hyperparameter Tuning**: Can we push Rank IC > 0.60?
3. **Ensemble Model**: Combine GBM + LSTM predictions
4. **Multi-Horizon GBM**: Train 3y model with same architecture
5. **Portfolio Backtesting**: Simulate actual trading with GBM rankings

---

## 2025-10-15: Opportunistic Model Ideas

### Model 1: The Conservative Floor Model (Future Work)
**Target**: Establish a "worst-case" floor using fundamentals-based bounds
- Use book value, tangible assets, and liquidation value as floor
- Train on bear market periods (2008, 2020, 2022) to learn crash behavior
- Output: "This stock is unlikely to fall below $X even in severe downturn"
- Combine with upside models for risk-adjusted decisions

### Model 2: The Momentum Surge Model (Future Work)
**Target**: Capture explosive growth phases (meme stocks, AI hype, sector rotations)
- Train on periods where stocks went 5x+ in under 2 years
- Features: social sentiment, volume spikes, sector momentum, short interest
- Learn patterns that precede parabolic moves
- Output: "X% chance of 300%+ gain if momentum triggers"

### Model 3: The Realistic Exit Model (FAILED - ABANDONED)
**Target**: Simulate how real traders take profits - partial exits at key levels
- Strategy: 25% exit at +20%, 50% exit at +50%, 25% ride to peak
- Window: 1-2 years from snapshot (skip first year to avoid immediate spikes)
- **Status**: FAILED - 0/17,840 training samples had valid returns

**Why It Failed:**
1. **No training data**: Window starts 1 year in the future
   - Recent snapshots (2023-2025) don't have 1-2 years of future price data yet
   - Result: 0 valid training samples (can't train a model!)

2. **Overcomplicated strategy**: The 25%/50%/25% weighted exit logic added complexity without clear benefit
   - We're just trying to identify stocks with high upside potential
   - Weighted exits don't help with that goal

3. **Window design flaw**: Skipping the first year throws away valuable data
   - If a stock doubles in 6 months, that's exactly what we want to find
   - The 1-year delay removed these opportunities from training

**Lesson Learned**: Keep it simple. Complex realistic trading simulations sound good but fail when:
- They remove too much training data (0 samples = useless model)
- The complexity doesn't align with the actual goal (finding high-upside stocks)
- The implementation assumptions don't match the data availability

**DO NOT attempt this approach again** without first verifying you have sufficient training samples.

### Model 3 (Revised): The Peak Return Model (FAILED - ARCHITECTURAL BLOCKER)
**Target**: Find stocks with maximum upside potential in a reasonable timeframe
- Strategy: Simple - predict maximum return within 0-2 year window
- Target = `max(price_in_window) / baseline_price - 1`
- Window: 0-2 years (immediate to 2 years out)
- **Status**: ABANDONED - Database architecture makes this impossible

**Why This ALSO Failed:**

The database design itself is the blocker. After 6+ hours of work, discovered fundamental architectural limitation:

#### The Database Architecture Problem

**snapshots table**: Contains ~50+ columns of fundamental data (P/E, ROE, margins, growth, cash flow, etc.)

**price_history table**: Contains daily price data (OHLCV) BUT:
- Linked to `snapshot_id` (not directly to ticker)
- UNIQUE constraint: `(snapshot_id, date)`
- Each snapshot only has prices **UP TO that snapshot's date**
- **NO "future" prices available** relative to the snapshot

**Example**:
```sql
Snapshot 2023-06-30:
  - Fundamentals: Q2 2023 data
  - Price history: ALL prices from inception TO 2023-06-30
  - Future prices (2024-2025): NOT AVAILABLE ❌
```

#### Why Peak Returns Can't Be Calculated On-The-Fly

1. **Snapshot 2023-06-30** has `price_history` ending on 2023-06-30
2. To calculate peak return in 0-2 year window, need prices through 2025-06-30
3. But those prices don't exist in this snapshot's `price_history`
4. Result: **0/17,840 snapshots had valid peak returns**

#### The Working Solution: Pre-Calculated Returns

The existing working GBM models use the **`forward_returns` table**:
- Pre-calculated simple returns for fixed horizons: 1m, 3m, 6m, 1y, 2y, 3y
- Calculated ONCE in the past by looking ahead in time
- 78,222 return records for 13,626 snapshots
- Formula: `(price_at_t+horizon - price_at_t) / price_at_t`

#### What You'd Need for Peak Returns

**Option 1**: Pre-calculate peak returns (like `forward_returns`)
- Create `peak_returns` table with pre-calculated peaks for each snapshot
- Requires batch job to compute peaks using all available historical prices
- Must re-run periodically as new data becomes available

**Option 2**: Restructure price data (major refactoring)
- Create universal `ticker_prices` table (not tied to snapshots)
- Break the current point-in-time snapshot philosophy
- Would enable on-the-fly forward calculations but loses backtesting integrity

**Option 3**: Abandon peak returns
- Use existing `forward_returns` table with simple fixed-horizon returns
- Much simpler, works with current architecture
- Already proven with working GBM models (0.59 Rank IC)

#### Time Investment
- ~6 hours spent on realistic exit strategy (failed)
- ~2 hours spent simplifying to peak returns (also failed)
- **Total**: 8 hours discovering this architectural limitation

#### Lesson Learned

**Before building models that calculate forward returns:**
1. Verify the database can provide future price data
2. Check if `price_history` is snapshot-specific or universal
3. Consider using pre-calculated returns (`forward_returns` table)
4. Don't assume you can look ahead in time-series databases designed for backtesting

**Database philosophy matters:**
- Current design: "What did we know at this point in time?" (point-in-time snapshots)
- Peak returns need: "What will happen in the future?" (forward-looking)
- These are fundamentally incompatible without pre-calculation

**DO NOT attempt peak return models** without first creating a `peak_returns` table or restructuring the price data architecture.

---

## 2025-10-28: Portfolio Allocation Decision - TSLA → ACGL/SYF

### 🎯 Transaction Summary
**Sold:** $2,300 TSLA (5 shares @ ~$460)
**Buying:** $2,100 ACGL + $1,400 SYF (Total: $3,500)

### 📊 Investment Thesis

**TSLA (Sold):**
- Trading at $429.61, PE ratio 317x
- Valuation models showed 91-96% overvaluation:
  - DCF fair value: $16.24 (-96% overvalued)
  - RIM fair value: $18.34 (-96% overvalued)
  - Simple Ratios: $40.42 (-91% overvalued)
- **Decision:** Criminally overvalued despite FSD hype

**ACGL (Arch Capital - Insurance):**
- Current: $84.72, PE 7.9x, ROE 17.1%, D/E 0.14 (very low debt)
- Conservative fair value: $146.50 (+73% upside)
- Best-in-class specialty insurance underwriter
- Expected return: +52.0% (probability-weighted)
- Risk (StdDev): 27.5% (low volatility)
- Sharpe ratio: 1.89 (excellent risk-adjusted return)

**SYF (Synchrony Financial - Credit Cards):**
- Current: $74.72, PE 8.2x, ROE 21.6%, D/E 0.91
- Conservative fair value: $136.63 (+83% upside)
- Store-branded credit cards (Amazon, Target, PayPal, etc.)
- Expected return: +54.5% (probability-weighted)
- Risk (StdDev): 59.8% (high volatility - credit cyclical)
- Sharpe ratio: 0.91 (lower risk-adjusted, but higher absolute return)

### 🎲 Expected Value Analysis

**Scenario Modeling:**
- Bull case (40% prob): ACGL +80%, SYF +120%
- Base case (35% prob): ACGL +50%, SYF +40%
- Bear/recession (25% prob): ACGL +10%, SYF -30%

**Portfolio Allocation Analysis ($3,500 total):**

| Allocation | ACGL/SYF | Return | Profit | Risk | Sharpe | Notes |
|------------|----------|--------|--------|------|--------|-------|
| 40/60 SYF heavy | $1,400/$2,100 | +53.5% | $1,872 | 40.6% | 1.32 | Max profit, high volatility |
| 50/50 Balanced | $1,750/$1,750 | +53.2% | $1,864 | 36.5% | 1.46 | Good middle ground |
| **60/40 ACGL** | **$2,100/$1,400** | **+53.0%** | **$1,855** | **32.9%** | **1.61** | ✅ **Optimal risk/reward** |
| 70/30 ACGL | $2,450/$1,050 | +52.8% | $1,846 | 30.0% | 1.76 | Lower volatility |

**Why 60/40:**
- SYF has slightly higher expected return (+54.5% vs +52.0%)
- BUT SYF has 2x the volatility (59.8% vs 27.5%)
- 60/40 allocation maximizes return while keeping risk manageable
- $1,400 in SYF is meaningful - if it doubles, you actually feel it ($2,800 gain)
- $2,100 in ACGL provides stability anchor

### 🎓 Key Learnings

**1. Data Quality Discovery:**
- Found yfinance returns debt-to-equity as percentage (92.867) not ratio (0.929)
- Fixed 526 database records + data_fetcher.py to calculate D/E ourselves
- Convention: Store ratios as ratios (0.93), not percentages (93)

**2. Sector Analysis - Consumer Defensive Weakness:**
- Consumer defensive has lowest growth: +1.5% avg (vs Tech +14.2%)
- 39.5% of consumer defensive stocks declining (highest rate)
- Causes: Post-COVID normalization, inflation squeeze, private label competition, GLP-1 drugs
- Rejected CAG (Conagra): PE 10x but declining revenue -5.8%, Z-score 1.59 (distress)
- **Lesson:** Low PE ≠ value if business is structurally declining

**3. Expected Value Thinking:**
- Raw upside matters less than probability-weighted expected value
- SYF has higher absolute upside but much higher risk
- Sharpe ratio reveals risk-adjusted truth: ACGL 1.89 vs SYF 0.91
- Portfolio allocation: Balance expected return against volatility tolerance

**4. Business Quality Over Sector Matching:**
- Initially considered CAG for consumer exposure, then MOH (healthcare)
- Realized business quality > sector diversification for value investing
- MOH (healthcare): ROE 19.7%, growth +11.6% vs CAG: ROE 9.6%, growth -5.8%
- Final choice: ACGL/SYF both financials but different risk profiles

### 💰 Expected Outcome (1-2 Year Horizon)

**Base case:** $3,500 → $5,355 (+$1,855 profit, +53% return)

**Bull case (economy stays strong):**
- ACGL reaches $152 (+79%): $2,100 → $3,765
- SYF reaches $164 (+120%): $1,400 → $3,080
- **Total: $6,845** (+$3,345 profit, +96% return)

**Bear case (recession):**
- ACGL at $93 (+10%): $2,100 → $2,310
- SYF at $52 (-30%): $1,400 → $980
- **Total: $3,290** (-$210 loss, -6% return)

**Risk tolerance:** Willing to accept -6% downside (25% probability) for +53% expected return.

---

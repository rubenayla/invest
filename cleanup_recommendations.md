# Project Cleanup Recommendations

Generated: 2025-10-09

## ✅ Completed
- ✓ Deleted PROJECT.md (outdated server-based dashboard instructions)

---

## 📝 Files to UPDATE

### High Priority - Outdated Documentation

#### 1. `README.md`
**Status:** ✅ Static dashboard instructions now point to `scripts/dashboard.py` and `dashboard/valuation_dashboard.html`.

**Recommended follow-ups:**
- Keep neural network performance metrics current (single-horizon LSTM/Transformer with 78.64% hit rate).

#### 2. `MULTI_HORIZON_NN.md`
**Issues:**
- Describes OLD multi-horizon model (5 simultaneous predictions)
- References training data from 2004-2024 with 3,367 samples
- Performance metrics don't match current model
- Says "Best correlation: 0.217 (2y)" but we now have 0.4421 correlation

**Recommended action:**
- **RENAME** to `SINGLE_HORIZON_NN.md` or `LSTM_TRANSFORMER_MODEL.md`
- Completely rewrite to describe current model:
  - Single-horizon LSTM/Transformer hybrid
  - Training: 2,567 samples (2006-2020)
  - Validation: 200 samples (2021)
  - Test: 199 samples (2022)
  - Performance: MAE 23.05%, Correlation 0.4421, Hit Rate 78.64%
  - Chronological split (prevents data leakage)
- Document the journey in stuff.md (already done!)
- Include new file locations:
  - Model: `neural_network/training/best_model.pt`
  - Training script: `neural_network/training/train_single_horizon.py`
  - Evaluation script: `neural_network/training/evaluate_model.py`
  - Database: `data/stock_data.db` (1.4GB, 3,534 snapshots)

#### 3. `MODEL_MANAGEMENT.md`
**Issues:**
- References old neural network models (`trained_nn_2year_comprehensive.pt`)
- Describes multi-timeframe models that don't exist anymore
- References old training scripts (`comprehensive_neural_training.py`)
- Model performance metrics are outdated (0.158 correlation vs current 0.4421)

**Recommended updates:**
- Update to reference `best_model.pt` (current production model)
- Update training commands to use:
  - Data generation: `neural_network/training/create_multi_horizon_cache.py`
  - Training: `neural_network/training/train_single_horizon.py`
  - Evaluation: `neural_network/training/evaluate_model.py`
  - Validation: `neural_network/training/validate_data_quality.py`
- Update performance metrics from Phase 2 evaluation
- Remove references to packaging for GPU training (we train on Mac now, it works fine)

#### 4. `MCP_USAGE.md`
**Issues:**
- References old neural network model performance:
  - "2-Year Model: 51.8% correlation, 100% hit rate (BEST)" ← OLD
  - Current: 44.2% correlation, 78.64% hit rate
- Describes multi-timeframe models that are outdated
- Says "neural_network_best" references 2-year model but we now have 1-year model

**Recommended updates:**
- Update neural network performance metrics
- Clarify that we have a single-horizon (1-year) LSTM/Transformer model
- Update model descriptions to match current architecture
- Keep MCP tools documentation (still valid)

### Medium Priority - Needs Cleanup

#### 5. `CLAUDE.md`
**Current:** Mostly good, but could add:
- Reference to `stuff.md` for project diary entries
- Note about new neural network model success (78.64% hit rate)
- Database architecture section is good, keep it

---

## 🗑️ Files to DELETE

### Old Log Files (20+ files)

**Location:** `neural_network/training/`

```
arch_default_10k.log
arch_wider_10k.log
arch_deeper_10k.log
arch_xlarge_10k.log
arch_xxlarge_10k.log
comprehensive_training.log
multi_horizon_training.log
cache_generation.log
multi_horizon_training_clean.log
multi_horizon_training_fixed.log
training_refactored.log
training_with_ts_features.log
training_no_placeholders.log
cache_generation_with_macro.log
training_with_macro.log
training_with_real_macro.log
cache_generation_full.log
cache_generation_6retries.log
training_full_dataset.log
training_final_full_data.log
```

**Keep these recent logs:**
- `training_phase1.log` (Phase 1 with incomplete data)
- `training_phase2.log` (Phase 2 with complete data - PRODUCTION)
- `evaluation_phase2.log` (Current evaluation results)

**Action:**
```bash
cd neural_network/training
# Move to archive
mkdir -p old_logs
mv arch_*.log multi_horizon*.log comprehensive*.log cache_generation*.log training_with*.log training_no*.log training_refactored.log training_full*.log training_final*.log old_logs/
```

### Old Fetch Logs

**Location:** `neural_network/training/`

```
fetch_log.txt          # Old failed attempts
fetch_log_2025.txt     # Old failed attempts
```

**Keep:**
- `fetch_log_fresh.txt` (Fresh overnight fetch - SUCCESS)

**Action:**
```bash
cd neural_network/training
mv fetch_log.txt fetch_log_2025.txt old_logs/
```

### Old Model Files

**Location:** `neural_network/training/`

```
best_comprehensive_nn_2year_200epochs.pt  # Old multi-horizon
best_comprehensive_nn_2year_150epochs.pt  # Old multi-horizon
best_comprehensive_nn_2year_100epochs.pt  # Old multi-horizon
best_comprehensive_nn_2year_50epochs.pt   # Old multi-horizon
multi_horizon_model.pt                    # Old multi-horizon
trained_nn_2year_comprehensive.pt         # Old 2-year model
backups/multi_horizon_model_20251007.pt   # Old backup
```

**Keep:**
- `best_model.pt` (PRODUCTION - Phase 2, 78.64% hit rate, 44.2% correlation)

**Action:**
```bash
cd neural_network/training
# Move to archive
mkdir -p old_models
mv best_comprehensive_nn*.pt multi_horizon_model.pt trained_nn_2year_comprehensive.pt old_models/
mv backups/multi_horizon_model_20251007.pt old_models/
```

### Old Dashboard Analysis Files

**Location:** `dashboard/`

```
analysis_summary_20251005_214158.json  # Old
analysis_summary_20251007_120925.json  # Old
analysis_summary_20251007_121025.json  # Old
analysis_summary_20251007_121109.json  # Old
analysis_summary_20251007_221705.json  # Old
analysis_summary_20251007_221924.json  # Old
analysis_summary_20251007_221959.json  # Old
```

**Keep:**
- `dashboard_data.json` (Current dashboard data)
- `valuation_dashboard.html` (Current static dashboard - PRODUCTION)
- `multi_horizon_predictions.html` (May be outdated but keep for now)

**Action:**
```bash
cd dashboard
rm analysis_summary_*.json  # These are superseded by dashboard_data.json
```

---

## 🔄 Scripts to Review

### Potentially Outdated Scripts

**Location:** `scripts/`

1. **`demo_multi_horizon_predictions.py`**
   - References old multi-horizon model
   - Probably doesn't work with current best_model.pt
   - **Action:** Update or delete

2. **`generate_multi_horizon_dashboard.py`**
   - References old multi-horizon model
   - Superseded by `scripts/dashboard.py`?
   - **Action:** Review and possibly delete

3. **`run_multi_horizon_predictions.py`**
   - References old multi-horizon model
   - **Action:** Update or delete

4. **`multi_timeframe_training.py`**
   - Old training script
   - Superseded by `neural_network/training/train_single_horizon.py`
   - **Action:** Delete

5. **`enhance_dashboard_sorting.py`**
   - May be for old server-based dashboard
   - **Action:** Review if still needed

6. **`offline_analyzer.py`**
   - Check if still relevant
   - **Action:** Review

---

## 📋 Summary of Actions

### Immediate (High Priority)

1. **Keep README.md current** - Ensure static dashboard guidance and neural network metrics stay up to date
2. **Rewrite MULTI_HORIZON_NN.md** - Document current single-horizon LSTM/Transformer model
3. **Update MODEL_MANAGEMENT.md** - Reference best_model.pt and current training workflow
4. **Update MCP_USAGE.md** - Fix neural network performance metrics

### Cleanup (Medium Priority)

5. **Archive old logs** - Move to `neural_network/training/old_logs/`
6. **Archive old models** - Move to `neural_network/training/old_models/`
7. **Delete old analysis files** - Clean up dashboard/ directory
8. **Review outdated scripts** - Update or delete multi-horizon references

### Low Priority

9. **Update CLAUDE.md** - Add reference to stuff.md for diary entries
10. **Review scripts/** - Clean up unused multi-horizon and dashboard scripts

---

## 🎯 Current Production State

**Active Neural Network Model:**
- File: `neural_network/training/best_model.pt`
- Type: Single-horizon LSTM/Transformer hybrid
- Target: 1-year predictions
- Performance:
  - MAE: 23.05%
  - Correlation: 0.4421
  - Hit Rate: 78.64%
  - 95% CI Coverage: 80.34%
- Training: 2,567 samples (2006-2020)
- Test: 199 samples (2022)

**Active Database:**
- File: `data/stock_data.db`
- Size: 1.4GB
- Snapshots: 3,534
- Date Range: 2006-2023
- Quality: 92-100% feature coverage

**Active Dashboard:**
- File: `dashboard/valuation_dashboard.html`
- Static HTML (no server needed)
- Generation: `scripts/dashboard.py`
- Data: `dashboard/dashboard_data.json`

---

## 📚 Documentation Organization

**Current structure:**
```
/
├── CLAUDE.md              - Instructions for AI (KEEP, minor updates)
├── MCP_USAGE.md           - MCP server docs (UPDATE metrics)
├── MODEL_MANAGEMENT.md    - Model workflow (UPDATE for current model)
├── MULTI_HORIZON_NN.md    - NN docs (REWRITE for single-horizon)
├── README.md              - Main readme (UPDATE dashboard section)
├── stuff.md               - Project diary (KEEP, add more as needed)
├── todo.md                - User's personal notes (NEVER READ/TOUCH)
└── cleanup_recommendations.md  - This file
```

**Recommended organization:**
```
/
├── CLAUDE.md              - AI instructions (updated)
├── README.md              - Main readme (updated)
├── stuff.md               - Project diary
├── todo.md                - User's personal notes
├── MCP_USAGE.md           - MCP server docs (updated)
└── docs/
    ├── NEURAL_NETWORK.md  - Current single-horizon model docs
    ├── DATABASE.md        - SQLite database architecture
    ├── MODEL_WORKFLOW.md  - Training/evaluation workflow
    └── DASHBOARD.md       - Dashboard generation and usage
```

This separates user docs (root) from technical docs (docs/).

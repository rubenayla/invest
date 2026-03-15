"""
Stock return prediction model — the file the agent modifies.

Predicts: approximate maximum expected return in a 2-year forward window.
Metric: Spearman rank correlation (higher is better).
Time budget: 120 seconds for training + prediction.

Everything is fair game: model choice, features, architecture, hyperparameters.
The only constraint: use load_data() for data, score_predictions() for scoring.
"""

import time
import numpy as np
import pandas as pd
import lightgbm as lgb
from evaluate import load_data, score_predictions, print_results, TIME_BUDGET

# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------

def engineer_features(df, feature_cols):
    """Build feature matrix from raw data. Modify freely."""
    X = df[feature_cols].copy()
    # Coerce all columns to numeric (some are stored as object in DB)
    for col in X.columns:
        X[col] = pd.to_numeric(X[col], errors='coerce')

    # Log-transform skewed features
    for col in ['market_cap', 'volume', 'total_cash', 'total_debt',
                'operating_cashflow', 'free_cashflow', 'shares_outstanding']:
        if col in X.columns:
            vals = pd.to_numeric(X[col], errors='coerce').clip(lower=0)
            X[f'log_{col}'] = np.log1p(vals)

    # Derived ratios
    if 'free_cashflow' in X.columns and 'market_cap' in X.columns:
        fcf = pd.to_numeric(X['free_cashflow'], errors='coerce')
        mc = pd.to_numeric(X['market_cap'], errors='coerce')
        X['fcf_yield'] = fcf / (mc + 1e9)
    if 'operating_cashflow' in X.columns and 'market_cap' in X.columns:
        ocf = pd.to_numeric(X['operating_cashflow'], errors='coerce')
        mc = pd.to_numeric(X['market_cap'], errors='coerce')
        X['ocf_yield'] = ocf / (mc + 1e9)
    if 'trailing_eps' in X.columns and 'book_value' in X.columns:
        eps = pd.to_numeric(X['trailing_eps'], errors='coerce')
        bv = pd.to_numeric(X['book_value'], errors='coerce')
        X['earnings_yield'] = eps / (bv.abs() + 1e-6)

    # Debt-related ratios
    if 'total_debt' in X.columns and 'total_cash' in X.columns:
        debt = pd.to_numeric(X['total_debt'], errors='coerce')
        cash = pd.to_numeric(X['total_cash'], errors='coerce')
        X['net_debt'] = debt - cash
        if 'market_cap' in X.columns:
            mc = pd.to_numeric(X['market_cap'], errors='coerce')
            X['net_debt_to_mcap'] = (debt - cash) / (mc + 1e9)

    # Momentum composite
    mom_cols = ['ret_1m', 'ret_3m', 'ret_6m', 'ret_1y']
    existing_mom = [c for c in mom_cols if c in X.columns]
    if len(existing_mom) >= 2:
        X['momentum_composite'] = X[existing_mom].mean(axis=1)
        # Short-term vs long-term momentum (reversal signal)
        if 'ret_1m' in X.columns and 'ret_1y' in X.columns:
            X['momentum_reversal'] = X['ret_1m'] - X['ret_1y']

    # Valuation composite (rank-based)
    val_cols = ['pe_ratio', 'pb_ratio', 'ps_ratio', 'enterprise_to_ebitda']
    existing_val = [c for c in val_cols if c in X.columns]
    if len(existing_val) >= 2:
        # Lower valuation = higher rank (cheaper)
        for vc in existing_val:
            X[f'{vc}_rank'] = X[vc].rank(pct=True)
        rank_cols = [f'{vc}_rank' for vc in existing_val]
        X['valuation_rank_avg'] = X[rank_cols].mean(axis=1)

    # Quality composite
    quality_cols = ['return_on_equity', 'return_on_assets', 'profit_margins', 'operating_margins']
    existing_q = [c for c in quality_cols if c in X.columns]
    if len(existing_q) >= 2:
        for qc in existing_q:
            X[f'{qc}_rank'] = X[qc].rank(pct=True)
        qrank_cols = [f'{qc}_rank' for qc in existing_q]
        X['quality_rank_avg'] = X[qrank_cols].mean(axis=1)

    # Growth features
    if 'revenue_growth' in X.columns and 'earnings_growth' in X.columns:
        rg = pd.to_numeric(X['revenue_growth'], errors='coerce')
        eg = pd.to_numeric(X['earnings_growth'], errors='coerce')
        X['growth_composite'] = (rg + eg) / 2

    # Volatility-adjusted momentum
    if 'ret_6m' in X.columns and 'vol_60d' in X.columns:
        X['sharpe_6m'] = X['ret_6m'] / (X['vol_60d'] + 1e-6)

    # Distance from 52w high as pct (already there but interaction)
    if 'dist_52w_high' in X.columns and 'vol_60d' in X.columns:
        X['dist_high_vol_ratio'] = X['dist_52w_high'] / (X['vol_60d'] + 1e-6)

    return X


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

def train_and_predict(train_df, test_df, feature_cols):
    """Train model on train_df, return predictions for test_df."""

    X_train = engineer_features(train_df, feature_cols)
    X_test = engineer_features(test_df, feature_cols)
    y_train = train_df['peak_return_2y'].values

    # Log-transform target (right-skewed)
    y_train_log = np.log1p(y_train)

    # LightGBM with tuned params
    params = {
        'objective': 'regression',
        'metric': 'mae',
        'learning_rate': 0.03,
        'num_leaves': 127,
        'max_depth': 10,
        'min_child_samples': 30,
        'subsample': 0.8,
        'colsample_bytree': 0.7,
        'reg_alpha': 0.1,
        'reg_lambda': 1.0,
        'verbose': -1,
        'n_jobs': -1,
        'seed': 42,
    }

    train_data = lgb.Dataset(X_train, label=y_train_log)
    model = lgb.train(params, train_data, num_boost_round=1000)
    predictions_log = model.predict(X_test)

    # Inverse transform (not needed for ranking, but keeps scale sensible)
    predictions = np.expm1(predictions_log)

    return predictions


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    # Load data (fixed harness)
    train_df, test_df, feature_cols = load_data()

    # Train and predict (timed)
    print("\nTraining model...")
    t0 = time.time()
    predictions = train_and_predict(train_df, test_df, feature_cols)
    training_seconds = time.time() - t0
    print(f"Training + prediction: {training_seconds:.1f}s")

    if training_seconds > TIME_BUDGET:
        print(f"WARNING: exceeded time budget ({TIME_BUDGET}s)")

    # Score (fixed harness)
    results = score_predictions(test_df['peak_return_2y'].values, predictions)
    print_results(results, training_seconds=training_seconds)

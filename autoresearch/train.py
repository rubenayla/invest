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

    return X


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

def train_and_predict(train_df, test_df, feature_cols):
    """Train model on train_df, return predictions for test_df."""

    X_train = engineer_features(train_df, feature_cols)
    X_test = engineer_features(test_df, feature_cols)
    y_train = train_df['peak_return_2y'].values

    # LightGBM baseline
    params = {
        'objective': 'regression',
        'metric': 'mae',
        'learning_rate': 0.05,
        'num_leaves': 63,
        'max_depth': 8,
        'min_child_samples': 50,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'reg_alpha': 0.1,
        'reg_lambda': 1.0,
        'verbose': -1,
        'n_jobs': -1,
        'seed': 42,
    }

    train_data = lgb.Dataset(X_train, label=y_train)
    model = lgb.train(params, train_data, num_boost_round=500)
    predictions = model.predict(X_test)

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

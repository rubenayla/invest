#!/usr/bin/env python3
"""
Generate GBM Opportunistic 1-year stock predictions and save to valuation_results.

Loads trained GBM model, makes predictions on latest data using same
feature engineering as training, and assigns decile-based confidence.
"""

import json
import logging
import sqlite3
import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'neural_network/training'))

# Import feature engineering from training script
# Import feature configuration
from gbm_feature_config import (
    BASE_FEATURES,
    CASHFLOW_FEATURES,
    CATEGORICAL_FEATURES,
    FUNDAMENTAL_FEATURES,
    LAG_PERIODS,
    MARKET_FEATURES,
    PRICE_FEATURES,
    ROLLING_WINDOWS,
)
from train_gbm_stock_ranker import (
    create_change_features,
    create_lag_features,
    create_rolling_features,
    standardize_by_date,
    winsorize_by_date,
)

from invest.data.stock_data_reader import StockDataReader

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_gbm_model(model_path: str) -> lgb.Booster:
    """Load trained GBM model."""
    if not Path(model_path).exists():
        raise FileNotFoundError(f'GBM model not found at {model_path}')

    model = lgb.Booster(model_file=model_path)
    logger.info(f'Loaded GBM model from {model_path}')
    return model


def load_and_engineer_features(db_path: str) -> pd.DataFrame:
    """Load data and engineer features exactly like training."""
    conn = sqlite3.connect(db_path)

    # Build query for all required columns
    snapshot_cols = (
        ['a.symbol as ticker', 'a.sector', 's.snapshot_date', 's.id as snapshot_id'] +
        [f's.{col}' for col in FUNDAMENTAL_FEATURES + MARKET_FEATURES + CASHFLOW_FEATURES]
    )

    query = f'''
        SELECT
            {', '.join(snapshot_cols)}
        FROM snapshots s
        JOIN assets a ON s.asset_id = a.id
        WHERE s.vix IS NOT NULL
        AND s.snapshot_date >= date('now', '-3 years')
        ORDER BY a.symbol, s.snapshot_date
    '''

    df = pd.read_sql(query, conn)
    df['snapshot_date'] = pd.to_datetime(df['snapshot_date'])

    logger.info(f'Loaded {len(df)} snapshots for feature engineering')

    # Convert all numeric columns to float (SQLite sometimes returns as object)
    for col in FUNDAMENTAL_FEATURES + MARKET_FEATURES + CASHFLOW_FEATURES:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Add price features
    df = add_price_features(df, conn)
    conn.close()

    # Sort by ticker and date
    df = df.sort_values(['ticker', 'snapshot_date']).reset_index(drop=True)

    # Create computed features (same as training)
    logger.info('Creating computed features...')
    df['log_market_cap'] = np.log(df['market_cap'] + 1e9)
    df['fcf_yield'] = df['free_cashflow'] / (df['market_cap'] + 1e9)
    df['ocf_yield'] = df['operating_cashflow'] / (df['market_cap'] + 1e9)
    df['earnings_yield'] = df['trailing_eps'] / (df['market_cap'] / df['book_value'] + 1e-9)

    # Create lag features
    df = create_lag_features(df, BASE_FEATURES, lags=LAG_PERIODS)
    logger.info(f'Created lag features for {len(BASE_FEATURES)} features')

    # Create change features
    df = create_change_features(df, BASE_FEATURES)
    logger.info('Created change features')

    # Create rolling features
    df = create_rolling_features(df, BASE_FEATURES, windows=ROLLING_WINDOWS)
    logger.info('Created rolling features')

    # Add missingness flags
    for feat in BASE_FEATURES:
        df[f'{feat}_missing'] = df[feat].isna().astype(int)

    logger.info(f'Feature engineering complete: {len(df.columns)} columns')

    # Filter to only LATEST snapshot per ticker
    latest_df = df.loc[df.groupby('ticker')['snapshot_date'].idxmax()]

    logger.info(f'Filtered to {len(latest_df)} latest snapshots')

    return latest_df


def add_price_features(df: pd.DataFrame, conn) -> pd.DataFrame:
    """Add price-based features (same as training)."""
    price_query = '''
        SELECT
            ticker,
            date,
            close,
            volume
        FROM price_history
        ORDER BY ticker, date
    '''
    price_df = pd.read_sql(price_query, conn)
    price_df['date'] = pd.to_datetime(price_df['date'])

    logger.info(f'Loaded {len(price_df)} price history records')

    price_groups = price_df.groupby('ticker')

    def calc_price_features(row):
        ticker = row['ticker']
        snapshot_date = row['snapshot_date']

        if ticker not in price_groups.groups:
            return pd.Series({feat: np.nan for feat in PRICE_FEATURES})

        ticker_prices = price_groups.get_group(ticker)
        ticker_prices = ticker_prices[ticker_prices['date'] <= snapshot_date].sort_values('date')

        if len(ticker_prices) >= 21:
            # Get last 252 trading days (~1 year) or available data
            recent_prices = ticker_prices.tail(252)
            closes = recent_prices['close'].values
            volumes = recent_prices['volume'].values

            # Calculate returns for multiple periods
            returns_1m = (closes[-1] - closes[-21]) / closes[-21] if len(closes) >= 21 else 0.0
            returns_3m = (closes[-1] - closes[-63]) / closes[-63] if len(closes) >= 63 else 0.0
            returns_6m = (closes[-1] - closes[-126]) / closes[-126] if len(closes) >= 126 else 0.0
            returns_1y = (closes[-1] - closes[0]) / closes[0] if len(closes) >= 252 else 0.0

            # Calculate volatility (std of daily returns over last 60 days)
            recent_closes = closes[-60:] if len(closes) >= 60 else closes
            daily_returns = np.diff(recent_closes) / recent_closes[:-1]
            volatility = np.std(daily_returns) if len(daily_returns) > 0 else 0.0

            # Calculate volume trend
            vol_avg = np.mean(volumes)
            vol_recent = np.mean(volumes[-5:]) if len(volumes) >= 5 else vol_avg
            volume_trend = (vol_recent - vol_avg) / (vol_avg + 1e-9) if vol_avg > 0 else 0.0
        else:
            # If less than 21 days, set features to 0
            returns_1m = np.nan
            returns_3m = np.nan
            returns_6m = np.nan
            returns_1y = np.nan
            volatility = np.nan
            volume_trend = np.nan

        return pd.Series({
            'returns_1m': returns_1m,
            'returns_3m': returns_3m,
            'returns_6m': returns_6m,
            'returns_1y': returns_1y,
            'volatility': volatility,
            'volume_trend': volume_trend
        })

    price_features = df.apply(calc_price_features, axis=1)
    df = pd.concat([df, price_features], axis=1)

    # Fill missing values
    for feat in PRICE_FEATURES:
        df[feat] = df[feat].fillna(0.0)

    logger.info(f'Added price features: {", ".join(PRICE_FEATURES)}')
    return df


def prepare_features(df: pd.DataFrame) -> tuple:
    """Prepare features for prediction (same as training)."""
    # Exclude metadata, categorical, and base cashflow features
    # Note: We don't engineer features FOR cashflow features, we only use them to compute yields
    exclude_cols = (
        ['ticker', 'snapshot_date', 'snapshot_id'] +
        CATEGORICAL_FEATURES +
        CASHFLOW_FEATURES  # Only base features, no engineered versions exist
    )

    numeric_features = [
        col for col in df.columns
        if col not in exclude_cols and df[col].dtype in [np.float64, np.int64]
    ]

    logger.info(f'Excluding {len(exclude_cols)} columns')
    logger.info(f'Found {len(numeric_features)} numeric features')

    # Debug: show some excluded cashflow features
    cashflow_excluded = [c for c in exclude_cols if any(cf in c for cf in CASHFLOW_FEATURES)]
    logger.info(f'Cashflow-related exclusions: {len(cashflow_excluded)} features')

    # Check which excluded columns actually exist
    existing_excluded = [c for c in exclude_cols if c in df.columns]
    missing_excluded = [c for c in exclude_cols if c not in df.columns]
    logger.info(f'Excluded columns that exist: {len(existing_excluded)}')
    logger.info(f'Excluded columns that DON\'T exist: {len(missing_excluded)}')
    if missing_excluded:
        logger.warning(f'Missing exclusions (first 10): {missing_excluded[:10]}')

    # Winsorize and standardize (using current data only)
    df_norm = df.copy()
    df_norm = winsorize_by_date(df_norm, numeric_features, lower_pct=0.01, upper_pct=0.99)
    df_norm = standardize_by_date(df_norm, numeric_features)

    # Create feature matrix
    feature_cols = numeric_features + CATEGORICAL_FEATURES
    X = df_norm[feature_cols].copy()

    # Handle categoricals
    for cat_col in CATEGORICAL_FEATURES:
        X[cat_col] = X[cat_col].fillna('Unknown').astype('category')

    logger.info(f'Prepared {len(feature_cols)} features for prediction')
    logger.info(f'  Feature matrix shape: {X.shape}')

    return X, feature_cols, df_norm


def assign_confidence(predictions: np.ndarray) -> list:
    """
    Assign confidence based on decile ranking.

    Top 20% (deciles 9-10): High confidence (strong buy)
    Bottom 20% (deciles 1-2): High confidence (strong avoid)
    Middle 60%: Medium confidence
    """
    ranks = pd.qcut(predictions, q=10, labels=False, duplicates='drop')

    confidences = []
    for rank in ranks:
        if rank >= 8:  # Top 20%
            confidences.append('High')
        elif rank <= 1:  # Bottom 20%
            confidences.append('High')
        else:
            confidences.append('Medium')

    return confidences


def save_to_database(df: pd.DataFrame, predictions: np.ndarray, confidences: list, db_path: str):
    """Save predictions to valuation_results table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Delete existing GBM predictions
    cursor.execute("DELETE FROM valuation_results WHERE model_name = 'gbm_opportunistic_1y'")
    logger.info(f'Deleted {cursor.rowcount} existing gbm_opportunistic_1y predictions')

    # Initialize StockDataReader for current price lookup
    reader = StockDataReader(db_path)

    # Insert new predictions
    inserted = 0
    skipped = 0

    for i, (idx, row) in enumerate(df.iterrows()):
        ticker = row['ticker']

        # Get current price from current_stock_data table
        stock_data = reader.get_stock_data(ticker)
        if not stock_data or 'info' not in stock_data:
            logger.warning(f'Skipping {ticker}: no data in current_stock_data')
            skipped += 1
            continue

        current_price = stock_data['info'].get('currentPrice', 0)
        if not current_price or current_price == 0:
            logger.warning(f'Skipping {ticker}: no valid current price in current_stock_data')
            skipped += 1
            continue

        # GBM predicts opportunistic 1-year return (e.g., 0.75 = 75% expected return over 3 years)
        predicted_return = predictions[i]

        # Calculate "fair value" as current price * (1 + predicted_return)
        fair_value = current_price * (1 + predicted_return)

        # Upside is the predicted return
        upside_pct = predicted_return * 100

        # Margin of safety (use predicted return)
        margin_of_safety = predicted_return

        # Ranking percentile
        all_predictions = predictions.copy()
        percentile = (all_predictions < predicted_return).sum() / len(all_predictions) * 100

        # Details JSON
        details = {
            'predicted_return_opportunistic_1y': float(predicted_return),
            'ranking_percentile': float(percentile)
        }

        cursor.execute('''
            INSERT INTO valuation_results
            (ticker, model_name, fair_value, current_price, margin_of_safety,
             upside_pct, suitable, confidence, details_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ticker,
            'gbm_opportunistic_1y',
            float(fair_value),
            float(current_price),
            float(margin_of_safety),
            float(upside_pct),
            1,  # suitable = True
            confidences[i],
            json.dumps(details)
        ))
        inserted += 1

    conn.commit()
    conn.close()

    logger.info(f'Inserted {inserted} GBM predictions into database')
    if skipped > 0:
        logger.info(f'Skipped {skipped} stocks (no current price)')


def main():
    """Generate and save GBM predictions."""
    # Paths
    project_root = Path(__file__).parent.parent
    model_path = project_root / 'neural_network/training/gbm_opportunistic_model_1y.txt'
    db_path = project_root / 'data/stock_data.db'

    # Load model
    model = load_gbm_model(str(model_path))

    # Load data and engineer features
    df = load_and_engineer_features(str(db_path))

    # Prepare features
    X, feature_cols, df_norm = prepare_features(df)

    # Make predictions
    logger.info('Making predictions...')
    predictions = model.predict(X)

    # Assign confidence
    confidences = assign_confidence(predictions)

    # Log summary
    logger.info('Predictions summary:')
    logger.info(f'  Mean predicted return: {np.mean(predictions):.2%}')
    logger.info(f'  Median predicted return: {np.median(predictions):.2%}')
    logger.info(f'  Top prediction: {np.max(predictions):.2%}')
    logger.info(f'  Bottom prediction: {np.min(predictions):.2%}')
    logger.info(f'  High confidence: {confidences.count("High")} stocks')
    logger.info(f'  Medium confidence: {confidences.count("Medium")} stocks')

    # Top 5 picks
    top5_idx = np.argsort(predictions)[-5:][::-1]
    logger.info('Top 5 picks:')
    for idx in top5_idx:
        logger.info(f'  {df.iloc[idx]["ticker"]}: {predictions[idx]:.2%}')

    # Save to database
    save_to_database(df, predictions, confidences, str(db_path))

    logger.info('GBM predictions complete!')


if __name__ == '__main__':
    main()

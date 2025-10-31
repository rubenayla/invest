#!/usr/bin/env python3
"""
Generate GBM stock predictions and save to valuation_results.

Unified script supporting all GBM variants (standard, lite, opportunistic)
and horizons (1y, 3y).

Usage:
    uv run python scripts/run_gbm_predictions.py --variant standard --horizon 1y
    uv run python scripts/run_gbm_predictions.py --variant lite --horizon 3y
    uv run python scripts/run_gbm_predictions.py --variant opportunistic --horizon 1y
"""

import argparse
import importlib
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

from invest.data.stock_data_reader import StockDataReader

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_variant_config(variant: str):
    """
    Dynamically load feature config and training functions based on variant.

    Parameters
    ----------
    variant : str
        One of 'standard', 'lite', 'opportunistic'

    Returns
    -------
    tuple
        (training_module, feature_config_module)
    """
    if variant == 'standard':
        training_module = importlib.import_module('train_gbm_stock_ranker')
        feature_config = importlib.import_module('gbm_feature_config')
    elif variant == 'lite':
        training_module = importlib.import_module('train_gbm_lite_stock_ranker')
        feature_config = importlib.import_module('gbm_lite_feature_config')
    elif variant == 'opportunistic':
        training_module = importlib.import_module('train_gbm_opportunistic')
        feature_config = importlib.import_module('gbm_feature_config')
    else:
        raise ValueError(f'Unknown variant: {variant}')

    return training_module, feature_config


def get_model_metadata(variant: str, horizon: str) -> dict:
    """
    Get model file path and database name based on variant and horizon.

    Parameters
    ----------
    variant : str
        One of 'standard', 'lite', 'opportunistic'
    horizon : str
        One of '1y', '3y'

    Returns
    -------
    dict
        {'model_file': str, 'model_name': str, 'description': str}
    """
    if variant == 'standard':
        model_file = f'gbm_model_{horizon}.txt'
        model_name = f'gbm_{horizon}'
        description = f'GBM {horizon} predictions'
    elif variant == 'lite':
        model_file = f'gbm_lite_model_{horizon}.txt'
        model_name = f'gbm_lite_{horizon}'
        description = f'GBM Lite {horizon} predictions (limited history stocks)'
    elif variant == 'opportunistic':
        model_file = f'gbm_opportunistic_model_{horizon}.txt'
        model_name = f'gbm_opportunistic_{horizon}'
        description = f'GBM Opportunistic {horizon} predictions (max price in window)'
    else:
        raise ValueError(f'Unknown variant: {variant}')

    return {
        'model_file': model_file,
        'model_name': model_name,
        'description': description,
        'horizon': horizon
    }


def load_gbm_model(model_path: str) -> lgb.Booster:
    """Load trained GBM model."""
    if not Path(model_path).exists():
        raise FileNotFoundError(f'GBM model not found at {model_path}')

    model = lgb.Booster(model_file=model_path)
    logger.info(f'Loaded GBM model from {model_path}')
    return model


def load_and_engineer_features(
    db_path: str,
    feature_config,
    training_module
) -> pd.DataFrame:
    """Load data and engineer features exactly like training."""
    conn = sqlite3.connect(db_path)

    # Build query for all required columns
    history_cols = (
        ['a.symbol as ticker', 'a.sector', 'fh.snapshot_date', 'fh.id as snapshot_id'] +
        [f'fh.{col}' for col in (
            feature_config.FUNDAMENTAL_FEATURES +
            feature_config.MARKET_FEATURES +
            feature_config.CASHFLOW_FEATURES
        )]
    )

    query = f'''
        SELECT
            {', '.join(history_cols)}
        FROM fundamental_history fh
        JOIN assets a ON fh.asset_id = a.id
        WHERE fh.vix IS NOT NULL
        AND fh.snapshot_date >= date('now', '-3 years')
        ORDER BY a.symbol, fh.snapshot_date
    '''

    df = pd.read_sql(query, conn)
    df['snapshot_date'] = pd.to_datetime(df['snapshot_date'])

    logger.info(f'Loaded {len(df)} snapshots for feature engineering')

    # Convert all numeric columns to float (SQLite sometimes returns as object)
    for col in (feature_config.FUNDAMENTAL_FEATURES +
                feature_config.MARKET_FEATURES +
                feature_config.CASHFLOW_FEATURES):
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Add price features
    df = add_price_features(df, conn, feature_config.PRICE_FEATURES)
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
    df = training_module.create_lag_features(
        df,
        feature_config.BASE_FEATURES,
        lags=feature_config.LAG_PERIODS
    )
    logger.info(f'Created lag features for {len(feature_config.BASE_FEATURES)} features')

    # Create change features
    df = training_module.create_change_features(df, feature_config.BASE_FEATURES)
    logger.info('Created change features')

    # Create rolling features
    df = training_module.create_rolling_features(
        df,
        feature_config.BASE_FEATURES,
        windows=feature_config.ROLLING_WINDOWS
    )
    logger.info('Created rolling features')

    # Add missingness flags
    for feat in feature_config.BASE_FEATURES:
        df[f'{feat}_missing'] = df[feat].isna().astype(int)

    logger.info(f'Feature engineering complete: {len(df.columns)} columns')

    # Filter to only LATEST snapshot per ticker
    latest_df = df.loc[df.groupby('ticker')['snapshot_date'].idxmax()]

    logger.info(f'Filtered to {len(latest_df)} latest snapshots')

    return latest_df


def add_price_features(df: pd.DataFrame, conn, price_features: list) -> pd.DataFrame:
    """Add price-based features (same as training)."""
    price_query = '''
        SELECT
            fh.id as snapshot_id,
            ph.date,
            ph.close,
            ph.volume
        FROM fundamental_history fh
        JOIN assets a ON fh.asset_id = a.id
        JOIN price_history ph ON a.symbol = ph.ticker
        ORDER BY fh.id, ph.date
    '''
    price_df = pd.read_sql(price_query, conn)
    price_df['date'] = pd.to_datetime(price_df['date'])

    logger.info(f'Loaded {len(price_df)} price history records')

    price_groups = price_df.groupby('snapshot_id')

    def calc_price_features(row):
        snapshot_id = row['snapshot_id']
        snapshot_date = row['snapshot_date']

        if snapshot_id not in price_groups.groups:
            return pd.Series({feat: np.nan for feat in price_features})

        snapshot_prices = price_groups.get_group(snapshot_id)
        snapshot_prices = snapshot_prices[snapshot_prices['date'] <= snapshot_date].sort_values('date')

        if len(snapshot_prices) >= 21:
            # Get last 252 trading days (~1 year) or available data
            recent_prices = snapshot_prices.tail(252)
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
            # If less than 21 days, set features to nan
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

    price_features_df = df.apply(calc_price_features, axis=1)
    df = pd.concat([df, price_features_df], axis=1)

    # Fill missing values
    for feat in price_features:
        df[feat] = df[feat].fillna(0.0)

    logger.info(f'Added price features: {", ".join(price_features)}')
    return df


def prepare_features(
    df: pd.DataFrame,
    feature_config,
    training_module
) -> tuple:
    """Prepare features for prediction (same as training)."""
    # Exclude metadata, categorical, and base cashflow features
    exclude_cols = (
        ['ticker', 'snapshot_date', 'snapshot_id'] +
        feature_config.CATEGORICAL_FEATURES +
        feature_config.CASHFLOW_FEATURES
    )

    numeric_features = [
        col for col in df.columns
        if col not in exclude_cols and df[col].dtype in [np.float64, np.int64]
    ]

    logger.info(f'Excluding {len(exclude_cols)} columns')
    logger.info(f'Found {len(numeric_features)} numeric features')

    # Winsorize and standardize (using current data only)
    df_norm = df.copy()
    df_norm = training_module.winsorize_by_date(
        df_norm, numeric_features, lower_pct=0.01, upper_pct=0.99
    )
    df_norm = training_module.standardize_by_date(df_norm, numeric_features)

    # Create feature matrix
    feature_cols = numeric_features + feature_config.CATEGORICAL_FEATURES
    X = df_norm[feature_cols].copy()

    # Handle categoricals
    for cat_col in feature_config.CATEGORICAL_FEATURES:
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


def save_to_database(
    df: pd.DataFrame,
    predictions: np.ndarray,
    confidences: list,
    db_path: str,
    metadata: dict
):
    """Save predictions to valuation_results table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    model_name = metadata['model_name']
    horizon = metadata['horizon']

    # Delete existing predictions
    cursor.execute(f"DELETE FROM valuation_results WHERE model_name = '{model_name}'")
    logger.info(f'Deleted {cursor.rowcount} existing {model_name} predictions')

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

        # GBM predicts return over horizon
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
            f'predicted_return_{horizon}': float(predicted_return),
            'ranking_percentile': float(percentile)
        }

        cursor.execute('''
            INSERT INTO valuation_results
            (ticker, model_name, fair_value, current_price, margin_of_safety,
             upside_pct, suitable, confidence, details_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ticker,
            model_name,
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

    logger.info(f'Inserted {inserted} {model_name} predictions into database')
    if skipped > 0:
        logger.info(f'Skipped {skipped} stocks (no current price)')


def main():
    """Generate and save GBM predictions."""
    parser = argparse.ArgumentParser(
        description='Generate GBM predictions for stocks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --variant standard --horizon 1y
  %(prog)s --variant lite --horizon 3y
  %(prog)s --variant opportunistic --horizon 1y
        """
    )
    parser.add_argument(
        '--variant',
        choices=['standard', 'lite', 'opportunistic'],
        required=True,
        help='GBM variant to use'
    )
    parser.add_argument(
        '--horizon',
        choices=['1y', '3y'],
        required=True,
        help='Prediction horizon'
    )
    args = parser.parse_args()

    # Get model metadata
    metadata = get_model_metadata(args.variant, args.horizon)
    logger.info(f'Running {metadata["description"]}')

    # Paths
    project_root = Path(__file__).parent.parent
    model_path = project_root / 'neural_network/training' / metadata['model_file']
    db_path = project_root / 'data/stock_data.db'

    # Load variant-specific config
    training_module, feature_config = load_variant_config(args.variant)

    # Load model
    model = load_gbm_model(str(model_path))

    # Load data and engineer features
    df = load_and_engineer_features(str(db_path), feature_config, training_module)

    # Prepare features
    X, feature_cols, df_norm = prepare_features(df, feature_config, training_module)

    # Make predictions
    logger.info('Making predictions...')
    predictions = model.predict(X)

    # Assign confidence
    confidences = assign_confidence(predictions)

    # Log summary
    logger.info(f'Predictions summary:')
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
    save_to_database(df, predictions, confidences, str(db_path), metadata)

    logger.info(f'{metadata["description"]} complete!')


if __name__ == '__main__':
    main()

"""
GBM-based ranking strategy for backtesting.
Uses trained Gradient Boosted Machine models to predict stock returns and rank stocks.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging
import lightgbm as lgb
import sys

# Add neural_network/training to path for imports
training_path = Path(__file__).parent.parent.parent / 'neural_network' / 'training'
sys.path.insert(0, str(training_path))

from gbm_feature_config import (
    BASE_FEATURES,
    FUNDAMENTAL_FEATURES,
    PRICE_FEATURES,
    LAG_PERIODS,
    ROLLING_WINDOWS
)

from backtesting.data.snapshot_provider import SnapshotDataProvider

logger = logging.getLogger(__name__)


class GBMRankingStrategy:
    """
    Investment strategy using GBM model predictions for stock ranking.

    This strategy:
    1. Loads historical fundamental snapshots (no look-ahead bias)
    2. Engineers same features as training (lags, rolling windows)
    3. Runs GBM model to predict returns
    4. Ranks stocks and selects top performers
    5. Constructs portfolio with configurable weighting
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize GBM ranking strategy.

        Parameters
        ----------
        config : Dict[str, Any], optional
            Strategy configuration including:
            - model_path: Path to trained GBM model file
            - model_type: 'full' or 'lite' (determines min_snapshots requirement)
            - selection_method: 'top_decile', 'top_quintile', 'top_n'
            - num_positions: Number of stocks to hold (if top_n)
            - weighting: 'equal_weight', 'prediction_weighted', 'inverse_volatility'
            - min_prediction: Minimum predicted return to include (default 0.0)
        """
        self.config = config or {}

        # Model configuration
        model_path = self.config.get('model_path')
        if model_path is None:
            raise ValueError('model_path must be specified in config')

        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f'Model not found: {self.model_path}')

        # Load GBM model
        logger.info(f'Loading GBM model from {self.model_path}')
        self.model = lgb.Booster(model_file=str(self.model_path))

        # Model type determines minimum snapshot requirement
        self.model_type = self.config.get('model_type', 'full')
        self.min_snapshots = 12 if self.model_type == 'full' else 4

        # Selection configuration
        self.selection_method = self.config.get('selection_method', 'top_decile')
        self.num_positions = self.config.get('num_positions', 15)
        self.min_prediction = self.config.get('min_prediction', 0.0)

        # Weighting configuration
        self.weighting = self.config.get('weighting', 'equal_weight')

        # Initialize data provider
        self.snapshot_provider = SnapshotDataProvider()

        logger.info(f'Initialized GBMRankingStrategy: {self.selection_method}, '
                   f'{self.weighting}, min_snapshots={self.min_snapshots}')

    def generate_signals(self, market_data: Dict[str, Any],
                        current_portfolio: Dict[str, float],
                        date: pd.Timestamp) -> Dict[str, float]:
        """
        Generate target portfolio weights using GBM predictions.

        Parameters
        ----------
        market_data : Dict[str, Any]
            Point-in-time market data (not used, we fetch from database)
        current_portfolio : Dict[str, float]
            Current portfolio holdings
        date : pd.Timestamp
            Current date

        Returns
        -------
        Dict[str, float]
            Target weights for each ticker
        """
        logger.info(f'Generating GBM signals for {date}')

        # Get available tickers as of this date
        tickers = self.snapshot_provider.get_available_tickers_as_of(
            date, min_snapshots=self.min_snapshots
        )

        if len(tickers) == 0:
            logger.warning(f'No tickers with sufficient history as of {date}')
            return {}

        logger.info(f'Found {len(tickers)} tickers with {self.min_snapshots}+ snapshots')

        # Generate predictions for all tickers
        predictions = []

        for ticker in tickers:
            try:
                # Get historical snapshots for feature engineering
                snapshots = self.snapshot_provider.get_historical_snapshots(
                    ticker, date, lookback_quarters=12
                )

                if len(snapshots) < self.min_snapshots:
                    continue

                # Get price data for momentum features
                price_data = self.snapshot_provider.get_price_data(ticker, date)

                if len(price_data) < 20:
                    continue

                # Engineer features
                features = self._engineer_features(snapshots, price_data, date)

                if features is None:
                    continue

                # Predict return
                predicted_return = self.model.predict([features])[0]

                predictions.append({
                    'ticker': ticker,
                    'predicted_return': predicted_return,
                    'volatility': features[-7] if len(features) > 7 else 0.0  # volatility feature
                })

            except Exception as e:
                logger.warning(f'Error generating prediction for {ticker}: {e}')
                continue

        if len(predictions) == 0:
            logger.warning('No valid predictions generated')
            return {}

        # Convert to DataFrame for ranking
        pred_df = pd.DataFrame(predictions)
        pred_df = pred_df.sort_values('predicted_return', ascending=False)

        logger.info(f'Generated {len(pred_df)} predictions')
        logger.info(f'Top prediction: {pred_df.iloc[0]["ticker"]} '
                   f'({pred_df.iloc[0]["predicted_return"]:.2%})')
        logger.info(f'Bottom prediction: {pred_df.iloc[-1]["ticker"]} '
                   f'({pred_df.iloc[-1]["predicted_return"]:.2%})')

        # Select stocks
        selected_stocks = self._select_stocks(pred_df)

        if len(selected_stocks) == 0:
            logger.warning('No stocks selected')
            return {}

        # Calculate weights
        target_weights = self._calculate_weights(selected_stocks)

        logger.info(f'Selected {len(target_weights)} stocks, '
                   f'total weight: {sum(target_weights.values()):.2%}')

        return target_weights

    def _engineer_features(self, snapshots: pd.DataFrame,
                          price_data: pd.DataFrame,
                          as_of_date: pd.Timestamp) -> Optional[np.ndarray]:
        """
        Engineer features matching training data.

        This must match EXACTLY the feature engineering in train_gbm_stock_ranker.py.

        Parameters
        ----------
        snapshots : pd.DataFrame
            Historical snapshots for this ticker
        price_data : pd.DataFrame
            Historical price data
        as_of_date : pd.Timestamp
            Current date

        Returns
        -------
        np.ndarray or None
            Feature vector, or None if insufficient data
        """
        if len(snapshots) < self.min_snapshots:
            return None

        # Use most recent snapshot
        current = snapshots.iloc[-1]

        features = []

        # Base fundamental features
        for feat in FUNDAMENTAL_FEATURES:
            value = current.get(feat, 0.0)
            # Handle missing values
            if pd.isna(value) or value is None:
                value = 0.0
            features.append(float(value))

        # Market regime features
        features.append(float(current.get('vix', 20.0)))  # Default VIX = 20
        features.append(float(current.get('treasury_10y', 0.03)))  # Default 3%

        # Price features
        price_features = self.snapshot_provider.compute_price_features(price_data)
        for feat in PRICE_FEATURES:
            features.append(float(price_features.get(feat, 0.0)))

        # Computed features
        market_cap = current.get('market_cap', 1e9)
        fcf = current.get('free_cashflow', 0.0)
        ocf = current.get('operating_cashflow', 0.0)
        eps = current.get('trailing_eps', 0.0)
        book_value = current.get('book_value', 0.0)

        # Yields
        fcf_yield = fcf / market_cap if market_cap > 0 else 0.0
        ocf_yield = ocf / market_cap if market_cap > 0 else 0.0
        earnings_yield = eps / book_value if book_value > 0 else 0.0

        features.extend([fcf_yield, ocf_yield, earnings_yield])

        # Log market cap
        log_market_cap = np.log(max(market_cap, 1e6))
        features.append(log_market_cap)

        # Lag features (if we have enough history)
        for lag in LAG_PERIODS:
            if len(snapshots) > lag:
                lagged_snapshot = snapshots.iloc[-(lag+1)]
                for feat in FUNDAMENTAL_FEATURES + ['vix', 'treasury_10y']:
                    value = lagged_snapshot.get(feat, 0.0)
                    if pd.isna(value) or value is None:
                        value = 0.0
                    features.append(float(value))
            else:
                # Not enough history - pad with zeros
                features.extend([0.0] * (len(FUNDAMENTAL_FEATURES) + 2))

        # Rolling window features
        for window in ROLLING_WINDOWS:
            if len(snapshots) >= window:
                window_data = snapshots.iloc[-window:]

                for feat in FUNDAMENTAL_FEATURES:
                    values = window_data[feat].replace([np.inf, -np.inf], np.nan).dropna()

                    if len(values) > 0:
                        mean_val = float(values.mean())
                        std_val = float(values.std()) if len(values) > 1 else 0.0

                        # Trend (linear regression slope)
                        if len(values) > 2:
                            x = np.arange(len(values))
                            slope = np.polyfit(x, values, 1)[0]
                        else:
                            slope = 0.0
                    else:
                        mean_val, std_val, slope = 0.0, 0.0, 0.0

                    features.extend([mean_val, std_val, slope])
            else:
                # Not enough history - pad with zeros
                features.extend([0.0] * (len(FUNDAMENTAL_FEATURES) * 3))

        return np.array(features, dtype=np.float32)

    def _select_stocks(self, pred_df: pd.DataFrame) -> pd.DataFrame:
        """
        Select stocks based on selection method.

        Parameters
        ----------
        pred_df : pd.DataFrame
            DataFrame with columns: ticker, predicted_return, volatility

        Returns
        -------
        pd.DataFrame
            Selected stocks
        """
        # Filter by minimum prediction
        pred_df = pred_df[pred_df['predicted_return'] >= self.min_prediction]

        if len(pred_df) == 0:
            return pd.DataFrame()

        if self.selection_method == 'top_decile':
            # Top 10%
            n = max(1, len(pred_df) // 10)
            return pred_df.head(n)

        elif self.selection_method == 'top_quintile':
            # Top 20%
            n = max(1, len(pred_df) // 5)
            return pred_df.head(n)

        elif self.selection_method == 'top_n':
            # Top N stocks
            return pred_df.head(self.num_positions)

        else:
            raise ValueError(f'Unknown selection method: {self.selection_method}')

    def _calculate_weights(self, selected_stocks: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate portfolio weights for selected stocks.

        Parameters
        ----------
        selected_stocks : pd.DataFrame
            Selected stocks with predicted_return and volatility

        Returns
        -------
        Dict[str, float]
            Ticker -> weight mapping
        """
        if len(selected_stocks) == 0:
            return {}

        if self.weighting == 'equal_weight':
            # Equal weight all positions
            weight = 1.0 / len(selected_stocks)
            return {row['ticker']: weight for _, row in selected_stocks.iterrows()}

        elif self.weighting == 'prediction_weighted':
            # Weight by predicted return (higher return = higher weight)
            # Normalize predictions to [0, 1] range
            pred_values = selected_stocks['predicted_return'].values
            min_pred = pred_values.min()
            max_pred = pred_values.max()

            if max_pred > min_pred:
                normalized = (pred_values - min_pred) / (max_pred - min_pred)
            else:
                normalized = np.ones(len(pred_values))

            # Add small constant to avoid zero weights
            normalized = normalized + 0.1

            # Normalize to sum to 1.0
            weights = normalized / normalized.sum()

            return {
                row['ticker']: float(weights[i])
                for i, (_, row) in enumerate(selected_stocks.iterrows())
            }

        elif self.weighting == 'inverse_volatility':
            # Weight inversely to volatility (lower vol = higher weight)
            vol_values = selected_stocks['volatility'].values

            # Handle zero volatility
            vol_values = np.maximum(vol_values, 0.01)

            # Inverse volatility
            inv_vol = 1.0 / vol_values

            # Normalize to sum to 1.0
            weights = inv_vol / inv_vol.sum()

            return {
                row['ticker']: float(weights[i])
                for i, (_, row) in enumerate(selected_stocks.iterrows())
            }

        else:
            raise ValueError(f'Unknown weighting method: {self.weighting}')

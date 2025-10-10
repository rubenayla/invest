#!/usr/bin/env python3
"""
Run 3-Year LSTM/Transformer predictions on all stocks in database.

This script:
- Loads the trained 3-Year single-horizon model (78.64% hit rate)
- Gets stock list from current_stock_data table (database is ONLY source)
- Runs predictions with MC Dropout for confidence estimation
- Saves predictions to valuation_results table
"""

import json
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from invest.valuation.lstm_transformer_model import LSTMTransformerNetwork


class NeuralNetworkPredictor:
    """Runs 3-Year LSTM/Transformer predictions on dashboard stocks."""

    def __init__(self):
        self.project_root = project_root
        self.model_path = project_root / 'neural_network' / 'training' / 'best_model_3y.pt'
        self.db_path = project_root / 'data' / 'stock_data.db'
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        print(f'Loading 3-year model from {self.model_path}')
        self.model = self._load_model()

    def _load_model(self) -> LSTMTransformerNetwork:
        """Load trained model with correct dimensions (includes fundamentals)."""
        # Updated dimensions: 17 temporal (4 price + 5 macro + 8 fundamental), 30 static (5 macro + 14 fundamental + 11 sectors)
        model = LSTMTransformerNetwork(
            temporal_features=17,
            static_features=30,
            lstm_hidden=256,
            transformer_heads=8,
            dropout_rate=0.3
        )

        state_dict = torch.load(self.model_path, map_location=self.device)
        model.load_state_dict(state_dict)
        model.to(self.device)
        model.eval()

        print('✓ Model loaded successfully (17 temporal, 30 static features - with fundamentals)')
        return model

    def get_latest_snapshots(
        self,
        ticker: str,
        num_snapshots: int = 4
    ) -> Optional[pd.DataFrame]:
        """
        Get latest N snapshots for a ticker from database.

        Parameters
        ----------
        ticker : str
            Stock ticker
        num_snapshots : int
            Number of historical snapshots needed

        Returns
        -------
        pd.DataFrame or None
            Latest snapshots with features, or None if insufficient data
        """
        conn = sqlite3.connect(self.db_path)

        # Updated query: fetch real data (macro indicators + fundamentals + snapshot IDs for price history)
        query = '''
            SELECT
                s.id,
                a.symbol,
                a.sector,
                s.snapshot_date,
                s.vix,
                s.treasury_10y,
                s.dollar_index,
                s.oil_price,
                s.gold_price,
                s.pe_ratio,
                s.pb_ratio,
                s.ps_ratio,
                s.profit_margins,
                s.operating_margins,
                s.return_on_equity,
                s.revenue_growth,
                s.earnings_growth,
                s.debt_to_equity,
                s.current_ratio,
                s.trailing_eps,
                s.book_value,
                s.free_cashflow,
                s.operating_cashflow,
                s.market_cap
            FROM snapshots s
            JOIN assets a ON s.asset_id = a.id
            WHERE a.symbol = ?
                AND s.vix IS NOT NULL
            ORDER BY s.snapshot_date DESC
            LIMIT ?
        '''

        df = pd.read_sql_query(query, conn, params=(ticker, num_snapshots))
        conn.close()

        if len(df) < num_snapshots:
            return None

        # Reverse to get chronological order (oldest first)
        return df.iloc[::-1].reset_index(drop=True)

    def _extract_temporal(self, snapshots: pd.DataFrame, price_history: List[Tuple]) -> np.ndarray:
        """
        Extract temporal features from price history, macro indicators, and fundamentals.

        Uses real data with fundamentals (matches train_single_horizon.py).

        Parameters
        ----------
        snapshots : pd.DataFrame
            Sequence of snapshots in chronological order
        price_history : List[Tuple]
            Price history (date, close, volume) for most recent snapshot

        Returns
        -------
        np.ndarray
            Temporal features, shape (num_snapshots, 17)
        """
        # Calculate price-based features from last 60 days
        recent_prices = [p[1] for p in price_history[-60:]]
        recent_volumes = [p[2] for p in price_history[-60:]]

        if len(recent_prices) < 60:
            return None

        # Price momentum
        returns_1m = (recent_prices[-1] - recent_prices[-21]) / recent_prices[-21] if len(recent_prices) >= 21 else 0.0
        returns_3m = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
        volatility = np.std(np.diff(recent_prices) / recent_prices[:-1])

        # Volume trend
        vol_avg = np.mean(recent_volumes)
        vol_recent = np.mean(recent_volumes[-5:])
        volume_trend = (vol_recent - vol_avg) / vol_avg if vol_avg > 0 else 0.0

        # Temporal sequence from macro indicators + fundamentals
        temporal_features = []
        for _, snapshot in snapshots.iterrows():
            # Calculate cash flow yields
            market_cap = snapshot.market_cap if pd.notna(snapshot.market_cap) and snapshot.market_cap > 0 else 1e9
            fcf = snapshot.free_cashflow if pd.notna(snapshot.free_cashflow) else 0.0
            ocf = snapshot.operating_cashflow if pd.notna(snapshot.operating_cashflow) else 0.0
            fcf_yield = fcf / market_cap
            ocf_yield = ocf / market_cap

            features = [
                # Price-based features (4)
                returns_1m,
                returns_3m,
                volatility,
                volume_trend,
                # Macro indicators (5)
                snapshot.vix if pd.notna(snapshot.vix) else 20.0,
                snapshot.treasury_10y if pd.notna(snapshot.treasury_10y) else 3.0,
                snapshot.dollar_index if pd.notna(snapshot.dollar_index) else 100.0,
                snapshot.oil_price if pd.notna(snapshot.oil_price) else 70.0,
                snapshot.gold_price if pd.notna(snapshot.gold_price) else 1800.0,
                # Fundamental features (8)
                min(max(snapshot.pe_ratio if pd.notna(snapshot.pe_ratio) else 20.0, -50.0), 100.0),
                min(max(snapshot.pb_ratio if pd.notna(snapshot.pb_ratio) else 3.0, 0.0), 20.0),
                snapshot.profit_margins if pd.notna(snapshot.profit_margins) else 0.10,
                snapshot.operating_margins if pd.notna(snapshot.operating_margins) else 0.15,
                snapshot.return_on_equity if pd.notna(snapshot.return_on_equity) else 0.10,
                min(max(snapshot.debt_to_equity if pd.notna(snapshot.debt_to_equity) else 0.5, 0.0), 5.0),
                fcf_yield,
                ocf_yield,
            ]
            temporal_features.append(features)

        return np.array(temporal_features)

    def _extract_static(self, snapshot: pd.Series, sector: str) -> np.ndarray:
        """
        Extract static features from macro indicators, fundamentals, and sector.

        Uses real data with fundamentals (matches train_single_horizon.py).

        Parameters
        ----------
        snapshot : pd.Series
            Most recent snapshot
        sector : str
            Company sector

        Returns
        -------
        np.ndarray
            Static features, shape (30,)
        """
        features = []

        # Macro indicators (5)
        features.extend([
            snapshot.vix if pd.notna(snapshot.vix) else 20.0,
            snapshot.treasury_10y if pd.notna(snapshot.treasury_10y) else 3.0,
            snapshot.dollar_index if pd.notna(snapshot.dollar_index) else 100.0,
            snapshot.oil_price if pd.notna(snapshot.oil_price) else 70.0,
            snapshot.gold_price if pd.notna(snapshot.gold_price) else 1800.0,
        ])

        # Fundamental features (14)
        # Valuation ratios
        pe_ratio = snapshot.pe_ratio if pd.notna(snapshot.pe_ratio) else 20.0
        features.append(min(max(pe_ratio, -50.0), 100.0))

        pb_ratio = snapshot.pb_ratio if pd.notna(snapshot.pb_ratio) else 3.0
        features.append(min(max(pb_ratio, 0.0), 20.0))

        ps_ratio = snapshot.ps_ratio if pd.notna(snapshot.ps_ratio) else 2.0
        features.append(min(max(ps_ratio, 0.0), 20.0))

        # Profitability metrics
        features.append(snapshot.profit_margins if pd.notna(snapshot.profit_margins) else 0.10)
        features.append(snapshot.operating_margins if pd.notna(snapshot.operating_margins) else 0.15)
        features.append(snapshot.return_on_equity if pd.notna(snapshot.return_on_equity) else 0.10)

        # Growth metrics
        revenue_growth = snapshot.revenue_growth if pd.notna(snapshot.revenue_growth) else 0.05
        features.append(min(max(revenue_growth, -0.5), 2.0))

        earnings_growth = snapshot.earnings_growth if pd.notna(snapshot.earnings_growth) else 0.05
        features.append(min(max(earnings_growth, -1.0), 3.0))

        # Financial health
        debt_to_equity = snapshot.debt_to_equity if pd.notna(snapshot.debt_to_equity) else 0.5
        features.append(min(max(debt_to_equity, 0.0), 5.0))

        features.append(snapshot.current_ratio if pd.notna(snapshot.current_ratio) else 1.5)

        # Per-share metrics
        features.append(snapshot.trailing_eps if pd.notna(snapshot.trailing_eps) else 0.0)
        features.append(snapshot.book_value if pd.notna(snapshot.book_value) else 0.0)

        # Cash flow metrics (normalized by market cap)
        market_cap = snapshot.market_cap if pd.notna(snapshot.market_cap) and snapshot.market_cap > 0 else 1e9
        fcf = snapshot.free_cashflow if pd.notna(snapshot.free_cashflow) else 0.0
        ocf = snapshot.operating_cashflow if pd.notna(snapshot.operating_cashflow) else 0.0
        features.append(fcf / market_cap)  # FCF yield
        features.append(ocf / market_cap)  # OCF yield

        # Sector one-hot encoding (11)
        sectors = [
            'Technology', 'Healthcare', 'Financial Services', 'Consumer Cyclical',
            'Industrials', 'Communication Services', 'Consumer Defensive',
            'Energy', 'Utilities', 'Real Estate', 'Basic Materials'
        ]
        for s in sectors:
            features.append(1.0 if sector == s else 0.0)

        return np.array(features)

    def predict_with_mc_dropout(
        self,
        ticker: str,
        current_price: float,
        n_samples: int = 100
    ) -> Optional[dict]:
        """
        Make prediction with MC Dropout confidence estimation.

        Parameters
        ----------
        ticker : str
            Stock ticker
        current_price : float
            Current stock price
        n_samples : int
            Number of MC Dropout samples

        Returns
        -------
        dict or None
            Prediction result or None if insufficient data
        """
        # Get latest snapshots
        snapshots = self.get_latest_snapshots(ticker)

        if snapshots is None:
            return {
                'suitable': False,
                'error': 'Insufficient historical data (need 4 snapshots)',
                'reason': 'Missing historical snapshots'
            }

        # Get price history for most recent snapshot
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        latest_snapshot_id = int(snapshots.iloc[-1]['id'])
        cursor.execute('''
            SELECT date, close, volume
            FROM price_history
            WHERE snapshot_id = ?
            ORDER BY date
        ''', (latest_snapshot_id,))
        price_history = cursor.fetchall()
        conn.close()

        if len(price_history) < 60:
            return {
                'suitable': False,
                'error': f'Insufficient price history (need 60 days, have {len(price_history)})',
                'reason': 'Missing price history'
            }

        # Extract features
        temporal = self._extract_temporal(snapshots, price_history)
        if temporal is None:
            return {
                'suitable': False,
                'error': 'Failed to extract temporal features',
                'reason': 'Insufficient price data'
            }

        static = self._extract_static(snapshots.iloc[-1], snapshots.iloc[0].sector)

        # Convert to tensors
        temporal_tensor = torch.FloatTensor(temporal).unsqueeze(0).to(self.device)
        static_tensor = torch.FloatTensor(static).unsqueeze(0).to(self.device)

        # Enable dropout for MC sampling
        for module in self.model.modules():
            if isinstance(module, nn.Dropout):
                module.train()
            elif isinstance(module, nn.BatchNorm1d):
                module.eval()

        # Run MC Dropout
        predictions = []
        with torch.no_grad():
            for _ in range(n_samples):
                pred = self.model(temporal_tensor, static_tensor)
                predictions.append(pred.cpu().numpy()[0, 0])

        predictions = np.array(predictions)
        mean_return = float(np.mean(predictions))
        std_return = float(np.std(predictions))

        # Calculate confidence intervals
        lower_bound = float(mean_return - 2 * std_return)
        upper_bound = float(mean_return + 2 * std_return)

        # Calculate fair value
        fair_value = current_price * (1 + mean_return)
        upside = ((fair_value / current_price) - 1) * 100 if current_price > 0 else 0
        margin_of_safety = mean_return

        # Determine confidence level
        if std_return < 0.05:  # < 5% std
            confidence = 'high'
        elif std_return < 0.15:  # < 15% std
            confidence = 'medium'
        else:
            confidence = 'low'

        return {
            'suitable': True,
            'fair_value': float(fair_value),
            'current_price': float(current_price),
            'upside': float(upside),
            'margin_of_safety': float(margin_of_safety),
            'confidence': confidence,
            'details': {
                'expected_return_3y': float(mean_return * 100),  # Convert to percentage
                'confidence_std': float(std_return),
                'confidence_lower_95': float(lower_bound * 100),
                'confidence_upper_95': float(upper_bound * 100),
                'mc_dropout_samples': n_samples,
                'model': 'LSTM/Transformer 3-Year',
                'hit_rate': 78.64,  # From evaluation
                'correlation': 44.2  # From evaluation
            }
        }


def save_to_database(conn: sqlite3.Connection, ticker: str, result: dict):
    """Save prediction result to valuation_results table."""

    cursor = conn.cursor()

    if result.get('suitable'):
        # Successful prediction
        details_json = json.dumps(result.get('details', {}))

        cursor.execute('''
            INSERT INTO valuation_results (
                ticker, model_name, fair_value, current_price,
                margin_of_safety, upside_pct, suitable,
                confidence, details_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ticker,
            'nn_3y',
            result['fair_value'],
            result['current_price'],
            result['margin_of_safety'],
            result['upside'],
            True,
            result['confidence'],
            details_json
        ))
    else:
        # Failed prediction
        cursor.execute('''
            INSERT INTO valuation_results (
                ticker, model_name, suitable, error_message, failure_reason
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            ticker,
            'nn_3y',
            False,
            result.get('error', 'Unknown error'),
            result.get('reason', 'Unknown reason')
        ))

    conn.commit()


def main():
    """Run neural network predictions on all stocks in database."""

    print('🧠 Running 3-Year Neural Network Predictions')
    print('=' * 60)
    print('Model: LSTM/Transformer (78.64% hit rate, 44.2% correlation)')
    print('=' * 60)

    # Initialize predictor
    print(f'\n🔧 Initializing neural network predictor...')
    predictor = NeuralNetworkPredictor()

    # Get list of tickers from database
    print(f'\n📂 Loading tickers from database...')
    conn = sqlite3.connect(predictor.db_path)
    query = 'SELECT DISTINCT ticker FROM current_stock_data WHERE current_price IS NOT NULL'
    tickers = [row[0] for row in conn.execute(query).fetchall()]
    print(f'   Found {len(tickers)} tickers with price data')

    # Statistics
    stats = {
        'success': 0,
        'insufficient_data': 0,
        'error': 0
    }

    # Run predictions
    print(f'\n🔄 Running predictions...')

    for i, ticker in enumerate(tickers):
        try:
            # Get current price from database
            cursor = conn.execute(
                'SELECT current_price FROM current_stock_data WHERE ticker = ?',
                (ticker,)
            )
            row = cursor.fetchone()

            if not row or not row[0]:
                stats['error'] += 1
                continue

            current_price = row[0]

            # Run prediction
            result = predictor.predict_with_mc_dropout(ticker, current_price)

            # Save to database
            save_to_database(conn, ticker, result)

            if result.get('suitable'):
                stats['success'] += 1
            else:
                if 'insufficient' in result.get('error', '').lower():
                    stats['insufficient_data'] += 1
                else:
                    stats['error'] += 1

        except Exception as e:
            print(f'   [{i+1}/{len(tickers)}] {ticker}: Error - {str(e)}')
            # Save error to database
            error_result = {
                'suitable': False,
                'error': str(e),
                'reason': f'Unexpected error: {type(e).__name__}'
            }
            save_to_database(conn, ticker, error_result)
            stats['error'] += 1

        # Progress update
        if (i + 1) % 50 == 0:
            print(f'   [{i+1}/{len(tickers)}] Processed {ticker}...')

    conn.close()

    # Summary
    print(f'\n✅ Neural network predictions complete!')
    print('=' * 60)
    print(f'📊 Results:')
    print(f'   Success:           {stats["success"]:3}')
    print(f'   Insufficient data: {stats["insufficient_data"]:3}')
    print(f'   Errors:            {stats["error"]:3}')
    print(f'   Total:             {len(tickers):3}')
    print()
    print(f'💾 Saved to database: data/stock_data.db (valuation_results table)')
    print('💡 Run regenerate_dashboard_html.py to update the dashboard HTML')

    return 0


if __name__ == '__main__':
    sys.exit(main())

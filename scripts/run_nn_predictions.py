#!/usr/bin/env python3
"""
Run Phase 2 LSTM/Transformer predictions on all stocks in database.

This script:
- Loads the trained Phase 2 single-horizon model (78.64% hit rate)
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
    """Runs Phase 2 LSTM/Transformer predictions on dashboard stocks."""

    def __init__(self):
        self.project_root = project_root
        self.model_path = project_root / 'neural_network' / 'training' / 'best_model.pt'
        self.db_path = project_root / 'data' / 'stock_data.db'
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        print(f'Loading Phase 2 model from {self.model_path}')
        self.model = self._load_model()

    def _load_model(self) -> LSTMTransformerNetwork:
        """Load trained Phase 2 model with correct dimensions."""
        model = LSTMTransformerNetwork(
            temporal_features=11,
            static_features=22,
            lstm_hidden=256,
            transformer_heads=8,
            dropout_rate=0.3
        )

        state_dict = torch.load(self.model_path, map_location=self.device)
        model.load_state_dict(state_dict)
        model.to(self.device)
        model.eval()

        print('✓ Model loaded successfully')
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

        query = '''
            SELECT
                a.symbol,
                a.sector,
                s.snapshot_date,
                s.market_cap,
                s.pe_ratio,
                s.pb_ratio,
                s.profit_margins,
                s.operating_margins,
                s.return_on_equity,
                s.revenue_growth,
                s.earnings_growth,
                s.debt_to_equity,
                s.current_ratio,
                s.free_cashflow,
                s.beta
            FROM snapshots s
            JOIN assets a ON s.asset_id = a.id
            WHERE a.symbol = ?
                AND s.pe_ratio IS NOT NULL
                AND s.pb_ratio IS NOT NULL
            ORDER BY s.snapshot_date DESC
            LIMIT ?
        '''

        df = pd.read_sql_query(query, conn, params=(ticker, num_snapshots))
        conn.close()

        if len(df) < num_snapshots:
            return None

        # Reverse to get chronological order (oldest first)
        return df.iloc[::-1].reset_index(drop=True)

    def _extract_temporal(self, snapshots: pd.DataFrame) -> np.ndarray:
        """
        Extract temporal features from sequence of snapshots.

        Must match training feature extraction exactly!

        Parameters
        ----------
        snapshots : pd.DataFrame
            Sequence of snapshots in chronological order

        Returns
        -------
        np.ndarray
            Temporal features, shape (num_snapshots, 11)
        """
        temporal_features = []

        for _, snapshot in snapshots.iterrows():
            features = [
                np.log10(snapshot.market_cap + 1) if pd.notna(snapshot.market_cap) else 0.0,
                snapshot.pe_ratio if pd.notna(snapshot.pe_ratio) else 0.0,
                snapshot.pb_ratio if pd.notna(snapshot.pb_ratio) else 0.0,
                snapshot.profit_margins if pd.notna(snapshot.profit_margins) else 0.0,
                snapshot.operating_margins if pd.notna(snapshot.operating_margins) else 0.0,
                snapshot.return_on_equity if pd.notna(snapshot.return_on_equity) else 0.0,
                snapshot.revenue_growth if pd.notna(snapshot.revenue_growth) else 0.0,
                snapshot.earnings_growth if pd.notna(snapshot.earnings_growth) else 0.0,
                snapshot.debt_to_equity if pd.notna(snapshot.debt_to_equity) else 0.0,
                snapshot.current_ratio if pd.notna(snapshot.current_ratio) else 0.0,
                np.log10(abs(snapshot.free_cashflow) + 1) if pd.notna(snapshot.free_cashflow) else 0.0,
            ]
            temporal_features.append(features)

        return np.array(temporal_features)

    def _extract_static(self, snapshot: pd.Series, sector: str) -> np.ndarray:
        """
        Extract static features from most recent snapshot.

        Must match training feature extraction exactly!

        Parameters
        ----------
        snapshot : pd.Series
            Most recent snapshot
        sector : str
            Company sector

        Returns
        -------
        np.ndarray
            Static features, shape (22,)
        """
        features = []

        # Valuation ratios (2)
        features.extend([
            snapshot.pe_ratio if pd.notna(snapshot.pe_ratio) else 0.0,
            snapshot.pb_ratio if pd.notna(snapshot.pb_ratio) else 0.0,
        ])

        # Profitability (3)
        features.extend([
            snapshot.profit_margins if pd.notna(snapshot.profit_margins) else 0.0,
            snapshot.operating_margins if pd.notna(snapshot.operating_margins) else 0.0,
            snapshot.return_on_equity if pd.notna(snapshot.return_on_equity) else 0.0,
        ])

        # Growth (2)
        features.extend([
            snapshot.revenue_growth if pd.notna(snapshot.revenue_growth) else 0.0,
            snapshot.earnings_growth if pd.notna(snapshot.earnings_growth) else 0.0,
        ])

        # Financial health (2)
        features.extend([
            snapshot.debt_to_equity if pd.notna(snapshot.debt_to_equity) else 0.0,
            snapshot.current_ratio if pd.notna(snapshot.current_ratio) else 0.0,
        ])

        # Beta (1)
        features.append(snapshot.beta if pd.notna(snapshot.beta) else 1.0)

        # Market cap log (1)
        market_cap_log = np.log10(snapshot.market_cap + 1) if pd.notna(snapshot.market_cap) else 0.0
        features.append(market_cap_log)

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

        # Extract features
        temporal = self._extract_temporal(snapshots)
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
                'expected_return_1y': float(mean_return * 100),  # Convert to percentage
                'confidence_std': float(std_return),
                'confidence_lower_95': float(lower_bound * 100),
                'confidence_upper_95': float(upper_bound * 100),
                'mc_dropout_samples': n_samples,
                'model': 'LSTM/Transformer Phase 2',
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
            'single_horizon_nn',
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
            'single_horizon_nn',
            False,
            result.get('error', 'Unknown error'),
            result.get('reason', 'Unknown reason')
        ))

    conn.commit()


def main():
    """Run neural network predictions on all stocks in database."""

    print('🧠 Running Phase 2 Neural Network Predictions')
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

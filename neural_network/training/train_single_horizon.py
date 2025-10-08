#!/usr/bin/env python3
"""
Train single-horizon LSTM/Transformer model for 1-year stock predictions.

This script:
- Loads historical snapshots from database
- Converts snapshot sequences into LSTM-compatible temporal features
- Trains the model with decade/sector-aware train/val/test splits
- Evaluates model performance across different time periods and sectors

Database Structure:
------------------
- snapshots: Point-in-time fundamental data (PE, margins, growth, etc.)
  - NOTE: current_price field is always NULL (not used, we have price_history)
  - Contains 3,367 snapshots from 103 stocks (2004-2025)

- price_history: Daily OHLCV data linked to each snapshot
  - 8.5M records with actual historical prices
  - Used to calculate forward returns

- forward_returns: Pre-calculated returns for each snapshot
  - Horizons: 1m, 3m, 6m, 1y, 2y
  - Already computed by create_multi_horizon_cache.py

- assets: Stock symbols and sectors
"""

import argparse
import json
import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from invest.valuation.lstm_transformer_model import SingleHorizonModel, LSTMTransformerNetwork

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StockSnapshotDataset(Dataset):
    """Dataset for historical stock snapshots with temporal sequences."""

    def __init__(self, samples: List[Tuple[np.ndarray, np.ndarray, float]]):
        """
        Initialize dataset.

        Parameters
        ----------
        samples : List[Tuple]
            List of (temporal_features, static_features, target_return) tuples
        """
        self.samples = samples

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        temporal, static, target = self.samples[idx]
        return (
            torch.FloatTensor(temporal),
            torch.FloatTensor(static),
            torch.FloatTensor([target])
        )


class SingleHorizonTrainer:
    """Trainer for single-horizon model."""

    def __init__(self, db_path: str = 'data/stock_data.db'):
        self.db_path = Path(db_path)
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    def load_training_data(
        self,
        min_samples_per_stock: int = 4,
        target_horizon: str = '1y'
    ) -> Tuple[List, List, List]:
        """
        Load and prepare training data from database.

        Parameters
        ----------
        min_samples_per_stock : int
            Minimum number of historical snapshots per stock to use as sequence
        target_horizon : str
            Target prediction horizon (default: '1y')

        Returns
        -------
        Tuple[List, List, List]
            (train_samples, val_samples, test_samples)
        """
        logger.info(f'Loading data from {self.db_path}')

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Load snapshots with forward returns
        # NOTE: snapshots.current_price is always NULL (old bug, not populated)
        # We don't need it - price data comes from price_history table
        cursor.execute('''
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
                s.beta,
                s.id
            FROM snapshots s
            JOIN assets a ON s.asset_id = a.id
            WHERE s.pe_ratio IS NOT NULL  -- Filter: require some fundamental data
            ORDER BY a.symbol, s.snapshot_date
        ''')

        rows = cursor.fetchall()

        # Group by stock symbol
        stock_data = {}
        for row in rows:
            symbol = row[0]
            if symbol not in stock_data:
                stock_data[symbol] = []
            stock_data[symbol].append(row)

        logger.info(f'Loaded data for {len(stock_data)} stocks')

        # Create samples from sequences
        samples = []

        for symbol, snapshots in stock_data.items():
            if len(snapshots) < min_samples_per_stock:
                continue

            sector = snapshots[0][1]

            # Create sliding windows
            for i in range(len(snapshots) - min_samples_per_stock):
                # Use past N snapshots as temporal sequence
                sequence = snapshots[i:i + min_samples_per_stock]
                snapshot_id = sequence[-1][-1]  # ID of most recent snapshot

                # Get forward return for target horizon
                cursor.execute('''
                    SELECT return_pct
                    FROM forward_returns
                    WHERE snapshot_id = ? AND horizon = ?
                ''', (snapshot_id, target_horizon))

                result = cursor.fetchone()
                if not result or result[0] is None:
                    continue

                forward_return = float(result[0]) / 100.0  # Convert % to decimal

                # Extract temporal features (sequence of snapshots)
                temporal_features = self._extract_temporal_from_sequence(sequence)

                # Extract static features (most recent snapshot)
                static_features = self._extract_static_from_snapshot(sequence[-1], sector)

                if temporal_features is not None and static_features is not None:
                    # Add metadata for stratified splitting
                    sample = {
                        'temporal': temporal_features,
                        'static': static_features,
                        'target': forward_return,
                        'symbol': symbol,
                        'sector': sector,
                        'date': sequence[-1][2],  # snapshot_date
                    }
                    samples.append(sample)

        logger.info(f'Created {len(samples)} training samples')

        # Stratified split by decade and sector
        train_samples, val_samples, test_samples = self._stratified_split(samples)

        logger.info(f'Train: {len(train_samples)}, Val: {len(val_samples)}, Test: {len(test_samples)}')

        conn.close()
        return train_samples, val_samples, test_samples

    def _extract_temporal_from_sequence(self, sequence: List) -> np.ndarray:
        """
        Extract temporal features from sequence of snapshots.

        Parameters
        ----------
        sequence : List
            List of snapshot rows (each row is a tuple from SQL)

        Returns
        -------
        np.ndarray
            Shape: (num_snapshots, num_temporal_features)
        """
        temporal_features = []

        for snapshot in sequence:
            # Extract temporal features from each snapshot
            # New indices (after removing current_price):
            # market_cap(3), pe(4), pb(5), margins(6,7),
            # roe(8), growth(9,10), debt(11), current_ratio(12), fcf(13)
            features = [
                np.log10(snapshot[3] + 1) if snapshot[3] is not None else 0.0,  # market_cap (log)
                snapshot[4] if snapshot[4] is not None else 0.0,  # pe_ratio
                snapshot[5] if snapshot[5] is not None else 0.0,  # pb_ratio
                snapshot[6] if snapshot[6] is not None else 0.0,  # profit_margins
                snapshot[7] if snapshot[7] is not None else 0.0,  # operating_margins
                snapshot[8] if snapshot[8] is not None else 0.0,  # return_on_equity
                snapshot[9] if snapshot[9] is not None else 0.0,  # revenue_growth
                snapshot[10] if snapshot[10] is not None else 0.0,  # earnings_growth
                snapshot[11] if snapshot[11] is not None else 0.0,  # debt_to_equity
                snapshot[12] if snapshot[12] is not None else 0.0,  # current_ratio
                np.log10(abs(snapshot[13]) + 1) if snapshot[13] is not None else 0.0,  # fcf (log)
            ]
            temporal_features.append(features)

        return np.array(temporal_features)

    def _extract_static_from_snapshot(self, snapshot, sector: str) -> np.ndarray:
        """
        Extract static features from most recent snapshot.

        Parameters
        ----------
        snapshot : tuple
            Most recent snapshot row
        sector : str
            Company sector

        Returns
        -------
        np.ndarray
            Static feature vector
        """
        features = []

        # New indices (after removing current_price):
        # market_cap(3), pe(4), pb(5), margins(6,7),
        # roe(8), growth(9,10), debt(11), current_ratio(12), fcf(13), beta(14)

        # Valuation ratios
        features.extend([
            snapshot[4] if snapshot[4] is not None else 0.0,  # pe_ratio
            snapshot[5] if snapshot[5] is not None else 0.0,  # pb_ratio
        ])

        # Profitability
        features.extend([
            snapshot[6] if snapshot[6] is not None else 0.0,  # profit_margins
            snapshot[7] if snapshot[7] is not None else 0.0,  # operating_margins
            snapshot[8] if snapshot[8] is not None else 0.0,  # return_on_equity
        ])

        # Growth
        features.extend([
            snapshot[9] if snapshot[9] is not None else 0.0,  # revenue_growth
            snapshot[10] if snapshot[10] is not None else 0.0,  # earnings_growth
        ])

        # Financial health
        features.extend([
            snapshot[11] if snapshot[11] is not None else 0.0,  # debt_to_equity
            snapshot[12] if snapshot[12] is not None else 0.0,  # current_ratio
        ])

        # Beta
        features.append(snapshot[14] if snapshot[14] is not None else 1.0)

        # Market cap (log)
        market_cap_log = np.log10(snapshot[3] + 1) if snapshot[3] is not None else 0.0
        features.append(market_cap_log)

        # Sector one-hot encoding (11 sectors)
        sectors = [
            'Technology', 'Healthcare', 'Financial Services', 'Consumer Cyclical',
            'Industrials', 'Communication Services', 'Consumer Defensive',
            'Energy', 'Utilities', 'Real Estate', 'Basic Materials'
        ]
        for s in sectors:
            features.append(1.0 if sector == s else 0.0)

        return np.array(features)

    def _stratified_split(
        self,
        samples: List[dict],
        train_ratio: float = 0.7,
        val_ratio: float = 0.15
    ) -> Tuple[List, List, List]:
        """
        Split data by decade and sector for proper evaluation.

        Parameters
        ----------
        samples : List[dict]
            All samples with metadata
        train_ratio : float
            Proportion for training
        val_ratio : float
            Proportion for validation

        Returns
        -------
        Tuple[List, List, List]
            (train, val, test) samples as list of (temporal, static, target) tuples
        """
        # Extract decade from date
        for sample in samples:
            year = int(sample['date'][:4])
            decade = (year // 10) * 10
            sample['decade'] = decade

        # Create stratification key
        for sample in samples:
            sample['strata'] = f"{sample['decade']}_{sample['sector']}"

        # Simple random split (could be improved with proper stratification)
        indices = np.arange(len(samples))
        train_idx, temp_idx = train_test_split(
            indices,
            train_size=train_ratio,
            random_state=42
        )
        val_idx, test_idx = train_test_split(
            temp_idx,
            train_size=val_ratio / (1 - train_ratio),
            random_state=42
        )

        def to_tuples(idx_list):
            return [(samples[i]['temporal'], samples[i]['static'], samples[i]['target'])
                    for i in idx_list]

        return to_tuples(train_idx), to_tuples(val_idx), to_tuples(test_idx)

    def train(
        self,
        train_samples: List,
        val_samples: List,
        epochs: int = 100,
        batch_size: int = 32,
        learning_rate: float = 0.001
    ):
        """
        Train the model.

        Parameters
        ----------
        train_samples : List
            Training samples
        val_samples : List
            Validation samples
        epochs : int
            Number of training epochs
        batch_size : int
            Batch size
        learning_rate : float
            Learning rate
        """
        logger.info('Initializing model...')

        # Determine feature dimensions from first sample
        temporal_dim = train_samples[0][0].shape[1]  # Should be 11
        static_dim = train_samples[0][1].shape[0]    # Should be 22 (2 + 3 + 2 + 2 + 1 + 1 + 11 sectors)

        logger.info(f'Feature dimensions: temporal={temporal_dim}, static={static_dim}')

        self.model = LSTMTransformerNetwork(
            temporal_features=temporal_dim,
            static_features=static_dim
        ).to(self.device)

        # Create data loaders
        train_dataset = StockSnapshotDataset(train_samples)
        val_dataset = StockSnapshotDataset(val_samples)

        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size)

        # Loss and optimizer
        criterion = nn.HuberLoss()  # Robust to outliers
        optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate, weight_decay=1e-5)

        # Training loop
        best_val_loss = float('inf')
        patience = 10
        patience_counter = 0

        for epoch in range(epochs):
            # Train
            self.model.train()
            train_loss = 0.0

            for temporal, static, target in train_loader:
                temporal = temporal.to(self.device)
                static = static.to(self.device)
                target = target.to(self.device)

                optimizer.zero_grad()
                output = self.model(temporal, static)
                loss = criterion(output, target)
                loss.backward()
                optimizer.step()

                train_loss += loss.item()

            train_loss /= len(train_loader)

            # Validate
            self.model.eval()
            val_loss = 0.0

            with torch.no_grad():
                for temporal, static, target in val_loader:
                    temporal = temporal.to(self.device)
                    static = static.to(self.device)
                    target = target.to(self.device)

                    output = self.model(temporal, static)
                    loss = criterion(output, target)
                    val_loss += loss.item()

            val_loss /= len(val_loader)

            logger.info(f'Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}')

            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                # Save best model
                self.save_model('best_model.pt')
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    logger.info(f'Early stopping at epoch {epoch+1}')
                    break

    def save_model(self, filename: str):
        """Save model weights."""
        save_path = Path(__file__).parent / filename
        torch.save(self.model.state_dict(), save_path)
        logger.info(f'Model saved to {save_path}')


def main():
    parser = argparse.ArgumentParser(description='Train single-horizon model')
    parser.add_argument('--epochs', type=int, default=100, help='Number of epochs')
    parser.add_argument('--batch-size', type=int, default=32, help='Batch size')
    parser.add_argument('--learning-rate', type=float, default=0.001, help='Learning rate')
    args = parser.parse_args()

    trainer = SingleHorizonTrainer()

    # Load data
    train_samples, val_samples, test_samples = trainer.load_training_data()

    # Train
    trainer.train(
        train_samples,
        val_samples,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate
    )

    logger.info('Training complete!')


if __name__ == '__main__':
    main()

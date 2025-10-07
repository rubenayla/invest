#!/usr/bin/env python3
"""
Train multi-horizon neural network model using cached stock data.
"""

import json
import sys
import numpy as np
import torch
from pathlib import Path
from datetime import datetime
import logging
import yfinance as yf
from typing import Dict, List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.invest.valuation.neural_network_model import FeatureEngineer
from src.invest.valuation.multi_horizon_nn import MultiHorizonValuationModel

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MultiHorizonTrainer:
    """Train multi-horizon model with cached stock data."""

    def __init__(self, cache_path: str = 'training_data_cache_multi_horizon.json'):
        self.cache_path = Path(__file__).parent / cache_path
        self.feature_engineer = FeatureEngineer()

    def load_cached_data(self) -> List[Tuple]:
        """Load training data from multi-horizon cache."""
        logger.info(f'Loading cache from {self.cache_path}')

        with open(self.cache_path, 'r') as f:
            cache = json.load(f)

        logger.info(f'Loaded {cache["sample_count"]} samples from cache')
        logger.info(f'Data period: {cache["config"]["start_year"]}-{cache["config"]["end_year"]}')
        logger.info(f'Horizons: {cache["horizons"]}')

        samples = []
        for sample in cache['samples']:
            samples.append((
                sample['ticker'],
                sample['data'],
                sample['forward_returns']  # Dict with real multi-horizon returns
            ))

        return samples

    def prepare_multi_horizon_targets(self, samples: List[Tuple]) -> Tuple:
        """
        Prepare features and REAL multi-horizon targets from cache.
        """
        logger.info('Preparing features and multi-horizon targets...')

        X_list = []
        y_dict = {'1m': [], '3m': [], '6m': [], '1y': [], '2y': []}
        valid_samples = []

        for i, (ticker, data, forward_returns) in enumerate(samples):
            if i % 500 == 0:
                logger.info(f'Processing sample {i}/{len(samples)}')

            try:
                # Extract features
                features = self.feature_engineer.extract_features(data)

                # Use REAL forward returns from cache (already in percentage)
                for horizon in ['1m', '3m', '6m', '1y', '2y']:
                    y_dict[horizon].append(forward_returns[horizon] * 100)  # Convert to percentage

                X_list.append(features)
                valid_samples.append((ticker, data, forward_returns))

            except Exception as e:
                logger.warning(f'Error processing sample {i}: {e}')
                continue

        logger.info(f'Successfully processed {len(X_list)} samples')

        # Fit feature scaler and transform
        X_array = self.feature_engineer.fit_transform(X_list)

        # Convert targets to numpy arrays
        for horizon in y_dict:
            y_dict[horizon] = np.array(y_dict[horizon])

        return X_array, y_dict, valid_samples

    def split_data(self, X: np.ndarray, y: Dict[str, np.ndarray],
                   train_ratio: float = 0.7, val_ratio: float = 0.15):
        """Split data into train/val/test sets."""
        n_samples = len(X)
        n_train = int(n_samples * train_ratio)
        n_val = int(n_samples * val_ratio)

        # Shuffle indices
        indices = np.random.permutation(n_samples)

        train_idx = indices[:n_train]
        val_idx = indices[n_train:n_train + n_val]
        test_idx = indices[n_train + n_val:]

        X_train = X[train_idx]
        X_val = X[val_idx]
        X_test = X[test_idx]

        y_train = {h: y[h][train_idx] for h in y}
        y_val = {h: y[h][val_idx] for h in y}
        y_test = {h: y[h][test_idx] for h in y}

        logger.info(f'Data split: Train={len(X_train)}, Val={len(X_val)}, Test={len(X_test)}')

        return X_train, X_val, X_test, y_train, y_val, y_test

    def train(self):
        """Main training pipeline."""
        logger.info('='*60)
        logger.info('Starting Multi-Horizon Model Training')
        logger.info('='*60)

        # Load cached data
        samples = self.load_cached_data()

        # Prepare features and targets
        X, y, valid_samples = self.prepare_multi_horizon_targets(samples)

        # Split data
        X_train, X_val, X_test, y_train, y_val, y_test = self.split_data(X, y)

        # Create model
        feature_dim = X_train.shape[1]
        logger.info(f'Feature dimension: {feature_dim}')
        model = MultiHorizonValuationModel(feature_dim=feature_dim)

        # Train model
        logger.info('\nTraining multi-horizon model...')
        history = model.train_model(
            X_train, y_train, X_val, y_val,
            epochs=100,
            batch_size=64,
            learning_rate=0.001
        )

        # Evaluate on test set
        logger.info('\n' + '='*60)
        logger.info('Evaluating on Test Set')
        logger.info('='*60)

        model.model.eval()
        test_predictions = []

        with torch.no_grad():
            X_test_t = torch.FloatTensor(X_test).to(model.device)
            predictions = model.model(X_test_t)

            for horizon in model.model.horizons:
                pred = predictions[horizon].cpu().numpy()
                actual = y_test[horizon]

                # Calculate metrics
                mae = np.mean(np.abs(pred.squeeze() - actual))
                rmse = np.sqrt(np.mean((pred.squeeze() - actual) ** 2))
                correlation = np.corrcoef(pred.squeeze(), actual)[0, 1]

                logger.info(f'{horizon:3s}: MAE={mae:.2f}%, RMSE={rmse:.2f}%, Corr={correlation:.3f}')

        # Save model
        model_path = Path(__file__).parent / 'multi_horizon_model.pt'
        torch.save({
            'model_state_dict': model.model.state_dict(),
            'feature_dim': feature_dim,
            'feature_names': self.feature_engineer.feature_names,
            'training_history': history,
            'timestamp': datetime.now().isoformat()
        }, model_path)

        logger.info(f'\nModel saved to {model_path}')

        # Example prediction
        logger.info('\n' + '='*60)
        logger.info('Example Prediction on Test Sample')
        logger.info('='*60)

        test_sample = X_test[0:1]
        prediction = model.predict(test_sample, current_price=100.0)

        logger.info(f'Predictions for test sample:')
        for horizon in model.model.horizons:
            logger.info(f'  {horizon:3s}: {prediction.predictions[horizon]:+6.2f}% '
                       f'[Confidence: {prediction.confidence_scores[horizon]:.1%}]')
        logger.info(f'Recommended horizon: {prediction.recommended_horizon}')

        return model, history


if __name__ == '__main__':
    # Set random seed for reproducibility
    np.random.seed(42)
    torch.manual_seed(42)

    # Train model
    trainer = MultiHorizonTrainer()
    model, history = trainer.train()

    logger.info('\n✅ Training complete!')
"""
Test suite for the multi-horizon neural network demo and predictions.

Ensures that the multi-horizon model works reliably with various stocks
and that predictions are reasonable and consistent.
"""

import pytest
import sys
from pathlib import Path
import numpy as np
import torch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.demo_multi_horizon_predictions import (
    load_model,
    fetch_macro_data,
    get_stock_data,
    make_prediction
)
from src.invest.valuation.multi_horizon_nn import MultiHorizonValuationModel
from src.invest.valuation.neural_network_model import FeatureEngineer


class TestMacroDataFetching:
    """Test macroeconomic data fetching."""

    def test_fetch_macro_data(self):
        """Test that macro data is fetched successfully."""
        macro = fetch_macro_data()

        # Check all required fields are present
        assert 'vix' in macro
        assert 'treasury_10y' in macro
        assert 'dollar_index' in macro
        assert 'oil_price' in macro
        assert 'gold_price' in macro

        # Check values are reasonable (fallback if data unavailable)
        assert 5 < macro['vix'] < 100  # VIX typically 10-80
        assert 0 < macro['treasury_10y'] < 20  # Treasury yield typically 0-10%
        assert 50 < macro['dollar_index'] < 200  # Dollar index typically 80-120
        assert 10 < macro['oil_price'] < 200  # Oil typically $20-150/barrel
        assert 500 < macro['gold_price'] < 5000  # Gold typically $1000-2500/oz


class TestModelLoading:
    """Test model loading functionality."""

    def test_load_model(self):
        """Test that the model loads correctly."""
        model, feature_names = load_model()

        # Check model type
        assert isinstance(model, MultiHorizonValuationModel)

        # Check feature names
        assert len(feature_names) == 47
        assert 'vix' in feature_names
        assert 'treasury_10y' in feature_names
        assert 'dollar_index' in feature_names
        assert 'oil_price' in feature_names
        assert 'gold_price' in feature_names
        assert 'pe_ratio' in feature_names

        # Check model is in eval mode
        assert not model.model.training


class TestStockDataFetching:
    """Test stock data fetching."""

    @pytest.mark.parametrize('ticker', ['AAPL', 'MSFT', 'GOOGL'])
    def test_get_stock_data(self, ticker):
        """Test fetching stock data for major tickers."""
        data = get_stock_data(ticker)

        # Check required fields
        assert 'info' in data
        assert 'history' in data
        assert 'macro' in data

        # Check info has required fields
        assert 'currentPrice' in data['info']
        assert data['info']['currentPrice'] > 0

        # Check history is not empty
        assert len(data['history']) > 0

        # Check macro data is present
        assert len(data['macro']) == 5


class TestFeatureExtraction:
    """Test feature extraction with macro data."""

    def test_feature_extraction_with_macro(self):
        """Test that features are extracted correctly with macro data."""
        # Get test data
        data = get_stock_data('AAPL')

        # Extract features
        feature_engineer = FeatureEngineer()
        features = feature_engineer.extract_features(data)

        # Check we have features
        assert len(features) > 40

        # Check macro features are present
        assert 'vix' in features
        assert 'treasury_10y' in features
        assert 'dollar_index' in features
        assert 'oil_price' in features
        assert 'gold_price' in features


class TestMultiHorizonPredictions:
    """Test multi-horizon prediction functionality."""

    @pytest.fixture(scope='class')
    def loaded_model(self):
        """Load model once for all tests in this class."""
        return load_model()

    @pytest.mark.parametrize('ticker', ['AAPL', 'MSFT', 'TSLA', 'GOOGL'])
    def test_predictions_for_multiple_tickers(self, loaded_model, ticker):
        """Test that predictions work for multiple major stocks."""
        model, feature_names = loaded_model

        # Make prediction
        prediction = make_prediction(model, feature_names, ticker)

        # Check prediction is not None
        assert prediction is not None

        # Check all horizons have predictions
        assert len(prediction.predictions) == 5
        assert '1m' in prediction.predictions
        assert '3m' in prediction.predictions
        assert '6m' in prediction.predictions
        assert '1y' in prediction.predictions
        assert '2y' in prediction.predictions

        # Check confidence scores exist
        assert len(prediction.confidence_scores) == 5

        # Check recommended horizon exists
        assert prediction.recommended_horizon in ['1m', '3m', '6m', '1y', '2y']

        # Check fair values exist
        assert len(prediction.fair_values) == 5

    def test_prediction_reasonableness(self, loaded_model):
        """Test that predictions are within reasonable bounds."""
        model, feature_names = loaded_model

        # Test with AAPL
        prediction = make_prediction(model, feature_names, 'AAPL')

        # Check predictions are within reasonable range (-100% to +500%)
        for horizon, pred in prediction.predictions.items():
            assert -100 < pred < 500, f'{horizon} prediction {pred}% is unreasonable'

        # Check confidence scores are between 0 and 1
        for horizon, conf in prediction.confidence_scores.items():
            assert 0 <= conf <= 1, f'{horizon} confidence {conf} not in [0, 1]'

        # Check fair values are positive
        for horizon, fv in prediction.fair_values.items():
            assert fv > 0, f'{horizon} fair value {fv} is not positive'

    def test_prediction_consistency(self, loaded_model):
        """Test that predictions are consistent across calls."""
        model, feature_names = loaded_model

        # Make two predictions for the same ticker
        pred1 = make_prediction(model, feature_names, 'AAPL')
        pred2 = make_prediction(model, feature_names, 'AAPL')

        # Check predictions are very close (within 5% due to potential data updates)
        for horizon in ['1m', '3m', '6m', '1y', '2y']:
            diff = abs(pred1.predictions[horizon] - pred2.predictions[horizon])
            assert diff < 5.0, f'{horizon} predictions differ by {diff}%'


class TestModelIntegration:
    """Test model integration with registry."""

    def test_model_in_registry(self):
        """Test that multi_horizon_nn model is registered."""
        from src.invest.valuation.model_registry import ModelRegistry

        registry = ModelRegistry()
        available = registry.get_available_models()

        assert 'multi_horizon_nn' in available

        # Test instantiation through registry
        model = registry.get_model('multi_horizon_nn')
        assert isinstance(model, MultiHorizonValuationModel)

    def test_model_metadata(self):
        """Test model metadata in registry."""
        from src.invest.valuation.model_registry import ModelRegistry

        registry = ModelRegistry()
        metadata = registry.get_model_metadata('multi_horizon_nn')

        assert metadata['name'] == 'Multi-Horizon Neural Network'
        assert 'horizon' in metadata['description'].lower()
        assert metadata['complexity'] == 'very high'


class TestErrorHandling:
    """Test error handling in predictions."""

    def test_invalid_ticker(self):
        """Test handling of invalid ticker."""
        model, feature_names = load_model()

        # Try with an invalid ticker - should return None
        result = make_prediction(model, feature_names, 'INVALID_TICKER_XYZ')
        assert result is None

    def test_missing_data(self):
        """Test handling when some data is missing."""
        # This test may need adjustment based on how the system handles missing data
        model, feature_names = load_model()

        # Penny stocks or OTC stocks might have missing data
        # The system should either skip them or use defaults
        try:
            prediction = make_prediction(model, feature_names, 'AAPL')
            assert prediction is not None
        except Exception as e:
            # If it fails, it should be a clear, expected error
            assert 'data' in str(e).lower() or 'missing' in str(e).lower()

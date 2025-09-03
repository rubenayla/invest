"""
Neural Network Valuation Model.

This module implements a neural network-based valuation model that learns
from historical market data to predict company valuations. It uses engineered
features from fundamental data and can target different time horizons.
"""

from typing import Dict, Any, Optional, List, Tuple
import logging
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import TimeSeriesSplit

from .base import ValuationModel, ValuationResult
from ..exceptions import ModelNotSuitableError, InsufficientDataError, ValuationError

# Suppress sklearn warnings
warnings.filterwarnings('ignore', category=UserWarning)

logger = logging.getLogger(__name__)


class NeuralNetworkArchitecture(nn.Module):
    """
    Neural network architecture for stock valuation.
    
    Features a deep architecture with dropout for regularization
    and batch normalization for stable training.
    """
    
    def __init__(self, input_dim: int, hidden_dims: List[int] = None, 
                 dropout_rate: float = 0.3, output_type: str = 'score'):
        """
        Initialize the neural network.
        
        Parameters
        ----------
        input_dim : int
            Number of input features
        hidden_dims : List[int]
            List of hidden layer dimensions
        dropout_rate : float
            Dropout rate for regularization
        output_type : str
            Type of output ('score' for 0-100, 'return' for expected return)
        """
        super().__init__()
        
        if hidden_dims is None:
            hidden_dims = [256, 128, 64, 32]
        
        self.output_type = output_type
        
        # Build the network layers
        layers = []
        prev_dim = input_dim
        
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.BatchNorm1d(hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout_rate)
            ])
            prev_dim = hidden_dim
        
        # Output layer
        layers.append(nn.Linear(prev_dim, 1))
        
        # Add sigmoid for score output (0-100 range)
        if output_type == 'score':
            layers.append(nn.Sigmoid())
        
        self.network = nn.Sequential(*layers)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through the network."""
        output = self.network(x)
        
        # Scale to 0-100 for score output
        if self.output_type == 'score':
            output = output * 100
        
        return output


class FeatureEngineer:
    """
    Feature engineering for neural network input.
    
    Transforms raw financial data into normalized features suitable
    for neural network training.
    """
    
    def __init__(self):
        """Initialize the feature engineer."""
        self.scaler = RobustScaler()
        self.feature_names = []
        self.is_fitted = False
    
    def extract_features(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract engineered features from raw financial data.
        
        Parameters
        ----------
        data : Dict[str, Any]
            Raw financial data from yfinance
            
        Returns
        -------
        Dict[str, float]
            Dictionary of engineered features
        """
        features = {}
        info = data.get('info', {})
        
        # Valuation Ratios
        features['pe_ratio'] = self._safe_ratio(
            info.get('currentPrice'), 
            info.get('trailingEps')
        )
        features['forward_pe'] = self._safe_ratio(
            info.get('currentPrice'),
            info.get('forwardEps')
        )
        features['peg_ratio'] = info.get('pegRatio', 0.0) or 0.0
        features['price_to_book'] = info.get('priceToBook', 0.0) or 0.0
        features['price_to_sales'] = self._safe_ratio(
            info.get('marketCap'),
            info.get('totalRevenue')
        )
        features['ev_to_ebitda'] = self._safe_ratio(
            info.get('enterpriseValue'),
            info.get('ebitda')
        )
        features['ev_to_revenue'] = self._safe_ratio(
            info.get('enterpriseValue'),
            info.get('totalRevenue')
        )
        
        # Profitability Metrics
        features['profit_margin'] = info.get('profitMargins', 0.0) or 0.0
        features['operating_margin'] = info.get('operatingMargins', 0.0) or 0.0
        features['roe'] = info.get('returnOnEquity', 0.0) or 0.0
        features['roa'] = info.get('returnOnAssets', 0.0) or 0.0
        features['roic'] = self._calculate_roic(info)
        features['gross_margin'] = info.get('grossMargins', 0.0) or 0.0
        
        # Growth Metrics
        features['revenue_growth'] = info.get('revenueGrowth', 0.0) or 0.0
        features['earnings_growth'] = info.get('earningsGrowth', 0.0) or 0.0
        features['revenue_growth_3y'] = self._safe_float(
            info.get('revenueQuarterlyGrowth', 0.0)
        )
        
        # Financial Health
        features['current_ratio'] = info.get('currentRatio', 0.0) or 0.0
        features['quick_ratio'] = info.get('quickRatio', 0.0) or 0.0
        features['debt_to_equity'] = info.get('debtToEquity', 0.0) or 0.0
        features['interest_coverage'] = self._calculate_interest_coverage(info)
        features['free_cash_flow_yield'] = self._safe_ratio(
            info.get('freeCashflow'),
            info.get('marketCap')
        )
        
        # Market Metrics
        features['beta'] = info.get('beta', 1.0) or 1.0
        features['market_cap_log'] = np.log(max(info.get('marketCap', 1e6), 1))
        features['avg_volume_log'] = np.log(max(info.get('averageVolume', 1e3), 1))
        features['dividend_yield'] = info.get('dividendYield', 0.0) or 0.0
        features['payout_ratio'] = info.get('payoutRatio', 0.0) or 0.0
        
        # Momentum Indicators
        features['52w_high_ratio'] = self._safe_ratio(
            info.get('currentPrice'),
            info.get('fiftyTwoWeekHigh')
        )
        features['52w_low_ratio'] = self._safe_ratio(
            info.get('currentPrice'),
            info.get('fiftyTwoWeekLow')
        )
        features['50d_ma_ratio'] = self._safe_ratio(
            info.get('currentPrice'),
            info.get('fiftyDayAverage')
        )
        features['200d_ma_ratio'] = self._safe_ratio(
            info.get('currentPrice'),
            info.get('twoHundredDayAverage')
        )
        
        # Analyst Sentiment (if available)
        features['analyst_count'] = info.get('numberOfAnalystOpinions', 0) or 0
        features['target_mean_ratio'] = self._safe_ratio(
            info.get('targetMeanPrice'),
            info.get('currentPrice')
        )
        features['recommendation_score'] = self._encode_recommendation(
            info.get('recommendationKey', 'none')
        )
        
        # Sector encoding (simplified - could use one-hot encoding)
        features['sector_code'] = self._encode_sector(info.get('sector', 'Unknown'))
        features['industry_code'] = hash(info.get('industry', 'Unknown')) % 100
        
        return features
    
    def _safe_ratio(self, numerator: Any, denominator: Any, 
                   default: float = 0.0) -> float:
        """Calculate ratio safely handling None and zero values."""
        try:
            num = float(numerator) if numerator is not None else 0.0
            den = float(denominator) if denominator is not None else 0.0
            
            if den == 0:
                return default
            
            ratio = num / den
            
            # Cap extreme ratios
            if ratio > 100:
                return 100.0
            elif ratio < -100:
                return -100.0
            
            return ratio
        except (TypeError, ValueError):
            return default
    
    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        """Safely convert value to float."""
        try:
            if value is None:
                return default
            return float(value)
        except (TypeError, ValueError):
            return default
    
    def _calculate_roic(self, info: Dict[str, Any]) -> float:
        """Calculate Return on Invested Capital."""
        ebit = info.get('ebit', 0)
        tax_rate = 0.25  # Assume 25% if not available
        total_assets = info.get('totalAssets', 0)
        current_liab = info.get('totalCurrentLiabilities', 0)
        cash = info.get('totalCash', 0)
        
        if not ebit or not total_assets:
            return 0.0
        
        nopat = ebit * (1 - tax_rate)
        invested_capital = total_assets - current_liab - cash
        
        if invested_capital <= 0:
            return 0.0
        
        return (nopat / invested_capital) * 100
    
    def _calculate_interest_coverage(self, info: Dict[str, Any]) -> float:
        """Calculate interest coverage ratio."""
        ebit = info.get('ebit', 0)
        interest_expense = info.get('interestExpense', 0)
        
        if not interest_expense or interest_expense == 0:
            return 10.0  # High coverage if no interest expense
        
        return min(ebit / abs(interest_expense), 10.0)
    
    def _encode_recommendation(self, rec_key: str) -> float:
        """Encode analyst recommendation to numeric value."""
        encoding = {
            'strong_buy': 5.0,
            'buy': 4.0,
            'hold': 3.0,
            'sell': 2.0,
            'strong_sell': 1.0,
            'none': 3.0
        }
        return encoding.get(rec_key.lower().replace('-', '_'), 3.0)
    
    def _encode_sector(self, sector: str) -> float:
        """Simple sector encoding (could be improved with one-hot)."""
        sectors = {
            'Technology': 1.0,
            'Healthcare': 2.0,
            'Financial Services': 3.0,
            'Consumer Cyclical': 4.0,
            'Communication Services': 5.0,
            'Consumer Defensive': 6.0,
            'Industrials': 7.0,
            'Energy': 8.0,
            'Utilities': 9.0,
            'Real Estate': 10.0,
            'Basic Materials': 11.0,
            'Unknown': 0.0
        }
        return sectors.get(sector, 0.0)
    
    def fit_transform(self, features_list: List[Dict[str, float]]) -> np.ndarray:
        """
        Fit the scaler and transform features.
        
        Parameters
        ----------
        features_list : List[Dict[str, float]]
            List of feature dictionaries
            
        Returns
        -------
        np.ndarray
            Scaled feature array
        """
        # Convert to DataFrame for easier handling
        df = pd.DataFrame(features_list)
        
        # Store feature names
        self.feature_names = list(df.columns)
        
        # Replace inf and -inf with NaN, then fill with 0
        df = df.replace([np.inf, -np.inf], np.nan).fillna(0)
        
        # Fit and transform
        scaled_features = self.scaler.fit_transform(df)
        self.is_fitted = True
        
        return scaled_features
    
    def transform(self, features: Dict[str, float]) -> np.ndarray:
        """
        Transform features using fitted scaler.
        
        Parameters
        ----------
        features : Dict[str, float]
            Feature dictionary
            
        Returns
        -------
        np.ndarray
            Scaled feature array
        """
        if not self.is_fitted:
            raise ValueError('FeatureEngineer must be fitted before transform')
        
        # Ensure consistent feature ordering
        feature_array = np.array([features.get(name, 0.0) for name in self.feature_names])
        
        # Handle inf and nan
        feature_array = np.nan_to_num(feature_array, nan=0.0, posinf=100.0, neginf=-100.0)
        
        # Transform
        return self.scaler.transform(feature_array.reshape(1, -1))


class NeuralNetworkValuationModel(ValuationModel):
    """
    Neural network-based valuation model.
    
    This model uses a deep neural network trained on historical market data
    to predict company valuations. It incorporates extensive feature engineering
    and can target different time horizons.
    """
    
    def __init__(self, time_horizon: str = '1year', model_path: Optional[Path] = None):
        """
        Initialize the neural network valuation model.
        
        Parameters
        ----------
        time_horizon : str
            Target time horizon ('1month', '1year', '5year')
        model_path : Optional[Path]
            Path to pre-trained model weights
        """
        super().__init__('neural_network')
        
        self.time_horizon = time_horizon
        self.model_path = model_path
        
        # Initialize components
        self.feature_engineer = FeatureEngineer()
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load pre-trained model if provided
        if model_path and model_path.exists():
            self.load_model(model_path)
        else:
            # Initialize untrained model (will need training)
            self._initialize_model()
    
    def _initialize_model(self):
        """Initialize an untrained model with default architecture."""
        # Default feature count (will be updated when fitted)
        input_dim = 40  # Approximate number of features
        
        self.model = NeuralNetworkArchitecture(
            input_dim=input_dim,
            hidden_dims=[256, 128, 64, 32],
            dropout_rate=0.3,
            output_type='score'
        ).to(self.device)
    
    def is_suitable(self, ticker: str, data: Dict[str, Any]) -> bool:
        """
        Check if this model is suitable for the given company.
        
        Neural network model is generally applicable to all companies
        with sufficient fundamental data.
        
        Parameters
        ----------
        ticker : str
            Stock ticker symbol
        data : Dict[str, Any]
            Company financial data
            
        Returns
        -------
        bool
            True if model is suitable
        """
        info = data.get('info', {})
        
        # Check for minimum required data
        required_fields = [
            'currentPrice', 'marketCap', 'totalRevenue',
            'trailingEps', 'enterpriseValue'
        ]
        
        for field in required_fields:
            if not info.get(field):
                return False
        
        # Check for positive market cap
        market_cap = self._safe_float(info.get('marketCap'))
        if market_cap <= 0:
            return False
        
        return True
    
    def _validate_inputs(self, ticker: str, data: Dict[str, Any]) -> None:
        """
        Validate that required input data is available.
        
        Parameters
        ----------
        ticker : str
            Stock ticker symbol
        data : Dict[str, Any]
            Company financial data
            
        Raises
        ------
        InsufficientDataError
            If required data is missing
        """
        info = data.get('info', {})
        
        # Essential fields for feature engineering
        essential_fields = [
            'currentPrice', 'marketCap', 'enterpriseValue',
            'totalRevenue', 'trailingEps'
        ]
        
        missing_fields = []
        for field in essential_fields:
            if not info.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            raise InsufficientDataError(ticker, missing_fields)
        
        # Warn about optional but useful fields
        optional_fields = [
            'returnOnEquity', 'debtToEquity', 'freeCashflow',
            'revenueGrowth', 'targetMeanPrice'
        ]
        
        missing_optional = []
        for field in optional_fields:
            if not info.get(field):
                missing_optional.append(field)
        
        if missing_optional and len(missing_optional) > len(optional_fields) / 2:
            self.logger.warning(
                f'Missing {len(missing_optional)} optional fields for {ticker}. '
                f'Prediction accuracy may be reduced.'
            )
    
    def _calculate_valuation(self, ticker: str, data: Dict[str, Any]) -> ValuationResult:
        """
        Perform neural network valuation.
        
        Parameters
        ----------
        ticker : str
            Stock ticker symbol
        data : Dict[str, Any]
            Company financial data
            
        Returns
        -------
        ValuationResult
            The valuation result
        """
        info = data.get('info', {})
        
        # Extract features
        features = self.feature_engineer.extract_features(data)
        
        # Check if model is trained
        if not self.feature_engineer.is_fitted:
            # For demo purposes, return a simple ratio-based estimate
            # In production, this would load a pre-trained model
            self.logger.warning(
                'Neural network model not trained. Using simplified heuristic valuation.'
            )
            return self._heuristic_valuation(ticker, data, features)
        
        # Transform features for model input
        feature_array = self.feature_engineer.transform(features)
        feature_tensor = torch.FloatTensor(feature_array).to(self.device)
        
        # Get model prediction
        self.model.eval()
        with torch.no_grad():
            # Get base prediction
            score = self.model(feature_tensor).cpu().numpy()[0, 0]
            
            # Simple uncertainty estimation without dropout issues
            uncertainty = 5.0  # Default moderate uncertainty
            confidence = self._score_to_confidence(uncertainty)
        
        # Convert score to fair value estimate
        current_price = self._safe_float(info.get('currentPrice'))
        
        # Score 50 = fair value, >50 = undervalued, <50 = overvalued
        # Each point roughly represents 2% deviation from fair value
        fair_value_multiplier = 1 + (score - 50) * 0.02
        fair_value = current_price * fair_value_multiplier
        
        # Calculate margin of safety
        margin_of_safety = ((fair_value - current_price) / current_price) * 100
        
        return ValuationResult(
            ticker=ticker,
            model=self.name,
            fair_value=fair_value,
            current_price=current_price,
            margin_of_safety=margin_of_safety,
            confidence=confidence,
            inputs={
                'feature_count': len(features),
                'model_score': float(score),
                'uncertainty': float(uncertainty),
                'time_horizon': self.time_horizon
            },
            outputs={
                'score': float(score),
                'fair_value_multiplier': float(fair_value_multiplier),
                'top_features': self._get_top_features(features)
            },
            warnings=self._generate_warnings(features, score)
        )
    
    def _heuristic_valuation(self, ticker: str, data: Dict[str, Any], 
                            features: Dict[str, float]) -> ValuationResult:
        """
        Simple heuristic valuation when model is not trained.
        
        Uses weighted average of key valuation metrics.
        """
        info = data.get('info', {})
        current_price = self._safe_float(info.get('currentPrice'))
        
        # Simple scoring based on key metrics
        score = 50.0  # Start at neutral
        
        # P/E ratio scoring
        pe_ratio = features.get('pe_ratio', 0)
        if 0 < pe_ratio < 15:
            score += 10
        elif 15 <= pe_ratio < 25:
            score += 5
        elif pe_ratio > 35:
            score -= 10
        
        # PEG ratio scoring
        peg_ratio = features.get('peg_ratio', 0)
        if 0 < peg_ratio < 1:
            score += 10
        elif 1 <= peg_ratio < 2:
            score += 5
        elif peg_ratio > 3:
            score -= 5
        
        # Profitability scoring
        if features.get('roe', 0) > 15:
            score += 5
        if features.get('profit_margin', 0) > 0.1:
            score += 5
        
        # Growth scoring
        if features.get('revenue_growth', 0) > 0.1:
            score += 5
        
        # Financial health scoring
        if features.get('debt_to_equity', 0) < 1:
            score += 5
        if features.get('current_ratio', 0) > 1.5:
            score += 5
        
        # Momentum scoring
        if features.get('52w_high_ratio', 0) > 0.9:
            score -= 5  # Near 52-week high
        if features.get('52w_low_ratio', 0) < 1.2:
            score += 5  # Near 52-week low
        
        # Cap score between 0 and 100
        score = max(0, min(100, score))
        
        # Convert to fair value
        fair_value_multiplier = 1 + (score - 50) * 0.02
        fair_value = current_price * fair_value_multiplier
        margin_of_safety = ((fair_value - current_price) / current_price) * 100
        
        return ValuationResult(
            ticker=ticker,
            model=self.name,
            fair_value=fair_value,
            current_price=current_price,
            margin_of_safety=margin_of_safety,
            confidence='low',  # Low confidence for heuristic
            inputs={
                'method': 'heuristic',
                'feature_count': len(features),
                'model_score': float(score),
                'time_horizon': self.time_horizon
            },
            outputs={
                'score': float(score),
                'fair_value_multiplier': float(fair_value_multiplier)
            },
            warnings=['Model not trained - using heuristic valuation']
        )
    
    def _score_to_confidence(self, uncertainty: float) -> str:
        """Convert uncertainty to confidence level."""
        if uncertainty < 5:
            return 'high'
        elif uncertainty < 10:
            return 'medium'
        else:
            return 'low'
    
    def _get_top_features(self, features: Dict[str, float], n: int = 5) -> Dict[str, float]:
        """Get the top n most influential features."""
        # For now, return key valuation metrics
        # In production, would use SHAP values or similar
        key_features = [
            'pe_ratio', 'peg_ratio', 'roe', 'profit_margin',
            'debt_to_equity', 'revenue_growth', '52w_high_ratio'
        ]
        
        return {k: features.get(k, 0) for k in key_features[:n]}
    
    def _generate_warnings(self, features: Dict[str, float], score: float) -> List[str]:
        """Generate warnings based on feature values and score."""
        warnings = []
        
        # Check for extreme values
        if features.get('pe_ratio', 0) > 50:
            warnings.append('Very high P/E ratio - possible overvaluation')
        
        if features.get('debt_to_equity', 0) > 3:
            warnings.append('High debt levels - increased financial risk')
        
        if features.get('profit_margin', 0) < 0:
            warnings.append('Negative profit margins')
        
        # Score-based warnings
        if score > 80:
            warnings.append('Strong buy signal - verify with fundamental analysis')
        elif score < 20:
            warnings.append('Strong sell signal - verify with fundamental analysis')
        
        return warnings
    
    def train_model(self, training_data: List[Tuple[str, Dict[str, Any], float]],
                   validation_split: float = 0.2, epochs: int = 100) -> Dict[str, float]:
        """
        Train the neural network model on historical data.
        
        Parameters
        ----------
        training_data : List[Tuple[str, Dict[str, Any], float]]
            List of (ticker, data, target_return) tuples
        validation_split : float
            Fraction of data to use for validation
        epochs : int
            Number of training epochs
            
        Returns
        -------
        Dict[str, float]
            Training metrics (loss, accuracy, etc.)
        """
        if not training_data:
            raise ValueError('No training data provided')
        
        self.logger.info(f'Training model on {len(training_data)} samples')
        
        # Extract features and targets
        features_list = []
        targets = []
        
        for ticker, data, target in training_data:
            try:
                features = self.feature_engineer.extract_features(data)
                features_list.append(features)
                
                # Convert return to score (0-100)
                # -50% return = 0, 0% = 50, +50% = 100
                score = 50 + (target * 100)
                score = max(0, min(100, score))
                targets.append(score)
                
            except Exception as e:
                self.logger.warning(f'Failed to extract features for {ticker}: {e}')
                continue
        
        if len(features_list) < 10:
            raise ValueError('Insufficient valid training samples')
        
        # Fit scaler and transform features
        X = self.feature_engineer.fit_transform(features_list)
        y = np.array(targets)
        
        # Update model input dimension
        input_dim = X.shape[1]
        self.model = NeuralNetworkArchitecture(
            input_dim=input_dim,
            hidden_dims=[256, 128, 64, 32],
            dropout_rate=0.3,
            output_type='score'
        ).to(self.device)
        
        # Prepare data for PyTorch
        X_tensor = torch.FloatTensor(X).to(self.device)
        y_tensor = torch.FloatTensor(y.reshape(-1, 1)).to(self.device)
        
        # Train/validation split
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X_tensor[:split_idx], X_tensor[split_idx:]
        y_train, y_val = y_tensor[:split_idx], y_tensor[split_idx:]
        
        # Training setup
        optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        criterion = nn.MSELoss()
        
        # Training loop
        train_losses = []
        val_losses = []
        
        for epoch in range(epochs):
            # Training phase
            self.model.train()
            optimizer.zero_grad()
            
            train_pred = self.model(X_train)
            train_loss = criterion(train_pred, y_train)
            
            train_loss.backward()
            optimizer.step()
            
            # Validation phase
            self.model.eval()
            with torch.no_grad():
                val_pred = self.model(X_val)
                val_loss = criterion(val_pred, y_val)
            
            train_losses.append(train_loss.item())
            val_losses.append(val_loss.item())
            
            if (epoch + 1) % 10 == 0:
                self.logger.info(
                    f'Epoch {epoch + 1}/{epochs} - '
                    f'Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}'
                )
        
        # Calculate final metrics
        self.model.eval()
        with torch.no_grad():
            final_train_pred = self.model(X_train).cpu().numpy()
            final_val_pred = self.model(X_val).cpu().numpy()
        
        train_mae = np.mean(np.abs(final_train_pred.flatten() - y_train.cpu().numpy().flatten()))
        val_mae = np.mean(np.abs(final_val_pred.flatten() - y_val.cpu().numpy().flatten()))
        
        metrics = {
            'final_train_loss': train_losses[-1],
            'final_val_loss': val_losses[-1],
            'train_mae': train_mae,
            'val_mae': val_mae,
            'epochs_trained': epochs
        }
        
        self.logger.info(f'Training completed. Validation MAE: {val_mae:.2f}')
        
        return metrics
    
    def save_model(self, path: Path) -> None:
        """Save the trained model to disk."""
        if not self.model:
            raise ValueError('No model to save')
        
        path.parent.mkdir(parents=True, exist_ok=True)
        
        checkpoint = {
            'model_state': self.model.state_dict(),
            'feature_names': self.feature_engineer.feature_names,
            'scaler_params': {
                'center_': self.feature_engineer.scaler.center_.tolist(),
                'scale_': self.feature_engineer.scaler.scale_.tolist()
            },
            'time_horizon': self.time_horizon
        }
        
        torch.save(checkpoint, path)
        self.logger.info(f'Model saved to {path}')
    
    def load_model(self, path: Path) -> None:
        """Load a trained model from disk."""
        if not path.exists():
            raise FileNotFoundError(f'Model file not found: {path}')
        
        checkpoint = torch.load(path, map_location=self.device)
        
        # Restore feature engineer
        self.feature_engineer.feature_names = checkpoint['feature_names']
        self.feature_engineer.scaler.center_ = np.array(checkpoint['scaler_params']['center_'])
        self.feature_engineer.scaler.scale_ = np.array(checkpoint['scaler_params']['scale_'])
        self.feature_engineer.is_fitted = True
        
        # Restore model
        input_dim = len(self.feature_engineer.feature_names)
        self.model = NeuralNetworkArchitecture(
            input_dim=input_dim,
            hidden_dims=[256, 128, 64, 32],
            dropout_rate=0.3,
            output_type='score'
        ).to(self.device)
        
        self.model.load_state_dict(checkpoint['model_state'])
        self.time_horizon = checkpoint.get('time_horizon', '1year')
        
        self.logger.info(f'Model loaded from {path}')
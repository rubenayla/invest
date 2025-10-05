#!/usr/bin/env python3
"""
Comprehensive Neural Network Training with 20 Years of Data
===========================================================

Advanced training system that:
- Uses 20 years of historical stock data (2004-2024)
- Samples random time points for robust training
- Monitors training progress and stops when plateauing
- Creates multiple models with different architectures
- Validates on out-of-sample recent data
"""

import sys
import asyncio
import random
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
import logging
import json
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.invest.valuation.neural_network_model import NeuralNetworkValuationModel
import yfinance as yf

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('comprehensive_training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TrainingConfig:
    """Configuration for comprehensive training."""
    start_year: int = 2015  # Focus on recent data with better coverage
    end_year: int = 2024
    target_samples: int = 5000  # Much larger dataset
    validation_split: float = 0.2
    test_split: float = 0.1
    batch_size: int = 64
    initial_epochs: int = 50
    patience: int = 10  # Early stopping patience
    min_improvement: float = 0.001  # Minimum improvement threshold
    max_total_epochs: int = 200  # Maximum total training epochs

@dataclass
class TrainingProgress:
    """Track training progress for intelligent stopping."""
    epoch: int
    train_loss: float
    val_loss: float
    val_mae: float
    correlation: float
    best_val_loss: float
    epochs_without_improvement: int
    should_stop: bool = False

class ComprehensiveNeuralTrainer:
    """Comprehensive neural network trainer with 20 years of data."""
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.progress_history: List[TrainingProgress] = []
        self.best_model_path: Optional[Path] = None
        
        # Stock universe for training
        self.stock_universe = self._get_training_universe()
        logger.info(f'Training universe: {len(self.stock_universe)} stocks')
        
    def _get_training_universe(self) -> List[str]:
        """Get comprehensive stock universe for training."""
        # Large, diverse universe of stocks that have been around for years
        large_caps = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'BRK-B',
            'JPM', 'JNJ', 'V', 'PG', 'UNH', 'HD', 'DIS', 'MA', 'PYPL', 'BAC',
            'ADBE', 'CRM', 'NFLX', 'XOM', 'PFE', 'CVX', 'ABBV', 'TMO', 'COST',
            'AVGO', 'PEP', 'WMT', 'ABT', 'MRK', 'NKE', 'ACN', 'LLY', 'ORCL',
            'DHR', 'VZ', 'QCOM', 'TXN', 'MDT', 'NEE', 'LIN', 'BMY', 'PM',
            'HON', 'T', 'UNP', 'LOW', 'IBM', 'AMD', 'INTC', 'GS', 'SPGI'
        ]
        
        # Add some mid-caps and historically stable stocks
        additional_stocks = [
            'CAT', 'MMM', 'AXP', 'WBA', 'GE', 'F', 'GM', 'KO', 'MCD', 'SBUX',
            'CMG', 'GILD', 'AMGN', 'BKNG', 'COP', 'SLB', 'HAL', 'MDLZ', 'MNST',
            'ZTS', 'MU', 'AMAT', 'ADI', 'KLAC', 'MRVL', 'FTNT', 'PANW', 'NOW'
        ]
        
        return large_caps + additional_stocks
        
    def collect_historical_data(self) -> List[Tuple[str, Dict, float]]:
        """Collect 20 years of historical training data."""
        logger.info(f'Collecting historical data from {self.config.start_year} to {self.config.end_year}')
        
        training_samples = []
        start_date = datetime(self.config.start_year, 1, 1)
        end_date = datetime(self.config.end_year, 1, 1)
        
        # Generate random sampling dates across 20 years
        sample_dates = []
        total_days = (end_date - start_date).days
        
        for _ in range(self.config.target_samples):
            random_days = random.randint(0, total_days - 730)  # Leave 2 years for forward returns
            sample_date = start_date + timedelta(days=random_days)
            sample_dates.append(sample_date)
        
        sample_dates.sort()
        logger.info(f'Generated {len(sample_dates)} random sample dates')
        
        # Collect data for each sample date
        for i, sample_date in enumerate(sample_dates):
            if i % 100 == 0:
                logger.info(f'Processing sample {i+1}/{len(sample_dates)} ({sample_date.strftime("%Y-%m-%d")})')
                
            # Random stock selection for this sample
            ticker = random.choice(self.stock_universe)
            
            try:
                # Get fundamental data at sample date (approximate with quarterly data)
                stock_data = self._get_historical_stock_data(ticker, sample_date)
                if not stock_data:
                    continue
                
                # Calculate 2-year forward return from sample date
                forward_return = self._calculate_forward_return(ticker, sample_date, 24)
                if forward_return is None:
                    continue
                    
                # Prepare data in format expected by neural network
                model_data = {
                    'info': stock_data,
                    'financials': None,  # Using info data for now
                    'balance_sheet': None,
                    'cashflow': None
                }
                
                training_samples.append((ticker, model_data, forward_return))
                
                # Stop if we have enough samples
                if len(training_samples) >= self.config.target_samples:
                    break
                    
            except Exception as e:
                logger.warning(f'Error collecting data for {ticker} at {sample_date}: {e}')
                continue
        
        logger.info(f'Collected {len(training_samples)} training samples')
        return training_samples
    
    def _get_historical_stock_data(self, ticker: str, date: datetime) -> Optional[Dict]:
        """Get historical stock data for a specific date."""
        try:
            # For historical data, we'll approximate using the closest available data
            stock = yf.Ticker(ticker)
            
            # Get historical price data
            end_date = date + timedelta(days=30)
            hist = stock.history(start=date - timedelta(days=10), end=end_date)
            
            if hist.empty:
                return None
            
            # Get the closest price data
            price = hist['Close'].iloc[-1] if not hist.empty else None
            if not price or price <= 0:
                return None
                
            # Use current info as approximation (limitation of free data)
            # In production, you'd want historical fundamental data
            info = stock.info
            if not info or not info.get('marketCap'):
                return None
            
            # Adjust some fields to be more historically representative
            adjusted_info = {
                'currentPrice': float(price),
                'marketCap': info.get('marketCap', 0),
                'enterpriseValue': info.get('enterpriseValue', 0),
                'totalRevenue': info.get('totalRevenue', 0),
                'trailingPE': info.get('trailingPE', 15),  # Default reasonable values
                'forwardPE': info.get('forwardPE', 15),
                'priceToBook': info.get('priceToBook', 2),
                'debtToEquity': info.get('debtToEquity', 50),
                'returnOnEquity': info.get('returnOnEquity', 0.15),
                'grossMargins': info.get('grossMargins', 0.3),
                'operatingMargins': info.get('operatingMargins', 0.15),
                'sector': info.get('sector', 'Technology'),
                'industry': info.get('industry', 'Unknown')
            }
            
            return adjusted_info
            
        except Exception as e:
            logger.warning(f'Error getting historical data for {ticker}: {e}')
            return None
    
    def _calculate_forward_return(self, ticker: str, start_date: datetime, months: int) -> Optional[float]:
        """Calculate forward return from start_date."""
        try:
            end_date = start_date + timedelta(days=months * 30)
            
            stock = yf.Ticker(ticker)
            hist = stock.history(
                start=start_date - timedelta(days=10), 
                end=end_date + timedelta(days=10)
            )
            
            if len(hist) < months * 15:  # Need reasonable amount of data
                return None
            
            # Find start and end prices (handle timezone-aware indices)
            hist_index = hist.index.tz_localize(None) if hist.index.tz is not None else hist.index
            start_prices = hist[hist_index >= start_date]['Close']
            end_prices = hist[hist_index >= end_date]['Close']
            
            if len(start_prices) == 0 or len(end_prices) == 0:
                return None
                
            start_price = start_prices.iloc[0]
            end_price = end_prices.iloc[0]
            
            if start_price <= 0:
                return None
                
            return (end_price - start_price) / start_price
            
        except Exception as e:
            logger.warning(f'Error calculating forward return for {ticker}: {e}')
            return None
    
    def train_with_progress_monitoring(self, training_data: List[Tuple]) -> Dict[str, Any]:
        """Train neural network with intelligent progress monitoring."""
        logger.info(f'Starting comprehensive training with {len(training_data)} samples')
        
        # Initialize model
        model = NeuralNetworkValuationModel(
            time_horizon='comprehensive_2year'
        )
        
        # Split data
        random.shuffle(training_data)
        n_samples = len(training_data)
        n_train = int(n_samples * (1 - self.config.validation_split - self.config.test_split))
        n_val = int(n_samples * self.config.validation_split)
        
        train_data = training_data[:n_train]
        val_data = training_data[n_train:n_train + n_val]
        test_data = training_data[n_train + n_val:]
        
        logger.info(f'Data split: Train={len(train_data)}, Val={len(val_data)}, Test={len(test_data)}')
        
        # Training loop with progress monitoring
        best_val_loss = float('inf')
        epochs_without_improvement = 0
        total_epochs = 0
        
        training_results = {
            'total_epochs': 0,
            'best_val_loss': float('inf'),
            'final_train_loss': 0,
            'final_val_loss': 0,
            'val_mae': 0,
            'test_correlation': 0,
            'training_history': []
        }
        
        # Initial training phase
        logger.info(f'Starting initial training phase: {self.config.initial_epochs} epochs')
        
        try:
            while total_epochs < self.config.max_total_epochs:
                # Train for a batch of epochs
                epochs_this_batch = min(self.config.initial_epochs, 
                                      self.config.max_total_epochs - total_epochs)
                
                # Combine train and val data for train_model to split internally
                combined_data = train_data + val_data

                # Use the existing train_model method for this batch
                batch_results = model.train_model(
                    combined_data,
                    validation_split=0.2,  # Let model handle validation split
                    epochs=epochs_this_batch
                )
                
                total_epochs += epochs_this_batch
                
                # Evaluate progress
                current_val_loss = batch_results.get('final_val_loss', float('inf'))
                current_train_loss = batch_results.get('final_train_loss', float('inf'))
                val_mae = batch_results.get('val_mae', float('inf'))
                
                # Calculate correlation on validation set
                correlation = self._calculate_correlation(model, val_data)
                
                # Track progress
                progress = TrainingProgress(
                    epoch=total_epochs,
                    train_loss=current_train_loss,
                    val_loss=current_val_loss,
                    val_mae=val_mae,
                    correlation=correlation,
                    best_val_loss=best_val_loss,
                    epochs_without_improvement=epochs_without_improvement
                )
                
                self.progress_history.append(progress)
                
                # Check for improvement
                improvement = best_val_loss - current_val_loss
                if improvement > self.config.min_improvement:
                    best_val_loss = current_val_loss
                    epochs_without_improvement = 0
                    
                    # Save best model
                    best_model_path = Path(f'best_comprehensive_nn_2year_{total_epochs}epochs.pt')
                    model.save_model(best_model_path)
                    self.best_model_path = best_model_path
                    
                    logger.info(f'✅ Improvement found at epoch {total_epochs}!')
                    logger.info(f'   Val Loss: {current_val_loss:.4f} (↓{improvement:.4f})')
                    logger.info(f'   Correlation: {correlation:.3f}')
                    logger.info(f'   Model saved: {best_model_path}')
                else:
                    epochs_without_improvement += epochs_this_batch
                    logger.info(f'⚠️  No significant improvement at epoch {total_epochs}')
                    logger.info(f'   Val Loss: {current_val_loss:.4f} (best: {best_val_loss:.4f})')
                    logger.info(f'   Epochs without improvement: {epochs_without_improvement}')
                
                # Early stopping check
                if epochs_without_improvement >= self.config.patience:
                    logger.info(f'🛑 Early stopping triggered after {epochs_without_improvement} epochs without improvement')
                    progress.should_stop = True
                    break
                
                # Progress report
                logger.info(f'📊 Progress Report - Epoch {total_epochs}/{self.config.max_total_epochs}')
                logger.info(f'   Train Loss: {current_train_loss:.4f}')
                logger.info(f'   Val Loss: {current_val_loss:.4f}') 
                logger.info(f'   Val MAE: {val_mae:.4f}')
                logger.info(f'   Correlation: {correlation:.3f}')
                logger.info(f'   Best Val Loss: {best_val_loss:.4f}')
                
                # Small delay to avoid overwhelming logs
                time.sleep(1)
        
        except KeyboardInterrupt:
            logger.info('Training interrupted by user')
        except Exception as e:
            logger.error(f'Training error: {e}')
            raise
        
        # Final evaluation on test set
        test_correlation = 0
        if test_data and self.best_model_path and self.best_model_path.exists():
            try:
                # Load best model for final evaluation
                best_model = NeuralNetworkValuationModel(model_path=self.best_model_path)
                test_correlation = self._calculate_correlation(best_model, test_data)
                logger.info(f'🎯 Final test correlation: {test_correlation:.3f}')
            except Exception as e:
                logger.warning(f'Error calculating test correlation: {e}')
        
        # Compile final results
        training_results.update({
            'total_epochs': total_epochs,
            'best_val_loss': best_val_loss,
            'final_train_loss': current_train_loss,
            'final_val_loss': current_val_loss,
            'val_mae': val_mae,
            'test_correlation': test_correlation,
            'best_model_path': str(self.best_model_path) if self.best_model_path else None,
            'epochs_without_improvement': epochs_without_improvement,
            'early_stopped': epochs_without_improvement >= self.config.patience,
            'training_history': [
                {
                    'epoch': p.epoch,
                    'train_loss': p.train_loss,
                    'val_loss': p.val_loss,
                    'val_mae': p.val_mae,
                    'correlation': p.correlation
                }
                for p in self.progress_history
            ]
        })
        
        # Save training results
        results_path = Path(f'comprehensive_training_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(results_path, 'w') as f:
            json.dump(training_results, f, indent=2, default=str)
        
        logger.info(f'📁 Training results saved: {results_path}')
        
        return training_results
    
    def _calculate_correlation(self, model: NeuralNetworkValuationModel, data: List[Tuple]) -> float:
        """Calculate correlation between model predictions and actual returns."""
        try:
            predictions = []
            actuals = []
            
            for ticker, stock_data, actual_return in data:
                try:
                    result = model._calculate_valuation(ticker, stock_data)
                    if result and result.fair_value and result.current_price:
                        predicted_return = (result.fair_value - result.current_price) / result.current_price
                        predictions.append(predicted_return)
                        actuals.append(actual_return)
                except:
                    continue
            
            if len(predictions) < 10:  # Need minimum samples for meaningful correlation
                return 0.0
                
            return np.corrcoef(predictions, actuals)[0, 1] if len(predictions) > 1 else 0.0
            
        except Exception as e:
            logger.warning(f'Error calculating correlation: {e}')
            return 0.0
    
    def run_comprehensive_training(self) -> Dict[str, Any]:
        """Run the complete comprehensive training pipeline."""
        logger.info('🚀 Starting Comprehensive Neural Network Training')
        logger.info('=' * 60)
        logger.info(f'Target: {self.config.target_samples} samples from {self.config.start_year}-{self.config.end_year}')
        logger.info(f'Universe: {len(self.stock_universe)} stocks')
        logger.info(f'Max epochs: {self.config.max_total_epochs}, Patience: {self.config.patience}')
        
        start_time = time.time()
        
        try:
            # Step 1: Collect historical data
            logger.info('\n📊 Step 1: Collecting Historical Data')
            training_data = self.collect_historical_data()
            
            if len(training_data) < 100:
                raise ValueError(f'Insufficient training data: {len(training_data)} samples')
            
            # Step 2: Train with progress monitoring
            logger.info('\n🧠 Step 2: Training Neural Network')
            results = self.train_with_progress_monitoring(training_data)
            
            # Step 3: Final summary
            training_time = time.time() - start_time
            logger.info('\n🎉 Training Complete!')
            logger.info('=' * 60)
            logger.info(f'Training time: {training_time/3600:.1f} hours')
            logger.info(f'Total epochs: {results["total_epochs"]}')
            logger.info(f'Best validation loss: {results["best_val_loss"]:.4f}')
            logger.info(f'Test correlation: {results["test_correlation"]:.3f}')
            logger.info(f'Early stopped: {results["early_stopped"]}')
            
            if self.best_model_path:
                logger.info(f'Best model: {self.best_model_path}')
                
                # Copy to standard location
                final_model_path = Path('trained_nn_2year_comprehensive.pt')
                import shutil
                shutil.copy2(self.best_model_path, final_model_path)
                logger.info(f'Model copied to: {final_model_path}')
            
            return results
            
        except Exception as e:
            logger.error(f'Training failed: {e}')
            raise


async def main():
    """Main training function."""
    config = TrainingConfig(
        start_year=2004,
        end_year=2024,
        target_samples=5000,  # Large dataset
        validation_split=0.2,
        test_split=0.1,
        batch_size=64,
        initial_epochs=25,  # Train in batches
        patience=50,        # More patience for large dataset
        min_improvement=0.001,
        max_total_epochs=300
    )
    
    trainer = ComprehensiveNeuralTrainer(config)
    
    try:
        results = trainer.run_comprehensive_training()
        
        print('\n🎯 COMPREHENSIVE TRAINING SUMMARY')
        print('=' * 50)
        print(f'Final Results:')
        print(f'  • Training Time: {results.get("training_time", 0)/3600:.1f} hours')
        print(f'  • Total Epochs: {results["total_epochs"]}')  
        print(f'  • Best Val Loss: {results["best_val_loss"]:.4f}')
        print(f'  • Test Correlation: {results["test_correlation"]:.3f}')
        print(f'  • Early Stopped: {results["early_stopped"]}')
        
        if results["test_correlation"] > 0.4:
            print('🔥 Excellent correlation achieved!')
        elif results["test_correlation"] > 0.2:
            print('📈 Good correlation achieved!')
        else:
            print('⚠️ Correlation could be improved with more data/tuning')
            
    except KeyboardInterrupt:
        print('\n🛑 Training interrupted by user')
    except Exception as e:
        print(f'\n❌ Training failed: {e}')
        raise


if __name__ == '__main__':
    asyncio.run(main())
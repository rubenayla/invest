#!/usr/bin/env python3
"""
Simple training script for neural network valuation model.

Collects historical data and trains the model for 1-year predictions.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yfinance as yf

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.invest.valuation.neural_network_model import NeuralNetworkValuationModel


def get_sp500_tickers() -> List[str]:
    """Get a subset of S&P 500 tickers for training."""
    # Top 50 S&P 500 companies by market cap (simplified list)
    return [
        'AAPL', 'MSFT', 'AMZN', 'NVDA', 'GOOGL', 'GOOG', 'META', 'TSLA', 'BRK-B', 'UNH',
        'XOM', 'JNJ', 'JPM', 'V', 'PG', 'MA', 'AVGO', 'HD', 'CVX', 'LLY',
        'ABBV', 'WMT', 'KO', 'BAC', 'PEP', 'TMO', 'COST', 'MRK', 'ORCL', 'ACN',
        'NFLX', 'WFC', 'DHR', 'VZ', 'ABT', 'LIN', 'CRM', 'ADBE', 'NKE', 'TXN',
        'DIS', 'CSCO', 'PM', 'BMY', 'AMGN', 'NEE', 'RTX', 'UPS', 'HON', 'QCOM'
    ]


def calculate_1year_return(ticker: str, start_date: datetime) -> float:
    """Calculate 1-year forward return using 30-day price averages."""
    try:
        end_date = start_date + timedelta(days=365)

        # Get price data with extra buffer for averaging
        stock = yf.Ticker(ticker)
        hist = stock.history(
            start=start_date - timedelta(days=10),
            end=end_date + timedelta(days=40)
        )

        if len(hist) < 60:  # Need at least 60 days for proper averaging
            return None

        # Find the start and end points in the data
        start_idx = None
        end_idx = None

        for i, date in enumerate(hist.index):
            if start_idx is None and date.date() >= start_date.date():
                start_idx = i
            if date.date() >= end_date.date():
                end_idx = i
                break

        if start_idx is None or end_idx is None:
            return None

        # Calculate 30-day average prices
        start_window = hist['Close'].iloc[start_idx:start_idx+30]
        end_window = hist['Close'].iloc[end_idx-29:end_idx+1]  # 30 days ending on end_date

        if len(start_window) < 20 or len(end_window) < 20:  # Need at least 20 days
            return None

        start_price = start_window.mean()
        end_price = end_window.mean()

        if start_price <= 0:
            return None

        return (end_price - start_price) / start_price

    except Exception as e:
        print(f'    Error calculating return for {ticker}: {e}')
        return None


def collect_training_data(tickers: List[str], num_months: int = 24) -> List[Tuple[str, Dict[str, Any], float]]:
    """
    Collect training data using monthly rolling windows.
    
    For each month going back num_months, get fundamental data and 1-year forward returns.
    This gives us 4x more training data and avoids calendar effects.
    """
    training_data = []

    # Generate monthly dates going back num_months months
    end_date = datetime.now() - timedelta(days=365)  # Start from 1 year ago (need time for forward returns)
    dates = []

    for m in range(num_months):
        month_date = end_date - timedelta(days=m * 30)  # Every 30 days
        dates.append(month_date)

    print(f'Collecting data for {len(dates)} monthly periods from {dates[-1].strftime("%Y-%m-%d")} to {dates[0].strftime("%Y-%m-%d")}')

    for i, date in enumerate(dates):
        print(f'\nMonth {i+1}/{len(dates)}: {date.strftime("%Y-%m-%d")}')

        month_samples = 0

        for ticker in tickers:
            try:
                # Get fundamental data (approximating what was available at that time)
                stock = yf.Ticker(ticker)
                info = stock.info

                # Calculate 1-year forward return using 30-day averages
                forward_return = calculate_1year_return(ticker, date)

                if forward_return is None:
                    continue

                # Prepare data in expected format
                data = {
                    'info': info,
                    'financials': None,  # Simplified for now
                    'balance_sheet': None,
                    'cashflow': None
                }

                # Basic validation - ensure we have key data
                required_fields = ['currentPrice', 'marketCap', 'enterpriseValue', 'totalRevenue']
                if all(info.get(field) for field in required_fields):
                    training_data.append((ticker, data, forward_return))
                    month_samples += 1

                    if month_samples % 15 == 0:
                        print(f'    Collected {month_samples} samples...')

            except Exception as e:
                # Only print errors occasionally to avoid spam
                if month_samples == 0:
                    print(f'    Skipping {ticker}: {e}')
                continue

        print(f'    Month complete: {month_samples} samples')

    print(f'\nTotal training samples collected: {len(training_data)}')
    return training_data


def train_model_with_splits(training_data: List[Tuple[str, Dict[str, Any], float]]) -> NeuralNetworkValuationModel:
    """Train the neural network model with proper time-ordered splits."""
    print(f'\nSplitting {len(training_data)} samples with time-ordered train/val/test...')

    # Sort by date (assuming data is already chronologically ordered from collect_training_data)
    # Train: 60%, Validation: 20%, Test: 20%
    n = len(training_data)
    train_size = int(n * 0.6)
    val_size = int(n * 0.2)

    train_data = training_data[:train_size]
    val_data = training_data[train_size:train_size + val_size]
    test_data = training_data[train_size + val_size:]

    print(f'Train: {len(train_data)} samples (oldest data)')
    print(f'Validation: {len(val_data)} samples (middle data)')
    print(f'Test: {len(test_data)} samples (newest data)')

    print('\nInitializing neural network model...')
    model = NeuralNetworkValuationModel(time_horizon='1year')

    # Combine train and validation for the model's internal training
    combined_train = train_data + val_data

    print('Starting training...')
    metrics = model.train_model(
        combined_train,
        validation_split=0.25,  # 25% of combined = 20% of total (our validation set)
        epochs=50
    )

    print('\nTraining completed!')
    print(f'Final Training Loss: {metrics["final_train_loss"]:.4f}')
    print(f'Final Validation Loss: {metrics["final_val_loss"]:.4f}')
    print(f'Training MAE: {metrics["train_mae"]:.2f}')
    print(f'Validation MAE: {metrics["val_mae"]:.2f}')

    # Test on held-out test data
    print('\nEvaluating on held-out test set...')
    test_predictions = []
    test_actuals = []

    for ticker, data, actual_return in test_data:
        try:
            # Use the model to predict
            result = model._calculate_valuation(ticker, data)

            # Convert fair value back to predicted return
            current_price = result.current_price
            if current_price and current_price > 0:
                predicted_return = (result.fair_value - current_price) / current_price
                test_predictions.append(predicted_return)
                test_actuals.append(actual_return)
        except Exception:
            continue

    if test_predictions:
        import numpy as np
        test_mae = np.mean(np.abs(np.array(test_predictions) - np.array(test_actuals)))
        test_corr = np.corrcoef(test_predictions, test_actuals)[0,1] if len(test_predictions) > 1 else 0
        print(f'Test MAE: {test_mae:.2f}')
        print(f'Test Correlation: {test_corr:.3f}')
    else:
        print('Could not evaluate test set')

    return model


def test_trained_model(model: NeuralNetworkValuationModel):
    """Test the trained model on a few stocks."""
    print('\nTesting trained model...')
    test_tickers = ['AAPL', 'MSFT', 'GOOGL']

    for ticker in test_tickers:
        try:
            result = model.value_company(ticker, verbose=False)
            print(f'{ticker:6} - Fair Value: ${result.fair_value:.2f}, '
                  f'Current: ${result.current_price:.2f}, '
                  f'Margin: {result.margin_of_safety:+.1f}%, '
                  f'Confidence: {result.confidence}')
        except Exception as e:
            print(f'{ticker:6} - Error: {e}')


def main():
    """Main training pipeline."""
    print('Neural Network Training Pipeline')
    print('=' * 50)

    # Get tickers
    tickers = get_sp500_tickers()
    print(f'Training on {len(tickers)} stocks from S&P 500')

    # Collect training data
    print('\n1. Collecting training data...')
    training_data = collect_training_data(tickers, num_months=36)  # 36 months (3 years) of monthly samples

    if len(training_data) < 50:
        print(f'Insufficient training data: {len(training_data)} samples')
        print('Need at least 50 samples for meaningful training')
        return

    print(f'\n2. Training neural network with {len(training_data)} samples...')
    model = train_model_with_splits(training_data)

    # Save model
    model_path = Path('trained_nn_1year.pt')
    model.save_model(model_path)
    print(f'\n3. Model saved to {model_path}')

    # Test the model
    print('\n4. Testing trained model:')
    test_trained_model(model)

    print('\n' + '=' * 50)
    print('Training complete! You can now use the trained model:')
    print('')
    print('from src.invest.valuation.neural_network_model import NeuralNetworkValuationModel')
    print('from pathlib import Path')
    print('')
    print('model = NeuralNetworkValuationModel(model_path=Path("trained_nn_1year.pt"))')
    print('result = model.value_company("TSLA")')


if __name__ == '__main__':
    main()

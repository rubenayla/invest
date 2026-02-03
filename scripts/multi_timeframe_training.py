#!/usr/bin/env python3
"""
Train neural network models for multiple time horizons.

Tests the hypothesis that performance follows a bell curve:
- Short term (1-3 months): Too much noise, hard to predict
- Medium term (6-12 months): Sweet spot for fundamental analysis
- Long term (2-5 years): Too many macro factors, fundamental analysis less relevant
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.invest.valuation.neural_network_model import NeuralNetworkValuationModel


def get_test_stocks() -> List[str]:
    """Get diverse test stocks for multi-timeframe analysis."""
    return [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA',  # Tech
        'JPM', 'BAC', 'WFC', 'V', 'MA',           # Finance
        'JNJ', 'PFE', 'UNH', 'ABBV', 'LLY',      # Healthcare
        'WMT', 'PG', 'KO', 'HD', 'NKE'           # Consumer
    ]


def calculate_forward_return(ticker: str, start_date: datetime, months: int) -> float:
    """Calculate N-month forward return using 30-day averages."""
    try:
        import yfinance as yf

        end_date = start_date + timedelta(days=months * 30)

        # Get price data with buffer for averaging
        stock = yf.Ticker(ticker)
        hist = stock.history(
            start=start_date - timedelta(days=10),
            end=end_date + timedelta(days=40)
        )

        if len(hist) < (months * 20):  # Need enough data
            return None

        # Find start and end indices
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
        days_to_avg = min(30, len(hist) - start_idx)
        start_window = hist['Close'].iloc[start_idx:start_idx + days_to_avg]

        days_to_avg_end = min(30, len(hist) - max(0, end_idx - 29))
        end_window = hist['Close'].iloc[max(0, end_idx - 29):end_idx + 1]

        if len(start_window) < 10 or len(end_window) < 10:
            return None

        start_price = start_window.mean()
        end_price = end_window.mean()

        if start_price <= 0:
            return None

        return (end_price - start_price) / start_price

    except Exception as e:
        print(f'    Error calculating {months}m return for {ticker}: {e}')
        return None


def collect_timeframe_data(tickers: List[str], months_forward: int,
                          num_periods: int = 15) -> List[Tuple[str, Dict[str, Any], float]]:
    """
    Collect training data for specific time horizon.
    
    Parameters
    ----------
    tickers : List[str]
        Stock tickers to use
    months_forward : int
        Forward return horizon in months
    num_periods : int
        Number of historical periods to collect
    """
    training_data = []

    # Calculate how far back to start (need time for forward returns)
    lookback_months = months_forward + num_periods
    end_date = datetime.now() - timedelta(days=months_forward * 30)

    dates = []
    for p in range(num_periods):
        period_date = end_date - timedelta(days=p * 30)  # Monthly periods
        dates.append(period_date)

    print(f'Collecting {months_forward}-month horizon data:')
    print(f'  Periods: {len(dates)} from {dates[-1].strftime("%Y-%m-%d")} to {dates[0].strftime("%Y-%m-%d")}')

    successful_samples = 0

    for i, date in enumerate(dates):
        print(f'  Period {i+1}/{len(dates)}: {date.strftime("%Y-%m-%d")}', end=' ')
        period_samples = 0

        for ticker in tickers:
            try:
                # Get fundamental data (current - would need historical in production)
                import yfinance as yf
                stock = yf.Ticker(ticker)
                info = stock.info

                # Calculate forward return for this time horizon
                forward_return = calculate_forward_return(ticker, date, months_forward)

                if forward_return is None:
                    continue

                # Prepare data
                data = {
                    'info': info,
                    'financials': None,
                    'balance_sheet': None,
                    'cashflow': None
                }

                # Validate essential fields
                required_fields = ['currentPrice', 'marketCap', 'enterpriseValue', 'totalRevenue']
                if all(info.get(field) for field in required_fields):
                    training_data.append((ticker, data, forward_return))
                    period_samples += 1

            except Exception:
                continue

        successful_samples += period_samples
        print(f'({period_samples} samples)')

    print(f'  Total: {len(training_data)} samples for {months_forward}-month horizon')
    return training_data


def train_timeframe_model(training_data: List[Tuple[str, Dict[str, Any], float]],
                         timeframe_name: str, months: int) -> Dict[str, float]:
    """Train neural network for specific timeframe and evaluate."""
    if len(training_data) < 50:
        print(f'  Insufficient data: {len(training_data)} samples')
        return {}

    print(f'  Training {timeframe_name} model with {len(training_data)} samples...')

    # Create model with timeframe in name
    model = NeuralNetworkValuationModel(time_horizon=timeframe_name)

    try:
        # Train with shorter epochs for multi-timeframe comparison
        metrics = model.train_model(
            training_data,
            validation_split=0.25,
            epochs=20  # Shorter for comparison
        )

        # Save model
        model_path = Path(f'trained_nn_{timeframe_name}.pt')
        model.save_model(model_path)

        print(f'    Training Loss: {metrics["final_train_loss"]:.2f}')
        print(f'    Validation Loss: {metrics["final_val_loss"]:.2f}')
        print(f'    Validation MAE: {metrics["val_mae"]:.3f}')
        print(f'    Model saved: {model_path}')

        return {
            'timeframe': timeframe_name,
            'months': months,
            'samples': len(training_data),
            'train_loss': metrics["final_train_loss"],
            'val_loss': metrics["final_val_loss"],
            'val_mae': metrics["val_mae"],
            'model_path': str(model_path)
        }

    except Exception as e:
        print(f'    Training failed: {e}')
        return {}


def test_timeframe_predictions(timeframe_results: List[Dict]) -> Dict[str, Dict]:
    """Test all trained models on recent stock performance."""
    print('\nTesting timeframe models on recent performance...')

    test_stocks = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
    comparison_results = {}

    for result in timeframe_results:
        if not result or 'model_path' not in result:
            continue

        timeframe_name = result['timeframe']
        months = result['months']
        model_path = Path(result['model_path'])

        if not model_path.exists():
            continue

        print(f'\n  Testing {timeframe_name} model:')

        try:
            # Load trained model
            model = NeuralNetworkValuationModel(model_path=model_path)

            predictions = []
            actuals = []

            for ticker in test_stocks:
                try:
                    # Get model prediction
                    result_obj = model.value_company(ticker, verbose=False)
                    if not result_obj or not result_obj.fair_value:
                        continue

                    predicted_return = (result_obj.fair_value - result_obj.current_price) / result_obj.current_price

                    # Get actual return for this timeframe
                    actual_return = calculate_forward_return(
                        ticker,
                        datetime.now() - timedelta(days=months * 30),
                        months
                    )

                    if actual_return is not None:
                        predictions.append(predicted_return)
                        actuals.append(actual_return)

                        print(f'    {ticker}: Pred {predicted_return:+.1%}, Actual {actual_return:+.1%}')

                except Exception as e:
                    print(f'    {ticker}: Error - {e}')
                    continue

            if len(predictions) >= 3:
                predictions = np.array(predictions)
                actuals = np.array(actuals)

                mae = np.mean(np.abs(predictions - actuals))
                correlation = np.corrcoef(predictions, actuals)[0,1] if len(predictions) > 1 else 0
                hit_rate = np.sum(np.sign(predictions) == np.sign(actuals)) / len(predictions)

                comparison_results[timeframe_name] = {
                    'months': months,
                    'predictions': len(predictions),
                    'mae': mae,
                    'correlation': correlation,
                    'hit_rate': hit_rate,
                    'val_mae': result.get('val_mae', 0)
                }

                print(f'    Results: MAE={mae:.3f}, Corr={correlation:.3f}, Hit Rate={hit_rate:.1%}')
            else:
                print('    Insufficient test data')

        except Exception as e:
            print(f'    Model test failed: {e}')
            continue

    return comparison_results


def analyze_performance_curve(comparison_results: Dict[str, Dict]) -> None:
    """Analyze if performance follows the expected bell curve."""
    print('\n' + '=' * 60)
    print('MULTI-TIMEFRAME PERFORMANCE ANALYSIS')
    print('=' * 60)

    if len(comparison_results) < 3:
        print('Insufficient results for curve analysis')
        return

    # Sort by timeframe
    sorted_results = sorted(comparison_results.items(), key=lambda x: x[1]['months'])

    print('\nPerformance by Time Horizon:')
    print(f'{"Timeframe":<12} {"Months":<7} {"Test MAE":<9} {"Val MAE":<8} {"Correlation":<12} {"Hit Rate":<10}')
    print('-' * 70)

    correlations = []
    timeframes = []

    for name, data in sorted_results:
        correlations.append(data['correlation'])
        timeframes.append(data['months'])

        print(f'{name:<12} {data["months"]:<7} {data["mae"]:<9.3f} {data["val_mae"]:<8.3f} '
              f'{data["correlation"]:<12.3f} {data["hit_rate"]:<10.1%}')

    # Find performance peak
    if correlations:
        best_idx = np.argmax(correlations)
        best_timeframe = timeframes[best_idx]
        best_correlation = correlations[best_idx]

        print(f'\nBest Performance: {best_timeframe} months (correlation: {best_correlation:.3f})')

        # Check for bell curve pattern
        print('\nBell Curve Analysis:')

        if len(correlations) >= 3:
            short_term_avg = np.mean(correlations[:len(correlations)//3])
            medium_term_avg = np.mean(correlations[len(correlations)//3:2*len(correlations)//3])
            long_term_avg = np.mean(correlations[2*len(correlations)//3:])

            print(f'  Short-term average (≤{timeframes[len(timeframes)//3-1]}m): {short_term_avg:.3f}')
            print(f'  Medium-term average: {medium_term_avg:.3f}')
            print(f'  Long-term average (≥{timeframes[2*len(timeframes)//3]}m): {long_term_avg:.3f}')

            if medium_term_avg > short_term_avg and medium_term_avg > long_term_avg:
                print('\n✓ Bell curve pattern confirmed! Medium-term performs best.')
            else:
                print('\n? Bell curve pattern not clear in this data.')

        # Investment recommendations
        print('\nRecommendations:')
        print(f'  • Use {best_timeframe}-month model for highest accuracy')
        print(f'  • Correlation {best_correlation:.3f} suggests {"strong" if best_correlation > 0.6 else "moderate" if best_correlation > 0.3 else "weak"} predictive power')

        # Save detailed results
        results_path = Path('multi_timeframe_results.json')
        with open(results_path, 'w') as f:
            json.dump(comparison_results, f, indent=2, default=str)
        print(f'  • Detailed results saved to {results_path}')


def main():
    """Main multi-timeframe training pipeline."""
    print('Multi-Timeframe Neural Network Training')
    print('=' * 50)
    print('Testing hypothesis: Performance follows bell curve with medium-term peak')

    # Define timeframes to test
    timeframes = [
        ('1month', 1),
        ('3month', 3),
        ('6month', 6),
        ('1year', 12),
        ('18month', 18),
        ('2year', 24),
        ('3year', 36)
    ]

    tickers = get_test_stocks()
    print(f'Using {len(tickers)} test stocks')

    timeframe_results = []

    # Train models for each timeframe
    print('\n' + '=' * 50)
    print('TRAINING PHASE')
    print('=' * 50)

    for timeframe_name, months in timeframes:
        print(f'\n{timeframe_name.upper()} ({months} months):')

        # Collect training data for this timeframe
        training_data = collect_timeframe_data(tickers, months, num_periods=12)

        # Train model
        result = train_timeframe_model(training_data, timeframe_name, months)
        if result:
            timeframe_results.append(result)

    # Test all models
    print('\n' + '=' * 50)
    print('TESTING PHASE')
    print('=' * 50)

    comparison_results = test_timeframe_predictions(timeframe_results)

    # Analyze performance curve
    analyze_performance_curve(comparison_results)


if __name__ == '__main__':
    main()

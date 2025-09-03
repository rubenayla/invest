#!/usr/bin/env python3
"""
Demo script for the Neural Network Valuation Model.

This script demonstrates:
1. Basic usage of the neural network model
2. Training with historical data
3. Making predictions on new stocks
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.invest.valuation.model_registry import ModelRegistry
from src.invest.valuation.neural_network_model import NeuralNetworkValuationModel
import yfinance as yf


def demo_basic_usage():
    """Demonstrate basic usage of the neural network model."""
    print('=' * 60)
    print('Neural Network Valuation Model Demo')
    print('=' * 60)
    
    # Get model from registry
    registry = ModelRegistry()
    model = registry.get_model('neural_network')
    
    print('\n1. Testing with a well-known stock (AAPL):')
    print('-' * 40)
    
    try:
        # Fetch data for Apple
        ticker = 'AAPL'
        stock = yf.Ticker(ticker)
        data = {
            'info': stock.info,
            'financials': stock.financials,
            'balance_sheet': stock.balance_sheet,
            'cashflow': stock.cashflow
        }
        
        # Check if model is suitable
        if model.is_suitable(ticker, data):
            print(f'✓ Model is suitable for {ticker}')
            
            # Perform valuation
            result = model._calculate_valuation(ticker, data)
            
            print(f'\nValuation Results for {ticker}:')
            print(f'  Current Price: ${result.current_price:.2f}')
            print(f'  Fair Value: ${result.fair_value:.2f}')
            print(f'  Margin of Safety: {result.margin_of_safety:.1f}%')
            print(f'  Model Score: {result.inputs.get("model_score", 0):.1f}/100')
            print(f'  Confidence: {result.confidence}')
            
            if result.warnings:
                print('\n  Warnings:')
                for warning in result.warnings:
                    print(f'    ⚠ {warning}')
        else:
            print(f'✗ Model not suitable for {ticker}')
            
    except Exception as e:
        print(f'Error: {e}')
    
    print('\n' + '=' * 60)


def demo_training_workflow():
    """Demonstrate training the neural network model."""
    print('\n2. Training the Neural Network Model:')
    print('-' * 40)
    print('Note: This is a simplified demo with limited data.')
    print('In production, use much more historical data.')
    
    # Create a new model instance for training
    model = NeuralNetworkValuationModel(time_horizon='1year')
    
    # Prepare training data (simplified demo)
    print('\nPreparing training data...')
    training_data = []
    
    # Sample tickers for training (use more in production)
    tickers = ['MSFT', 'GOOGL', 'JNJ', 'JPM', 'V']
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            data = {
                'info': stock.info,
                'financials': stock.financials,
                'balance_sheet': stock.balance_sheet,
                'cashflow': stock.cashflow
            }
            
            # Simplified target: Use P/E ratio as proxy for expected return
            # In production, use actual historical returns
            pe_ratio = data['info'].get('trailingPE', 20)
            if pe_ratio and pe_ratio > 0:
                # Lower P/E suggests higher expected return
                target_return = (30 - pe_ratio) / 100  # Simplified
                target_return = max(-0.5, min(0.5, target_return))  # Cap at ±50%
                
                training_data.append((ticker, data, target_return))
                print(f'  ✓ Added {ticker} with target return {target_return:.1%}')
        except Exception as e:
            print(f'  ✗ Failed to add {ticker}: {e}')
    
    if len(training_data) >= 3:
        print(f'\nTraining model with {len(training_data)} samples...')
        try:
            metrics = model.train_model(
                training_data,
                validation_split=0.2,
                epochs=10  # Use more epochs in production
            )
            
            print('\nTraining Results:')
            print(f'  Final Training Loss: {metrics["final_train_loss"]:.4f}')
            print(f'  Final Validation Loss: {metrics["final_val_loss"]:.4f}')
            print(f'  Training MAE: {metrics["train_mae"]:.2f}')
            print(f'  Validation MAE: {metrics["val_mae"]:.2f}')
            
            # Save the trained model
            model_path = Path('trained_nn_model.pt')
            model.save_model(model_path)
            print(f'\n✓ Model saved to {model_path}')
            
        except Exception as e:
            print(f'Training failed: {e}')
    else:
        print('Insufficient data for training demo')


def demo_different_horizons():
    """Demonstrate using different time horizons."""
    print('\n3. Different Time Horizons:')
    print('-' * 40)
    
    ticker = 'TSLA'
    print(f'Analyzing {ticker} with different time horizons...\n')
    
    try:
        # Fetch data once
        stock = yf.Ticker(ticker)
        data = {
            'info': stock.info,
            'financials': stock.financials,
            'balance_sheet': stock.balance_sheet,
            'cashflow': stock.cashflow
        }
        
        horizons = ['1month', '1year', '5year']
        
        for horizon in horizons:
            model = NeuralNetworkValuationModel(time_horizon=horizon)
            
            if model.is_suitable(ticker, data):
                result = model._calculate_valuation(ticker, data)
                print(f'{horizon:8} - Fair Value: ${result.fair_value:.2f}, '
                      f'Margin: {result.margin_of_safety:+.1f}%')
            else:
                print(f'{horizon:8} - Model not suitable')
                
    except Exception as e:
        print(f'Error analyzing {ticker}: {e}')


def main():
    """Run all demos."""
    print('\n' + '=' * 60)
    print('NEURAL NETWORK VALUATION MODEL - DEMO')
    print('=' * 60)
    
    # Basic usage
    demo_basic_usage()
    
    # Training workflow
    demo_training_workflow()
    
    # Different time horizons
    demo_different_horizons()
    
    print('\n' + '=' * 60)
    print('Demo completed!')
    print('=' * 60)
    print('\nKey Takeaways:')
    print('1. The model works with any stock that has sufficient data')
    print('2. Without training, it uses heuristic scoring')
    print('3. Training improves accuracy significantly')
    print('4. Different time horizons can give different valuations')
    print('5. Always verify results with fundamental analysis')


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
Run multi-horizon neural network predictions on all stocks in dashboard_data.json.
"""

import json
import sys
import torch
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from invest.valuation.multi_horizon_nn import MultiHorizonValuationModel
from invest.valuation.neural_network_model import FeatureEngineer
from invest.valuation.db_utils import get_db_connection, save_nn_prediction


def load_stock_cache(ticker: str, stock_cache_dir: Path) -> dict:
    """Load stock data from SQLite database (or fallback to JSON cache)."""
    # Try SQLite first
    try:
        import sys
        sys.path.insert(0, str(project_root / 'src'))
        from invest.data.stock_data_reader import StockDataReader

        reader = StockDataReader()
        stock_data = reader.get_stock_data(ticker)

        if stock_data:
            # Transform to format expected by FeatureEngineer
            return {
                'info': stock_data.get('info', {}),
                'financials': stock_data.get('financials', {}),
                'history': stock_data.get('price_data', {}),
                'cashflow': stock_data.get('cashflow', []),
                'balance_sheet': stock_data.get('balance_sheet', []),
                'income': stock_data.get('income', []),
            }
    except Exception as e:
        pass  # Silently fall back to JSON

    # Fallback to JSON cache
    cache_file = stock_cache_dir / f'{ticker}.json'
    if not cache_file.exists():
        return None

    with open(cache_file) as f:
        cache_data = json.load(f)

    stock_data = {
        'info': cache_data.get('info', {}),
        'financials': cache_data.get('financials', {}),
        'history': cache_data.get('price_data', {}),
    }

    return stock_data




def main():
    """Run predictions on all stocks in the dashboard."""

    print('🚀 Running Multi-Horizon NN predictions on dashboard stocks')
    print('=' * 60)

    # Load dashboard data
    dashboard_data_path = project_root / 'dashboard' / 'dashboard_data.json'
    print(f'\n📂 Loading dashboard data: {dashboard_data_path}')

    with open(dashboard_data_path) as f:
        data = json.load(f)

    stocks = data.get('stocks', {})
    print(f'   Found {len(stocks)} stocks')

    # Stock cache directory
    stock_cache_dir = project_root / 'data' / 'stock_cache'
    print(f'\n📦 Stock cache directory: {stock_cache_dir}')

    # Load model
    model_path = project_root / 'neural_network' / 'models' / 'multi_horizon_model.pt'
    if not model_path.exists():
        raise FileNotFoundError(
            'Multi-horizon model not found. Expected: '
            f'{model_path}'
        )
    print(f'\n🔧 Loading model from: {model_path}')

    checkpoint = torch.load(model_path, map_location='cpu')
    feature_dim = checkpoint['feature_dim']

    # Initialize model and load weights
    model = MultiHorizonValuationModel(feature_dim=feature_dim)
    model.model.load_state_dict(checkpoint['model_state_dict'])
    model.model.eval()

    print(f'   Model loaded successfully (feature_dim={feature_dim})')

    # Initialize feature engineer
    feature_engineer = FeatureEngineer()

    # Connect to database
    print(f'\n💾 Connecting to database...')
    db_conn = get_db_connection()
    print(f'   Database connected')

    # Run predictions on each stock
    print(f'\n🔄 Running predictions...')
    success_count = 0
    error_count = 0
    cache_miss_count = 0
    db_save_count = 0

    for i, (ticker, stock) in enumerate(stocks.items()):
        try:
            # Load stock data from cache
            stock_data = load_stock_cache(ticker, stock_cache_dir)

            if not stock_data:
                cache_miss_count += 1
                if 'valuations' not in stock:
                    stock['valuations'] = {}
                stock['valuations']['multi_horizon_nn'] = {
                    'error': 'Stock cache file not found',
                    'suitable': False
                }
                continue

            # Get current price
            current_price = stock_data['info'].get('currentPrice')
            if not current_price:
                current_price = stock_data['info'].get('regularMarketPrice', 100.0)

            # Extract features using FeatureEngineer
            features = feature_engineer.extract_features(stock_data)

            # Convert features dict to numpy array in correct order
            feature_array = np.array([features.get(name, 0.0) for name in checkpoint['feature_names']])

            # Run prediction
            prediction = model.predict(feature_array, current_price)
            prediction.ticker = ticker

            # Format result for dashboard (matching other models' format)
            # Convert numpy types to Python types for JSON serialization
            fair_value = float(prediction.fair_values[prediction.recommended_horizon])
            margin_of_safety = (fair_value - current_price) / current_price if current_price > 0 else 0
            upside_pct = ((fair_value / current_price) - 1) * 100 if current_price > 0 else 0

            details = {
                'predictions': {k: float(v) for k, v in prediction.predictions.items()},
                'fair_values': {k: float(v) for k, v in prediction.fair_values.items()},
                'confidence_scores': {k: float(v) for k, v in prediction.confidence_scores.items()},
                'recommended_horizon': prediction.recommended_horizon,
                'overall_score': float(prediction.overall_score)
            }

            result = {
                'fair_value': fair_value,
                'upside': float(upside_pct),
                'margin_of_safety': float(margin_of_safety),
                'suitable': True,
                'details': details
            }

            # Add to stock valuations
            if 'valuations' not in stock:
                stock['valuations'] = {}

            stock['valuations']['multi_horizon_nn'] = result

            # Also store current_price at stock level for dashboard display
            stock['current_price'] = float(current_price)

            save_nn_prediction(
                db_conn,
                'multi_horizon_nn',
                ticker,
                fair_value,
                float(current_price),
                float(margin_of_safety),
                float(upside_pct),
                confidence=float(prediction.overall_score),
                details=details
            )
            db_save_count += 1

            success_count += 1

            if (i + 1) % 50 == 0:
                print(f'   [{i+1}/{len(stocks)}] Processed {ticker}...')

        except Exception as e:
            import traceback
            if error_count < 3:  # Only print first 3 errors in detail
                print(f'   [{i+1}/{len(stocks)}] {ticker}: Error - {str(e)}')
                traceback.print_exc()
            if 'valuations' not in stock:
                stock['valuations'] = {}
            stock['valuations']['multi_horizon_nn'] = {
                'error': str(e),
                'suitable': False
            }
            error_count += 1

    # Close database connection
    db_conn.close()
    print(f'   Database connection closed')

    # Save updated data
    print(f'\n💾 Saving updated dashboard data...')
    with open(dashboard_data_path, 'w') as f:
        json.dump(data, f, indent=2)

    # Summary
    print(f'\n✅ Predictions complete!')
    print('=' * 60)
    print(f'📊 Summary:')
    print(f'   Successful predictions: {success_count}')
    print(f'   Saved to database: {db_save_count}')
    print(f'   Cache misses: {cache_miss_count}')
    print(f'   Errors: {error_count}')
    print(f'   Total stocks: {len(stocks)}')

    return 0


if __name__ == '__main__':
    sys.exit(main())

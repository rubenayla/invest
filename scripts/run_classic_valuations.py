#!/usr/bin/env python3
"""
Run classic valuation models (DCF, RIM, etc.) on all stocks in dashboard_data.json.

This script:
- Loads stock data from cache
- Runs classic valuation models (DCF, Enhanced DCF, RIM, Simple Ratios, etc.)
- Saves predictions to database
- Updates dashboard_data.json with valuation results
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from invest.valuation.model_registry import ModelRegistry
from invest.valuation.db_utils import get_db_connection, save_classic_prediction
from invest.valuation.base import ModelNotSuitableError
from invest.data.stock_data_reader import StockDataReader

# Models to run (excluding sector-specific and ensemble models for now)
# Format: (registry_name, db_name)
MODELS_TO_RUN = [
    ('dcf', 'dcf'),
    ('dcf_enhanced', 'enhanced_dcf'),
    ('rim', 'rim'),
    ('simple_ratios', 'simple_ratios'),
    ('growth_dcf', 'growth_dcf'),
    ('multi_stage_dcf', 'multi_stage_dcf'),
]


def load_stock_data(ticker: str, reader: StockDataReader) -> Optional[dict]:
    """
    Load stock data from SQLite database and convert to model-compatible format.

    Converts JSON-stored financial statements back to pandas DataFrames
    that valuation models expect.
    """
    cache_data = reader.get_stock_data(ticker)
    if not cache_data:
        return None

    # Convert JSON financial statements back to DataFrames
    # Models expect: {info: dict, cashflow: DataFrame, balance_sheet: DataFrame, income: DataFrame}
    # StockDataReader already merges financials into info, so just use it directly
    stock_data = {
        'info': cache_data.get('info', {})
    }

    # Convert cashflow from list of records to DataFrame
    # yfinance format: rows=metrics (Free Cash Flow, etc), columns=dates (timestamps)
    if 'cashflow' in cache_data and cache_data['cashflow']:
        try:
            df = pd.DataFrame(cache_data['cashflow'])
            # Set the metric name column as index
            if 'index' in df.columns:
                df = df.set_index('index')
            # No transpose needed - orient=records already has correct orientation
            stock_data['cashflow'] = df
        except Exception as e:
            print(f'Warning: Could not convert cashflow for {ticker}: {e}')

    # Convert balance_sheet from list of records to DataFrame
    if 'balance_sheet' in cache_data and cache_data['balance_sheet']:
        try:
            df = pd.DataFrame(cache_data['balance_sheet'])
            if 'index' in df.columns:
                df = df.set_index('index')
            stock_data['balance_sheet'] = df
        except Exception as e:
            print(f'Warning: Could not convert balance_sheet for {ticker}: {e}')

    # Convert income statement from list of records to DataFrame
    if 'income' in cache_data and cache_data['income']:
        try:
            df = pd.DataFrame(cache_data['income'])
            if 'index' in df.columns:
                df = df.set_index('index')
            stock_data['income'] = df
        except Exception as e:
            print(f'Warning: Could not convert income for {ticker}: {e}')

    return stock_data


def run_valuation(registry_name: str, ticker: str, stock_data: dict) -> Optional[dict]:
    """
    Run a single valuation model on a stock.

    Parameters
    ----------
    registry_name : str
        Model name as used in the ModelRegistry
    ticker : str
        Stock ticker
    stock_data : dict
        Stock data from cache

    Returns
    -------
    dict
        Valuation result or error information
    """
    registry = ModelRegistry()

    try:
        # Get model instance
        model = registry.get_model(registry_name)

        # Check if model is suitable for this stock
        if not model.is_suitable(ticker, stock_data):
            raise ModelNotSuitableError(ticker, f'Model {registry_name} not suitable', 'Data requirements not met')

        # Validate inputs
        model._validate_inputs(ticker, stock_data)

        # Run valuation
        result = model._calculate_valuation(ticker, stock_data)

        # Format result for dashboard
        details = {}
        if hasattr(result, 'inputs'):
            details.update(result.inputs)
        if hasattr(result, 'outputs'):
            details.update(result.outputs)

        return {
            'fair_value': float(result.fair_value),
            'current_price': float(result.current_price),
            'margin_of_safety': float(result.margin_of_safety),
            'upside': float(((result.fair_value / result.current_price) - 1) * 100) if result.current_price > 0 else 0,
            'suitable': True,
            'confidence': result.confidence,
            'details': details
        }

    except ModelNotSuitableError as e:
        return {
            'suitable': False,
            'error': str(e),
            'reason': e.reason if hasattr(e, 'reason') else 'Model not suitable for this stock'
        }

    except Exception as e:
        return {
            'suitable': False,
            'error': str(e),
            'reason': f'Unexpected error: {type(e).__name__}'
        }


def main():
    """Run classic valuations on all stocks in the dashboard."""

    print('🚀 Running Classic Valuation Models on dashboard stocks')
    print('=' * 60)

    # Load dashboard data
    dashboard_data_path = project_root / 'dashboard' / 'dashboard_data.json'
    print(f'\n📂 Loading dashboard data: {dashboard_data_path}')

    with open(dashboard_data_path) as f:
        data = json.load(f)

    stocks = data.get('stocks', {})
    print(f'   Found {len(stocks)} stocks')

    # Initialize stock data reader
    print(f'\n📦 Initializing stock data reader (SQLite database)...')
    reader = StockDataReader()
    print(f'   Reader initialized')

    # Connect to database
    print(f'\n💾 Connecting to valuation database...')
    db_conn = get_db_connection()
    print(f'   Database connected')

    # Statistics
    stats = {db_name: {'success': 0, 'unsuitable': 0, 'error': 0, 'cache_miss': 0} for _, db_name in MODELS_TO_RUN}

    # Run valuations on each stock
    print(f'\n🔄 Running valuations...')
    print(f'   Models: {", ".join(db_name for _, db_name in MODELS_TO_RUN)}')

    for i, (ticker, stock) in enumerate(stocks.items()):
        # Load stock data from SQLite
        stock_data = load_stock_data(ticker, reader)

        if not stock_data:
            for _, db_name in MODELS_TO_RUN:
                stats[db_name]['cache_miss'] += 1
                if 'valuations' not in stock:
                    stock['valuations'] = {}
                stock['valuations'][db_name] = {
                    'error': 'Stock cache file not found',
                    'suitable': False
                }
            continue

        # Initialize valuations dict if needed
        if 'valuations' not in stock:
            stock['valuations'] = {}

        # Run each model
        for registry_name, db_name in MODELS_TO_RUN:
            try:
                result = run_valuation(registry_name, ticker, stock_data)

                # Store in dashboard data (using DB name for consistency)
                stock['valuations'][db_name] = result

                # Save to database if suitable
                if result.get('suitable', False):
                    save_classic_prediction(
                        db_conn,
                        db_name,
                        ticker,
                        result['fair_value'],
                        result['current_price'],
                        result.get('margin_of_safety'),
                        result.get('upside'),
                        suitable=True,
                        details=result.get('details')
                    )
                    stats[db_name]['success'] += 1
                else:
                    # Save failure to database
                    save_classic_prediction(
                        db_conn,
                        db_name,
                        ticker,
                        0.0,  # fair_value not applicable
                        stock_data.get('info', {}).get('currentPrice', 0.0),
                        None,
                        None,
                        suitable=False,
                        failure_reason=result.get('reason', result.get('error', 'Unknown'))
                    )

                    if 'error' in result:
                        stats[db_name]['error'] += 1
                    else:
                        stats[db_name]['unsuitable'] += 1

            except Exception as e:
                print(f'   [{i+1}/{len(stocks)}] {ticker} - {db_name}: Unexpected error - {str(e)}')
                stock['valuations'][db_name] = {
                    'error': str(e),
                    'suitable': False
                }
                stats[db_name]['error'] += 1

        # Progress update
        if (i + 1) % 50 == 0:
            print(f'   [{i+1}/{len(stocks)}] Processed {ticker}...')

    # Close database connection
    db_conn.close()
    print(f'   Database connection closed')

    # Save updated data
    print(f'\n💾 Saving updated dashboard data...')
    with open(dashboard_data_path, 'w') as f:
        json.dump(data, f, indent=2)

    # Summary
    print(f'\n✅ Classic valuations complete!')
    print('=' * 60)
    print(f'📊 Results by model:')
    print()

    for _, db_name in MODELS_TO_RUN:
        model_stats = stats[db_name]
        total = sum(model_stats.values())
        print(f'{db_name:20} - Success: {model_stats["success"]:3} | '
              f'Unsuitable: {model_stats["unsuitable"]:3} | '
              f'Errors: {model_stats["error"]:3} | '
              f'Cache miss: {model_stats["cache_miss"]:3} | '
              f'Total: {total:3}')

    print()
    print(f'Total stocks processed: {len(stocks)}')

    return 0


if __name__ == '__main__':
    sys.exit(main())

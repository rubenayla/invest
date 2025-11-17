#!/usr/bin/env python3
"""
Generate the main valuation dashboard.

This is THE ONLY dashboard script you need to run.

Usage:
    uv run python scripts/dashboard.py

Reads ALL data from SQLite database (single source of truth):
- Stock info from current_stock_data table
- Valuation results from valuation_results table

Output:
    dashboard/valuation_dashboard.html
"""

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from invest.dashboard_components.html_generator import HTMLGenerator


def load_stocks_from_database() -> dict:
    """
    Load all stock data and valuations from database.

    Returns
    -------
    dict
        Stock data in format expected by HTMLGenerator:
        {
            'AAPL': {
                'ticker': 'AAPL',
                'company_name': 'Apple Inc.',
                'valuations': {
                    'single_horizon_nn': {...},
                    'dcf': {...},
                    ...
                }
            },
            ...
        }
    """
    db_path = project_root / 'data' / 'stock_data.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Access columns by name

    # Get all stocks with current price
    stocks_query = '''
        SELECT ticker, current_price, long_name, short_name, sector
        FROM current_stock_data
        WHERE current_price IS NOT NULL
    '''
    stocks = {}

    for row in conn.execute(stocks_query).fetchall():
        ticker = row['ticker']
        stocks[ticker] = {
            'ticker': ticker,
            'company_name': row['long_name'] or row['short_name'] or ticker,
            'sector': row['sector'],
            'current_price': row['current_price'],  # Add price from current_stock_data
            'valuations': {}
        }

    print(f'Loaded {len(stocks)} stocks from current_stock_data')

    # Get all valuation results (including unsuitable ones with error messages)
    valuations_query = '''
        SELECT ticker, model_name, suitable, fair_value, current_price,
               margin_of_safety, upside_pct, confidence, error_message,
               failure_reason, details_json, timestamp
        FROM valuation_results
    '''

    valuation_count = 0
    latest_price_by_ticker = {}
    for row in conn.execute(valuations_query).fetchall():
        ticker = row['ticker']

        # Skip if ticker not in stocks (shouldn't happen, but defensive)
        if ticker not in stocks:
            continue

        model_name = row['model_name']

        if row['suitable']:
            # Successful valuation
            valuation = {
                'suitable': True,
                'fair_value': row['fair_value'],
                'current_price': row['current_price'],
                'margin_of_safety': row['margin_of_safety'],
                'upside': row['upside_pct'],
                'confidence': row['confidence']
            }

            # Parse details JSON if present
            if row['details_json']:
                try:
                    valuation['details'] = json.loads(row['details_json'])
                except json.JSONDecodeError:
                    valuation['details'] = {}

            stocks[ticker]['valuations'][model_name] = valuation
            valuation_count += 1

            # Track latest price used in valuations for dashboard price column
            if row['current_price'] is not None and row['timestamp'] is not None:
                try:
                    ts = datetime.fromisoformat(row['timestamp'])
                except ValueError:
                    ts = None

                prev = latest_price_by_ticker.get(ticker)
                if ts is not None:
                    if not prev or ts > prev['timestamp']:
                        latest_price_by_ticker[ticker] = {
                            'price': row['current_price'],
                            'timestamp': ts
                        }
        else:
            # Failed valuation
            stocks[ticker]['valuations'][model_name] = {
                'suitable': False,
                'error': row['error_message'],
                'reason': row['failure_reason']
            }

    # Override displayed current price with the latest valuation price when available
    for ticker, price_data in latest_price_by_ticker.items():
        stocks[ticker]['current_price'] = price_data['price']

    conn.close()

    print(f'Loaded {valuation_count} successful valuations')

    return stocks


def main():
    """Regenerate dashboard HTML from database."""

    print('🔄 Regenerating dashboard HTML from database...')
    print('=' * 60)

    # Load all data from database (ONLY source)
    print('\n📂 Loading data from SQLite database...')
    stocks_data = load_stocks_from_database()

    # Count predictions by model
    model_counts = {}
    for stock in stocks_data.values():
        for model_name, valuation in stock.get('valuations', {}).items():
            if valuation.get('suitable'):
                model_counts[model_name] = model_counts.get(model_name, 0) + 1

    print('\nValuation counts by model:')
    for model_name, count in sorted(model_counts.items()):
        print(f'  {model_name:20s}: {count:3d} successful')

    # Generate HTML
    print('\n🎨 Generating HTML...')
    generator = HTMLGenerator()

    # Create progress_data structure for the HTML generator
    progress_data = {
        'total_analyzed': len(stocks_data),
        'successful': len(stocks_data),
        'failed': 0
    }

    html = generator.generate_dashboard_html(stocks_data, progress_data)

    # Save HTML
    output_path = project_root / 'dashboard' / 'valuation_dashboard.html'
    with open(output_path, 'w') as f:
        f.write(html)

    print(f'\n✅ Dashboard HTML saved: {output_path}')
    print(f'   Total stocks: {len(stocks_data)}')
    print(f'   Total valuations: {sum(model_counts.values())}')
    print('\n💡 Open in browser: file://{}'.format(output_path.absolute()))

    return 0


if __name__ == '__main__':
    sys.exit(main())

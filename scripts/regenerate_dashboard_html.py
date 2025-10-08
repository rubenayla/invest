#!/usr/bin/env python3
"""
Regenerate dashboard HTML from existing dashboard_data.json.
Does NOT re-run valuations - just generates HTML from stored data.
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from invest.dashboard_components.html_generator import HTMLGenerator
from invest.data.stock_data_reader import StockDataReader


def main():
    """Regenerate dashboard HTML from existing data."""

    print('🔄 Regenerating dashboard HTML from existing data...')
    print('=' * 60)

    # Load existing dashboard data
    dashboard_data_path = project_root / 'dashboard' / 'dashboard_data.json'
    print(f'\n📂 Loading: {dashboard_data_path}')

    if not dashboard_data_path.exists():
        print(f'❌ Error: {dashboard_data_path} not found!')
        return 1

    with open(dashboard_data_path) as f:
        data = json.load(f)

    stocks_data = data.get('stocks', {})

    # Enrich with company names from SQLite
    print('\n📊 Enriching with company names from SQLite...')
    reader = StockDataReader()
    enriched_count = 0
    for ticker in stocks_data:
        try:
            stock_info = reader.get_stock_data(ticker)
            if stock_info and stock_info.get('info'):
                stocks_data[ticker]['company_name'] = stock_info['info'].get('longName') or stock_info['info'].get('shortName') or ticker
                enriched_count += 1
        except Exception as e:
            stocks_data[ticker]['company_name'] = ticker  # Fallback to ticker
    print(f'   Enriched {enriched_count}/{len(stocks_data)} stocks with company names')
    print(f'   Found {len(stocks_data)} stocks')

    # Count stocks with multi_horizon_nn predictions
    with_predictions = sum(
        1 for stock in stocks_data.values()
        if stock.get('valuations', {}).get('multi_horizon_nn', {}).get('suitable')
    )
    print(f'   Multi-horizon predictions: {with_predictions}')

    # Generate HTML
    print('\n🎨 Generating HTML...')
    generator = HTMLGenerator()

    # Create minimal progress_data structure for the HTML generator
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
    print(f'   With multi-horizon predictions: {with_predictions}')
    print('\n💡 Open in browser: file://{}'.format(output_path.absolute()))

    return 0


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""
Generate a standalone dashboard for multi-horizon neural network predictions.

This script creates an HTML dashboard showing multi-horizon predictions
for a list of stocks with all 5 time horizons, confidence scores, and recommendations.
"""

import sys
from pathlib import Path
import json
from datetime import datetime
import yfinance as yf

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.demo_multi_horizon_predictions import load_model, get_stock_data, make_prediction


def get_cache_tickers():
    """Get list of tickers from training cache."""
    cache_path = project_root / 'neural_network' / 'training' / 'training_data_cache_multi_horizon.json'

    if not cache_path.exists():
        # Fallback to default list if cache doesn't exist
        return [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK.B',
            'V', 'JPM', 'JNJ', 'WMT', 'MA', 'PG', 'UNH', 'HD', 'DIS', 'BAC',
            'NFLX', 'AMD', 'CRM', 'ADBE', 'PFE', 'KO', 'PEP', 'ORCL', 'INTC'
        ]

    try:
        with open(cache_path) as f:
            data = json.load(f)
        tickers = sorted(set(sample['ticker'] for sample in data['samples']))
        return tickers
    except Exception as e:
        print(f'⚠️ Warning: Could not load cache: {e}')
        return [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK.B',
            'V', 'JPM', 'JNJ', 'WMT', 'MA', 'PG', 'UNH', 'HD', 'DIS', 'BAC',
            'NFLX', 'AMD', 'CRM', 'ADBE', 'PFE', 'KO', 'PEP', 'ORCL', 'INTC'
        ]


def generate_html_dashboard(predictions_data, output_path='dashboard/multi_horizon_predictions.html'):
    """Generate HTML dashboard from predictions data."""

    # Generate table rows
    rows_html = ''
    for data in predictions_data:
        ticker = data['ticker']
        current_price = data['current_price']
        predictions = data['predictions']
        confidence_scores = data['confidence_scores']
        fair_values = data['fair_values']
        recommended_horizon = data['recommended_horizon']

        # Create horizon cells
        horizon_cells = ''
        for horizon in ['1m', '3m', '6m', '1y', '2y']:
            pred_return = predictions[horizon]
            fair_value = fair_values[horizon]
            confidence = confidence_scores[horizon]

            # Color based on return
            color_class = 'positive' if pred_return > 5 else 'neutral' if pred_return > -5 else 'negative'
            star = '⭐' if horizon == recommended_horizon else ''

            horizon_cells += f'''
            <td class="{color_class}">
                {star}<strong>{pred_return:+.1f}%</strong><br/>
                <small>${fair_value:.2f}</small><br/>
                <span class="confidence">{confidence:.0%}</span>
            </td>'''

        rows_html += f'''
        <tr>
            <td><strong>{ticker}</strong></td>
            <td>${current_price:.2f}</td>
            {horizon_cells}
            <td class="recommended">{recommended_horizon}</td>
        </tr>'''

    # Complete HTML
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multi-Horizon Neural Network Predictions</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}

        header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}

        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .stat-card h3 {{
            color: #667eea;
            font-size: 0.9em;
            margin-bottom: 5px;
        }}

        .stat-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }}

        .table-container {{
            padding: 30px;
            overflow-x: auto;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
        }}

        th {{
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
        }}

        td {{
            padding: 15px;
            border-bottom: 1px solid #e0e0e0;
            text-align: center;
        }}

        td:first-child {{
            text-align: left;
            font-weight: bold;
        }}

        td:nth-child(2) {{
            text-align: right;
        }}

        tr:hover {{
            background: #f8f9fa;
        }}

        .positive {{
            background: #d4edda;
            color: #155724;
        }}

        .negative {{
            background: #f8d7da;
            color: #721c24;
        }}

        .neutral {{
            background: #fff3cd;
            color: #856404;
        }}

        .confidence {{
            display: inline-block;
            padding: 2px 8px;
            background: rgba(102, 126, 234, 0.2);
            border-radius: 10px;
            font-size: 0.85em;
            color: #667eea;
        }}

        .recommended {{
            font-size: 1.2em;
            font-weight: bold;
            color: #667eea;
        }}

        footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 1px solid #e0e0e0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🧠 Multi-Horizon Neural Network Predictions</h1>
            <p>AI-powered stock predictions across 5 time horizons with confidence scores</p>
            <p><small>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
        </header>

        <div class="stats">
            <div class="stat-card">
                <h3>Stocks Analyzed</h3>
                <div class="value">{len(predictions_data)}</div>
            </div>
            <div class="stat-card">
                <h3>Time Horizons</h3>
                <div class="value">5</div>
            </div>
            <div class="stat-card">
                <h3>Model Features</h3>
                <div class="value">47</div>
            </div>
            <div class="stat-card">
                <h3>Training Samples</h3>
                <div class="value">3,367</div>
            </div>
        </div>

        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Ticker</th>
                        <th>Current Price</th>
                        <th>1 Month<br/><small>Return / Target / Conf</small></th>
                        <th>3 Months<br/><small>Return / Target / Conf</small></th>
                        <th>6 Months<br/><small>Return / Target / Conf</small></th>
                        <th>1 Year<br/><small>Return / Target / Conf</small></th>
                        <th>2 Years<br/><small>Return / Target / Conf</small></th>
                        <th>Recommended<br/><small>Horizon</small></th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>

        <footer>
            <p>⚠️ These predictions are for informational purposes only and should not be considered investment advice.</p>
            <p>Model trained on historical data (2004-2024) using 47 features including fundamentals and macroeconomic indicators.</p>
        </footer>
    </div>
</body>
</html>'''

    # Write to file
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html)

    print(f'✅ Dashboard generated: {output_path}')
    return output_path


def main():
    """Main execution function."""
    print('🚀 Multi-Horizon Dashboard Generator')
    print('='*60)

    # Load model
    print('\n📦 Loading model...')
    model, feature_names = load_model()

    # Get tickers from command line or use cache
    if len(sys.argv) > 1:
        tickers = sys.argv[1:]
    else:
        tickers = get_cache_tickers()

    print(f'\n📊 Analyzing {len(tickers)} stocks from training cache...')

    predictions_data = []
    successful = 0
    failed = 0

    for i, ticker in enumerate(tickers, 1):
        try:
            print(f'  [{i}/{len(tickers)}] {ticker}... ', end='', flush=True)

            prediction = make_prediction(model, feature_names, ticker)

            if prediction:
                predictions_data.append({
                    'ticker': ticker,
                    'current_price': prediction.current_price,
                    'predictions': prediction.predictions,
                    'confidence_scores': prediction.confidence_scores,
                    'fair_values': prediction.fair_values,
                    'recommended_horizon': prediction.recommended_horizon,
                })
                print('✅')
                successful += 1
            else:
                print('❌ No data')
                failed += 1
        except Exception as e:
            print(f'❌ Error: {e}')
            failed += 1

    print(f'\n📈 Analysis complete: {successful} successful, {failed} failed')

    if predictions_data:
        # Generate HTML dashboard
        print('\n🎨 Generating HTML dashboard...')
        dashboard_path = generate_html_dashboard(predictions_data)

        print(f'\n✅ Dashboard ready!')
        print(f'   Open: {dashboard_path.absolute()}')
    else:
        print('\n❌ No predictions generated. Cannot create dashboard.')
        sys.exit(1)


if __name__ == '__main__':
    main()

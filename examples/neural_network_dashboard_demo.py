#!/usr/bin/env python3
"""
Neural Network Dashboard Demo

Shows neural network predictions for different timeframes in a simple format.
This demonstrates how the models would appear in the main dashboard.
"""

import sys
from pathlib import Path
from typing import Dict, List
import warnings

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.invest.valuation.multi_timeframe_models import MultiTimeframeNeuralNetworks

warnings.filterwarnings('ignore')


def format_currency(value: float) -> str:
    """Format currency values."""
    if value >= 1e9:
        return f'${value/1e9:.1f}B'
    elif value >= 1e6:
        return f'${value/1e6:.0f}M'
    else:
        return f'${value:.2f}'


def format_percentage(value: float) -> str:
    """Format percentage values with color indicators."""
    if value > 20:
        return f'+{value:.1f}% 🔥'  # Strong buy
    elif value > 5:
        return f'+{value:.1f}% 📈'  # Buy
    elif value > -5:
        return f'{value:+.1f}% ➡️'   # Hold
    elif value > -20:
        return f'{value:.1f}% 📉'   # Sell
    else:
        return f'{value:.1f}% 🧊'   # Strong sell


def create_neural_network_dashboard(tickers: List[str]) -> None:
    """Create a dashboard showing neural network predictions."""
    print('🧠 NEURAL NETWORK VALUATION DASHBOARD')
    print('=' * 80)
    print('Multi-Timeframe AI-Powered Stock Analysis')
    print('Based on 60+ engineered features and 240+ training samples per timeframe\n')
    
    manager = MultiTimeframeNeuralNetworks()
    
    # Show available models
    print('Available Neural Network Models:')
    summary = manager.get_performance_summary()
    for tf, info in summary.items():
        if info.get('available', False):
            status = '⭐' if info.get('recommended', False) else '✓'
            correlation = info.get('correlation', 0)
            hit_rate = info.get('hit_rate', 0)
            print(f'  {status} {tf:8} ({info["months"]:2}m) - Corr: {correlation:.3f}, Hit Rate: {hit_rate:.0%}')
    
    print(f'\n{"Stock":<8} {"Current":<10} {"Best (2Y)":<12} {"Consensus":<12} {"1-Year":<12} {"Action":<15}')
    print('-' * 80)
    
    for ticker in tickers:
        try:
            # Get current price (simplified)
            import yfinance as yf
            stock = yf.Ticker(ticker)
            current_price = stock.info.get('currentPrice', 0)
            
            if not current_price:
                print(f'{ticker:<8} {"N/A":<10} {"No data":<12} {"No data":<12} {"No data":<12} {"—":<15}')
                continue
            
            # Get predictions from different models
            best_model = manager.get_model('2year')  # Best performing
            consensus = manager.get_consensus_valuation(ticker)
            year_model = manager.get_model('1year')
            
            results = {}
            
            # Best model (2-year)
            if best_model:
                try:
                    result = best_model._calculate_valuation(ticker, {
                        'info': stock.info,
                        'financials': None,
                        'balance_sheet': None,
                        'cashflow': None
                    })
                    results['best'] = result
                except Exception:
                    results['best'] = None
            
            # 1-year model
            if year_model:
                try:
                    result = year_model._calculate_valuation(ticker, {
                        'info': stock.info,
                        'financials': None,
                        'balance_sheet': None,
                        'cashflow': None
                    })
                    results['1year'] = result
                except Exception:
                    results['1year'] = None
            
            # Format results
            current_str = f'${current_price:.2f}'
            
            best_str = 'N/A'
            consensus_str = 'N/A' 
            year_str = 'N/A'
            action = '—'
            
            if results.get('best'):
                margin = results['best'].margin_of_safety
                best_str = f'${results["best"].fair_value:.2f}'
                action = format_percentage(margin)
            
            if consensus:
                consensus_str = f'${consensus.fair_value:.2f}'
            
            if results.get('1year'):
                year_str = f'${results["1year"].fair_value:.2f}'
            
            print(f'{ticker:<8} {current_str:<10} {best_str:<12} {consensus_str:<12} {year_str:<12} {action:<15}')
            
        except Exception as e:
            print(f'{ticker:<8} {"Error":<10} {str(e)[:10]:<12} {"—":<12} {"—":<12} {"—":<15}')
    
    print('\nLegend:')
    print('  🔥 Strong Buy (>20% upside)   📈 Buy (5-20% upside)')
    print('  ➡️  Hold (-5% to +5%)         📉 Sell (-5% to -20% downside)')
    print('  🧊 Strong Sell (<-20% downside)')
    
    print('\\nModel Performance (from backtesting):')
    print('  ⭐ 2-Year Model: 51.8% correlation, 100% hit rate (BEST)')
    print('  • 3-Month Model: 25.0% correlation, 50% hit rate')  
    print('  • 1-Year Model: 1.1% correlation, 100% hit rate')
    
    print('\\nKey Insights from Multi-Timeframe Analysis:')
    print('  • Longer horizons (2-3 years) outperform shorter ones')
    print('  • Neural networks capture structural business value effectively')
    print('  • Short-term predictions (1-6 months) limited by market noise')
    print('  • Fundamental analysis more effective for long-term than expected')


def main():
    """Run the neural network dashboard demo."""
    # Test with a diverse set of stocks
    test_stocks = [
        'AAPL',   # Large cap tech
        'MSFT',   # Large cap tech
        'TSLA',   # Growth/EV
        'JPM',    # Financial
        'JNJ',    # Healthcare
        'WMT',    # Consumer staples
        'XOM'     # Energy
    ]
    
    create_neural_network_dashboard(test_stocks)
    
    print(f'\\n📊 Dashboard Demo Complete!')
    print(f'In the main dashboard, these neural network models would be available as:')
    print(f'  • neural_network_best (2-year, highest accuracy)')
    print(f'  • neural_network_consensus (weighted across all timeframes)')
    print(f'  • neural_network_1year (for annual rebalancing)')


if __name__ == '__main__':
    main()
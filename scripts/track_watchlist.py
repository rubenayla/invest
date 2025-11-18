#!/usr/bin/env python
"""Track watchlist companies over time and identify momentum/value changes."""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import json
from pathlib import Path
import yaml

def load_watchlist():
    """Load watchlist from YAML config."""
    config_path = Path('notes/watchlist/watchlist.yaml')
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            tickers = []
            for category in config['watchlist'].values():
                tickers.extend([item['ticker'] for item in category])
            return list(set(tickers))  # Remove duplicates
    return []

def get_momentum_signals(ticker, days=30):
    """Get price momentum and volume signals."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=f'{days}d')
        
        if len(hist) < 2:
            return {}
        
        # Calculate momentum indicators
        price_change = (hist['Close'][-1] - hist['Close'][0]) / hist['Close'][0] * 100
        avg_volume = hist['Volume'].mean()
        recent_volume = hist['Volume'][-5:].mean()  # Last 5 days
        volume_surge = (recent_volume - avg_volume) / avg_volume * 100 if avg_volume > 0 else 0
        
        # RSI calculation (simplified)
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return {
            f'{days}d_price_change': price_change,
            f'{days}d_volume_surge': volume_surge,
            'rsi': rsi.iloc[-1] if len(rsi) > 0 else None,
            'price_trend': 'UP' if price_change > 5 else 'DOWN' if price_change < -5 else 'FLAT'
        }
    except:
        return {}

def analyze_watchlist_with_signals():
    """Analyze watchlist with momentum and timing signals."""
    tickers = load_watchlist()
    results = []
    
    print("Analyzing watchlist with momentum signals...")
    print("=" * 80)
    
    for ticker in tickers:
        print(f"Analyzing {ticker}...")
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Get basic metrics
            metrics = {
                'ticker': ticker,
                'current_price': info.get('currentPrice', 0),
                'pe_ratio': info.get('trailingPE'),
                'pb_ratio': info.get('priceToBook'),
                'roe': info.get('returnOnEquity'),
                '52w_high': info.get('fiftyTwoWeekHigh'),
                '52w_low': info.get('fiftyTwoWeekLow'),
            }
            
            # Add momentum signals
            momentum = get_momentum_signals(ticker)
            metrics.update(momentum)
            
            # Calculate buy signal strength
            buy_score = 0
            if metrics.get('pe_ratio') and metrics['pe_ratio'] < 20:
                buy_score += 2
            if metrics.get('30d_price_change') and metrics['30d_price_change'] < -10:
                buy_score += 2  # Oversold
            if metrics.get('rsi') and metrics['rsi'] < 30:
                buy_score += 3  # Strong oversold signal
            if metrics.get('30d_volume_surge') and metrics['30d_volume_surge'] > 50:
                buy_score += 1  # High interest
            
            metrics['buy_signal_strength'] = buy_score
            results.append(metrics)
            
        except Exception as e:
            print(f"  Error: {e}")
    
    # Convert to DataFrame and sort by buy signal
    df = pd.DataFrame(results)
    df = df.sort_values('buy_signal_strength', ascending=False)
    
    # Save results with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = Path('data/watchlist_tracking')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_dir / f'watchlist_{timestamp}.csv', index=False)
    df.to_csv('latest_watchlist_analysis.csv', index=False)
    
    print("\n" + "=" * 80)
    print("STRONGEST BUY SIGNALS")
    print("=" * 80)
    
    top_signals = df.head(5)
    for _, row in top_signals.iterrows():
        print(f"\n{row['ticker']}")
        print(f"  Buy Signal: {row['buy_signal_strength']}/10")
        print(f"  Price: ${row['current_price']:.2f}")
        print(f"  30d Change: {row.get('30d_price_change', 0):.1f}%")
        if row.get('rsi'):
            print(f"  RSI: {row['rsi']:.1f}")
        print(f"  Trend: {row.get('price_trend', 'Unknown')}")
    
    return df

if __name__ == '__main__':
    analyze_watchlist_with_signals()

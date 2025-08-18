#!/usr/bin/env python
"""
Run the investment valuation dashboard.

Usage:
    poetry run python scripts/run_dashboard.py
    poetry run python scripts/run_dashboard.py AAPL MSFT GOOGL
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.invest.dashboard import create_dashboard

def main():
    # Get tickers from command line or use defaults
    if len(sys.argv) > 1:
        tickers = sys.argv[1:]
    else:
        # Default diverse set
        tickers = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN',  # Growth
            'JNJ', 'PG', 'KO',                # Dividend 
            'JPM', 'HD'                       # Mixed
        ]
    
    print(f"🎯 Creating dashboard for: {', '.join(tickers)}")
    print("📊 Running valuations (this may take a few minutes)...")
    
    try:
        html_path = create_dashboard(tickers)
        print(f"\n✅ Dashboard created successfully!")
        print(f"🌐 Open in browser: {html_path}")
        print("🔄 Dashboard auto-refreshes every 10 seconds while updating")
        
    except KeyboardInterrupt:
        print("\n⏹️  Dashboard creation interrupted")
    except Exception as e:
        print(f"\n❌ Error creating dashboard: {e}")

if __name__ == "__main__":
    main()
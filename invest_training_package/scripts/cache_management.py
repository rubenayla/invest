#!/usr/bin/env python3
"""
Cache Management Utility

This script provides utilities for managing the investment analysis cache system,
including viewing statistics, clearing caches, and warming up frequently used data.
"""

import argparse
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.invest.caching.cache_manager import get_cache_manager
from src.invest.caching.cache_decorators import get_cache_stats, clear_all_caches, cleanup_expired_cache
from src.invest.data.yahoo import get_sp500_tickers


def show_cache_stats():
    """Display comprehensive cache statistics."""
    print("=" * 60)
    print("CACHE STATISTICS")
    print("=" * 60)
    
    try:
        stats = get_cache_stats()
        
        # Manager statistics
        manager_stats = stats.get('manager_stats', {})
        print(f"\nManager Statistics:")
        print(f"  Hits: {manager_stats.get('hits', 0)}")
        print(f"  Misses: {manager_stats.get('misses', 0)}")
        print(f"  Sets: {manager_stats.get('sets', 0)}")
        print(f"  Hit Rate: {manager_stats.get('hit_rate', 0):.2%}")
        print(f"  Invalidations: {manager_stats.get('invalidations', 0)}")
        
        # Backend statistics
        backend_stats = stats.get('backend_stats', {})
        for backend_name, backend_data in backend_stats.items():
            print(f"\n{backend_name.upper()} Backend:")
            if 'error' in backend_data:
                print(f"  Error: {backend_data['error']}")
                continue
                
            for key, value in backend_data.items():
                if key != 'backend':
                    if key == 'hit_rate':
                        print(f"  {key.replace('_', ' ').title()}: {value:.2%}")
                    elif key.endswith('_bytes'):
                        print(f"  {key.replace('_', ' ').title()}: {value:,} bytes ({value/1024/1024:.1f} MB)")
                    else:
                        # Handle different value types safely
                        if isinstance(value, (int, float)):
                            print(f"  {key.replace('_', ' ').title()}: {value:,}")
                        else:
                            print(f"  {key.replace('_', ' ').title()}: {value}")
        
    except Exception as e:
        print(f"Error retrieving cache statistics: {e}")


def clear_caches():
    """Clear all caches."""
    print("Clearing all caches...")
    try:
        clear_all_caches()
        print("✓ All caches cleared successfully")
    except Exception as e:
        print(f"✗ Error clearing caches: {e}")


def cleanup_expired():
    """Clean up expired cache entries."""
    print("Cleaning up expired cache entries...")
    try:
        cleanup_expired_cache()
        print("✓ Expired cache entries cleaned up")
    except Exception as e:
        print(f"✗ Error cleaning up expired entries: {e}")


def warm_up_cache(num_tickers: int = 10):
    """Warm up cache with commonly used data."""
    print(f"Warming up cache with {num_tickers} tickers...")
    
    try:
        # Get S&P 500 tickers (this will cache them)
        print("Fetching S&P 500 tickers...")
        tickers = get_sp500_tickers()
        print(f"✓ Cached {len(tickers)} S&P 500 tickers")
        
        # Pre-cache data for top tickers
        from src.invest.data.yahoo import get_stock_data
        
        top_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NFLX', 'NVDA', 'BRK-B', 'JPM']
        for i, ticker in enumerate(top_tickers[:num_tickers]):
            print(f"Caching data for {ticker} ({i+1}/{num_tickers})...")
            try:
                data = get_stock_data(ticker)
                if data:
                    print(f"✓ Cached data for {ticker}")
                else:
                    print(f"⚠ No data available for {ticker}")
            except Exception as e:
                print(f"✗ Error caching {ticker}: {e}")
        
        print(f"✓ Cache warm-up completed for {num_tickers} tickers")
        
    except Exception as e:
        print(f"✗ Error during cache warm-up: {e}")


def test_cache_performance():
    """Test cache performance with a simple benchmark."""
    print("Running cache performance test...")
    
    import time
    from src.invest.data.yahoo import get_stock_data
    
    ticker = "AAPL"
    
    try:
        # First call (cache miss)
        print(f"Testing cache miss for {ticker}...")
        start_time = time.time()
        data1 = get_stock_data(ticker)
        miss_time = time.time() - start_time
        
        # Second call (cache hit)
        print(f"Testing cache hit for {ticker}...")
        start_time = time.time()
        data2 = get_stock_data(ticker)
        hit_time = time.time() - start_time
        
        # Results
        if data1 and data2:
            speedup = miss_time / hit_time if hit_time > 0 else float('inf')
            print(f"\nPerformance Results:")
            print(f"  Cache miss time: {miss_time:.3f} seconds")
            print(f"  Cache hit time: {hit_time:.3f} seconds")
            print(f"  Speedup: {speedup:.1f}x faster")
            
            if speedup > 2:
                print("✓ Cache is providing significant performance improvement")
            else:
                print("⚠ Cache speedup is lower than expected")
        else:
            print("✗ Failed to retrieve data for performance test")
            
    except Exception as e:
        print(f"✗ Error during performance test: {e}")


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Cache management utility for investment analysis system",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'command',
        choices=['stats', 'clear', 'cleanup', 'warmup', 'test'],
        help='Cache management command to execute'
    )
    
    parser.add_argument(
        '--tickers', '-t',
        type=int,
        default=10,
        help='Number of tickers for warmup (default: 10)'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output statistics in JSON format'
    )
    
    args = parser.parse_args()
    
    if args.command == 'stats':
        if args.json:
            try:
                stats = get_cache_stats()
                print(json.dumps(stats, indent=2, default=str))
            except Exception as e:
                print(json.dumps({"error": str(e)}, indent=2))
        else:
            show_cache_stats()
            
    elif args.command == 'clear':
        clear_caches()
        
    elif args.command == 'cleanup':
        cleanup_expired()
        
    elif args.command == 'warmup':
        warm_up_cache(args.tickers)
        
    elif args.command == 'test':
        test_cache_performance()


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
Test script for concurrent data fetching performance.
"""

import time
from src.invest.data.concurrent_fetcher import fetch_multiple_stocks_basic
from src.invest.data.yahoo import get_stock_data


def test_concurrent_vs_sequential():
    """Compare concurrent vs sequential fetching performance."""
    
    # Test with a small sample
    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NFLX', 'NVDA', 'AMD', 'INTC']
    
    print(f"Testing with {len(test_tickers)} tickers: {', '.join(test_tickers)}")
    print("=" * 60)
    
    # Test concurrent fetching
    print("\n🚀 Testing Concurrent Fetching:")
    start_time = time.time()
    
    def progress_callback(completed: int, total: int):
        print(f"  Progress: {completed}/{total} ({completed/total*100:.1f}%)")
    
    concurrent_results = fetch_multiple_stocks_basic(
        test_tickers,
        progress_callback=progress_callback
    )
    
    concurrent_duration = time.time() - start_time
    concurrent_success_count = sum(1 for data in concurrent_results.values() if data is not None)
    
    print(f"✅ Concurrent: {concurrent_success_count}/{len(test_tickers)} successful in {concurrent_duration:.2f}s")
    print(f"   Average per ticker: {concurrent_duration/len(test_tickers):.2f}s")
    
    # Test sequential fetching for comparison  
    print("\n🐌 Testing Sequential Fetching:")
    start_time = time.time()
    
    sequential_results = {}
    sequential_success_count = 0
    
    for i, ticker in enumerate(test_tickers):
        try:
            stock_data = get_stock_data(ticker)
            sequential_results[ticker] = stock_data
            if stock_data:
                sequential_success_count += 1
            print(f"  Progress: {i+1}/{len(test_tickers)} ({(i+1)/len(test_tickers)*100:.1f}%)")
        except Exception as e:
            print(f"  ❌ Failed {ticker}: {e}")
            sequential_results[ticker] = None
    
    sequential_duration = time.time() - start_time
    
    print(f"✅ Sequential: {sequential_success_count}/{len(test_tickers)} successful in {sequential_duration:.2f}s")
    print(f"   Average per ticker: {sequential_duration/len(test_tickers):.2f}s")
    
    # Performance comparison
    print("\n📊 Performance Comparison:")
    print("=" * 60)
    if sequential_duration > 0:
        speedup = sequential_duration / concurrent_duration
        time_saved = sequential_duration - concurrent_duration
        print(f"🏆 Speedup: {speedup:.2f}x faster")
        print(f"⏰ Time saved: {time_saved:.2f} seconds ({time_saved/sequential_duration*100:.1f}%)")
    
    print(f"\nSuccess rates:")
    print(f"  Concurrent: {concurrent_success_count/len(test_tickers)*100:.1f}%")
    print(f"  Sequential: {sequential_success_count/len(test_tickers)*100:.1f}%")
    
    # Show sample of data quality
    print(f"\n🔍 Data Quality Check:")
    for ticker in test_tickers[:3]:  # Check first 3
        concurrent_data = concurrent_results.get(ticker)
        sequential_data = sequential_results.get(ticker)
        
        if concurrent_data and sequential_data:
            concurrent_price = concurrent_data.get('currentPrice', 'N/A')
            sequential_price = sequential_data.get('currentPrice', 'N/A')
            print(f"  {ticker}: Concurrent=${concurrent_price}, Sequential=${sequential_price}")
            if concurrent_price == sequential_price:
                print(f"    ✅ Data matches")
            else:
                print(f"    ⚠️ Data differs (could be timing)")


if __name__ == "__main__":
    test_concurrent_vs_sequential()
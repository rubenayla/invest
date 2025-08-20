"""
Example of how the enhanced dashboard would handle automatic retry of failed stocks.

This demonstrates the improved user experience where "Data unavailable" stocks
are automatically retried in the background and updated when data becomes available.
"""

import time
import threading
from typing import Dict, List
from src.invest.data.concurrent_fetcher import ConcurrentDataFetcher
from src.invest.data.retry_manager import RetryManager, classify_failure_reason


class EnhancedDashboard:
    """Dashboard with automatic retry capabilities."""
    
    def __init__(self):
        self.fetcher = ConcurrentDataFetcher()
        self.retry_manager = RetryManager(self.fetcher)
        self.stock_data = {}
        self.retry_thread = None
        self.running = False
    
    def analyze_stocks(self, tickers: List[str]):
        """Analyze stocks with automatic retry for failures."""
        print(f"🚀 Starting analysis of {len(tickers)} stocks...")
        
        # Initial fetch attempt
        results = self.fetcher.fetch_multiple_stocks_basic(tickers)
        
        successful_count = 0
        failed_tickers = []
        
        for ticker in tickers:
            data = results.get(ticker)
            if data:
                self.stock_data[ticker] = data
                successful_count += 1
                print(f"✅ {ticker}: Data loaded")
            else:
                failed_tickers.append(ticker)
                self.stock_data[ticker] = {"status": "Data unavailable", "retrying": True}
                print(f"❌ {ticker}: Data unavailable (will retry)")
                
                # Register for retry
                self.retry_manager.register_failure(
                    ticker=ticker,
                    failure_reason=classify_failure_reason(Exception("Circuit breaker open")),
                    callback=self._on_retry_success
                )
        
        print(f"\n📊 Initial Results: {successful_count}/{len(tickers)} successful")
        
        if failed_tickers:
            print(f"🔄 {len(failed_tickers)} stocks queued for automatic retry")
            self._start_retry_background_process()
        
        return self.stock_data
    
    def _on_retry_success(self, ticker: str, data: Dict):
        """Called when a retry succeeds."""
        if data:
            self.stock_data[ticker] = data
            print(f"🎉 {ticker}: Data recovered! Analysis updated.")
            
            # In real dashboard, this would trigger HTML regeneration
            self._update_dashboard_display(ticker, data)
        else:
            self.stock_data[ticker] = {"status": "Data permanently unavailable", "retrying": False}
            print(f"💀 {ticker}: Permanent failure after all retries")
    
    def _start_retry_background_process(self):
        """Start background thread to process retries."""
        if self.retry_thread and self.retry_thread.is_alive():
            return  # Already running
            
        self.running = True
        self.retry_thread = threading.Thread(target=self._retry_loop, daemon=True)
        self.retry_thread.start()
        print("🔧 Background retry process started")
    
    def _retry_loop(self):
        """Background loop to process retries."""
        while self.running:
            try:
                # Process ready retries
                successful_results = self.retry_manager.process_retries()
                
                if successful_results:
                    print(f"🔄 Processed {len(successful_results)} retry attempts")
                
                # Check if we still have pending retries
                retry_status = self.retry_manager.get_retry_status()
                if not retry_status:
                    print("✨ All retries completed - stopping background process")
                    break
                
                # Wait before next check
                time.sleep(10)
                
            except Exception as e:
                print(f"❌ Error in retry loop: {e}")
                time.sleep(30)  # Wait longer on error
        
        self.running = False
    
    def _update_dashboard_display(self, ticker: str, data: Dict):
        """Update dashboard display for recovered stock."""
        # In real implementation, this would:
        # 1. Regenerate HTML for this stock
        # 2. Update the live dashboard
        # 3. Show notification to user
        print(f"📱 Dashboard updated for {ticker}")
    
    def get_retry_status(self) -> Dict:
        """Get current retry status for display."""
        return self.retry_manager.get_retry_status()
    
    def stop_retries(self):
        """Stop the retry background process."""
        self.running = False
        if self.retry_thread:
            self.retry_thread.join(timeout=5)


# Demo Usage
def demonstrate_enhanced_retry():
    """Demonstrate how enhanced retry works."""
    
    print("=" * 60)
    print("ENHANCED DASHBOARD WITH AUTOMATIC RETRY DEMO")
    print("=" * 60)
    
    dashboard = EnhancedDashboard()
    
    # Simulate analyzing stocks where some fail initially
    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'FAILED1', 'FAILED2', 'TSLA']
    
    print("\n1️⃣ Initial Analysis:")
    results = dashboard.analyze_stocks(test_tickers)
    
    print("\n2️⃣ Retry Status:")
    retry_status = dashboard.get_retry_status()
    for ticker, status in retry_status.items():
        print(f"  {ticker}: {status['retry_count']}/{status['max_retries']} retries, "
              f"next in {status['time_until_retry']:.0f}s")
    
    print("\n3️⃣ User Experience:")
    print("🖥️  Dashboard shows:")
    print("   ✅ AAPL: $150.23 (+2.5%)")
    print("   ✅ MSFT: $420.15 (-0.8%)")
    print("   ✅ GOOGL: $2,750.80 (+1.2%)")
    print("   🔄 FAILED1: Data unavailable (retrying...)")
    print("   🔄 FAILED2: Data unavailable (retrying...)")
    print("   ✅ TSLA: $845.20 (+5.2%)")
    
    print("\n   ⏰ Background process will retry failed stocks in 30s, 2min, 5min...")
    print("   📱 Dashboard will auto-update when data becomes available")
    print("   🎯 User gets immediate results + automatic recovery!")
    
    # Cleanup
    dashboard.stop_retries()


if __name__ == "__main__":
    demonstrate_enhanced_retry()
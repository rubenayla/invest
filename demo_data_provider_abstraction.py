#!/usr/bin/env python3
"""
Demonstration of the data provider abstraction layer benefits.

This script shows how the abstraction layer enables:
1. Easy switching between data providers
2. Fallback when primary provider fails  
3. Unified data format across providers
4. Testing with mock data
5. Provider health monitoring
"""

import time
from src.invest.data.providers import (
    setup_default_providers, 
    get_provider_manager,
    get_stock_info,
    create_mock_provider
)


def demo_basic_usage():
    """Demonstrate basic provider usage."""
    print("🔧 Setting up data providers...")
    setup_default_providers(use_mock=False)  # Use real Yahoo Finance
    
    print("\n📊 Fetching stock data through abstraction layer:")
    
    # Method 1: Direct convenience function
    try:
        stock_info = get_stock_info("AAPL")
        print(f"✅ {stock_info.ticker}: ${stock_info.current_price:.2f}")
        print(f"   Company: {stock_info.name}")
        print(f"   Sector: {stock_info.sector}")
        print(f"   Market Cap: ${stock_info.market_cap:,}")
        print(f"   Data Provider: {stock_info.data_provider}")
    except Exception as e:
        print(f"❌ Failed to fetch AAPL: {e}")
    
    # Method 2: Through manager
    manager = get_provider_manager()
    try:
        stock_info = manager.get_stock_info("MSFT") 
        print(f"✅ {stock_info.ticker}: ${stock_info.current_price:.2f}")
        print(f"   P/E Ratio: {stock_info.pe_ratio:.1f}" if stock_info.pe_ratio else "   P/E Ratio: N/A")
    except Exception as e:
        print(f"❌ Failed to fetch MSFT: {e}")


def demo_provider_switching():
    """Demonstrate easy provider switching."""
    print("\n" + "="*60)
    print("DEMO: PROVIDER SWITCHING")
    print("="*60)
    
    manager = get_provider_manager()
    
    print("\n1️⃣ Using Yahoo Finance Provider:")
    setup_default_providers(use_mock=False)
    
    try:
        stock_info = get_stock_info("GOOGL")
        print(f"   Data from: {stock_info.data_provider}")
        print(f"   GOOGL: ${stock_info.current_price:.2f}")
        print(f"   Last updated: {stock_info.last_updated}")
    except Exception as e:
        print(f"   ❌ Yahoo Finance failed: {e}")
    
    print("\n2️⃣ Switching to Mock Provider:")
    setup_default_providers(use_mock=True, mock_failure_rate=0.0)
    
    try:
        stock_info = get_stock_info("GOOGL")
        print(f"   Data from: {stock_info.data_provider}")
        print(f"   GOOGL: ${stock_info.current_price:.2f}")  # Mock data
        print(f"   Last updated: {stock_info.last_updated}")
    except Exception as e:
        print(f"   ❌ Mock provider failed: {e}")
    
    print("\n✨ Same code, different data sources!")


def demo_fallback_behavior():
    """Demonstrate fallback when primary provider fails."""
    print("\n" + "="*60)
    print("DEMO: AUTOMATIC FALLBACK")
    print("="*60)
    
    # Setup primary provider that might fail + fallback
    manager = get_provider_manager()
    
    # Clear existing providers
    manager.providers.clear()
    manager.primary_provider = None
    manager.fallback_providers.clear()
    
    # Add mock provider with high failure rate as primary
    failing_mock = create_mock_provider(simulate_failures=True, failure_rate=0.8)
    manager.register_provider(failing_mock, is_primary=True)
    
    # Add reliable mock provider as fallback
    reliable_mock = create_mock_provider(simulate_failures=False)
    reliable_mock.name = "reliable_mock"  # Different name
    manager.register_provider(reliable_mock, is_primary=False)
    
    print("🔧 Setup: Failing primary + reliable fallback")
    
    # Test fallback behavior
    successes = 0
    attempts = 5
    
    for i in range(attempts):
        try:
            stock_info = manager.get_stock_info("TSLA")
            successes += 1
            print(f"✅ Attempt {i+1}: Success via {stock_info.data_provider}")
        except Exception as e:
            print(f"❌ Attempt {i+1}: Failed - {e}")
    
    print(f"\n📈 Success rate: {successes}/{attempts} ({successes/attempts*100:.1f}%)")
    print("   Without fallback, success rate would be ~20%!")


def demo_provider_monitoring():
    """Demonstrate provider health monitoring."""
    print("\n" + "="*60)
    print("DEMO: PROVIDER HEALTH MONITORING")  
    print("="*60)
    
    setup_default_providers(use_mock=False)
    manager = get_provider_manager()
    
    print("🔍 Checking provider status...")
    status = manager.get_provider_status()
    
    for provider_name, provider_status in status.items():
        if provider_status.get('available'):
            print(f"✅ {provider_name}:")
            print(f"   Status: Available ({'Primary' if provider_status['is_primary'] else 'Fallback'})")
            
            rate_limit = provider_status.get('rate_limit', {})
            if rate_limit:
                print(f"   Rate Limits: {rate_limit.get('requests_per_second', 'N/A')} req/sec")
        else:
            print(f"❌ {provider_name}:")
            print(f"   Status: Unavailable")
            print(f"   Error: {provider_status.get('error', 'Unknown')}")


def demo_unified_data_format():
    """Demonstrate unified data format across providers."""
    print("\n" + "="*60)
    print("DEMO: UNIFIED DATA FORMAT")
    print("="*60)
    
    def display_stock_info(stock_info, provider_name):
        """Helper to display stock info consistently."""
        print(f"\n📊 Data from {provider_name}:")
        print(f"   Ticker: {stock_info.ticker}")
        print(f"   Name: {stock_info.name}")
        print(f"   Price: ${stock_info.current_price:.2f}" if stock_info.current_price else "   Price: N/A")
        print(f"   Market Cap: ${stock_info.market_cap:,}" if stock_info.market_cap else "   Market Cap: N/A")
        print(f"   P/E Ratio: {stock_info.pe_ratio:.1f}" if stock_info.pe_ratio else "   P/E Ratio: N/A")
        print(f"   Sector: {stock_info.sector}")
        
        # Show that .to_dict() works for backward compatibility
        legacy_dict = stock_info.to_dict()
        print(f"   Legacy format: {len(legacy_dict)} fields available")
    
    # Test with different providers
    ticker = "AAPL"
    
    # Yahoo Finance
    try:
        setup_default_providers(use_mock=False)
        stock_info = get_stock_info(ticker)
        display_stock_info(stock_info, "Yahoo Finance")
    except Exception as e:
        print(f"❌ Yahoo Finance failed: {e}")
    
    # Mock Provider  
    try:
        setup_default_providers(use_mock=True)
        stock_info = get_stock_info(ticker)
        display_stock_info(stock_info, "Mock Provider")
    except Exception as e:
        print(f"❌ Mock provider failed: {e}")
    
    print(f"\n✨ Same StockInfo interface regardless of data source!")


def demo_testing_benefits():
    """Demonstrate testing benefits."""
    print("\n" + "="*60)
    print("DEMO: TESTING BENEFITS")
    print("="*60)
    
    print("🧪 Setting up test environment with mock data...")
    
    # Setup mock provider with predictable data
    setup_default_providers(use_mock=True, mock_failure_rate=0.0)
    
    # Test a valuation function (simulated)
    def simple_pe_valuation(ticker: str) -> dict:
        """Simple valuation based on P/E ratio."""
        try:
            stock_info = get_stock_info(ticker)
            
            if not stock_info.pe_ratio or not stock_info.current_price:
                return {"error": "Insufficient data"}
            
            # Simple valuation: fair value based on sector average P/E
            sector_avg_pe = {
                'Technology': 25.0,
                'Healthcare': 20.0,
                'Consumer Discretionary': 18.0
            }.get(stock_info.sector, 20.0)
            
            earnings_per_share = stock_info.current_price / stock_info.pe_ratio
            fair_value = earnings_per_share * sector_avg_pe
            
            return {
                "ticker": ticker,
                "current_price": stock_info.current_price,
                "fair_value": fair_value,
                "recommendation": "BUY" if fair_value > stock_info.current_price * 1.1 else "HOLD"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    # Test the function with different tickers
    test_tickers = ['AAPL', 'MSFT', 'TSLA', 'GOOGL']
    
    print("\n📊 Testing valuation function:")
    for ticker in test_tickers:
        result = simple_pe_valuation(ticker)
        if "error" not in result:
            print(f"✅ {result['ticker']}: {result['recommendation']} "
                  f"(${result['current_price']:.2f} vs ${result['fair_value']:.2f} fair value)")
        else:
            print(f"❌ {ticker}: {result['error']}")
    
    print("\n✅ Benefits for testing:")
    print("   • No API calls - tests run instantly")
    print("   • Predictable data - tests are reliable")
    print("   • No rate limits - can run unlimited tests")
    print("   • Simulate failures - test error handling")


if __name__ == "__main__":
    print("DATA PROVIDER ABSTRACTION LAYER DEMO")
    print("=" * 60)
    
    try:
        demo_basic_usage()
        demo_provider_switching()
        demo_fallback_behavior()
        demo_provider_monitoring()
        demo_unified_data_format()
        demo_testing_benefits()
        
        print("\n" + "="*60)
        print("🎯 SUMMARY: Data Provider Abstraction Benefits")
        print("="*60)
        print("✅ Provider Independence - Easy to switch data sources")
        print("✅ Automatic Fallback - System stays resilient when providers fail")
        print("✅ Unified Interface - Same code works with any provider")
        print("✅ Health Monitoring - Track provider availability and limits")
        print("✅ Testing Support - Mock providers for fast, reliable tests")
        print("✅ Backward Compatibility - Existing code continues to work")
        print("✅ Future-Proof - Easy to add new providers (Alpha Vantage, etc.)")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
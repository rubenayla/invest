#!/usr/bin/env python
"""
Test script for ETF valuation functionality.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.invest.utils.asset_type import get_asset_type, is_etf, get_etf_info
from src.invest.valuation.etf import calculate_etf_valuation, compare_etfs


def test_asset_detection():
    """Test asset type detection."""
    print("="*60)
    print("TESTING ASSET TYPE DETECTION")
    print("="*60)
    
    test_tickers = ['SPY', 'AAPL', 'QQQ', 'MSFT', 'GLD', 'GOOGL']
    
    for ticker in test_tickers:
        asset_type = get_asset_type(ticker)
        print(f"{ticker}: {asset_type} (ETF: {is_etf(ticker)})")
    print()


def test_etf_valuation():
    """Test ETF valuation for a single ETF."""
    print("="*60)
    print("TESTING ETF VALUATION")
    print("="*60)
    
    # Test SPY valuation
    try:
        results = calculate_etf_valuation('SPY', verbose=True)
        print(f"\nValuation successful for SPY")
        print(f"Composite Score: {results['composite_score']:.0f}/100")
    except Exception as e:
        print(f"Error valuing SPY: {e}")


def test_etf_comparison():
    """Test ETF comparison functionality."""
    print("\n" + "="*60)
    print("TESTING ETF COMPARISON")
    print("="*60)
    
    etfs = ['SPY', 'QQQ', 'IWM', 'VTI']
    
    try:
        comparison = compare_etfs(etfs, verbose=True)
        print(f"\nCompared {len(comparison)} ETFs successfully")
    except Exception as e:
        print(f"Error comparing ETFs: {e}")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("ETF FUNCTIONALITY TEST SUITE")
    print("="*60 + "\n")
    
    # Test asset detection
    test_asset_detection()
    
    # Test ETF valuation
    test_etf_valuation()
    
    # Test ETF comparison
    test_etf_comparison()
    
    print("\n" + "="*60)
    print("TESTS COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
"""
Claude Desktop tools for stock data retrieval and analysis.

These tools provide Claude with easy access to financial data and metrics
for individual stocks or groups of stocks.
"""

from typing import Any, Dict, List, Optional

from ..core.analysis import (
    analyze_stock_trend_indicators,
    compare_multiple_stocks,
    get_comprehensive_stock_data,
    get_sector_stock_analysis,
    get_specific_financial_metrics,
)


def get_stock_data_detailed(ticker: str) -> Dict[str, Any]:
    """
    Get comprehensive stock data for a single ticker.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')

    Returns:
        Dict containing detailed stock information formatted for analysis
    """
    return get_comprehensive_stock_data(ticker)


def get_financial_metrics(
    ticker: str, metric_categories: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Get specific financial metrics for a stock.

    Args:
        ticker: Stock ticker symbol
        metric_categories: Categories to include. Options:
                          ['valuation', 'profitability', 'growth', 'financial_health', 'efficiency']

    Returns:
        Dict containing requested financial metrics
    """
    return get_specific_financial_metrics(ticker, metric_categories)


def compare_stocks(
    tickers: List[str], comparison_metrics: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Compare multiple stocks side by side.

    Args:
        tickers: List of stock ticker symbols
        comparison_metrics: Metrics to compare. Options:
                           ['valuation', 'profitability', 'growth', 'size', 'financial_health']

    Returns:
        Dict containing side-by-side comparison of stocks
    """
    return compare_multiple_stocks(tickers, comparison_metrics)


def get_sector_stocks(
    sector: str, min_market_cap: Optional[float] = None, max_results: int = 50
) -> Dict[str, Any]:
    """
    Get stocks from a specific sector with basic metrics.

    Args:
        sector: Sector name (e.g., 'Technology', 'Healthcare')
        min_market_cap: Minimum market cap in billions (optional)
        max_results: Maximum number of stocks to return

    Returns:
        Dict containing stocks from the specified sector
    """
    return get_sector_stock_analysis(sector, min_market_cap, max_results)


def analyze_stock_trends(ticker: str, trend_periods: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Analyze trends in key metrics for a stock (using available data).

    Args:
        ticker: Stock ticker symbol
        trend_periods: Time periods to analyze (limited by available data)

    Returns:
        Dict containing trend analysis based on available data
    """
    return analyze_stock_trend_indicators(ticker, trend_periods)

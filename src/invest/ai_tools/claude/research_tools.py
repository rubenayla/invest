"""
Claude Desktop tools for stock research and analysis.

These tools enable Claude to perform web-based research and qualitative analysis
that complements the systematic quantitative screening.
"""

from typing import Any, Dict, List, Optional

from ..core.research import (
    prepare_competitive_analysis,
    prepare_news_research,
    prepare_sector_analysis,
    prepare_stock_research,
)


def research_stock(
    ticker: str, research_areas: Optional[List[str]] = None, time_horizon: str = "3_months"
) -> Dict[str, Any]:
    """
    Research a specific stock using available data and prompt Claude for web research.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        research_areas: List of areas to focus on. Options:
                       ['competitive_position', 'recent_news', 'management',
                        'industry_trends', 'risks', 'catalysts']
        time_horizon: Time period for analysis ('1_month', '3_months', '6_months', '1_year')

    Returns:
        Dict containing available stock data and research framework for Claude
    """
    research_data = prepare_stock_research(ticker, research_areas, time_horizon)

    if "error" not in research_data:
        # Add Claude-specific prompts
        research_data["claude_research_prompts"] = research_data.get("research_prompts", [])

    return research_data


def analyze_sector(
    sector: str, focus_areas: Optional[List[str]] = None, include_stocks: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Analyze a specific sector with context for investment decisions.

    Args:
        sector: Sector name (e.g., 'Technology', 'Healthcare', 'Energy')
        focus_areas: Areas to analyze. Options:
                    ['cycle_position', 'trends', 'valuations', 'regulations', 'risks']
        include_stocks: Specific stocks in the sector to highlight

    Returns:
        Dict containing sector analysis framework for Claude
    """
    sector_data = prepare_sector_analysis(sector, focus_areas, include_stocks)

    if "error" not in sector_data:
        # Add Claude-specific prompts
        sector_data["claude_research_prompts"] = sector_data.get("research_prompts", [])

    return sector_data


def get_recent_news(
    ticker: str, news_types: Optional[List[str]] = None, days_back: int = 30
) -> Dict[str, Any]:
    """
    Get framework for researching recent news about a stock.

    Args:
        ticker: Stock ticker symbol
        news_types: Types of news to focus on. Options:
                   ['earnings', 'analyst_updates', 'product_launches', 'regulatory', 'partnerships']
        days_back: Number of days to look back for news

    Returns:
        Dict containing news research framework for Claude
    """
    news_data = prepare_news_research(ticker, news_types, days_back)

    if "error" not in news_data:
        # Add Claude-specific prompts
        news_data["claude_search_prompts"] = news_data.get("search_prompts", [])

    return news_data


def compare_competitive_position(
    primary_ticker: str, competitor_tickers: List[str], comparison_areas: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Compare competitive positions of multiple stocks in the same sector.

    Args:
        primary_ticker: Main stock to analyze
        competitor_tickers: List of competitor ticker symbols
        comparison_areas: Areas to compare. Options:
                         ['market_share', 'profitability', 'growth', 'valuation', 'strengths_weaknesses']

    Returns:
        Dict containing competitive analysis framework
    """
    competitive_data = prepare_competitive_analysis(
        primary_ticker, competitor_tickers, comparison_areas
    )

    if "error" not in competitive_data:
        # Add Claude-specific prompts
        competitive_data["claude_analysis_prompts"] = competitive_data.get("analysis_prompts", [])

    return competitive_data

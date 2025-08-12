"""
Claude Desktop Tools for Investment Analysis

This module provides tools that Claude Desktop can use to interact with
the systematic investment analysis framework.

Usage in Claude Desktop:
1. Open Claude Desktop
2. Navigate to the invest project directory
3. Ask questions like:
   - "Screen for undervalued growth stocks"
   - "Analyze AAPL's competitive position" 
   - "Build me a dividend portfolio"

Claude will automatically use these tools to provide comprehensive analysis
combining systematic screening with AI-powered research.
"""

from .screening_tools import systematic_screen, get_screening_configs
from .research_tools import research_stock, analyze_sector, get_recent_news
from .data_tools import get_stock_data, get_financial_metrics, compare_stocks
from .portfolio_tools import build_portfolio, analyze_portfolio_risk, optimize_allocation

__all__ = [
    # Screening tools
    'systematic_screen',
    'get_screening_configs',
    
    # Research tools  
    'research_stock',
    'analyze_sector',
    'get_recent_news',
    
    # Data tools
    'get_stock_data',
    'get_financial_metrics', 
    'compare_stocks',
    
    # Portfolio tools
    'build_portfolio',
    'analyze_portfolio_risk',
    'optimize_allocation'
]
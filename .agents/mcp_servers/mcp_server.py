#!/usr/bin/env python3
"""MCP Server for Stock Analysis with cached data access."""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd
from mcp.server import Server

# Import your existing modules
from src.data_fetcher import DataFetcher
from src.systematic_tracker import SystematicTracker
from src.valuation_models import DCFModel, GrahamModel, SimpleRatiosModel

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockAnalysisMCPServer:
    """MCP Server for stock analysis with cache integration."""

    def __init__(self):
        self.server = Server('stock-analysis')
        self.data_fetcher = DataFetcher()
        self.tracker = SystematicTracker()
        self.cache_dir = Path('data/cache')

        # Register tools
        self._register_tools()

    def _register_tools(self):
        """Register all available MCP tools."""

        @self.server.tool()
        async def analyze_stock(ticker: str, use_cache: bool = True) -> str:
            """
            Analyze a stock with multiple valuation models.

            Args:
                ticker: Stock ticker symbol
                use_cache: Whether to use cached data (default: True)

            Returns:
                Comprehensive stock analysis with valuations
            """
            try:
                # Fetch data
                data = self.data_fetcher.fetch_stock_data(ticker, use_cache=use_cache)

                if not data:
                    return f"Failed to fetch data for {ticker}"

                # Run valuation models
                models = [SimpleRatiosModel(), DCFModel(), GrahamModel()]
                results = []

                for model in models:
                    try:
                        valuation = model.calculate(data)
                        results.append({
                            'model': model.__class__.__name__,
                            'fair_value': valuation.get('fair_value', 'N/A'),
                            'margin_of_safety': valuation.get('margin_of_safety', 'N/A')
                        })
                    except Exception as e:
                        results.append({
                            'model': model.__class__.__name__,
                            'error': str(e)
                        })

                # Format response
                current_price = data.get('currentPrice', 'N/A')
                response = f"=== Analysis for {ticker} ===\n"
                response += f"Current Price: ${current_price}\n"
                response += f"P/E Ratio: {data.get('trailingPE', 'N/A')}\n"
                response += f"Market Cap: ${data.get('marketCap', 0)/1e9:.1f}B\n\n"
                response += "Valuations:\n"

                for result in results:
                    if 'error' in result:
                        response += f"- {result['model']}: Error - {result['error']}\n"
                    else:
                        response += f"- {result['model']}: ${result['fair_value']:.2f} "
                        response += f"(Margin: {result['margin_of_safety']:.1f}%)\n"

                return response

            except Exception as e:
                return f"Error analyzing {ticker}: {str(e)}"

        @self.server.tool()
        async def compare_stocks(tickers: List[str]) -> str:
            """
            Compare multiple stocks side by side.

            Args:
                tickers: List of stock ticker symbols

            Returns:
                Comparison table with key metrics
            """
            try:
                comparison_data = []

                for ticker in tickers[:10]:  # Limit to 10 stocks
                    data = self.data_fetcher.fetch_stock_data(ticker)
                    if data:
                        comparison_data.append({
                            'Ticker': ticker,
                            'Price': data.get('currentPrice', 'N/A'),
                            'P/E': round(data.get('trailingPE', 0), 1) if data.get('trailingPE') else 'N/A',
                            'P/B': round(data.get('priceToBook', 0), 1) if data.get('priceToBook') else 'N/A',
                            'ROE': f"{data.get('returnOnEquity', 0)*100:.1f}%" if data.get('returnOnEquity') else 'N/A',
                            'Margin': f"{data.get('grossMargins', 0)*100:.1f}%" if data.get('grossMargins') else 'N/A',
                            'Debt/Eq': round(data.get('debtToEquity', 0)/100, 2) if data.get('debtToEquity') else 'N/A'
                        })

                # Create DataFrame for formatting
                df = pd.DataFrame(comparison_data)
                return f"Stock Comparison:\n\n{df.to_string(index=False)}"

            except Exception as e:
                return f"Error comparing stocks: {str(e)}"

        @self.server.tool()
        async def get_cached_data(ticker: str) -> str:
            """
            Retrieve cached data for a stock.

            Args:
                ticker: Stock ticker symbol

            Returns:
                Cached data with timestamp
            """
            try:
                cache_file = self.cache_dir / f"{ticker.upper()}.json"

                if not cache_file.exists():
                    return f"No cached data found for {ticker}"

                with open(cache_file, 'r') as f:
                    data = json.load(f)

                # Get cache age
                cache_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                age_hours = (datetime.now() - cache_time).total_seconds() / 3600

                # Format key metrics
                response = f"=== Cached Data for {ticker} ===\n"
                response += f"Cache Age: {age_hours:.1f} hours\n"
                response += f"Last Updated: {cache_time.strftime('%Y-%m-%d %H:%M')}\n\n"
                response += "Key Metrics:\n"
                response += f"- Current Price: ${data.get('currentPrice', 'N/A')}\n"
                response += f"- 52W Range: ${data.get('fiftyTwoWeekLow', 'N/A')} - ${data.get('fiftyTwoWeekHigh', 'N/A')}\n"
                response += f"- Market Cap: ${data.get('marketCap', 0)/1e9:.1f}B\n"
                response += f"- P/E Ratio: {data.get('trailingPE', 'N/A')}\n"
                response += f"- Revenue: ${data.get('totalRevenue', 0)/1e9:.1f}B\n"

                return response

            except Exception as e:
                return f"Error retrieving cached data: {str(e)}"

        @self.server.tool()
        async def clear_cache(ticker: Optional[str] = None) -> str:
            """
            Clear cached data for a specific ticker or all tickers.

            Args:
                ticker: Stock ticker to clear (None = clear all)

            Returns:
                Confirmation message
            """
            try:
                if ticker:
                    cache_file = self.cache_dir / f"{ticker.upper()}.json"
                    if cache_file.exists():
                        cache_file.unlink()
                        return f"Cleared cache for {ticker}"
                    return f"No cache found for {ticker}"
                else:
                    # Clear all cache files
                    count = 0
                    for cache_file in self.cache_dir.glob('*.json'):
                        cache_file.unlink()
                        count += 1
                    return f"Cleared {count} cached files"

            except Exception as e:
                return f"Error clearing cache: {str(e)}"

        @self.server.tool()
        async def track_portfolio(tickers: List[str]) -> str:
            """
            Track portfolio performance with systematic analysis.

            Args:
                tickers: List of stock tickers in portfolio

            Returns:
                Portfolio analysis and recommendations
            """
            try:
                results = self.tracker.analyze_positions(tickers)

                response = "=== Portfolio Analysis ===\n\n"

                for ticker, analysis in results.items():
                    response += f"{ticker}:\n"
                    response += f"  Status: {analysis.get('status', 'Unknown')}\n"
                    response += f"  Score: {analysis.get('score', 0):.1f}/100\n"

                    if 'signals' in analysis:
                        response += f"  Signals: {', '.join(analysis['signals'])}\n"

                    if 'recommendation' in analysis:
                        response += f"  Action: {analysis['recommendation']}\n"

                    response += "\n"

                return response

            except Exception as e:
                return f"Error tracking portfolio: {str(e)}"

        @self.server.tool()
        async def find_value_stocks(
            min_pe: Optional[float] = None,
            max_pe: Optional[float] = 15,
            min_roe: Optional[float] = 15,
            sector: Optional[str] = None
        ) -> str:
            """
            Find undervalued stocks based on criteria.

            Args:
                min_pe: Minimum P/E ratio
                max_pe: Maximum P/E ratio (default: 15)
                min_roe: Minimum ROE percentage (default: 15)
                sector: Specific sector to search

            Returns:
                List of stocks meeting criteria
            """
            try:
                # This would ideally connect to a screener API
                # For now, analyze known watchlist
                watchlist = ['MOH', 'ACGL', 'NEM', 'HIG', 'STLD', 'CVX', 'DHI']
                matches = []

                for ticker in watchlist:
                    data = self.data_fetcher.fetch_stock_data(ticker)
                    if not data:
                        continue

                    pe = data.get('trailingPE', float('inf'))
                    roe = data.get('returnOnEquity', 0) * 100 if data.get('returnOnEquity') else 0

                    # Check criteria
                    if min_pe and pe < min_pe:
                        continue
                    if max_pe and pe > max_pe:
                        continue
                    if min_roe and roe < min_roe:
                        continue

                    matches.append({
                        'ticker': ticker,
                        'pe': pe,
                        'roe': roe,
                        'price': data.get('currentPrice', 'N/A')
                    })

                if not matches:
                    return "No stocks found matching criteria"

                response = f"=== Value Stocks (P/E < {max_pe}, ROE > {min_roe}%) ===\n\n"
                for match in matches:
                    response += f"{match['ticker']}: "
                    response += f"P/E={match['pe']:.1f}, "
                    response += f"ROE={match['roe']:.1f}%, "
                    response += f"Price=${match['price']}\n"

                return response

            except Exception as e:
                return f"Error finding value stocks: {str(e)}"

    async def run(self):
        """Run the MCP server."""
        async with self.server:
            logger.info("Stock Analysis MCP Server running...")
            await self.server.wait_for_shutdown()

async def main():
    """Main entry point."""
    server = StockAnalysisMCPServer()
    await server.run()

if __name__ == '__main__':
    asyncio.run(main())

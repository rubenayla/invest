#!/usr/bin/env python3
"""
MCP Server for Stock Analysis.
Provides tools for analyzing stocks with cached data access.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import your existing modules
from src.data_fetcher import DataFetcher
from src.valuation_models import SimpleRatiosModel, DCFModel, GrahamModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
data_fetcher = DataFetcher()
cache_dir = Path('data/cache')

async def analyze_stock(arguments: dict[str, Any]) -> list[types.TextContent]:
    """Analyze a stock with multiple valuation models."""
    ticker = arguments.get('ticker', '').upper()
    use_cache = arguments.get('use_cache', True)
    
    try:
        # Fetch data
        data = data_fetcher.fetch_stock_data(ticker, use_cache=use_cache)
        
        if not data:
            return [types.TextContent(
                type='text',
                text=f'Failed to fetch data for {ticker}'
            )]
        
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
        response = f'=== Analysis for {ticker} ===\n'
        response += f'Current Price: ${current_price}\n'
        response += f'P/E Ratio: {data.get("trailingPE", "N/A")}\n'
        response += f'Market Cap: ${data.get("marketCap", 0)/1e9:.1f}B\n\n'
        response += 'Valuations:\n'
        
        for result in results:
            if 'error' in result:
                response += f'- {result["model"]}: Error - {result["error"]}\n'
            else:
                response += f'- {result["model"]}: ${result["fair_value"]:.2f} '
                response += f'(Margin: {result["margin_of_safety"]:.1f}%)\n'
        
        return [types.TextContent(type='text', text=response)]
        
    except Exception as e:
        return [types.TextContent(
            type='text',
            text=f'Error analyzing {ticker}: {str(e)}'
        )]

async def compare_stocks(arguments: dict[str, Any]) -> list[types.TextContent]:
    """Compare multiple stocks side by side."""
    tickers = arguments.get('tickers', [])
    
    if not tickers:
        return [types.TextContent(
            type='text',
            text='Please provide a list of tickers to compare'
        )]
    
    try:
        comparison_data = []
        
        for ticker in tickers[:10]:  # Limit to 10 stocks
            data = data_fetcher.fetch_stock_data(ticker)
            if data:
                comparison_data.append({
                    'Ticker': ticker,
                    'Price': data.get('currentPrice', 'N/A'),
                    'P/E': round(data.get('trailingPE', 0), 1) if data.get('trailingPE') else 'N/A',
                    'P/B': round(data.get('priceToBook', 0), 1) if data.get('priceToBook') else 'N/A',
                    'ROE': f'{data.get("returnOnEquity", 0)*100:.1f}%' if data.get('returnOnEquity') else 'N/A',
                    'Margin': f'{data.get("grossMargins", 0)*100:.1f}%' if data.get('grossMargins') else 'N/A'
                })
        
        # Format as text table
        if not comparison_data:
            return [types.TextContent(
                type='text',
                text='No data available for the provided tickers'
            )]
        
        # Create formatted table
        headers = list(comparison_data[0].keys())
        col_widths = {h: max(len(h), max(len(str(r.get(h, ''))) for r in comparison_data)) for h in headers}
        
        # Header row
        header_line = ' | '.join(h.ljust(col_widths[h]) for h in headers)
        separator = '-+-'.join('-' * col_widths[h] for h in headers)
        
        # Data rows
        data_lines = []
        for row in comparison_data:
            data_lines.append(' | '.join(str(row.get(h, '')).ljust(col_widths[h]) for h in headers))
        
        response = 'Stock Comparison:\n\n'
        response += header_line + '\n'
        response += separator + '\n'
        response += '\n'.join(data_lines)
        
        return [types.TextContent(type='text', text=response)]
        
    except Exception as e:
        return [types.TextContent(
            type='text',
            text=f'Error comparing stocks: {str(e)}'
        )]

async def get_cached_data(arguments: dict[str, Any]) -> list[types.TextContent]:
    """Retrieve cached data for a stock."""
    ticker = arguments.get('ticker', '').upper()
    
    try:
        cache_file = cache_dir / f'{ticker}.json'
        
        if not cache_file.exists():
            return [types.TextContent(
                type='text',
                text=f'No cached data found for {ticker}'
            )]
        
        with open(cache_file, 'r') as f:
            data = json.load(f)
        
        # Get cache age
        cache_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
        age_hours = (datetime.now() - cache_time).total_seconds() / 3600
        
        # Format key metrics
        response = f'=== Cached Data for {ticker} ===\n'
        response += f'Cache Age: {age_hours:.1f} hours\n'
        response += f'Last Updated: {cache_time.strftime("%Y-%m-%d %H:%M")}\n\n'
        response += 'Key Metrics:\n'
        response += f'- Current Price: ${data.get("currentPrice", "N/A")}\n'
        response += f'- 52W Range: ${data.get("fiftyTwoWeekLow", "N/A")} - ${data.get("fiftyTwoWeekHigh", "N/A")}\n'
        response += f'- Market Cap: ${data.get("marketCap", 0)/1e9:.1f}B\n'
        response += f'- P/E Ratio: {data.get("trailingPE", "N/A")}\n'
        
        return [types.TextContent(type='text', text=response)]
        
    except Exception as e:
        return [types.TextContent(
            type='text',
            text=f'Error retrieving cached data: {str(e)}'
        )]

async def clear_cache(arguments: dict[str, Any]) -> list[types.TextContent]:
    """Clear cached data."""
    ticker = arguments.get('ticker')
    
    try:
        if ticker:
            cache_file = cache_dir / f'{ticker.upper()}.json'
            if cache_file.exists():
                cache_file.unlink()
                return [types.TextContent(
                    type='text',
                    text=f'Cleared cache for {ticker}'
                )]
            return [types.TextContent(
                type='text',
                text=f'No cache found for {ticker}'
            )]
        else:
            # Clear all cache files
            count = 0
            for cache_file in cache_dir.glob('*.json'):
                cache_file.unlink()
                count += 1
            return [types.TextContent(
                type='text',
                text=f'Cleared {count} cached files'
            )]
            
    except Exception as e:
        return [types.TextContent(
            type='text',
            text=f'Error clearing cache: {str(e)}'
        )]

async def find_value_stocks(arguments: dict[str, Any]) -> list[types.TextContent]:
    """Find undervalued stocks based on criteria."""
    max_pe = arguments.get('max_pe', 15)
    min_roe = arguments.get('min_roe', 15)
    
    try:
        # Analyze known watchlist
        watchlist = ['MOH', 'ACGL', 'NEM', 'HIG', 'STLD', 'CVX', 'DHI', 'ALLE', 'NUE']
        matches = []
        
        for ticker in watchlist:
            data = data_fetcher.fetch_stock_data(ticker)
            if not data:
                continue
            
            pe = data.get('trailingPE', float('inf'))
            roe = data.get('returnOnEquity', 0) * 100 if data.get('returnOnEquity') else 0
            
            # Check criteria
            if pe <= max_pe and roe >= min_roe:
                matches.append({
                    'ticker': ticker,
                    'pe': pe,
                    'roe': roe,
                    'price': data.get('currentPrice', 'N/A'),
                    'name': data.get('longName', ticker)
                })
        
        if not matches:
            return [types.TextContent(
                type='text',
                text='No stocks found matching criteria'
            )]
        
        # Sort by P/E ratio
        matches.sort(key=lambda x: x['pe'])
        
        response = f'=== Value Stocks (P/E ≤ {max_pe}, ROE ≥ {min_roe}%) ===\n\n'
        for match in matches:
            response += f'{match["ticker"]} ({match["name"]})\n'
            response += f'  P/E: {match["pe"]:.1f}\n'
            response += f'  ROE: {match["roe"]:.1f}%\n'
            response += f'  Price: ${match["price"]}\n\n'
        
        return [types.TextContent(type='text', text=response)]
        
    except Exception as e:
        return [types.TextContent(
            type='text',
            text=f'Error finding value stocks: {str(e)}'
        )]

# Define available tools
TOOLS = [
    Tool(
        name='analyze_stock',
        description='Analyze a stock with multiple valuation models',
        inputSchema={
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'Stock ticker symbol'
                },
                'use_cache': {
                    'type': 'boolean',
                    'description': 'Whether to use cached data (default: true)',
                    'default': True
                }
            },
            'required': ['ticker']
        }
    ),
    Tool(
        name='compare_stocks',
        description='Compare multiple stocks side by side',
        inputSchema={
            'type': 'object',
            'properties': {
                'tickers': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'List of stock ticker symbols'
                }
            },
            'required': ['tickers']
        }
    ),
    Tool(
        name='get_cached_data',
        description='Retrieve cached data for a stock',
        inputSchema={
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'Stock ticker symbol'
                }
            },
            'required': ['ticker']
        }
    ),
    Tool(
        name='clear_cache',
        description='Clear cached data for a ticker or all tickers',
        inputSchema={
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'Stock ticker to clear (omit to clear all)'
                }
            }
        }
    ),
    Tool(
        name='find_value_stocks',
        description='Find undervalued stocks based on P/E and ROE criteria',
        inputSchema={
            'type': 'object',
            'properties': {
                'max_pe': {
                    'type': 'number',
                    'description': 'Maximum P/E ratio (default: 15)',
                    'default': 15
                },
                'min_roe': {
                    'type': 'number',
                    'description': 'Minimum ROE percentage (default: 15)',
                    'default': 15
                }
            }
        }
    )
]

# Tool handlers mapping
TOOL_HANDLERS = {
    'analyze_stock': analyze_stock,
    'compare_stocks': compare_stocks,
    'get_cached_data': get_cached_data,
    'clear_cache': clear_cache,
    'find_value_stocks': find_value_stocks
}

async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await mcp.server.stdio.run_stdio_server(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name='stock-analysis',
                server_version='1.0.0'
            ),
            TOOLS,
            TOOL_HANDLERS
        )

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
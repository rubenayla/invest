#!/usr/bin/env python3
"""
Stock Analysis MCP Server - provides tools for stock analysis via MCP protocol.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent

# Import existing modules from the project
from src.data_fetcher import DataFetcher
from src.valuation_models import SimpleRatiosModel, DCFModel, GrahamModel

# Initialize server and data fetcher
server = Server('stock-analysis')
data_fetcher = DataFetcher()
cache_dir = Path('data/cache')

@server.tool()
async def analyze_stock(ticker: str, use_cache: bool = True) -> list[TextContent]:
    """
    Analyze a stock with multiple valuation models.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        use_cache: Whether to use cached data (default: True)
    
    Returns:
        Comprehensive analysis including valuations and key metrics
    """
    try:
        ticker = ticker.upper()
        data = data_fetcher.fetch_stock_data(ticker, use_cache=use_cache)
        
        if not data:
            return [TextContent(
                type='text',
                text=f'❌ Failed to fetch data for {ticker}'
            )]
        
        # Run valuation models
        models = [SimpleRatiosModel(), DCFModel(), GrahamModel()]
        valuations = []
        
        for model in models:
            try:
                result = model.calculate(data)
                valuations.append({
                    'model': model.__class__.__name__.replace('Model', ''),
                    'fair_value': result.get('fair_value', 0),
                    'margin_of_safety': result.get('margin_of_safety', 0)
                })
            except Exception as e:
                valuations.append({
                    'model': model.__class__.__name__.replace('Model', ''),
                    'error': str(e)
                })
        
        # Build response
        current_price = data.get('currentPrice', 0)
        response_lines = [
            f'📊 Analysis for {ticker}',
            f'{"="*40}',
            f'Current Price: ${current_price:.2f}',
            f'Market Cap: ${data.get("marketCap", 0)/1e9:.1f}B',
            f'P/E Ratio: {data.get("trailingPE", "N/A")}',
            f'P/B Ratio: {data.get("priceToBook", "N/A")}',
            f'ROE: {data.get("returnOnEquity", 0)*100:.1f}%' if data.get('returnOnEquity') else 'ROE: N/A',
            f'',
            f'💰 Valuations:',
        ]
        
        for val in valuations:
            if 'error' in val:
                response_lines.append(f'  • {val["model"]}: ⚠️ {val["error"]}')
            else:
                response_lines.append(
                    f'  • {val["model"]}: ${val["fair_value"]:.2f} '
                    f'({"🟢" if val["margin_of_safety"] > 0 else "🔴"} '
                    f'{val["margin_of_safety"]:.1f}%)'
                )
        
        return [TextContent(type='text', text='\n'.join(response_lines))]
        
    except Exception as e:
        return [TextContent(
            type='text',
            text=f'❌ Error analyzing {ticker}: {str(e)}'
        )]

@server.tool()
async def compare_stocks(*tickers: str) -> list[TextContent]:
    """
    Compare multiple stocks side by side.
    
    Args:
        tickers: Stock ticker symbols to compare (e.g., 'AAPL', 'MSFT', 'GOOGL')
    
    Returns:
        Comparison table with key metrics for each stock
    """
    if not tickers:
        return [TextContent(
            type='text',
            text='❌ Please provide at least one ticker to analyze'
        )]
    
    try:
        results = []
        
        for ticker in tickers[:8]:  # Limit to 8 stocks
            ticker = ticker.upper()
            data = data_fetcher.fetch_stock_data(ticker)
            
            if data:
                results.append({
                    'Ticker': ticker,
                    'Price': f'${data.get("currentPrice", 0):.2f}',
                    'P/E': f'{data.get("trailingPE", 0):.1f}' if data.get('trailingPE') else 'N/A',
                    'P/B': f'{data.get("priceToBook", 0):.1f}' if data.get('priceToBook') else 'N/A',
                    'ROE': f'{data.get("returnOnEquity", 0)*100:.1f}%' if data.get('returnOnEquity') else 'N/A',
                    'Margin': f'{data.get("grossMargins", 0)*100:.1f}%' if data.get('grossMargins') else 'N/A',
                    'Cap': f'${data.get("marketCap", 0)/1e9:.0f}B' if data.get('marketCap') else 'N/A'
                })
        
        if not results:
            return [TextContent(
                type='text',
                text='❌ No data available for provided tickers'
            )]
        
        # Format as table
        headers = list(results[0].keys())
        col_widths = {h: max(len(h), max(len(str(r[h])) for r in results)) for h in headers}
        
        lines = ['📊 Stock Comparison', '=' * 60]
        
        # Header
        header_line = ' | '.join(h.ljust(col_widths[h]) for h in headers)
        separator = '-+-'.join('-' * col_widths[h] for h in headers)
        lines.extend([header_line, separator])
        
        # Data rows
        for result in results:
            lines.append(' | '.join(str(result[h]).ljust(col_widths[h]) for h in headers))
        
        return [TextContent(type='text', text='\n'.join(lines))]
        
    except Exception as e:
        return [TextContent(
            type='text',
            text=f'❌ Error comparing stocks: {str(e)}'
        )]

@server.tool()
async def get_cache_info(ticker: str = None) -> list[TextContent]:
    """
    Get information about cached data.
    
    Args:
        ticker: Specific ticker to check (optional, shows all if not provided)
    
    Returns:
        Cache status and age information
    """
    try:
        if ticker:
            ticker = ticker.upper()
            cache_file = cache_dir / f'{ticker}.json'
            
            if not cache_file.exists():
                return [TextContent(
                    type='text',
                    text=f'❌ No cached data for {ticker}'
                )]
            
            # Get cache info
            cache_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
            age_hours = (datetime.now() - cache_time).total_seconds() / 3600
            
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            lines = [
                f'📦 Cache Info for {ticker}',
                f'{"="*40}',
                f'Last Updated: {cache_time.strftime("%Y-%m-%d %H:%M")}',
                f'Age: {age_hours:.1f} hours',
                f'File Size: {cache_file.stat().st_size / 1024:.1f} KB',
                f'',
                f'Cached Metrics:',
                f'  Price: ${data.get("currentPrice", "N/A")}',
                f'  52W Range: ${data.get("fiftyTwoWeekLow", 0):.2f} - ${data.get("fiftyTwoWeekHigh", 0):.2f}',
                f'  Market Cap: ${data.get("marketCap", 0)/1e9:.1f}B'
            ]
            
            return [TextContent(type='text', text='\n'.join(lines))]
        
        else:
            # Show all cached files
            cache_files = list(cache_dir.glob('*.json'))
            
            if not cache_files:
                return [TextContent(
                    type='text',
                    text='📦 Cache is empty'
                )]
            
            lines = ['📦 Cached Tickers', '=' * 40]
            
            for cache_file in sorted(cache_files):
                ticker = cache_file.stem
                cache_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                age_hours = (datetime.now() - cache_time).total_seconds() / 3600
                
                status = '🟢' if age_hours < 24 else '🟡' if age_hours < 72 else '🔴'
                lines.append(f'{status} {ticker}: {age_hours:.1f}h old')
            
            lines.append(f'\nTotal: {len(cache_files)} cached tickers')
            
            return [TextContent(type='text', text='\n'.join(lines))]
            
    except Exception as e:
        return [TextContent(
            type='text',
            text=f'❌ Error checking cache: {str(e)}'
        )]

@server.tool()
async def find_value_stocks(max_pe: float = 15, min_roe: float = 15) -> list[TextContent]:
    """
    Find undervalued stocks based on P/E and ROE criteria.
    
    Args:
        max_pe: Maximum P/E ratio (default: 15)
        min_roe: Minimum ROE percentage (default: 15)
    
    Returns:
        List of stocks meeting the value criteria
    """
    try:
        # Check watchlist tickers
        watchlist = [
            'MOH', 'ACGL', 'NEM', 'HIG', 'STLD', 'CVX', 'DHI',
            'ALLE', 'NUE', 'BRK-B', 'SQM', 'TSLA'
        ]
        
        value_stocks = []
        
        for ticker in watchlist:
            data = data_fetcher.fetch_stock_data(ticker)
            if not data:
                continue
            
            pe = data.get('trailingPE', float('inf'))
            roe = (data.get('returnOnEquity', 0) * 100) if data.get('returnOnEquity') else 0
            
            if pe <= max_pe and roe >= min_roe:
                value_stocks.append({
                    'ticker': ticker,
                    'name': data.get('longName', ticker),
                    'pe': pe,
                    'roe': roe,
                    'price': data.get('currentPrice', 0),
                    'pb': data.get('priceToBook', 0)
                })
        
        if not value_stocks:
            return [TextContent(
                type='text',
                text=f'❌ No stocks found with P/E ≤ {max_pe} and ROE ≥ {min_roe}%'
            )]
        
        # Sort by P/E ratio
        value_stocks.sort(key=lambda x: x['pe'])
        
        lines = [
            f'💎 Value Stocks (P/E ≤ {max_pe}, ROE ≥ {min_roe}%)',
            '=' * 60
        ]
        
        for stock in value_stocks:
            lines.extend([
                f'\n🎯 {stock["ticker"]} - {stock["name"]}',
                f'  Price: ${stock["price"]:.2f}',
                f'  P/E: {stock["pe"]:.1f} ✅',
                f'  P/B: {stock["pb"]:.1f}',
                f'  ROE: {stock["roe"]:.1f}% ✅'
            ])
        
        lines.append(f'\n📊 Found {len(value_stocks)} value stocks')
        
        return [TextContent(type='text', text='\n'.join(lines))]
        
    except Exception as e:
        return [TextContent(
            type='text',
            text=f'❌ Error finding value stocks: {str(e)}'
        )]

@server.tool()
async def clear_cache(ticker: str = None) -> list[TextContent]:
    """
    Clear cached data for a specific ticker or all tickers.
    
    Args:
        ticker: Specific ticker to clear (optional, clears all if not provided)
    
    Returns:
        Confirmation of cache clearing
    """
    try:
        if ticker:
            ticker = ticker.upper()
            cache_file = cache_dir / f'{ticker}.json'
            
            if cache_file.exists():
                cache_file.unlink()
                return [TextContent(
                    type='text',
                    text=f'✅ Cleared cache for {ticker}'
                )]
            else:
                return [TextContent(
                    type='text',
                    text=f'❌ No cache found for {ticker}'
                )]
        else:
            # Clear all cache files
            cache_files = list(cache_dir.glob('*.json'))
            count = len(cache_files)
            
            for cache_file in cache_files:
                cache_file.unlink()
            
            return [TextContent(
                type='text',
                text=f'✅ Cleared {count} cached files'
            )]
            
    except Exception as e:
        return [TextContent(
            type='text',
            text=f'❌ Error clearing cache: {str(e)}'
        )]

async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == '__main__':
    asyncio.run(main())
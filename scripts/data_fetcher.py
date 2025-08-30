#!/usr/bin/env python
"""
Asynchronous Data Fetcher Service

This service fetches stock data independently from analysis.
Data is cached locally for offline analysis.

Usage:
    poetry run python scripts/data_fetcher.py --universe sp500 --max-stocks 1000
"""

import asyncio
import json
import logging
import argparse
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Set
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockDataCache:
    """Manages local stock data cache"""
    
    def __init__(self, cache_dir: str = 'data/stock_cache'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.cache_dir / 'cache_index.json'
        self.load_index()
    
    def load_index(self):
        """Load cache index tracking what data we have"""
        if self.index_file.exists():
            with open(self.index_file, 'r') as f:
                self.index = json.load(f)
        else:
            self.index = {
                'stocks': {},
                'last_updated': datetime.now().isoformat(),
                'version': '1.0'
            }
    
    def save_index(self):
        """Save cache index atomically to prevent corruption"""
        self.index['last_updated'] = datetime.now().isoformat()
        
        # Write to temporary file first, then atomic rename
        temp_file = self.index_file.with_suffix('.tmp')
        try:
            with open(temp_file, 'w') as f:
                json.dump(self.index, f, indent=2)
            # Atomic rename prevents corruption from concurrent writes
            os.rename(temp_file, self.index_file)
        except Exception as e:
            # Clean up temp file if write failed
            if temp_file.exists():
                temp_file.unlink()
            raise e
    
    def get_update_order(self, tickers: List[str]) -> List[str]:
        """Get tickers in update order: empty stocks first, then oldest to newest"""
        empty_stocks = []
        cached_stocks = []
        
        for ticker in tickers:
            if ticker not in self.index['stocks']:
                empty_stocks.append(ticker)
            else:
                cached_stocks.append(ticker)
        
        # Sort cached stocks by age (oldest first)
        cached_stocks.sort(key=lambda t: self.index['stocks'][t]['last_updated'])
        
        return empty_stocks + cached_stocks
    
    def get_cached_data(self, ticker: str) -> Optional[Dict]:
        """Get cached data for a ticker"""
        cache_file = self.cache_dir / f'{ticker}.json'
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                return json.load(f)
        return None
    
    def save_stock_data(self, ticker: str, data: Dict):
        """Save stock data to cache atomically"""
        cache_file = self.cache_dir / f'{ticker}.json'
        temp_file = cache_file.with_suffix('.tmp')
        
        # Add metadata
        data['_cache_metadata'] = {
            'ticker': ticker,
            'cached_at': datetime.now().isoformat(),
            'data_source': 'yfinance'
        }
        
        # Save data atomically
        try:
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            os.rename(temp_file, cache_file)
        except Exception as e:
            if temp_file.exists():
                temp_file.unlink()
            raise e
        
        # Update index
        self.index['stocks'][ticker] = {
            'last_updated': datetime.now().isoformat(),
            'file_size': cache_file.stat().st_size,
            'has_financials': 'financials' in data,
            'has_info': 'info' in data
        }
        self.save_index()
    
    def get_cached_tickers(self) -> Set[str]:
        """Get all tickers we have cached data for"""
        return set(self.index['stocks'].keys())


class AsyncStockDataFetcher:
    """Fetches stock data using thread pool (simplified)"""
    
    def __init__(self, max_workers: int = 10):
        self.cache = StockDataCache()
        self.max_workers = max_workers
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def fetch_stock_data_sync(self, ticker: str) -> Dict:
        """Fetch fresh data for a single stock"""
        try:
            logger.info(f"Fetching fresh data for {ticker}")
            
            # Fetch from yfinance
            stock = yf.Ticker(ticker)
            
            # Get comprehensive data
            data = {
                'ticker': ticker,
                'info': {},
                'financials': {},
                'price_data': {},
                'fetch_timestamp': datetime.now().isoformat()
            }
            
            # Basic info (most important)
            try:
                info = stock.info
                data['info'] = {
                    'currentPrice': info.get('currentPrice'),
                    'marketCap': info.get('marketCap'),
                    'sector': info.get('sector'),
                    'industry': info.get('industry'),
                    'longName': info.get('longName'),
                    'shortName': info.get('shortName'),
                    'symbol': info.get('symbol'),
                    'currency': info.get('currency'),
                    'exchange': info.get('exchange'),
                    'country': info.get('country')
                }
            except Exception as e:
                logger.warning(f"Could not fetch info for {ticker}: {e}")
            
            # Key financial metrics
            try:
                data['financials'] = {
                    'trailingPE': info.get('trailingPE'),
                    'forwardPE': info.get('forwardPE'),
                    'priceToBook': info.get('priceToBook'),
                    'returnOnEquity': info.get('returnOnEquity'),
                    'debtToEquity': info.get('debtToEquity'),
                    'currentRatio': info.get('currentRatio'),
                    'revenueGrowth': info.get('revenueGrowth'),
                    'earningsGrowth': info.get('earningsGrowth'),
                    'operatingMargins': info.get('operatingMargins'),
                    'profitMargins': info.get('profitMargins'),
                    'totalRevenue': info.get('totalRevenue'),
                    'totalCash': info.get('totalCash'),
                    'totalDebt': info.get('totalDebt'),
                    'sharesOutstanding': info.get('sharesOutstanding')
                }
            except Exception as e:
                logger.warning(f"Could not fetch financials for {ticker}: {e}")
            
            # Recent price data (for charts/trends)
            try:
                hist = stock.history(period='1y')
                if not hist.empty:
                    data['price_data'] = {
                        'current_price': float(hist['Close'].iloc[-1]),
                        'price_52w_high': float(hist['High'].max()),
                        'price_52w_low': float(hist['Low'].min()),
                        'avg_volume': int(hist['Volume'].mean()),
                        'price_trend_30d': float((hist['Close'].iloc[-1] / hist['Close'].iloc[-30] - 1) * 100) if len(hist) >= 30 else None
                    }
            except Exception as e:
                logger.warning(f"Could not fetch price data for {ticker}: {e}")
            
            # Cache the data
            self.cache.save_stock_data(ticker, data)
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch data for {ticker}: {e}")
            return {
                'ticker': ticker,
                'error': str(e),
                'fetch_timestamp': datetime.now().isoformat()
            }
    
    async def fetch_multiple_stocks(self, tickers: List[str], max_concurrent: int = 10) -> Dict[str, Dict]:
        """Fetch data for multiple stocks concurrently"""
        results = {}
        
        # Use ThreadPoolExecutor for yfinance calls (they're synchronous)
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            # Submit all tasks
            future_to_ticker = {
                executor.submit(self.fetch_stock_data_sync, ticker): ticker 
                for ticker in tickers
            }
            
            # Collect results as they complete
            for i, future in enumerate(as_completed(future_to_ticker), 1):
                ticker = future_to_ticker[future]
                try:
                    data = future.result(timeout=30)  # 30 second timeout per stock
                    results[ticker] = data
                    
                    if i % 10 == 0 or i == len(tickers):
                        logger.info(f"Completed {i}/{len(tickers)} stocks")
                        
                except Exception as e:
                    logger.error(f"Failed to fetch {ticker}: {e}")
                    results[ticker] = {
                        'ticker': ticker,
                        'error': str(e),
                        'fetch_timestamp': datetime.now().isoformat()
                    }
        
        return results


def get_universe_tickers(universe: str, max_stocks: int = 1000) -> List[str]:
    """Get ticker list for a universe using dynamic index manager."""
    from scripts.index_manager import IndexManager
    
    try:
        # Initialize the index manager
        index_manager = IndexManager()
        
        # Map universe names to index manager methods
        if universe == 'sp500':
            tickers = index_manager.get_index_tickers('sp500')
        elif universe == 'international':
            # Combine multiple international indices
            tickers = []
            tickers.extend(index_manager.get_index_tickers('ftse100'))
            # Add more indices as they become available
            tickers = list(dict.fromkeys(tickers))  # Remove duplicates
        elif universe == 'all':
            # Get all known tickers from the registry
            tickers = index_manager.get_all_tickers()
        elif universe == 'cached':
            # Return all companies in our registry
            tickers = list(index_manager.companies['companies'].keys())
        else:
            # Fallback universes - small curated lists for specific themes
            universe_configs = {
                'japan': [
                    '7203.T', '6098.T', '4063.T', '4502.T', '9984.T', '9432.T', '8316.T',
                    '6758.T', '7267.T', '6861.T', '6954.T', '6920.T', '6752.T', '4543.T'
                ],
                'growth': [
                    'TSLA', 'SHOP', 'ROKU', 'ZM', 'SNOW', 'PLTR', 'RBLX', 'U', 'DDOG', 'CRWD'
                ],
                'tech': [
                    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'ORCL', 'CRM', 'ADBE', 'INTC',
                    'AMD', 'QCOM', 'CSCO', 'IBM', 'NOW', 'INTU', 'TXN', 'MU', 'AMAT', 'LRCX'
                ],
            }
            tickers = universe_configs.get(universe, [])
        
        # Log the result
        logger.info(f"Universe '{universe}': {len(tickers)} tickers (from dynamic index manager)")
        
        return tickers[:max_stocks]
        
    except Exception as e:
        logger.error(f"Failed to get dynamic tickers for {universe}: {e}")
        
        # Fallback to legacy sp500_tickers.json for S&P 500
        if universe == 'sp500':
            try:
                import json
                with open('sp500_tickers.json', 'r') as f:
                    fallback_tickers = json.load(f)
                logger.info(f"Fallback: loaded {len(fallback_tickers)} S&P 500 tickers from file")
                return fallback_tickers[:max_stocks]
            except:
                pass
        
        # Final fallback - minimal set
        fallback_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'ORCL', 'CRM', 'ADBE']
        logger.warning(f"Using minimal fallback: {len(fallback_tickers)} tickers")
        return fallback_tickers


async def main():
    """Main data fetching routine"""
    parser = argparse.ArgumentParser(description='Fetch stock data asynchronously')
    parser.add_argument('--universe', default='sp500', help='Stock universe to fetch')
    parser.add_argument('--max-stocks', type=int, default=500, help='Maximum stocks to fetch')
    parser.add_argument('--max-concurrent', type=int, default=10, help='Max concurrent requests')
    parser.add_argument('--force-refresh', action='store_true', help='Ignore cache and fetch fresh data')
    
    args = parser.parse_args()
    
    # Get ticker list
    tickers = get_universe_tickers(args.universe, args.max_stocks)
    logger.info(f"Planning to fetch data for {len(tickers)} stocks from {args.universe} universe")
    
    # Get update order: empty stocks first, then oldest to newest
    cache = StockDataCache()
    tickers = cache.get_update_order(tickers)
    
    logger.info(f"Will update {len(tickers)} stocks in optimal order (empty first, then oldest to newest)")
    
    # Fetch data
    start_time = time.time()
    
    async with AsyncStockDataFetcher(max_workers=args.max_concurrent) as fetcher:
        results = await fetcher.fetch_multiple_stocks(tickers, args.max_concurrent)
    
    # Report results
    successful = sum(1 for r in results.values() if 'error' not in r)
    failed = len(results) - successful
    elapsed = time.time() - start_time
    
    logger.info(f"""
Data fetching complete:
  - Total stocks: {len(results)}
  - Successful: {successful}
  - Failed: {failed}
  - Time elapsed: {elapsed:.1f} seconds
  - Average: {elapsed/len(results):.2f} sec/stock
  - Cache location: {fetcher.cache.cache_dir}
    """)
    
    # Save summary report
    summary = {
        'universe': args.universe,
        'total_requested': len(tickers),
        'successful_fetches': successful,
        'failed_fetches': failed,
        'time_elapsed': elapsed,
        'fetch_timestamp': datetime.now().isoformat(),
        'failed_tickers': [ticker for ticker, data in results.items() if 'error' in data]
    }
    
    summary_file = Path(f'data_fetch_summary_{args.universe}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Summary saved to: {summary_file}")


if __name__ == '__main__':
    asyncio.run(main())
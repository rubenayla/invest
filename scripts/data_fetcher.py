#!/usr/bin/env python
"""
Asynchronous Data Fetcher Service

This service fetches stock data independently from analysis.
Data is cached locally for offline analysis.

Usage:
    uv run python scripts/data_fetcher.py --universe sp500 --max-stocks 1000
"""

import asyncio
import json
import logging
import argparse
import time
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Set
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile
import os

# Import currency converter (dynamically since it's in scripts/)
import sys
from pathlib import Path as PathLib
if str(PathLib(__file__).parent) not in sys.path:
    sys.path.insert(0, str(PathLib(__file__).parent))
from currency_converter import convert_financials_to_usd, convert_financial_statements_to_usd

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockDataCache:
    """Manages local stock data cache"""
    
    def __init__(self, cache_dir: str = 'data/stock_cache', db_path: Optional[str] = None):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Database path
        if db_path is None:
            project_root = Path(__file__).parent.parent
            db_path = project_root / 'data' / 'stock_data.db'
        self.db_path = Path(db_path)

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
        """Get tickers in update order: broken/empty first, then oldest to newest"""
        empty_stocks = []
        broken_stocks = []
        cached_stocks = []

        for ticker in tickers:
            if ticker not in self.index['stocks']:
                empty_stocks.append(ticker)
            else:
                # Check if file is corrupted/empty (< 500 bytes)
                cache_file = self.cache_dir / f'{ticker}.json'
                if cache_file.exists() and cache_file.stat().st_size < 500:
                    broken_stocks.append(ticker)
                else:
                    cached_stocks.append(ticker)

        # Sort cached stocks by age (oldest first)
        cached_stocks.sort(key=lambda t: self.index['stocks'][t]['last_updated'])

        # Priority: 1) Empty (not in index), 2) Broken (< 500 bytes), 3) Oldest to newest
        return empty_stocks + broken_stocks + cached_stocks
    
    def get_cached_data(self, ticker: str) -> Optional[Dict]:
        """Get cached data for a ticker"""
        cache_file = self.cache_dir / f'{ticker}.json'
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                return json.load(f)
        return None
    
    def save_to_sqlite(self, ticker: str, data: Dict):
        """Save stock data to SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            info = data.get('info', {})
            financials = data.get('financials', {})
            price_data = data.get('price_data', {})

            cursor.execute('''
                INSERT OR REPLACE INTO current_stock_data (
                    ticker,
                    current_price, market_cap, sector, industry, long_name, short_name,
                    currency, exchange, country,
                    trailing_pe, forward_pe, price_to_book, return_on_equity, debt_to_equity,
                    current_ratio, revenue_growth, earnings_growth, operating_margins, profit_margins,
                    total_revenue, total_cash, total_debt, shares_outstanding,
                    trailing_eps, book_value, revenue_per_share, price_to_sales_ttm,
                    price_52w_high, price_52w_low, avg_volume, price_trend_30d,
                    cashflow_json, balance_sheet_json, income_json,
                    fetch_timestamp, last_updated
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?
                )
            ''', (
                ticker,
                info.get('currentPrice'), info.get('marketCap'), info.get('sector'),
                info.get('industry'), info.get('longName'), info.get('shortName'),
                info.get('currency'), info.get('exchange'), info.get('country'),
                financials.get('trailingPE'), financials.get('forwardPE'), financials.get('priceToBook'),
                financials.get('returnOnEquity'), financials.get('debtToEquity'), financials.get('currentRatio'),
                financials.get('revenueGrowth'), financials.get('earningsGrowth'), financials.get('operatingMargins'),
                financials.get('profitMargins'), financials.get('totalRevenue'), financials.get('totalCash'),
                financials.get('totalDebt'), financials.get('sharesOutstanding'), financials.get('trailingEps'),
                financials.get('bookValue'), financials.get('revenuePerShare'), financials.get('priceToSalesTrailing12Months'),
                price_data.get('price_52w_high'), price_data.get('price_52w_low'),
                price_data.get('avg_volume'), price_data.get('price_trend_30d'),
                json.dumps(data.get('cashflow', [])),
                json.dumps(data.get('balance_sheet', [])),
                json.dumps(data.get('income', [])),
                data.get('fetch_timestamp', datetime.now().isoformat()),
                datetime.now().isoformat()
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f'{ticker}: Failed to save to SQLite: {e}')

    def save_stock_data(self, ticker: str, data: Dict):
        """Save stock data to both JSON cache and SQLite database"""
        # VALIDATION: Check if data is valid before saving
        if 'error' in data:
            logger.error(f'{ticker}: Skipping save - data fetch failed: {data.get("error")}')
            return

        # Check for minimum required fields
        info = data.get('info', {})
        if not info or not info.get('currentPrice'):
            logger.error(f'{ticker}: Skipping save - missing currentPrice in info dict')
            return

        # Check if we have at least some data (not all None/empty)
        has_sector = info.get('sector') is not None
        has_market_cap = info.get('marketCap') is not None
        has_minimal_data = has_sector or has_market_cap

        if not has_minimal_data:
            logger.error(f'{ticker}: Skipping save - insufficient data (no sector, no market cap)')
            return

        logger.info(f'{ticker}: Data validation passed - saving to cache and database')

        cache_file = self.cache_dir / f'{ticker}.json'
        temp_file = cache_file.with_suffix('.tmp')

        # Add metadata
        data['_cache_metadata'] = {
            'ticker': ticker,
            'cached_at': datetime.now().isoformat(),
            'data_source': 'yfinance'
        }

        # Save to JSON atomically (backup)
        try:
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            os.rename(temp_file, cache_file)
        except Exception as e:
            if temp_file.exists():
                temp_file.unlink()
            raise e

        # Save to SQLite (primary)
        self.save_to_sqlite(ticker, data)

        # Update index
        self.index['stocks'][ticker] = {
            'last_updated': datetime.now().isoformat(),
            'file_size': cache_file.stat().st_size,
            'has_financials': 'financials' in data,
            'has_info': 'info' in data,
            'has_cashflow': 'cashflow' in data,
            'has_balance_sheet': 'balance_sheet' in data,
            'has_income': 'income' in data
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
    
    def fetch_stock_data_sync(self, ticker: str, max_retries: int = 6) -> Dict:
        """Fetch fresh data for a single stock with retry logic"""
        last_error = None

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    # Exponential backoff: 5s, 10s, 20s, 40s, 80s, 160s
                    wait_time = 5 * (2 ** (attempt - 1))
                    logger.info(f"{ticker}: Retry {attempt}/{max_retries} after {wait_time}s wait")
                    time.sleep(wait_time)

                logger.info(f"Fetching fresh data for {ticker} (attempt {attempt + 1}/{max_retries})")

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

                # Fetch stock info (required for everything else)
                info = stock.info

                # Basic info (most important)
                data['info'] = {
                    'currentPrice': info.get('currentPrice'),
                    'marketCap': info.get('marketCap'),
                    'sector': info.get('sector'),
                    'industry': info.get('industry'),
                    'longName': info.get('longName'),
                    'shortName': info.get('shortName'),
                    'symbol': info.get('symbol'),
                    'currency': info.get('currency'),
                    'financialCurrency': info.get('financialCurrency'),  # Added: explicit financial reporting currency
                    'exchange': info.get('exchange'),
                    'country': info.get('country')
                }

                # Key financial metrics
                try:
                    # Calculate debt-to-equity ourselves - yfinance returns it as percentage (92.867)
                    # but we store ratios as ratios (0.929), not percentages
                    debt_to_equity = None
                    total_debt = info.get('totalDebt')
                    book_value = info.get('bookValue')
                    shares_outstanding = info.get('sharesOutstanding')

                    if total_debt and book_value and shares_outstanding and book_value > 0:
                        total_equity = book_value * shares_outstanding
                        if total_equity > 0:
                            debt_to_equity = total_debt / total_equity

                    data['financials'] = {
                        'trailingPE': info.get('trailingPE'),
                        'forwardPE': info.get('forwardPE'),
                        'priceToBook': info.get('priceToBook'),
                        'returnOnEquity': info.get('returnOnEquity'),
                        'debtToEquity': debt_to_equity,  # Use calculated ratio, not yfinance's percentage
                        'currentRatio': info.get('currentRatio'),
                        'revenueGrowth': info.get('revenueGrowth'),
                        'earningsGrowth': info.get('earningsGrowth'),
                        'operatingMargins': info.get('operatingMargins'),
                        'profitMargins': info.get('profitMargins'),
                        'totalRevenue': info.get('totalRevenue'),
                        'totalCash': info.get('totalCash'),
                        'totalDebt': info.get('totalDebt'),
                        'sharesOutstanding': info.get('sharesOutstanding'),
                        # Per-share metrics needed by Simple Ratios model
                        'trailingEps': info.get('trailingEps'),
                        'bookValue': info.get('bookValue'),
                        'revenuePerShare': info.get('revenuePerShare'),
                        'priceToSalesTrailing12Months': info.get('priceToSalesTrailing12Months'),
                    }

                    # Convert foreign currency financials to USD
                    data['financials'] = convert_financials_to_usd(data['info'], data['financials'])

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

                # Raw financial statements (for DCF/RIM valuation models)
                try:
                    import pandas as pd

                    # Cash flow statement
                    cashflow = stock.cashflow
                    if cashflow is not None and not cashflow.empty:
                        # Reset index and convert timestamps to strings
                        df = cashflow.reset_index()
                        df.columns = df.columns.astype(str)  # Convert column names to strings
                        # Convert timestamp values to strings
                        for col in df.columns:
                            if pd.api.types.is_datetime64_any_dtype(df[col]):
                                df[col] = df[col].astype(str)
                        data['cashflow'] = df.to_dict(orient='records')

                    # Balance sheet
                    balance_sheet = stock.balance_sheet
                    if balance_sheet is not None and not balance_sheet.empty:
                        df = balance_sheet.reset_index()
                        df.columns = df.columns.astype(str)
                        for col in df.columns:
                            if pd.api.types.is_datetime64_any_dtype(df[col]):
                                df[col] = df[col].astype(str)
                        data['balance_sheet'] = df.to_dict(orient='records')

                    # Income statement
                    income_stmt = stock.income_stmt
                    if income_stmt is not None and not income_stmt.empty:
                        df = income_stmt.reset_index()
                        df.columns = df.columns.astype(str)
                        for col in df.columns:
                            if pd.api.types.is_datetime64_any_dtype(df[col]):
                                df[col] = df[col].astype(str)
                        data['income'] = df.to_dict(orient='records')

                    logger.info(f"Fetched financial statements for {ticker}")
                except Exception as e:
                    logger.warning(f"Could not fetch financial statements for {ticker}: {e}")

                # Convert financial statements if currency conversion was applied
                if data['financials'].get('_currency_converted'):
                    financial_currency = data['financials'].get('_original_currency')
                    exchange_rate = data['financials'].get('_exchange_rate_used')
                    if financial_currency and exchange_rate:
                        data = convert_financial_statements_to_usd(data, financial_currency, exchange_rate)

                # Cache the data
                self.cache.save_stock_data(ticker, data)

                # Success - return data
                return data

            except Exception as e:
                last_error = e
                logger.warning(f"{ticker}: Attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt == max_retries - 1:
                    # Final attempt failed
                    logger.error(f"{ticker}: All {max_retries} attempts failed. Last error: {e}")
                # Loop continues to next retry

        # All retries exhausted
        return {
            'ticker': ticker,
            'error': f'Failed after {max_retries} attempts: {str(last_error)}',
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


def get_universe_tickers(universe: str) -> List[str]:
    """Get ticker list for a universe using dynamic index manager."""
    import sys
    from pathlib import Path
    
    # Add project root to path for imports
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
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
                'spain': [
                    'SAN.MC', 'BBVA.MC', 'CABK.MC', 'SAB.MC', 'BKT.MC', 'MAP.MC',
                    'IBE.MC', 'ELE.MC', 'ENG.MC', 'RED.MC', 'REE.MC', 'NTGY.MC',
                    'REP.MC', 'TEF.MC', 'ITX.MC', 'ACS.MC', 'FER.MC', 'FCC.MC',
                    'ACX.MC', 'ANA.MC', 'AENA.MC', 'IAG.MC', 'MEL.MC', 'GRF.MC',
                    'IDR.MC', 'COL.MC', 'CLNX.MC', 'ALM.MC', 'AMS.MC', 'SGRE.MC',
                    'VIS.MC', 'MRL.MC', 'ROVI.MC', 'SLR.MC'
                ],
                'europe': [
                    # France
                    'MC.PA', 'OR.PA', 'SAN.PA', 'TTE.PA', 'AI.PA', 'SU.PA', 'BNP.PA',
                    'RMS.PA', 'CS.PA', 'DG.PA', 'SAF.PA', 'EL.PA', 'DSY.PA', 'CA.PA',
                    'ORA.PA', 'EN.PA', 'VIE.PA', 'SGO.PA', 'KER.PA', 'STLAM.PA',
                    # Germany
                    'SAP.DE', 'SIE.DE', 'AIR.DE', 'ALV.DE', 'BAS.DE', 'MBG.DE', 'VOW3.DE',
                    'BMW.DE', 'DTE.DE', 'EOAN.DE', 'MUV2.DE', 'ADS.DE', 'DB1.DE', 'IFX.DE',
                    'SHL.DE', 'BNR.DE',
                    # Netherlands
                    'ASML.AS', 'PHIA.AS', 'INGA.AS', 'ABN.AS', 'AD.AS', 'HEIA.AS',
                    # Italy
                    'ENI.MI', 'ISP.MI', 'ENEL.MI', 'G.MI', 'STM.MI',
                    # Spain
                    'SAN.MC', 'BBVA.MC', 'IBE.MC', 'ITX.MC',
                    # Belgium
                    'ABI.BR'
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
        
        return tickers
        
    except Exception as e:
        logger.error(f"Failed to get dynamic tickers for {universe}: {e}")
        
        # Fallback to legacy sp500_tickers.json for S&P 500
        if universe == 'sp500':
            try:
                import json
                with open('sp500_tickers.json', 'r') as f:
                    fallback_tickers = json.load(f)
                logger.info(f"Fallback: loaded {len(fallback_tickers)} S&P 500 tickers from file")
                return fallback_tickers
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
    parser.add_argument('--max-concurrent', type=int, default=10, help='Max concurrent requests')
    parser.add_argument('--force-refresh', action='store_true', help='Ignore cache and fetch fresh data')
    
    args = parser.parse_args()
    
    # Get ticker list
    tickers = get_universe_tickers(args.universe)
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
  - Average: {elapsed/len(results):.2f} sec/stock" if results else "  - Average: N/A (no results)"
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
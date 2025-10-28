#!/usr/bin/env python3
"""
Populate historical snapshots for stocks missing temporal data.

This script fetches historical fundamental data from yfinance at 6-month intervals
and populates the assets/snapshots tables so neural networks can make predictions.
"""

import logging
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set

import pandas as pd
import yfinance as yf

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HistoricalSnapshotFetcher:
    """Fetches historical fundamental data and populates snapshots table."""

    def __init__(self, db_path: str = 'data/stock_data.db'):
        self.db_path = Path(project_root) / db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        # Rate limiting
        self.request_count = 0
        self.last_request_time = time.time()
        self.requests_per_minute = 30  # Conservative limit

        # VIX cache (date -> VIX value)
        self.vix_cache = {}
        self._fetch_vix_history()

    def get_stocks_without_snapshots(self) -> List[tuple]:
        """Get list of stocks that don't have historical snapshots."""
        query = '''
        SELECT ticker, current_price, sector, industry
        FROM current_stock_data
        WHERE ticker NOT IN (SELECT DISTINCT symbol FROM assets)
        ORDER BY ticker
        '''
        return self.cursor.execute(query).fetchall()

    def get_or_create_asset(self, ticker: str, sector: str = None, industry: str = None) -> int:
        """Get asset_id or create new asset entry."""
        # Check if asset exists
        result = self.cursor.execute(
            'SELECT id FROM assets WHERE symbol = ?',
            (ticker,)
        ).fetchone()

        if result:
            return result[0]

        # Create new asset
        self.cursor.execute('''
            INSERT INTO assets (symbol, asset_type, sector, industry)
            VALUES (?, ?, ?, ?)
        ''', (ticker, 'stock', sector or 'Unknown', industry or 'Unknown'))

        self.conn.commit()
        return self.cursor.lastrowid

    def rate_limit(self):
        """Simple rate limiting to avoid overwhelming yfinance."""
        self.request_count += 1

        # Every 30 requests, wait a bit
        if self.request_count % self.requests_per_minute == 0:
            elapsed = time.time() - self.last_request_time
            if elapsed < 60:
                wait_time = 60 - elapsed
                logger.info(f'Rate limiting: waiting {wait_time:.1f}s...')
                time.sleep(wait_time)
            self.last_request_time = time.time()

    def _fetch_vix_history(self):
        """Fetch VIX historical data and cache it."""
        try:
            logger.info('Fetching VIX historical data...')
            vix = yf.Ticker('^VIX')

            # Fetch VIX history from 2000 to today
            hist = vix.history(start='2000-01-01', end=datetime.now().strftime('%Y-%m-%d'))

            if hist.empty:
                logger.warning('No VIX data retrieved, will use default value')
                return

            # Cache VIX close price by date
            for date, row in hist.iterrows():
                date_str = date.strftime('%Y-%m-%d')
                self.vix_cache[date_str] = float(row['Close'])

            logger.info(f'Cached VIX data for {len(self.vix_cache)} dates')

        except Exception as e:
            logger.warning(f'Error fetching VIX history: {e}. Will use default value.')

    def get_vix_for_date(self, date_str: str) -> Optional[float]:
        """Get VIX value for a specific date, or None if not available."""
        # Direct match
        if date_str in self.vix_cache:
            return self.vix_cache[date_str]

        # Try to find closest previous trading day (within 7 days)
        target_date = datetime.strptime(date_str, '%Y-%m-%d')
        for days_back in range(1, 8):
            check_date = (target_date - timedelta(days=days_back)).strftime('%Y-%m-%d')
            if check_date in self.vix_cache:
                return self.vix_cache[check_date]

        # Default fallback
        return 20.0  # Historical median

    def fetch_historical_snapshots(
        self,
        ticker: str,
        start_year: int = 2004,
        interval_months: int = 6
    ) -> List[Dict]:
        """
        Fetch historical fundamental data at regular intervals.

        Parameters
        ----------
        ticker : str
            Stock ticker symbol
        start_year : int
            Year to start fetching from
        interval_months : int
            Months between snapshots (default 6)

        Returns
        -------
        List[Dict]
            List of snapshot data dictionaries
        """
        self.rate_limit()

        try:
            stock = yf.Ticker(ticker)

            # Get current info for sector/industry
            try:
                info = stock.info
                sector = info.get('sector', 'Unknown')
                industry = info.get('industry', 'Unknown')
            except Exception as e:
                logger.warning(f'{ticker}: Could not fetch current info - {e}')
                sector = 'Unknown'
                industry = 'Unknown'

            # Get historical data
            snapshots = []
            current_date = datetime.now()
            snapshot_date = datetime(start_year, 1, 1)

            while snapshot_date < current_date:
                # Try to get fundamentals for this date
                # yfinance doesn't have direct historical fundamentals API,
                # so we'll use quarterly financials and match dates

                snapshot_date += timedelta(days=30 * interval_months)

                # For now, we'll just note that this approach has limitations
                # and we may need to use the current info repeated over time
                # or fetch from another data source

            # Alternative: Use available quarterly data
            try:
                # Get quarterly financials
                quarterly_financials = stock.quarterly_financials
                quarterly_balance_sheet = stock.quarterly_balance_sheet
                quarterly_cashflow = stock.quarterly_cashflow

                if quarterly_financials is not None and not quarterly_financials.empty:
                    # Get available dates
                    available_dates = quarterly_financials.columns

                    for date in available_dates:
                        # Extract data for this date
                        snapshot = self._extract_snapshot_from_quarterly(
                            ticker=ticker,
                            snapshot_date=date,
                            financials=quarterly_financials,
                            balance_sheet=quarterly_balance_sheet,
                            cashflow=quarterly_cashflow,
                            sector=sector
                        )

                        if snapshot:
                            snapshots.append(snapshot)

                    logger.info(f'{ticker}: Created {len(snapshots)} snapshots from quarterly data')
                else:
                    logger.warning(f'{ticker}: No quarterly financials available')

            except Exception as e:
                logger.warning(f'{ticker}: Error fetching quarterly data - {e}')

            return snapshots

        except Exception as e:
            logger.error(f'{ticker}: Failed to fetch data - {e}')
            return []

    def _extract_snapshot_from_quarterly(
        self,
        ticker: str,
        snapshot_date: pd.Timestamp,
        financials: pd.DataFrame,
        balance_sheet: pd.DataFrame,
        cashflow: pd.DataFrame,
        sector: str
    ) -> Optional[Dict]:
        """Extract snapshot data from quarterly financials."""
        try:
            # Get data for this date
            date_str = snapshot_date.strftime('%Y-%m-%d')

            # Extract key metrics
            snapshot = {
                'ticker': ticker,
                'snapshot_date': date_str,
                'sector': sector,
                'vix': self.get_vix_for_date(date_str)
            }

            # From financials
            if snapshot_date in financials.columns:
                fin = financials[snapshot_date]
                snapshot['total_revenue'] = fin.get('Total Revenue', None)
                snapshot['operating_income'] = fin.get('Operating Income', None)
                snapshot['net_income'] = fin.get('Net Income', None)
                snapshot['ebitda'] = fin.get('EBITDA', None)

            # From balance sheet
            if snapshot_date in balance_sheet.columns:
                bs = balance_sheet[snapshot_date]
                snapshot['total_assets'] = bs.get('Total Assets', None)
                snapshot['total_debt'] = bs.get('Total Debt', None)
                snapshot['total_equity'] = bs.get('Stockholders Equity', None)
                snapshot['cash'] = bs.get('Cash And Cash Equivalents', None)
                snapshot['current_assets'] = bs.get('Current Assets', None)
                snapshot['current_liabilities'] = bs.get('Current Liabilities', None)

            # From cashflow
            if snapshot_date in cashflow.columns:
                cf = cashflow[snapshot_date]
                snapshot['operating_cashflow'] = cf.get('Operating Cash Flow', None)
                snapshot['free_cashflow'] = cf.get('Free Cash Flow', None)
                snapshot['capex'] = cf.get('Capital Expenditure', None)

            # Calculate derived metrics if we have the data
            if snapshot.get('total_revenue') and snapshot.get('net_income'):
                snapshot['profit_margins'] = float(snapshot['net_income']) / float(snapshot['total_revenue'])

            if snapshot.get('total_revenue') and snapshot.get('operating_income'):
                snapshot['operating_margins'] = float(snapshot['operating_income']) / float(snapshot['total_revenue'])

            if snapshot.get('net_income') and snapshot.get('total_equity'):
                snapshot['return_on_equity'] = float(snapshot['net_income']) / float(snapshot['total_equity'])

            if snapshot.get('total_debt') and snapshot.get('total_equity'):
                snapshot['debt_to_equity'] = float(snapshot['total_debt']) / float(snapshot['total_equity'])

            if snapshot.get('current_assets') and snapshot.get('current_liabilities'):
                snapshot['current_ratio'] = float(snapshot['current_assets']) / float(snapshot['current_liabilities'])

            return snapshot

        except Exception as e:
            logger.warning(f'{ticker} ({date_str}): Error extracting snapshot - {e}')
            return None

    def save_snapshots(self, asset_id: int, snapshots: List[Dict]):
        """Save snapshots to database."""
        for snapshot in snapshots:
            try:
                self.cursor.execute('''
                    INSERT INTO snapshots (
                        asset_id, snapshot_date, market_cap, pe_ratio, pb_ratio,
                        profit_margins, operating_margins, return_on_equity,
                        revenue_growth, earnings_growth, debt_to_equity,
                        current_ratio, free_cashflow, beta, vix
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    asset_id,
                    snapshot['snapshot_date'],
                    snapshot.get('market_cap'),
                    snapshot.get('pe_ratio'),
                    snapshot.get('pb_ratio'),
                    snapshot.get('profit_margins'),
                    snapshot.get('operating_margins'),
                    snapshot.get('return_on_equity'),
                    snapshot.get('revenue_growth'),
                    snapshot.get('earnings_growth'),
                    snapshot.get('debt_to_equity'),
                    snapshot.get('current_ratio'),
                    snapshot.get('free_cashflow'),
                    snapshot.get('beta', 1.0),
                    snapshot.get('vix')
                ))
            except sqlite3.IntegrityError:
                # Snapshot already exists
                pass
            except Exception as e:
                logger.warning(f'Error saving snapshot: {e}')

        self.conn.commit()

    def process_stock(self, ticker: str, sector: str = None, industry: str = None) -> int:
        """Process a single stock and return number of snapshots created."""
        logger.info(f'{ticker}: Fetching historical snapshots...')

        # Get or create asset
        asset_id = self.get_or_create_asset(ticker, sector, industry)

        # Fetch snapshots
        snapshots = self.fetch_historical_snapshots(ticker)

        if snapshots:
            # Save to database
            self.save_snapshots(asset_id, snapshots)
            logger.info(f'{ticker}: Saved {len(snapshots)} snapshots')
            return len(snapshots)
        else:
            logger.warning(f'{ticker}: No snapshots created')
            return 0

    def close(self):
        """Close database connection."""
        self.conn.close()


def main():
    """Main execution function."""
    logger.info('=' * 60)
    logger.info('Populating Historical Snapshots')
    logger.info('=' * 60)

    fetcher = HistoricalSnapshotFetcher()

    # Get stocks without snapshots
    stocks = fetcher.get_stocks_without_snapshots()
    logger.info(f'Found {len(stocks)} stocks without historical snapshots')

    if not stocks:
        logger.info('All stocks already have snapshots!')
        return 0

    # Process each stock
    total_snapshots = 0
    successful_stocks = 0
    failed_stocks = 0

    for i, (ticker, price, sector, industry) in enumerate(stocks, 1):
        try:
            logger.info(f'\n[{i}/{len(stocks)}] Processing {ticker}...')
            count = fetcher.process_stock(ticker, sector, industry)

            if count > 0:
                total_snapshots += count
                successful_stocks += 1
            else:
                failed_stocks += 1

            # Progress update every 10 stocks
            if i % 10 == 0:
                logger.info(f'\nProgress: {i}/{len(stocks)} stocks processed')
                logger.info(f'  Successful: {successful_stocks}')
                logger.info(f'  Failed: {failed_stocks}')
                logger.info(f'  Total snapshots: {total_snapshots}')

        except Exception as e:
            logger.error(f'{ticker}: Unexpected error - {e}')
            failed_stocks += 1

    # Summary
    logger.info('\n' + '=' * 60)
    logger.info('Historical Snapshot Population Complete!')
    logger.info('=' * 60)
    logger.info(f'Total stocks processed: {len(stocks)}')
    logger.info(f'Successful: {successful_stocks}')
    logger.info(f'Failed: {failed_stocks}')
    logger.info(f'Total snapshots created: {total_snapshots}')
    logger.info('=' * 60)

    fetcher.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())

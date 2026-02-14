"""
SQLite Stock Data Reader

Provides unified interface to read stock data from SQLite database.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class StockDataReader:
    """Read stock data from SQLite database."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize reader with database path."""
        if db_path is None:
            # Default to project database
            project_root = Path(__file__).parent.parent.parent.parent
            db_path = project_root / 'data' / 'stock_data.db'
        self.db_path = Path(db_path)

    def get_stock_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get stock data for a single ticker.

        Returns data in the same format as the JSON cache files for compatibility.

        Parameters
        ----------
        ticker : str
            Stock ticker symbol

        Returns
        -------
        Optional[Dict[str, Any]]
            Stock data dictionary or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM current_stock_data WHERE ticker = ?
        ''', (ticker,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        # Parse JSON data
        cashflow_data = json.loads(row['cashflow_json']) if row['cashflow_json'] else []
        balance_sheet_data = json.loads(row['balance_sheet_json']) if row['balance_sheet_json'] else []
        income_data = json.loads(row['income_json']) if row['income_json'] else []

        # Extract most recent cash flow values for valuation models
        free_cashflow = None
        operating_cashflow = None
        if cashflow_data and isinstance(cashflow_data, list):
            for item in cashflow_data:
                if isinstance(item, dict) and 'index' in item:
                    # Get most recent year (first column after 'index')
                    dates = [k for k in item.keys() if k != 'index']
                    if dates:
                        recent_date = dates[0]  # Most recent is first
                        value = item.get(recent_date)
                        if item['index'] == 'Free Cash Flow' and value and not (isinstance(value, float) and value != value):  # Check for NaN
                            free_cashflow = value
                        elif item['index'] == 'Operating Cash Flow' and value and not (isinstance(value, float) and value != value):
                            operating_cashflow = value

        # Convert to dictionary matching JSON cache format
        data = {
            'ticker': row['ticker'],
            'info': {
                'currentPrice': row['current_price'],
                'marketCap': row['market_cap'],
                'sector': row['sector'],
                'industry': row['industry'],
                'longName': row['long_name'],
                'shortName': row['short_name'],
                'currency': row['currency'],
                'exchange': row['exchange'],
                'country': row['country'],
                # Critical fields for valuation models (also in financials for compatibility)
                'sharesOutstanding': row['shares_outstanding'],
                'totalRevenue': row['total_revenue'],
                'totalCash': row['total_cash'],
                'totalDebt': row['total_debt'],
                'trailingEps': row['trailing_eps'],
                'bookValue': row['book_value'],
                'revenuePerShare': row['revenue_per_share'],
                'freeCashflow': free_cashflow,
                'operatingCashflow': operating_cashflow,
            },
            'financials': {
                'trailingPE': row['trailing_pe'],
                'forwardPE': row['forward_pe'],
                'priceToBook': row['price_to_book'],
                'returnOnEquity': row['return_on_equity'],
                'debtToEquity': row['debt_to_equity'],
                'currentRatio': row['current_ratio'],
                'revenueGrowth': row['revenue_growth'],
                'earningsGrowth': row['earnings_growth'],
                'operatingMargins': row['operating_margins'],
                'profitMargins': row['profit_margins'],
                'totalRevenue': row['total_revenue'],
                'totalCash': row['total_cash'],
                'totalDebt': row['total_debt'],
                'sharesOutstanding': row['shares_outstanding'],
                'trailingEps': row['trailing_eps'],
                'bookValue': row['book_value'],
                'revenuePerShare': row['revenue_per_share'],
                'priceToSalesTrailing12Months': row['price_to_sales_ttm'],
            },
            'price_data': {
                'current_price': row['current_price'],
                'price_52w_high': row['price_52w_high'],
                'price_52w_low': row['price_52w_low'],
                'avg_volume': row['avg_volume'],
                'price_trend_30d': row['price_trend_30d'],
            },
            'cashflow': cashflow_data,
            'balance_sheet': balance_sheet_data,
            'income': income_data,
            'fetch_timestamp': row['fetch_timestamp'],
        }

        return data

    def get_all_tickers(self) -> List[str]:
        """Get list of all tickers in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT ticker FROM current_stock_data ORDER BY ticker')
        tickers = [row[0] for row in cursor.fetchall()]

        conn.close()
        return tickers

    def get_stocks_by_sector(self, sector: str) -> List[str]:
        """Get all tickers in a specific sector."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT ticker FROM current_stock_data
            WHERE sector = ?
            ORDER BY ticker
        ''', (sector,))
        tickers = [row[0] for row in cursor.fetchall()]

        conn.close()
        return tickers

    def get_stock_count(self) -> int:
        """Get total number of stocks in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM current_stock_data')
        count = cursor.fetchone()[0]

        conn.close()
        return count

    def get_fundamental_history(self, ticker: str, metric: str) -> Optional[Dict[str, float]]:
        """
        Extract historical values for a fundamental metric from JSON data.

        Reads directly from database JSON fields (income_json, cashflow_json, balance_sheet_json)
        to provide multi-year historical trends. This prevents errors from relying on single
        point-in-time growth rates.

        Parameters
        ----------
        ticker : str
            Stock ticker symbol
        metric : str
            Metric name to extract. Common metrics:
            - Income Statement: 'Net Income', 'Total Revenue', 'Operating Income'
            - Cash Flow: 'Free Cash Flow', 'Operating Cash Flow'
            - Balance Sheet: 'Total Assets', 'Total Debt', 'Cash And Cash Equivalents'

        Returns
        -------
        Optional[Dict[str, float]]
            Dictionary mapping year (YYYY) to value, sorted newest to oldest.
            Returns None if ticker not found or metric doesn't exist.

        Examples
        --------
        >>> reader = StockDataReader()
        >>> revenue = reader.get_fundamental_history('CAG', 'Total Revenue')
        >>> print(revenue)
        {'2025': 12000000000, '2024': 11500000000, '2023': 11800000000, ...}
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT income_json, cashflow_json, balance_sheet_json
            FROM current_stock_data
            WHERE ticker = ?
        ''', (ticker,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        # Parse all JSON sources
        income_json, cashflow_json, balance_sheet_json = row
        data_sources = [
            json.loads(income_json) if income_json else [],
            json.loads(cashflow_json) if cashflow_json else [],
            json.loads(balance_sheet_json) if balance_sheet_json else [],
        ]

        # Search for metric across all sources
        for data_list in data_sources:
            if not isinstance(data_list, list):
                continue

            for item in data_list:
                if not isinstance(item, dict) or 'index' not in item:
                    continue

                # Check if this row matches our metric (case-insensitive partial match)
                item_name = item['index'].lower()
                metric_lower = metric.lower()

                if metric_lower in item_name or item_name in metric_lower:
                    # Extract year:value pairs
                    history = {}
                    for key, value in item.items():
                        if key == 'index':
                            continue

                        # Extract year from date string (e.g., '2025-05-31 00:00:00' -> '2025')
                        year = key[:4] if len(key) >= 4 else key

                        # Skip NaN values
                        if value is not None and not (isinstance(value, float) and value != value):
                            history[year] = value

                    # Return sorted by year (newest first)
                    if history:
                        return dict(sorted(history.items(), reverse=True))

        return None

    def get_earnings_trend(self, ticker: str) -> Optional[Dict[str, float]]:
        """
        Get historical net income trend for a stock.

        Convenience method that extracts net income history from database.
        Use this to avoid mistakes from relying on single-year growth rates.

        Parameters
        ----------
        ticker : str
            Stock ticker symbol

        Returns
        -------
        Optional[Dict[str, float]]
            Dictionary mapping year to net income, or None if not found
        """
        return self.get_fundamental_history(ticker, 'Net Income')

    def get_revenue_trend(self, ticker: str) -> Optional[Dict[str, float]]:
        """
        Get historical revenue trend for a stock.

        Parameters
        ----------
        ticker : str
            Stock ticker symbol

        Returns
        -------
        Optional[Dict[str, float]]
            Dictionary mapping year to revenue, or None if not found
        """
        return self.get_fundamental_history(ticker, 'Total Revenue')

    def get_cashflow_trend(self, ticker: str) -> Optional[Dict[str, float]]:
        """
        Get historical free cash flow trend for a stock.

        Parameters
        ----------
        ticker : str
            Stock ticker symbol

        Returns
        -------
        Optional[Dict[str, float]]
            Dictionary mapping year to free cash flow, or None if not found
        """
        return self.get_fundamental_history(ticker, 'Free Cash Flow')

    def get_recent_price_closes(self, ticker: str, limit: int = 600) -> Dict[str, Any]:
        """
        Get most recent close prices for a ticker.

        Parameters
        ----------
        ticker : str
            Stock ticker symbol.
        limit : int
            Maximum number of rows to load.

        Returns
        -------
        Dict[str, Any]
            Price payload with `closes`, `dates`, `last_date`, and `price_points`.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT date, close
            FROM price_history
            WHERE ticker = ? AND close IS NOT NULL
            ORDER BY date DESC
            LIMIT ?
            ''',
            (ticker, limit),
        )
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return {'closes': [], 'dates': [], 'last_date': None, 'price_points': 0}

        # Reverse to ascending date order for return calculations.
        rows = list(reversed(rows))
        closes = [float(row['close']) for row in rows if row['close'] is not None]
        dates = [row['date'] for row in rows if row['close'] is not None]
        last_date = dates[-1] if dates else None

        return {
            'closes': closes,
            'dates': dates,
            'last_date': last_date,
            'price_points': len(closes),
        }

    def get_latest_macro_rate(self, rate_name: str = 'risk_free_rate') -> Optional[Dict[str, Any]]:
        """
        Get the most recent macro rate from `macro_rates`.

        Parameters
        ----------
        rate_name : str
            Name of rate series.

        Returns
        -------
        Optional[Dict[str, Any]]
            Latest rate payload or None when unavailable.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        table_exists = cursor.execute(
            '''
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table' AND name = 'macro_rates'
            '''
        ).fetchone()
        if not table_exists:
            conn.close()
            return None

        row = cursor.execute(
            '''
            SELECT rate_name, date, value, source, fetched_at
            FROM macro_rates
            WHERE rate_name = ?
            ORDER BY date DESC
            LIMIT 1
            ''',
            (rate_name,),
        ).fetchone()
        conn.close()

        if not row:
            return None

        return {
            'rate_name': row['rate_name'],
            'date': row['date'],
            'value': float(row['value']) if row['value'] is not None else None,
            'source': row['source'],
            'fetched_at': row['fetched_at'],
        }

    def get_market_inputs(
        self,
        ticker: str,
        min_price_points: int = 252,
        max_price_age_days: int = 30,
        max_rate_age_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get robust market inputs for structural valuation models.

        Parameters
        ----------
        ticker : str
            Stock ticker symbol.
        min_price_points : int
            Minimum close prices required by model.
        max_price_age_days : int
            Freshness threshold for close-price series.
        max_rate_age_days : int
            Freshness threshold for macro rate.

        Returns
        -------
        Dict[str, Any]
            Combined market inputs and quality metadata.
        """
        prices = self.get_recent_price_closes(ticker, limit=max(min_price_points + 50, 600))
        closes = prices.get('closes', [])
        last_price_date = prices.get('last_date')
        price_age_days = None
        price_is_fresh = False

        if last_price_date:
            try:
                last_dt = datetime.strptime(last_price_date, '%Y-%m-%d')
                price_age_days = (datetime.now() - last_dt).days
                price_is_fresh = price_age_days <= max_price_age_days
            except ValueError:
                price_age_days = None
                price_is_fresh = False

        macro = self.get_latest_macro_rate('risk_free_rate')
        risk_free_rate = None
        rate_source = 'default_config'
        rate_date = None
        rate_age_days = None
        rate_is_fresh = False

        if macro and isinstance(macro.get('value'), float):
            risk_free_rate = float(macro['value'])
            rate_source = str(macro.get('source') or 'macro_rates')
            rate_date = macro.get('date')

            if rate_date:
                try:
                    rate_dt = datetime.strptime(rate_date, '%Y-%m-%d')
                    rate_age_days = (datetime.now() - rate_dt).days
                    rate_is_fresh = rate_age_days <= max_rate_age_days
                except ValueError:
                    rate_age_days = None
                    rate_is_fresh = False

        return {
            'closes': closes,
            'price_points': len(closes),
            'price_last_date': last_price_date,
            'price_age_days': price_age_days,
            'price_is_fresh': price_is_fresh,
            'min_price_points': min_price_points,
            'risk_free_rate': risk_free_rate,
            'rate_source': rate_source,
            'rate_date': rate_date,
            'rate_age_days': rate_age_days,
            'rate_is_fresh': rate_is_fresh,
        }

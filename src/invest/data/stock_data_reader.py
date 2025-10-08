"""
SQLite Stock Data Reader

Provides unified interface to read stock data from SQLite database.
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any


class StockDataReader:
    """Read stock data from SQLite database."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize reader with database path."""
        if db_path is None:
            # Default to project database
            project_root = Path(__file__).parent.parent.parent.parent
            db_path = project_root / 'neural_network' / 'training' / 'stock_data.db'
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
                'totalCash': row['total_cash'],
                'totalDebt': row['total_debt'],
                'trailingEps': row['trailing_eps'],
                'bookValue': row['book_value'],
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

#!/usr/bin/env python3
"""
Create the current_stock_data table in the database.

This table stores the latest fetched data for each stock, replacing the JSON cache.
"""

import sqlite3
from pathlib import Path

# Get project root
project_root = Path(__file__).parent.parent
db_path = project_root / 'neural_network' / 'training' / 'stock_data.db'


def create_current_stock_data_table():
    """Create the current_stock_data table."""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS current_stock_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL UNIQUE,

            -- Basic info
            current_price REAL,
            market_cap REAL,
            sector TEXT,
            industry TEXT,
            long_name TEXT,
            short_name TEXT,
            currency TEXT,
            exchange TEXT,
            country TEXT,

            -- Financial metrics
            trailing_pe REAL,
            forward_pe REAL,
            price_to_book REAL,
            return_on_equity REAL,
            debt_to_equity REAL,
            current_ratio REAL,
            revenue_growth REAL,
            earnings_growth REAL,
            operating_margins REAL,
            profit_margins REAL,
            total_revenue REAL,
            total_cash REAL,
            total_debt REAL,
            shares_outstanding REAL,
            trailing_eps REAL,
            book_value REAL,
            revenue_per_share REAL,
            price_to_sales_ttm REAL,

            -- Price data
            price_52w_high REAL,
            price_52w_low REAL,
            avg_volume INTEGER,
            price_trend_30d REAL,

            -- Raw JSON storage for complex data
            cashflow_json TEXT,
            balance_sheet_json TEXT,
            income_json TEXT,

            -- Metadata
            fetch_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(ticker)
        )
    ''')

    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_current_ticker ON current_stock_data(ticker)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_current_updated ON current_stock_data(last_updated)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_current_sector ON current_stock_data(sector)')

    conn.commit()
    conn.close()

    print(f'✅ Created current_stock_data table in {db_path}')


if __name__ == '__main__':
    create_current_stock_data_table()

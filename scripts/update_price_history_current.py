#!/usr/bin/env python3
"""
Refresh `price_history` for tickers in `current_stock_data`.

Usage
-----
uv run python scripts/update_price_history_current.py
uv run python scripts/update_price_history_current.py --limit 50
"""

import argparse
import sqlite3
import time
from datetime import datetime
from pathlib import Path

import yfinance as yf


def load_tickers(conn: sqlite3.Connection, limit: int | None = None) -> list[str]:
    """Load tickers from current_stock_data."""
    query = 'SELECT ticker FROM current_stock_data WHERE current_price IS NOT NULL ORDER BY ticker'
    if limit is not None and limit > 0:
        query += f' LIMIT {int(limit)}'
    return [row[0] for row in conn.execute(query).fetchall()]


def upsert_price_history(conn: sqlite3.Connection, ticker: str, period: str) -> int:
    """
    Fetch and save historical prices for one ticker.

    Parameters
    ----------
    conn : sqlite3.Connection
        DB connection.
    ticker : str
        Stock ticker.
    period : str
        yfinance period string.

    Returns
    -------
    int
        Number of rows inserted/replaced.
    """
    history = yf.Ticker(ticker).history(period=period, auto_adjust=False)
    if history.empty:
        return 0

    rows = []
    for date, row in history.iterrows():
        rows.append(
            (
                ticker,
                date.strftime('%Y-%m-%d'),
                float(row['Open']) if row.get('Open') is not None else None,
                float(row['High']) if row.get('High') is not None else None,
                float(row['Low']) if row.get('Low') is not None else None,
                float(row['Close']) if row.get('Close') is not None else None,
                float(row['Volume']) if row.get('Volume') is not None else None,
                float(row['Dividends']) if row.get('Dividends') is not None else None,
                float(row['Stock Splits']) if row.get('Stock Splits') is not None else None,
                datetime.now().isoformat(),
            )
        )

    conn.executemany(
        '''
        INSERT OR REPLACE INTO price_history (
            ticker, date, open, high, low, close, volume, dividends, stock_splits, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        rows,
    )
    conn.commit()
    return len(rows)


def main() -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(description='Refresh price_history from yfinance')
    parser.add_argument('--db-path', default='data/stock_data.db', help='Path to SQLite database')
    parser.add_argument('--period', default='5y', help='yfinance period, e.g. 2y, 5y, 10y')
    parser.add_argument('--limit', type=int, default=None, help='Max tickers to refresh')
    parser.add_argument('--sleep', type=float, default=0.1, help='Delay between ticker requests')
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    db_path = (project_root / args.db_path).resolve()
    conn = sqlite3.connect(db_path)

    tickers = load_tickers(conn, limit=args.limit)
    print(f'Refreshing price history for {len(tickers)} tickers (period={args.period})')

    total_rows = 0
    success = 0
    failed = 0
    for i, ticker in enumerate(tickers, start=1):
        try:
            inserted = upsert_price_history(conn, ticker, period=args.period)
            total_rows += inserted
            success += 1
            if i % 25 == 0:
                print(f'  [{i}/{len(tickers)}] {ticker} rows={inserted}')
        except Exception as exc:
            failed += 1
            print(f'  [{i}/{len(tickers)}] {ticker} failed: {exc}')
        time.sleep(max(args.sleep, 0.0))

    conn.close()
    print(f'Completed. Success={success}, Failed={failed}, Rows saved={total_rows}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
"""
Migrate price_history table from snapshot_id-based to ticker-based design.

Old schema: price_history(snapshot_id, date, OHLCV)
New schema: price_history(ticker, date, OHLCV)

This simplifies the design following KISS principle - each table makes sense independently.
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'data/stock_data.db'


def main():
    """Execute the migration."""
    print(f'Starting migration of {DB_PATH}')

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Step 1: Rename old table
    print('\n1. Renaming old price_history to price_history_old...')
    cursor.execute('ALTER TABLE price_history RENAME TO price_history_old')
    conn.commit()
    print('   ✓ Renamed')

    # Step 2: Create new simple schema
    print('\n2. Creating new price_history table (ticker, date, OHLCV)...')
    cursor.execute('''
        CREATE TABLE price_history (
            ticker TEXT NOT NULL,
            date DATE NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            dividends REAL,
            stock_splits REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            PRIMARY KEY (ticker, date)
        )
    ''')
    conn.commit()
    print('   ✓ Created new table')

    # Step 3: Migrate data with deduplication
    print('\n3. Migrating data from old table...')
    print('   This will take several minutes for 38M rows...')

    # Insert with deduplication - if multiple snapshots have same ticker+date, take the most recent snapshot
    cursor.execute('''
        INSERT INTO price_history (ticker, date, open, high, low, close, volume, dividends, stock_splits, created_at)
        SELECT
            a.symbol as ticker,
            ph.date,
            ph.open,
            ph.high,
            ph.low,
            ph.close,
            ph.volume,
            ph.dividends,
            ph.stock_splits,
            ph.created_at
        FROM price_history_old ph
        JOIN fundamental_history s ON ph.snapshot_id = s.id
        JOIN assets a ON s.asset_id = a.id
        WHERE ph.date IS NOT NULL
        GROUP BY a.symbol, ph.date
        HAVING ph.snapshot_id = MAX(ph.snapshot_id)  -- Take most recent snapshot for duplicates
    ''')

    migrated = cursor.rowcount
    conn.commit()
    print(f'   ✓ Migrated {migrated:,} rows')

    # Step 4: Create index for performance
    print('\n4. Creating index on (ticker, date)...')
    cursor.execute('CREATE INDEX idx_price_ticker_date ON price_history(ticker, date)')
    conn.commit()
    print('   ✓ Index created')

    # Step 5: Verify migration
    print('\n5. Verifying migration...')

    cursor.execute('SELECT COUNT(*) FROM price_history_old')
    old_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM price_history')
    new_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(DISTINCT ticker) FROM price_history')
    ticker_count = cursor.fetchone()[0]

    cursor.execute('SELECT MIN(date), MAX(date) FROM price_history')
    min_date, max_date = cursor.fetchone()

    print(f'   Old table: {old_count:,} rows')
    print(f'   New table: {new_count:,} rows')
    print(f'   Unique tickers: {ticker_count}')
    print(f'   Date range: {min_date} to {max_date}')

    if new_count == 0:
        print('\n❌ ERROR: Migration failed - no rows migrated!')
        conn.close()
        sys.exit(1)

    # Check a sample
    print('\n6. Sample verification...')
    cursor.execute('''
        SELECT ticker, date, close
        FROM price_history
        ORDER BY date DESC
        LIMIT 5
    ''')

    print('   Latest 5 price records:')
    for ticker, date, close in cursor.fetchall():
        print(f'     {ticker} on {date}: ${close:.2f}')

    # Step 6: Drop old table
    print('\n7. Drop old table? (y/n): ', end='')
    response = input().strip().lower()

    if response == 'y':
        cursor.execute('DROP TABLE price_history_old')
        conn.commit()
        print('   ✓ Dropped price_history_old')
    else:
        print('   ⏭ Skipped - price_history_old retained for safety')

    conn.close()

    print('\n✅ Migration complete!')
    print('\nNew schema: price_history(ticker, date, OHLCV)')
    print('Query example: SELECT close FROM price_history WHERE ticker=\'AAPL\' AND date=\'2025-10-15\'')


if __name__ == '__main__':
    main()

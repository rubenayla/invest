#!/usr/bin/env python3
"""
Populate the NN training cache (stock_data.db) from the main database.

Uses fundamental_history for features and price_history for forward returns.
This avoids yfinance rate limits and uses point-in-time data.
"""

import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MAIN_DB = Path(__file__).parent.parent.parent / 'data' / 'stock_data.db'
TRAIN_DB = Path(__file__).parent / 'stock_data.db'

# Forward return horizons in trading days
HORIZONS = {'1m': 21, '3m': 63, '6m': 126, '1y': 252, '2y': 504}


def build_cache():
    logger.info(f'Main DB: {MAIN_DB}')
    logger.info(f'Training DB: {TRAIN_DB}')

    main = sqlite3.connect(str(MAIN_DB))
    main.row_factory = sqlite3.Row

    # --- 1. Create training DB schema ---
    from create_stock_database import create_database
    create_database(str(TRAIN_DB))
    train = sqlite3.connect(str(TRAIN_DB))
    train.execute('PRAGMA foreign_keys = ON')

    # --- 2. Copy assets ---
    assets = main.execute('SELECT id, symbol, sector, industry FROM assets').fetchall()
    asset_map = {}  # main_id -> train_id
    for a in assets:
        train.execute(
            'INSERT OR IGNORE INTO assets (symbol, asset_type, name, sector, industry) VALUES (?, ?, ?, ?, ?)',
            (a['symbol'], 'stock', None, a['sector'], a['industry'])
        )
        row = train.execute('SELECT id FROM assets WHERE symbol = ?', (a['symbol'],)).fetchone()
        asset_map[a['id']] = row[0]
    train.commit()
    logger.info(f'Copied {len(asset_map)} assets')

    # --- 3. Build per-ticker price index for fast forward-return lookups ---
    logger.info('Loading price history index...')
    # Load all prices grouped by ticker, sorted by date
    price_rows = main.execute(
        'SELECT ticker, date, close FROM price_history ORDER BY ticker, date'
    ).fetchall()

    from collections import defaultdict
    price_dates = defaultdict(list)   # ticker -> [date_str, ...]
    price_closes = defaultdict(list)  # ticker -> [close, ...]
    for r in price_rows:
        price_dates[r['ticker']].append(r['date'])
        price_closes[r['ticker']].append(r['close'])

    logger.info(f'Loaded prices for {len(price_dates)} tickers')

    # --- 4. Process fundamental_history snapshots ---
    snapshots = main.execute('''
        SELECT fh.*, a.symbol
        FROM fundamental_history fh
        JOIN assets a ON fh.asset_id = a.id
        ORDER BY fh.snapshot_date, a.symbol
    ''').fetchall()
    logger.info(f'Processing {len(snapshots)} fundamental snapshots...')

    cols = [desc[0] for desc in main.execute('SELECT * FROM fundamental_history LIMIT 1').description]

    inserted = 0
    skipped_no_price = 0
    skipped_no_forward = 0

    for i, snap in enumerate(snapshots):
        if i % 2000 == 0 and i > 0:
            logger.info(f'  {i}/{len(snapshots)} processed, {inserted} inserted')
            train.commit()

        ticker = snap['symbol']
        snap_date = snap['snapshot_date']
        main_asset_id = snap['asset_id']
        train_asset_id = asset_map.get(main_asset_id)
        if train_asset_id is None:
            continue

        # Find snapshot date in price history
        dates = price_dates.get(ticker, [])
        closes = price_closes.get(ticker, [])
        if not dates:
            skipped_no_price += 1
            continue

        # Binary search for the snapshot date
        import bisect
        idx = bisect.bisect_left(dates, snap_date)
        # Find closest date on or before snapshot_date
        if idx >= len(dates):
            idx = len(dates) - 1
        if dates[idx] > snap_date and idx > 0:
            idx -= 1

        current_price = closes[idx]
        if current_price is None or current_price <= 0:
            skipped_no_price += 1
            continue

        # Compute forward returns
        forward_returns = {}
        has_all = True
        for horizon_name, days_ahead in HORIZONS.items():
            future_idx = idx + days_ahead
            if future_idx >= len(dates):
                has_all = False
                break
            future_price = closes[future_idx]
            if future_price is None or future_price <= 0:
                has_all = False
                break
            forward_returns[horizon_name] = (future_price - current_price) / current_price

        if not has_all:
            skipped_no_forward += 1
            continue

        # Insert snapshot
        train.execute('''
            INSERT OR IGNORE INTO snapshots (
                asset_id, snapshot_date, current_price, volume, market_cap, shares_outstanding,
                pe_ratio, pb_ratio, ps_ratio, peg_ratio, price_to_book, price_to_sales,
                enterprise_to_revenue, enterprise_to_ebitda,
                profit_margins, operating_margins, gross_margins, ebitda_margins,
                return_on_assets, return_on_equity,
                revenue_growth, earnings_growth, earnings_quarterly_growth, revenue_per_share,
                total_cash, total_debt, debt_to_equity, current_ratio, quick_ratio,
                operating_cashflow, free_cashflow,
                trailing_eps, forward_eps, book_value,
                dividend_rate, dividend_yield, payout_ratio,
                price_change_pct, volatility, beta,
                fifty_day_average, two_hundred_day_average, fifty_two_week_high, fifty_two_week_low,
                vix, treasury_10y, dollar_index, oil_price, gold_price
            ) VALUES (
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?,
                ?, ?, ?, ?,
                ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?, ?
            )
        ''', (
            train_asset_id, snap_date, current_price,
            snap['volume'], snap['market_cap'], snap['shares_outstanding'],
            snap['pe_ratio'], snap['pb_ratio'], snap['ps_ratio'], snap['peg_ratio'],
            snap['price_to_book'], snap['price_to_sales'],
            snap['enterprise_to_revenue'], snap['enterprise_to_ebitda'],
            snap['profit_margins'], snap['operating_margins'], snap['gross_margins'], snap['ebitda_margins'],
            snap['return_on_assets'], snap['return_on_equity'],
            snap['revenue_growth'], snap['earnings_growth'], snap['earnings_quarterly_growth'], snap['revenue_per_share'],
            snap['total_cash'], snap['total_debt'], snap['debt_to_equity'], snap['current_ratio'], snap['quick_ratio'],
            snap['operating_cashflow'], snap['free_cashflow'],
            snap['trailing_eps'], snap['forward_eps'], snap['book_value'],
            snap['dividend_rate'], snap['dividend_yield'], snap['payout_ratio'],
            snap['price_change_pct'], snap['volatility'], snap['beta'],
            snap['fifty_day_average'], snap['two_hundred_day_average'],
            snap['fifty_two_week_high'], snap['fifty_two_week_low'],
            snap['vix'], snap['treasury_10y'], snap['dollar_index'], snap['oil_price'], snap['gold_price'],
        ))

        snapshot_id = train.execute(
            'SELECT id FROM snapshots WHERE asset_id = ? AND snapshot_date = ?',
            (train_asset_id, snap_date)
        ).fetchone()[0]

        # Insert forward returns
        for horizon_name, ret in forward_returns.items():
            train.execute(
                'INSERT OR IGNORE INTO forward_returns (snapshot_id, horizon, return_pct) VALUES (?, ?, ?)',
                (snapshot_id, horizon_name, ret)
            )

        inserted += 1

    train.commit()
    main.close()

    # Summary
    total_snapshots = train.execute('SELECT COUNT(*) FROM snapshots').fetchone()[0]
    total_returns = train.execute('SELECT COUNT(*) FROM forward_returns').fetchone()[0]
    date_range = train.execute('SELECT MIN(snapshot_date), MAX(snapshot_date) FROM snapshots').fetchone()

    train.close()

    logger.info(f'\nDone!')
    logger.info(f'  Snapshots inserted: {total_snapshots}')
    logger.info(f'  Forward returns: {total_returns}')
    logger.info(f'  Date range: {date_range[0]} to {date_range[1]}')
    logger.info(f'  Skipped (no price data): {skipped_no_price}')
    logger.info(f'  Skipped (insufficient forward data): {skipped_no_forward}')


if __name__ == '__main__':
    build_cache()

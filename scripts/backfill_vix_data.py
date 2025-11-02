#!/usr/bin/env python3
"""
Backfill VIX data for existing snapshots.

This one-time script fetches historical VIX data and updates all snapshots
that have NULL or missing VIX values. Should dramatically increase the number
of stocks the GBM model can analyze.
"""

import logging
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

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


def fetch_vix_history():
    """Fetch complete VIX history from Yahoo Finance."""
    logger.info('Fetching VIX historical data from Yahoo Finance...')

    try:
        vix = yf.Ticker('^VIX')

        # Fetch from 2000 to today
        hist = vix.history(start='2000-01-01', end=datetime.now().strftime('%Y-%m-%d'))

        if hist.empty:
            logger.error('No VIX data retrieved!')
            return {}

        # Create date -> VIX mapping
        vix_cache = {}
        for date, row in hist.iterrows():
            date_str = date.strftime('%Y-%m-%d')
            vix_cache[date_str] = float(row['Close'])

        logger.info(f'Successfully fetched VIX data for {len(vix_cache)} trading days')
        return vix_cache

    except Exception as e:
        logger.error(f'Error fetching VIX history: {e}')
        return {}


def get_vix_for_date(vix_cache: dict, date_str: str) -> float:
    """
    Get VIX value for a specific date.

    If exact date not available, looks back up to 7 days for closest trading day.
    Falls back to 20.0 (historical median) if no data found.
    """
    # Direct match
    if date_str in vix_cache:
        return vix_cache[date_str]

    # Try to find closest previous trading day (within 7 days)
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d')
        for days_back in range(1, 8):
            check_date = (target_date - timedelta(days=days_back)).strftime('%Y-%m-%d')
            if check_date in vix_cache:
                return vix_cache[check_date]
    except:
        pass

    # Default fallback
    return 20.0


def backfill_vix(db_path: str):
    """Backfill VIX data for all snapshots missing it."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all snapshots missing VIX
    cursor.execute('''
        SELECT id, snapshot_date
        FROM fundamental_history
        WHERE vix IS NULL
        ORDER BY snapshot_date
    ''')

    snapshots_to_update = cursor.fetchall()
    total_snapshots = len(snapshots_to_update)

    if total_snapshots == 0:
        logger.info('All snapshots already have VIX data!')
        conn.close()
        return

    logger.info(f'Found {total_snapshots} snapshots without VIX data')

    # Fetch VIX history
    vix_cache = fetch_vix_history()

    if not vix_cache:
        logger.error('Could not fetch VIX data. Aborting.')
        conn.close()
        return

    # Update snapshots
    logger.info('Updating snapshots with VIX data...')
    updated_count = 0

    for snapshot_id, snapshot_date in snapshots_to_update:
        vix_value = get_vix_for_date(vix_cache, snapshot_date)

        cursor.execute('''
            UPDATE fundamental_history
            SET vix = ?
            WHERE id = ?
        ''', (vix_value, snapshot_id))

        updated_count += 1

        # Progress updates
        if updated_count % 100 == 0:
            logger.info(f'Progress: {updated_count}/{total_snapshots} snapshots updated')
            conn.commit()

    # Final commit
    conn.commit()
    conn.close()

    logger.info(f'Successfully updated {updated_count} snapshots with VIX data!')


def verify_results(db_path: str):
    """Verify the backfill worked correctly."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check stats
    cursor.execute('''
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN vix IS NOT NULL THEN 1 END) as with_vix,
            COUNT(CASE WHEN vix IS NULL THEN 1 END) as without_vix
        FROM fundamental_history
    ''')

    total, with_vix, without_vix = cursor.fetchone()

    logger.info('\n' + '=' * 60)
    logger.info('VERIFICATION RESULTS')
    logger.info('=' * 60)
    logger.info(f'Total snapshots: {total}')
    logger.info(f'With VIX: {with_vix} ({with_vix/total*100:.1f}%)')
    logger.info(f'Without VIX: {without_vix} ({without_vix/total*100:.1f}%)')
    logger.info('=' * 60)

    # Check how many stocks now qualify for GBM
    cursor.execute('''
        SELECT COUNT(DISTINCT a.symbol)
        FROM assets a
        JOIN fundamental_history s ON a.id = s.asset_id
        WHERE s.vix IS NOT NULL
        AND s.snapshot_date >= date('now', '-3 years')
    ''')

    gbm_eligible_stocks = cursor.fetchone()[0]
    logger.info(f'\nStocks eligible for GBM analysis: {gbm_eligible_stocks}')
    logger.info('=' * 60 + '\n')

    conn.close()


def main():
    """Main execution function."""
    logger.info('=' * 60)
    logger.info('VIX Data Backfill Script')
    logger.info('=' * 60)

    db_path = project_root / 'data/stock_data.db'

    if not db_path.exists():
        logger.error(f'Database not found: {db_path}')
        return 1

    # Run backfill
    backfill_vix(str(db_path))

    # Verify results
    verify_results(str(db_path))

    logger.info('VIX backfill complete!')
    logger.info('\nNext steps:')
    logger.info('  1. Run GBM predictions: uv run python scripts/run_gbm_1y_predictions.py')
    logger.info('  2. Regenerate dashboard: uv run python scripts/dashboard.py')

    return 0


if __name__ == '__main__':
    sys.exit(main())

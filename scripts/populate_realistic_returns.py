#!/usr/bin/env python3
"""
Populate realistic exit returns for opportunistic GBM model.

This script calculates returns based on a realistic profit-taking strategy:
- 25% of position exits at +20% gain
- 50% of position exits at +50% gain
- 25% rides to the peak within 1-2 year window

These returns better reflect actual trading behavior compared to fixed-horizon returns.
"""

import logging
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def calculate_realistic_exit_return(
    snapshot_date: pd.Timestamp,
    price_data: pd.DataFrame,
    horizon_days: int = 730  # 2 years max
) -> tuple[float, dict]:
    """
    Calculate realistic exit return for a single snapshot.

    Simulates a trader who:
    1. Exits 25% at +20% gain
    2. Exits 50% at +50% gain
    3. Rides 25% to the peak in the 1-2 year window

    Parameters
    ----------
    snapshot_date : pd.Timestamp
        The date of the snapshot
    price_data : pd.DataFrame
        DataFrame with columns ['date', 'close'] sorted by date
    horizon_days : int
        Maximum holding period in days (default 730 = 2 years)

    Returns
    -------
    tuple[float, dict]
        (weighted_return, details) where details contains strategy breakdown
    """
    # Filter to window: 1 year to 2 years from snapshot
    window_start = snapshot_date + timedelta(days=365)  # 1 year later
    window_end = snapshot_date + timedelta(days=horizon_days)  # 2 years later

    # Get prices in the window
    window_data = price_data[
        (price_data['date'] > window_start) &
        (price_data['date'] <= window_end)
    ].copy()

    if len(window_data) == 0:
        return np.nan, {'error': 'No price data in 1-2 year window'}

    # Get baseline price (price at snapshot date)
    baseline_data = price_data[price_data['date'] <= snapshot_date]
    if len(baseline_data) == 0:
        return np.nan, {'error': 'No baseline price at snapshot date'}

    baseline_price = baseline_data.iloc[-1]['close']

    # Calculate returns for each day in window
    window_data['return'] = (window_data['close'] / baseline_price - 1)

    # Find exit points
    # 1. First time hitting +20%
    hit_20_mask = window_data['return'] >= 0.20
    if hit_20_mask.any():
        first_20_idx = hit_20_mask.idxmax()
        exit_20_price = window_data.loc[first_20_idx, 'close']
        exit_20_return = 0.20  # Exactly 20% gain
        exit_20_date = window_data.loc[first_20_idx, 'date']
    else:
        # If never hits 20%, use final price for this portion
        exit_20_price = window_data.iloc[-1]['close']
        exit_20_return = window_data.iloc[-1]['return']
        exit_20_date = window_data.iloc[-1]['date']

    # 2. First time hitting +50%
    hit_50_mask = window_data['return'] >= 0.50
    if hit_50_mask.any():
        first_50_idx = hit_50_mask.idxmax()
        exit_50_price = window_data.loc[first_50_idx, 'close']
        exit_50_return = 0.50  # Exactly 50% gain
        exit_50_date = window_data.loc[first_50_idx, 'date']
    else:
        # If never hits 50%, use final price for this portion
        exit_50_price = window_data.iloc[-1]['close']
        exit_50_return = window_data.iloc[-1]['return']
        exit_50_date = window_data.iloc[-1]['date']

    # 3. Peak price in window
    peak_idx = window_data['close'].idxmax()
    peak_price = window_data.loc[peak_idx, 'close']
    peak_return = window_data.loc[peak_idx, 'return']
    peak_date = window_data.loc[peak_idx, 'date']

    # Calculate weighted return
    # 25% at +20%, 50% at +50%, 25% at peak
    weighted_return = (
        0.25 * exit_20_return +
        0.50 * exit_50_return +
        0.25 * peak_return
    )

    details = {
        'baseline_price': float(baseline_price),
        'exit_20_return': float(exit_20_return),
        'exit_20_date': exit_20_date.strftime('%Y-%m-%d'),
        'exit_50_return': float(exit_50_return),
        'exit_50_date': exit_50_date.strftime('%Y-%m-%d'),
        'peak_return': float(peak_return),
        'peak_date': peak_date.strftime('%Y-%m-%d'),
        'weighted_return': float(weighted_return),
        'window_start': window_start.strftime('%Y-%m-%d'),
        'window_end': window_end.strftime('%Y-%m-%d'),
        'days_in_window': len(window_data)
    }

    return weighted_return, details


def main():
    """Calculate and populate realistic exit returns for all snapshots."""

    # Database path
    db_path = Path(__file__).parent.parent / 'data' / 'stock_data.db'

    if not db_path.exists():
        logger.error(f'Database not found at {db_path}')
        return 1

    conn = sqlite3.connect(db_path)

    try:
        # First, add the new columns if they don't exist
        cursor = conn.cursor()

        # Check if columns exist
        cursor.execute("PRAGMA table_info(fundamental_history)")
        existing_columns = [col[1] for col in cursor.fetchall()]

        if 'realistic_return_1y' not in existing_columns:
            logger.info('Adding realistic_return_1y column to fundamental_history table...')
            cursor.execute('ALTER TABLE fundamental_history ADD COLUMN realistic_return_1y REAL')
            conn.commit()

        if 'realistic_return_3y' not in existing_columns:
            logger.info('Adding realistic_return_3y column to fundamental_history table...')
            cursor.execute('ALTER TABLE fundamental_history ADD COLUMN realistic_return_3y REAL')
            conn.commit()

        # Get all snapshots that need realistic returns calculated
        query = """
            SELECT
                s.id as snapshot_id,
                s.snapshot_date,
                a.symbol as ticker
            FROM fundamental_history s
            JOIN assets a ON s.asset_id = a.id
            WHERE s.realistic_return_1y IS NULL
            ORDER BY s.snapshot_date, a.symbol
        """

        snapshots_df = pd.read_sql(query, conn)
        snapshots_df['snapshot_date'] = pd.to_datetime(snapshots_df['snapshot_date'])

        total_snapshots = len(snapshots_df)
        logger.info(f'Found {total_snapshots} snapshots needing realistic returns')

        if total_snapshots == 0:
            logger.info('All snapshots already have realistic returns calculated!')
            return 0

        # Load all price history (more efficient than per-snapshot queries)
        logger.info('Loading price history...')
        price_query = """
            SELECT
                snapshot_id,
                date,
                close
            FROM price_history
            ORDER BY snapshot_id, date
        """

        price_df = pd.read_sql(price_query, conn)
        price_df['date'] = pd.to_datetime(price_df['date'])

        logger.info(f'Loaded {len(price_df):,} price records')

        # Group price data by snapshot_id for efficient lookup
        price_groups = price_df.groupby('snapshot_id')

        # Calculate realistic returns for each snapshot
        updates_1y = []
        updates_3y = []
        errors = 0

        for idx, row in snapshots_df.iterrows():
            if idx % 100 == 0:
                logger.info(f'Processing snapshot {idx+1}/{total_snapshots} '
                          f'({100*(idx+1)/total_snapshots:.1f}%)')

            snapshot_id = row['snapshot_id']
            snapshot_date = row['snapshot_date']
            ticker = row['ticker']

            # Get price data for this snapshot
            if snapshot_id not in price_groups.groups:
                logger.warning(f'{ticker}: No price data for snapshot {snapshot_id}')
                errors += 1
                continue

            snapshot_prices = price_groups.get_group(snapshot_id)

            # Calculate 1-year realistic return (1y to 2y window)
            return_1y, details_1y = calculate_realistic_exit_return(
                snapshot_date,
                snapshot_prices,
                horizon_days=730  # 2 years max
            )

            # Calculate 3-year realistic return (1y to 3y window)
            return_3y, details_3y = calculate_realistic_exit_return(
                snapshot_date,
                snapshot_prices,
                horizon_days=1460  # 4 years max (1y start + 3y horizon)
            )

            if not np.isnan(return_1y):
                updates_1y.append((float(return_1y), snapshot_id))

                # Log interesting cases
                if return_1y > 1.0:  # More than 100% return
                    logger.debug(f'{ticker} ({snapshot_date:%Y-%m-%d}): '
                               f'Exceptional 1y return {return_1y:.1%} '
                               f'(20%: {details_1y["exit_20_return"]:.1%}, '
                               f'50%: {details_1y["exit_50_return"]:.1%}, '
                               f'peak: {details_1y["peak_return"]:.1%})')

            if not np.isnan(return_3y):
                updates_3y.append((float(return_3y), snapshot_id))

        # Batch update the database
        if updates_1y:
            logger.info(f'Updating {len(updates_1y)} snapshots with 1y realistic returns...')
            cursor.executemany(
                'UPDATE fundamental_history SET realistic_return_1y = ? WHERE id = ?',
                updates_1y
            )

        if updates_3y:
            logger.info(f'Updating {len(updates_3y)} snapshots with 3y realistic returns...')
            cursor.executemany(
                'UPDATE fundamental_history SET realistic_return_3y = ? WHERE id = ?',
                updates_3y
            )

        conn.commit()

        # Summary statistics
        if updates_1y:
            returns_1y = [r[0] for r in updates_1y]
            logger.info('\n1-Year Realistic Returns Summary:')
            logger.info(f'  Count: {len(returns_1y)}')
            logger.info(f'  Mean: {np.mean(returns_1y):.2%}')
            logger.info(f'  Median: {np.median(returns_1y):.2%}')
            logger.info(f'  Std: {np.std(returns_1y):.2%}')
            logger.info(f'  Min: {np.min(returns_1y):.2%}')
            logger.info(f'  Max: {np.max(returns_1y):.2%}')
            logger.info(f'  >50% returns: {sum(r > 0.5 for r in returns_1y)} '
                      f'({100*sum(r > 0.5 for r in returns_1y)/len(returns_1y):.1f}%)')
            logger.info(f'  >100% returns: {sum(r > 1.0 for r in returns_1y)} '
                      f'({100*sum(r > 1.0 for r in returns_1y)/len(returns_1y):.1f}%)')

        if updates_3y:
            returns_3y = [r[0] for r in updates_3y]
            logger.info('\n3-Year Realistic Returns Summary:')
            logger.info(f'  Count: {len(returns_3y)}')
            logger.info(f'  Mean: {np.mean(returns_3y):.2%}')
            logger.info(f'  Median: {np.median(returns_3y):.2%}')
            logger.info(f'  Std: {np.std(returns_3y):.2%}')
            logger.info(f'  Min: {np.min(returns_3y):.2%}')
            logger.info(f'  Max: {np.max(returns_3y):.2%}')
            logger.info(f'  >100% returns: {sum(r > 1.0 for r in returns_3y)} '
                      f'({100*sum(r > 1.0 for r in returns_3y)/len(returns_3y):.1f}%)')
            logger.info(f'  >200% returns: {sum(r > 2.0 for r in returns_3y)} '
                      f'({100*sum(r > 2.0 for r in returns_3y)/len(returns_3y):.1f}%)')

        logger.info(f'\n✅ Successfully populated realistic returns!')
        logger.info(f'  1y returns: {len(updates_1y)} snapshots')
        logger.info(f'  3y returns: {len(updates_3y)} snapshots')
        logger.info(f'  Errors: {errors} snapshots')

        # Verify the update worked
        cursor.execute("""
            SELECT COUNT(*) FROM fundamental_history
            WHERE realistic_return_1y IS NOT NULL
        """)
        count_1y = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM fundamental_history
            WHERE realistic_return_3y IS NOT NULL
        """)
        count_3y = cursor.fetchone()[0]

        logger.info(f'\nDatabase now contains:')
        logger.info(f'  {count_1y} snapshots with 1y realistic returns')
        logger.info(f'  {count_3y} snapshots with 3y realistic returns')

    except Exception as e:
        logger.error(f'Error: {e}')
        import traceback
        traceback.print_exc()
        return 1

    finally:
        conn.close()

    return 0


if __name__ == '__main__':
    sys.exit(main())
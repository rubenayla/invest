#!/usr/bin/env python3
"""
Populate snapshots table from SEC EDGAR data.

Simple approach:
1. Read ALL SEC quarterly filings for our stocks
2. For each filing: INSERT or UPDATE snapshot
3. Calculate fundamental ratios from raw SEC data
"""

import json
import logging
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DB_PATH = PROJECT_ROOT / 'data' / 'stock_data.db'
SEC_DATA_PATH = PROJECT_ROOT / 'data' / 'sec_edgar' / 'raw' / 'companyfacts'
TICKER_MAPPING_FILE = PROJECT_ROOT / 'data' / 'sec_edgar' / 'raw' / 'ticker_to_cik.json'


# XBRL tag mappings
XBRL_TAGS = {
    'revenue': ['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet'],
    'net_income': ['NetIncomeLoss', 'ProfitLoss'],
    'eps_basic': ['EarningsPerShareBasic'],
    'eps_diluted': ['EarningsPerShareDiluted'],
    'assets': ['Assets'],
    'assets_current': ['AssetsCurrent'],
    'liabilities': ['Liabilities'],
    'liabilities_current': ['LiabilitiesCurrent'],
    'equity': ['StockholdersEquity'],
    'shares_outstanding': ['CommonStockSharesOutstanding'],
    'cash': ['CashAndCashEquivalentsAtCarryingValue'],
    'long_term_debt': ['LongTermDebt'],
    'operating_income': ['OperatingIncomeLoss'],
    'operating_cash_flow': ['NetCashProvidedByUsedInOperatingActivities'],
    'investing_cash_flow': ['NetCashProvidedByUsedInInvestingActivities'],
}


def extract_metric(sec_data: Dict, tags: List[str], date: str) -> Optional[float]:
    """Extract metric value from SEC data for specific date."""
    if 'facts' not in sec_data or 'us-gaap' not in sec_data['facts']:
        return None

    us_gaap = sec_data['facts']['us-gaap']

    for tag in tags:
        if tag not in us_gaap or 'units' not in us_gaap[tag]:
            continue

        units = us_gaap[tag]['units']

        for unit_key in ['USD', 'shares', 'pure']:
            if unit_key not in units:
                continue

            # Find exact match or closest
            for dp in units[unit_key]:
                if dp.get('end') == date and 'val' in dp:
                    return float(dp['val'])

    return None


def get_asset_id(conn: sqlite3.Connection, ticker: str) -> Optional[int]:
    """Get or create asset_id for ticker."""
    cursor = conn.cursor()

    # Check if exists
    cursor.execute('SELECT id FROM assets WHERE symbol = ?', (ticker,))
    row = cursor.fetchone()

    if row:
        return row[0]

    # Create new asset
    cursor.execute(
        'INSERT INTO assets (symbol, sector) VALUES (?, ?)',
        (ticker, 'Unknown')
    )
    conn.commit()

    return cursor.lastrowid


def get_price_for_date(conn: sqlite3.Connection, ticker: str, date: str) -> Optional[float]:
    """Get stock price for date from price_history."""
    cursor = conn.cursor()

    # Try exact date first
    cursor.execute('''
        SELECT ph.close
        FROM price_history ph
        JOIN snapshots s ON ph.snapshot_id = s.id
        JOIN assets a ON s.asset_id = a.id
        WHERE a.symbol = ? AND ph.date = ?
        LIMIT 1
    ''', (ticker, date))

    row = cursor.fetchone()
    if row and row[0]:
        return float(row[0])

    # Try ±5 days
    date_obj = datetime.strptime(date, '%Y-%m-%d')
    for days_offset in range(-5, 6):
        check_date = (date_obj + timedelta(days=days_offset)).strftime('%Y-%m-%d')

        cursor.execute('''
            SELECT ph.close
            FROM price_history ph
            JOIN snapshots s ON ph.snapshot_id = s.id
            JOIN assets a ON s.asset_id = a.id
            WHERE a.symbol = ? AND ph.date = ?
            LIMIT 1
        ''', (ticker, check_date))

        row = cursor.fetchone()
        if row and row[0]:
            return float(row[0])

    return None


def calculate_ratios(sec_data: Dict, date: str, price: float) -> Dict:
    """Calculate fundamental ratios from raw SEC data."""
    # Extract raw metrics
    revenue = extract_metric(sec_data, XBRL_TAGS['revenue'], date)
    net_income = extract_metric(sec_data, XBRL_TAGS['net_income'], date)
    eps_basic = extract_metric(sec_data, XBRL_TAGS['eps_basic'], date)
    eps_diluted = extract_metric(sec_data, XBRL_TAGS['eps_diluted'], date)
    assets = extract_metric(sec_data, XBRL_TAGS['assets'], date)
    assets_current = extract_metric(sec_data, XBRL_TAGS['assets_current'], date)
    liabilities = extract_metric(sec_data, XBRL_TAGS['liabilities'], date)
    liabilities_current = extract_metric(sec_data, XBRL_TAGS['liabilities_current'], date)
    equity = extract_metric(sec_data, XBRL_TAGS['equity'], date)
    shares = extract_metric(sec_data, XBRL_TAGS['shares_outstanding'], date)
    cash = extract_metric(sec_data, XBRL_TAGS['cash'], date)
    debt = extract_metric(sec_data, XBRL_TAGS['long_term_debt'], date)
    op_income = extract_metric(sec_data, XBRL_TAGS['operating_income'], date)
    op_cf = extract_metric(sec_data, XBRL_TAGS['operating_cash_flow'], date)
    inv_cf = extract_metric(sec_data, XBRL_TAGS['investing_cash_flow'], date)

    ratios = {}

    # PE ratio
    eps = eps_diluted or eps_basic
    if eps and eps > 0:
        ratios['pe_ratio'] = min(max(price / eps, -50), 100)
        ratios['trailing_eps'] = eps

    # PB ratio
    if equity and shares and shares > 0:
        book_value = equity / shares
        if book_value > 0:
            ratios['pb_ratio'] = min(max(price / book_value, 0), 20)
            ratios['book_value'] = book_value

    # PS ratio
    if revenue and shares and shares > 0:
        revenue_per_share = revenue / shares
        if revenue_per_share > 0:
            ratios['ps_ratio'] = min(max(price / revenue_per_share, 0), 20)
            ratios['revenue_per_share'] = revenue_per_share

    # Margins
    if revenue and revenue > 0:
        if net_income:
            ratios['profit_margins'] = net_income / revenue
        if op_income:
            ratios['operating_margins'] = op_income / revenue

    # ROE
    if net_income and equity and equity > 0:
        ratios['return_on_equity'] = net_income / equity

    # Debt to equity
    if debt and equity and equity > 0:
        ratios['debt_to_equity'] = min(max(debt / equity, 0), 5)

    # Current ratio
    if assets_current and liabilities_current and liabilities_current > 0:
        ratios['current_ratio'] = assets_current / liabilities_current

    # Cash flows
    if op_cf:
        ratios['operating_cashflow'] = op_cf

    if op_cf and inv_cf:
        ratios['free_cashflow'] = op_cf - abs(inv_cf)

    # Market cap
    if shares:
        ratios['market_cap'] = price * shares

    return ratios


def upsert_snapshot(conn: sqlite3.Connection, asset_id: int, date: str, ratios: Dict, macro_data: Dict):
    """Insert or update snapshot."""
    cursor = conn.cursor()

    # Check if snapshot exists
    cursor.execute(
        'SELECT id FROM snapshots WHERE asset_id = ? AND snapshot_date = ?',
        (asset_id, date)
    )
    row = cursor.fetchone()

    if row:
        # UPDATE existing
        snapshot_id = row[0]
        cursor.execute('''
            UPDATE snapshots SET
                pe_ratio = ?,
                pb_ratio = ?,
                ps_ratio = ?,
                profit_margins = ?,
                operating_margins = ?,
                return_on_equity = ?,
                debt_to_equity = ?,
                current_ratio = ?,
                trailing_eps = ?,
                book_value = ?,
                revenue_per_share = ?,
                free_cashflow = ?,
                operating_cashflow = ?,
                market_cap = ?
            WHERE id = ?
        ''', (
            ratios.get('pe_ratio'),
            ratios.get('pb_ratio'),
            ratios.get('ps_ratio'),
            ratios.get('profit_margins'),
            ratios.get('operating_margins'),
            ratios.get('return_on_equity'),
            ratios.get('debt_to_equity'),
            ratios.get('current_ratio'),
            ratios.get('trailing_eps'),
            ratios.get('book_value'),
            ratios.get('revenue_per_share'),
            ratios.get('free_cashflow'),
            ratios.get('operating_cashflow'),
            ratios.get('market_cap'),
            snapshot_id
        ))
        action = 'UPDATED'
    else:
        # INSERT new
        cursor.execute('''
            INSERT INTO snapshots (
                asset_id, snapshot_date,
                pe_ratio, pb_ratio, ps_ratio,
                profit_margins, operating_margins, return_on_equity,
                debt_to_equity, current_ratio,
                trailing_eps, book_value, revenue_per_share,
                free_cashflow, operating_cashflow, market_cap,
                vix, treasury_10y, dollar_index, oil_price, gold_price
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            asset_id, date,
            ratios.get('pe_ratio'),
            ratios.get('pb_ratio'),
            ratios.get('ps_ratio'),
            ratios.get('profit_margins'),
            ratios.get('operating_margins'),
            ratios.get('return_on_equity'),
            ratios.get('debt_to_equity'),
            ratios.get('current_ratio'),
            ratios.get('trailing_eps'),
            ratios.get('book_value'),
            ratios.get('revenue_per_share'),
            ratios.get('free_cashflow'),
            ratios.get('operating_cashflow'),
            ratios.get('market_cap'),
            macro_data.get('vix'),
            macro_data.get('treasury_10y'),
            macro_data.get('dollar_index'),
            macro_data.get('oil_price'),
            macro_data.get('gold_price')
        ))
        action = 'INSERTED'

    conn.commit()
    return action


def get_macro_data(conn: sqlite3.Connection, date: str) -> Dict:
    """Get macro indicators for date (or closest)."""
    cursor = conn.cursor()

    # Try exact date
    cursor.execute('''
        SELECT vix, treasury_10y, dollar_index, oil_price, gold_price
        FROM snapshots
        WHERE snapshot_date = ? AND vix IS NOT NULL
        LIMIT 1
    ''', (date,))

    row = cursor.fetchone()
    if row:
        return {
            'vix': row[0],
            'treasury_10y': row[1],
            'dollar_index': row[2],
            'oil_price': row[3],
            'gold_price': row[4]
        }

    # Try closest (±30 days)
    date_obj = datetime.strptime(date, '%Y-%m-%d')
    for days in range(1, 31):
        for offset in [days, -days]:
            check_date = (date_obj + timedelta(days=offset)).strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT vix, treasury_10y, dollar_index, oil_price, gold_price
                FROM snapshots
                WHERE snapshot_date = ? AND vix IS NOT NULL
                LIMIT 1
            ''', (check_date,))

            row = cursor.fetchone()
            if row:
                return {
                    'vix': row[0],
                    'treasury_10y': row[1],
                    'dollar_index': row[2],
                    'oil_price': row[3],
                    'gold_price': row[4]
                }

    # Return defaults
    return {
        'vix': 20.0,
        'treasury_10y': 3.0,
        'dollar_index': 100.0,
        'oil_price': 70.0,
        'gold_price': 1800.0
    }


def main():
    """Process all SEC EDGAR data."""
    logger.info('Starting SEC EDGAR data processing...')

    # Load ticker to CIK mapping
    with open(TICKER_MAPPING_FILE, 'r') as f:
        ticker_to_cik = json.load(f)

    logger.info(f'Loaded {len(ticker_to_cik)} ticker mappings')

    # Connect to database
    conn = sqlite3.connect(DB_PATH)

    stats = {
        'companies_processed': 0,
        'filings_found': 0,
        'snapshots_inserted': 0,
        'snapshots_updated': 0,
        'skipped_no_price': 0,
        'skipped_insufficient_data': 0,
        'errors': 0
    }

    # Process each ticker
    for ticker, cik in ticker_to_cik.items():
        try:
            logger.info(f'Processing {ticker} (CIK{cik})...')

            # Load SEC data
            sec_file = SEC_DATA_PATH / f'CIK{cik}.json'
            if not sec_file.exists():
                logger.warning(f'  No SEC file found for {ticker}')
                continue

            with open(sec_file, 'r') as f:
                sec_data = json.load(f)

            # Get asset_id
            asset_id = get_asset_id(conn, ticker)

            # Extract all quarterly filing dates
            if 'facts' not in sec_data or 'us-gaap' not in sec_data['facts']:
                continue

            # Get all unique filing dates from revenue data
            revenue_tag = None
            for tag in XBRL_TAGS['revenue']:
                if tag in sec_data['facts']['us-gaap']:
                    revenue_tag = tag
                    break

            if not revenue_tag:
                continue

            revenue_data = sec_data['facts']['us-gaap'][revenue_tag]
            if 'units' not in revenue_data or 'USD' not in revenue_data['units']:
                continue

            # Get all quarterly dates
            dates = set()
            for dp in revenue_data['units']['USD']:
                if 'end' in dp and 'frame' in dp and 'Q' in dp.get('frame', ''):
                    dates.add(dp['end'])

            dates = sorted(dates)
            stats['filings_found'] += len(dates)

            logger.info(f'  Found {len(dates)} quarterly filings')

            # Process each date
            for date in dates:
                # Get price
                price = get_price_for_date(conn, ticker, date)
                if not price:
                    stats['skipped_no_price'] += 1
                    continue

                # Calculate ratios
                ratios = calculate_ratios(sec_data, date, price)

                # Need at least some ratios
                if not ratios or len(ratios) < 3:
                    stats['skipped_insufficient_data'] += 1
                    continue

                # Get macro data
                macro_data = get_macro_data(conn, date)

                # Insert or update
                action = upsert_snapshot(conn, asset_id, date, ratios, macro_data)

                if action == 'INSERTED':
                    stats['snapshots_inserted'] += 1
                else:
                    stats['snapshots_updated'] += 1

            stats['companies_processed'] += 1

            if stats['companies_processed'] % 10 == 0:
                logger.info(f'Progress: {stats["companies_processed"]}/{len(ticker_to_cik)} companies, '
                          f'{stats["snapshots_inserted"]} inserted, {stats["snapshots_updated"]} updated')

        except Exception as e:
            logger.error(f'Error processing {ticker}: {e}')
            stats['errors'] += 1
            continue

    conn.close()

    # Final stats
    logger.info('\\n' + '=' * 60)
    logger.info('SEC EDGAR PROCESSING COMPLETE')
    logger.info('=' * 60)
    logger.info(f'Companies processed:      {stats["companies_processed"]:5}')
    logger.info(f'Quarterly filings found:  {stats["filings_found"]:5}')
    logger.info(f'Snapshots inserted:       {stats["snapshots_inserted"]:5}')
    logger.info(f'Snapshots updated:        {stats["snapshots_updated"]:5}')
    logger.info(f'Skipped (no price):       {stats["skipped_no_price"]:5}')
    logger.info(f'Skipped (insufficient):   {stats["skipped_insufficient_data"]:5}')
    logger.info(f'Errors:                   {stats["errors"]:5}')
    logger.info('=' * 60)

    return 0


if __name__ == '__main__':
    sys.exit(main())

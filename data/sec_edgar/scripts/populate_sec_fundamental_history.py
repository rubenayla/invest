#!/usr/bin/env python3
"""
Populate snapshots table with real SEC EDGAR fundamental data.

This script:
1. Reads stock tickers from database
2. Loads corresponding SEC EDGAR JSON files
3. For each snapshot date, finds closest quarterly filing
4. Calculates fundamental ratios
5. Updates snapshots table with real data
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


# XBRL tag mappings (try multiple variants for each metric)
XBRL_TAGS = {
    'revenue': [
        'Revenues',
        'RevenueFromContractWithCustomerExcludingAssessedTax',
        'SalesRevenueNet',
        'RevenueFromContractWithCustomerIncludingAssessedTax'
    ],
    'net_income': [
        'NetIncomeLoss',
        'ProfitLoss',
        'NetIncomeLossAvailableToCommonStockholdersBasic'
    ],
    'eps_basic': [
        'EarningsPerShareBasic',
        'EarningsPerShareBasicAndDiluted'
    ],
    'eps_diluted': [
        'EarningsPerShareDiluted',
        'EarningsPerShareBasicAndDiluted'
    ],
    'assets': [
        'Assets',
        'AssetsCurrent'
    ],
    'assets_current': [
        'AssetsCurrent'
    ],
    'liabilities': [
        'Liabilities'
    ],
    'liabilities_current': [
        'LiabilitiesCurrent'
    ],
    'equity': [
        'StockholdersEquity',
        'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest'
    ],
    'shares_outstanding': [
        'CommonStockSharesOutstanding',
        'WeightedAverageNumberOfSharesOutstandingBasic'
    ],
    'cash': [
        'CashAndCashEquivalentsAtCarryingValue',
        'Cash'
    ],
    'long_term_debt': [
        'LongTermDebt',
        'LongTermDebtNoncurrent'
    ],
    'operating_income': [
        'OperatingIncomeLoss'
    ],
    'gross_profit': [
        'GrossProfit'
    ],
    'operating_cash_flow': [
        'NetCashProvidedByUsedInOperatingActivities'
    ],
    'investing_cash_flow': [
        'NetCashProvidedByUsedInInvestingActivities'
    ],
    'financing_cash_flow': [
        'NetCashProvidedByUsedInFinancingActivities'
    ]
}


class SECDataPopulator:
    """Populates snapshots table with SEC EDGAR fundamental data."""

    def __init__(self):
        self.db_path = DB_PATH
        self.sec_data_path = SEC_DATA_PATH

        # Load ticker to CIK mapping
        self.ticker_to_cik = self._load_ticker_cik_mapping()

        # Statistics
        self.stats = {
            'total_snapshots': 0,
            'snapshots_updated': 0,
            'snapshots_no_sec_data': 0,
            'snapshots_no_close_filing': 0,
            'snapshots_insufficient_metrics': 0,
            'errors': 0
        }

    def _load_ticker_cik_mapping(self) -> Dict[str, str]:
        """Load mapping of ticker symbols to CIK numbers."""
        logger.info('Loading ticker to CIK mapping from SEC data...')

        mapping = {}

        # Iterate through all SEC JSON files
        for json_file in self.sec_data_path.glob('CIK*.json'):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)

                cik = str(data.get('cik', '')).zfill(10)
                entity_name = data.get('entityName', '')

                # Try to get ticker from DEI facts
                if 'facts' in data and 'dei' in data['facts']:
                    if 'EntityCommonStockSharesOutstanding' in data['facts']['dei']:
                        # This company has common stock - likely has a ticker
                        # We'll need to match by CIK from database
                        mapping[cik] = entity_name
            except Exception:
                continue

        logger.info(f'Found {len(mapping)} companies with SEC data')
        return mapping

    def get_ticker_cik_from_db(self) -> Dict[str, str]:
        """Get CIK numbers for our tickers from the database (if available)."""
        # For now, we'll use a manual mapping for common stocks
        # In production, you'd want to fetch this from SEC's ticker.txt file

        # Load from SEC's company tickers JSON
        tickers_file = self.sec_data_path.parent / 'company_tickers.json'
        if tickers_file.exists():
            with open(tickers_file, 'r') as f:
                tickers_data = json.load(f)

            mapping = {}
            for item in tickers_data.values():
                ticker = item.get('ticker', '').upper()
                cik = str(item.get('cik_str', '')).zfill(10)
                mapping[ticker] = cik

            return mapping

        # Fallback: return empty dict, will need manual mapping
        return {}

    def find_closest_filing(
        self,
        target_date: datetime,
        datapoints: List[Dict],
        max_days: int = 90
    ) -> Optional[Dict]:
        """
        Find SEC filing closest to target date.

        Parameters
        ----------
        target_date : datetime
            Target snapshot date
        datapoints : List[Dict]
            List of SEC filing datapoints
        max_days : int
            Maximum days difference allowed

        Returns
        -------
        Dict or None
            Closest filing data, or None if no filing within max_days
        """
        closest = None
        min_diff = timedelta(days=max_days + 1)

        for dp in datapoints:
            if 'end' not in dp:
                continue

            filing_date = datetime.strptime(dp['end'], '%Y-%m-%d')
            diff = abs(filing_date - target_date)

            if diff < min_diff:
                min_diff = diff
                closest = dp

        if min_diff.days <= max_days:
            return closest

        return None

    def extract_metric(
        self,
        sec_data: Dict,
        metric_tags: List[str],
        target_date: datetime
    ) -> Optional[float]:
        """
        Extract a metric value from SEC data for a specific date.

        Parameters
        ----------
        sec_data : Dict
            Company's SEC EDGAR data
        metric_tags : List[str]
            List of possible XBRL tags for this metric
        target_date : datetime
            Target date

        Returns
        -------
        float or None
            Metric value, or None if not found
        """
        if 'facts' not in sec_data or 'us-gaap' not in sec_data['facts']:
            return None

        us_gaap = sec_data['facts']['us-gaap']

        # Try each tag variant
        for tag in metric_tags:
            if tag not in us_gaap:
                continue

            # Get datapoints
            if 'units' not in us_gaap[tag]:
                continue

            units = us_gaap[tag]['units']

            # Prefer USD, but try other units
            for unit_key in ['USD', 'shares', 'pure']:
                if unit_key not in units:
                    continue

                datapoints = units[unit_key]

                # Find closest filing
                closest = self.find_closest_filing(target_date, datapoints)

                if closest and 'val' in closest:
                    return float(closest['val'])

        return None

    def calculate_ratios(
        self,
        sec_data: Dict,
        snapshot_date: datetime,
        current_price: float
    ) -> Optional[Dict]:
        """
        Calculate all fundamental ratios for a snapshot.

        Parameters
        ----------
        sec_data : Dict
            Company's SEC EDGAR data
        snapshot_date : datetime
            Snapshot date
        current_price : float
            Stock price on snapshot date

        Returns
        -------
        Dict or None
            Dictionary of calculated ratios, or None if insufficient data
        """
        # Extract raw metrics
        revenue = self.extract_metric(sec_data, XBRL_TAGS['revenue'], snapshot_date)
        net_income = self.extract_metric(sec_data, XBRL_TAGS['net_income'], snapshot_date)
        eps_basic = self.extract_metric(sec_data, XBRL_TAGS['eps_basic'], snapshot_date)
        eps_diluted = self.extract_metric(sec_data, XBRL_TAGS['eps_diluted'], snapshot_date)
        assets = self.extract_metric(sec_data, XBRL_TAGS['assets'], snapshot_date)
        assets_current = self.extract_metric(sec_data, XBRL_TAGS['assets_current'], snapshot_date)
        liabilities = self.extract_metric(sec_data, XBRL_TAGS['liabilities'], snapshot_date)
        liabilities_current = self.extract_metric(sec_data, XBRL_TAGS['liabilities_current'], snapshot_date)
        equity = self.extract_metric(sec_data, XBRL_TAGS['equity'], snapshot_date)
        shares_outstanding = self.extract_metric(sec_data, XBRL_TAGS['shares_outstanding'], snapshot_date)
        cash = self.extract_metric(sec_data, XBRL_TAGS['cash'], snapshot_date)
        long_term_debt = self.extract_metric(sec_data, XBRL_TAGS['long_term_debt'], snapshot_date)
        operating_income = self.extract_metric(sec_data, XBRL_TAGS['operating_income'], snapshot_date)
        gross_profit = self.extract_metric(sec_data, XBRL_TAGS['gross_profit'], snapshot_date)
        operating_cf = self.extract_metric(sec_data, XBRL_TAGS['operating_cash_flow'], snapshot_date)
        investing_cf = self.extract_metric(sec_data, XBRL_TAGS['investing_cash_flow'], snapshot_date)

        # Need at least revenue, net_income, and equity
        if not revenue or not net_income or not equity:
            return None

        # Calculate ratios
        ratios = {}

        # PE ratio
        if eps_diluted and eps_diluted != 0:
            ratios['pe_ratio'] = current_price / eps_diluted
        elif eps_basic and eps_basic != 0:
            ratios['pe_ratio'] = current_price / eps_basic
        else:
            ratios['pe_ratio'] = None

        # PB ratio
        if equity and shares_outstanding and shares_outstanding > 0:
            book_value_per_share = equity / shares_outstanding
            if book_value_per_share > 0:
                ratios['pb_ratio'] = current_price / book_value_per_share
                ratios['book_value'] = book_value_per_share
            else:
                ratios['pb_ratio'] = None
                ratios['book_value'] = None
        else:
            ratios['pb_ratio'] = None
            ratios['book_value'] = None

        # PS ratio
        if revenue and shares_outstanding and shares_outstanding > 0:
            revenue_per_share = revenue / shares_outstanding
            if revenue_per_share > 0:
                ratios['ps_ratio'] = current_price / revenue_per_share
                ratios['revenue_per_share'] = revenue_per_share
            else:
                ratios['ps_ratio'] = None
                ratios['revenue_per_share'] = None
        else:
            ratios['ps_ratio'] = None
            ratios['revenue_per_share'] = None

        # Profit margin
        ratios['profit_margins'] = net_income / revenue if revenue > 0 else None

        # Operating margin
        ratios['operating_margins'] = operating_income / revenue if operating_income and revenue > 0 else None

        # ROE
        ratios['return_on_equity'] = net_income / equity if equity > 0 else None

        # Debt to equity
        if long_term_debt and equity and equity > 0:
            ratios['debt_to_equity'] = long_term_debt / equity
        else:
            ratios['debt_to_equity'] = None

        # Current ratio
        if assets_current and liabilities_current and liabilities_current > 0:
            ratios['current_ratio'] = assets_current / liabilities_current
        else:
            ratios['current_ratio'] = None

        # EPS
        ratios['trailing_eps'] = eps_diluted or eps_basic

        # Cash flows
        ratios['operating_cashflow'] = operating_cf

        # Free cash flow (operating CF - investing CF)
        if operating_cf and investing_cf:
            ratios['free_cashflow'] = operating_cf - abs(investing_cf)
        else:
            ratios['free_cashflow'] = None

        # Market cap
        if shares_outstanding:
            ratios['market_cap'] = current_price * shares_outstanding
        else:
            ratios['market_cap'] = None

        # Growth rates (YoY) - will calculate separately by comparing to previous year
        ratios['revenue_growth'] = None
        ratios['earnings_growth'] = None

        return ratios

    def update_snapshot(self, snapshot_id: int, ratios: Dict):
        """Update a snapshot with calculated ratios."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Cap extreme values
        if ratios.get('pe_ratio'):
            ratios['pe_ratio'] = max(min(ratios['pe_ratio'], 100), -50)

        if ratios.get('pb_ratio'):
            ratios['pb_ratio'] = max(min(ratios['pb_ratio'], 20), 0)

        if ratios.get('ps_ratio'):
            ratios['ps_ratio'] = max(min(ratios['ps_ratio'], 20), 0)

        if ratios.get('debt_to_equity'):
            ratios['debt_to_equity'] = max(min(ratios['debt_to_equity'], 5), 0)

        cursor.execute('''
            UPDATE snapshots
            SET
                pe_ratio = ?,
                pb_ratio = ?,
                ps_ratio = ?,
                profit_margins = ?,
                operating_margins = ?,
                return_on_equity = ?,
                revenue_growth = ?,
                earnings_growth = ?,
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
            ratios.get('revenue_growth'),
            ratios.get('earnings_growth'),
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

        conn.commit()
        conn.close()

    def process_all_snapshots(self):
        """Process all snapshots and populate with SEC EDGAR data."""
        logger.info('Starting SEC EDGAR data population...')

        # Get ticker to CIK mapping
        ticker_to_cik = self.get_ticker_cik_from_db()

        if not ticker_to_cik:
            logger.error('No ticker to CIK mapping available. Cannot proceed.')
            return

        logger.info(f'Loaded {len(ticker_to_cik)} ticker-to-CIK mappings')

        # Get all snapshots from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                s.id,
                a.symbol,
                s.snapshot_date,
                ph.close
            FROM snapshots s
            JOIN assets a ON s.asset_id = a.id
            LEFT JOIN (
                SELECT snapshot_id, close
                FROM price_history
                WHERE date = (
                    SELECT MAX(date)
                    FROM price_history ph2
                    WHERE ph2.snapshot_id = price_history.snapshot_id
                )
            ) ph ON s.id = ph.snapshot_id
            WHERE s.vix IS NOT NULL
            ORDER BY a.symbol, s.snapshot_date
        ''')

        snapshots = cursor.fetchall()
        conn.close()

        logger.info(f'Processing {len(snapshots)} snapshots...')

        self.stats['total_snapshots'] = len(snapshots)

        # Process each snapshot
        current_ticker = None
        sec_data = None

        for i, (snapshot_id, ticker, snapshot_date_str, price) in enumerate(snapshots):
            try:
                # Load SEC data for this ticker (cache per ticker)
                if ticker != current_ticker:
                    current_ticker = ticker

                    # Get CIK for this ticker
                    if ticker not in ticker_to_cik:
                        logger.debug(f'{ticker}: No CIK mapping found')
                        self.stats['snapshots_no_sec_data'] += 1
                        sec_data = None
                        continue

                    cik = ticker_to_cik[ticker]
                    sec_file = self.sec_data_path / f'CIK{cik}.json'

                    if not sec_file.exists():
                        logger.debug(f'{ticker}: No SEC data file found (CIK{cik})')
                        self.stats['snapshots_no_sec_data'] += 1
                        sec_data = None
                        continue

                    # Load SEC data
                    with open(sec_file, 'r') as f:
                        sec_data = json.load(f)

                    logger.info(f'[{i+1}/{len(snapshots)}] Processing {ticker} (CIK{cik})...')

                # Skip if no SEC data
                if sec_data is None:
                    continue

                # Skip if no price
                if not price or price <= 0:
                    continue

                # Parse snapshot date
                snapshot_date = datetime.strptime(snapshot_date_str, '%Y-%m-%d')

                # Calculate ratios
                ratios = self.calculate_ratios(sec_data, snapshot_date, price)

                if ratios is None:
                    self.stats['snapshots_insufficient_metrics'] += 1
                    continue

                # Update snapshot
                self.update_snapshot(snapshot_id, ratios)

                self.stats['snapshots_updated'] += 1

                # Progress update
                if (i + 1) % 100 == 0:
                    logger.info(f'Progress: {i+1}/{len(snapshots)} snapshots processed, '
                              f'{self.stats["snapshots_updated"]} updated')

            except Exception as e:
                logger.error(f'Error processing snapshot {snapshot_id} ({ticker}): {e}')
                self.stats['errors'] += 1
                continue

        # Final statistics
        logger.info('\\n' + '=' * 60)
        logger.info('SEC EDGAR POPULATION COMPLETE')
        logger.info('=' * 60)
        logger.info(f'Total snapshots:           {self.stats["total_snapshots"]:5}')
        logger.info(f'Successfully updated:      {self.stats["snapshots_updated"]:5}')
        logger.info(f'No SEC data:               {self.stats["snapshots_no_sec_data"]:5}')
        logger.info(f'No close filing:           {self.stats["snapshots_no_close_filing"]:5}')
        logger.info(f'Insufficient metrics:      {self.stats["snapshots_insufficient_metrics"]:5}')
        logger.info(f'Errors:                    {self.stats["errors"]:5}')
        logger.info('=' * 60)
        logger.info(f'Coverage: {self.stats["snapshots_updated"] / self.stats["total_snapshots"] * 100:.1f}%')


def main():
    """Run SEC EDGAR data population."""
    populator = SECDataPopulator()
    populator.process_all_snapshots()

    return 0


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""
Build ticker to CIK mapping using yfinance.

Each yfinance stock has sec_filings which contains the CIK number.
"""

import json
import logging
import sqlite3
import sys
from pathlib import Path

import yfinance as yf

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DB_PATH = PROJECT_ROOT / 'data' / 'stock_data.db'
OUTPUT_FILE = PROJECT_ROOT / 'data' / 'sec_edgar' / 'raw' / 'ticker_to_cik.json'


def get_tickers_from_db():
    """Get all tickers from database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT DISTINCT symbol FROM assets ORDER BY symbol')
    tickers = [row[0] for row in cursor.fetchall()]

    conn.close()
    return tickers


def get_cik_from_yfinance(ticker):
    """Get CIK number for a ticker using yfinance."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # CIK might be in different places
        if 'cik' in info:
            return str(info['cik']).zfill(10)

        # Try sec_filings
        if hasattr(stock, 'sec_filings') and stock.sec_filings:
            # CIK might be in the filings URL
            pass

        return None
    except Exception as e:
        logger.debug(f'{ticker}: Error getting CIK - {e}')
        return None


def main():
    """Build ticker to CIK mapping."""
    logger.info('Building ticker to CIK mapping...')

    tickers = get_tickers_from_db()
    logger.info(f'Found {len(tickers)} tickers in database')

    mapping = {}

    for i, ticker in enumerate(tickers):
        cik = get_cik_from_yfinance(ticker)

        if cik:
            mapping[ticker] = cik
            logger.info(f'[{i+1}/{len(tickers)}] {ticker} → CIK{cik}')
        else:
            logger.warning(f'[{i+1}/{len(tickers)}] {ticker} → No CIK found')

    # Save mapping
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(mapping, f, indent=2)

    logger.info(f'\\nSaved {len(mapping)}/{len(tickers)} mappings to {OUTPUT_FILE}')
    logger.info(f'Coverage: {len(mapping)/len(tickers)*100:.1f}%')

    return 0


if __name__ == '__main__':
    sys.exit(main())

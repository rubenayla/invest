#!/usr/bin/env python3
"""Re-fetch stocks that previously had empty data"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging

from scripts.data_fetcher import AsyncStockDataFetcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Read list of empty stocks
    with open('/tmp/empty_stocks.txt', 'r') as f:
        tickers = [line.strip() for line in f if line.strip()]

    logger.info(f'Re-fetching {len(tickers)} stocks that previously had empty data')
    logger.info(f'Sample tickers: {tickers[:10]}')

    # Fetch data for these stocks
    async with AsyncStockDataFetcher(max_workers=10) as fetcher:
        results = await fetcher.fetch_multiple_stocks(tickers, max_concurrent=10)

    # Report results
    successful = sum(1 for r in results.values() if 'error' not in r)
    failed = len(results) - successful

    logger.info(f'''
Re-fetch complete:
  - Total stocks: {len(results)}
  - Successful: {successful}
  - Failed: {failed}
  - Success rate: {successful/len(results)*100:.1f}%
''')

    if failed > 0:
        failed_tickers = [t for t, d in results.items() if 'error' in d]
        logger.info(f'Failed tickers ({failed}): {failed_tickers[:20]}')

if __name__ == '__main__':
    asyncio.run(main())

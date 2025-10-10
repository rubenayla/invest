#!/usr/bin/env python3
"""
Re-fetch foreign ADRs to apply currency conversion to financial statements.

This script specifically re-fetches the 18 foreign ADRs that need
currency conversion for their cashflow, balance sheet, and income statements.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.data_fetcher import AsyncStockDataFetcher

# Foreign ADRs that need currency conversion
FOREIGN_ADRS = [
    'MUFG',   # Japan - Mitsubishi UFJ Financial
    'SMFG',   # Japan - Sumitomo Mitsui Financial
    'SONY',   # Japan - Sony
    'TM',     # Japan - Toyota
    'TSM',    # Taiwan - Taiwan Semiconductor
    'NVO',    # Denmark - Novo Nordisk
    'BABA',   # China - Alibaba
    'MBT',    # Philippines - Metropolitan Bank
    'SAN',    # Spain - Banco Santander
    'UL',     # UK/Netherlands - Unilever
    'BCS',    # UK - Barclays
    'SNY',    # France - Sanofi
    'NVS',    # Switzerland - Novartis
    'HSBC',   # UK - HSBC
    'ITUB',   # Brazil - Itau Unibanco
    'VALE',   # Brazil - Vale
    'PBR',    # Brazil - Petrobras
    'KB',     # South Korea - KB Financial
]


async def main():
    print(f'🔄 Re-fetching {len(FOREIGN_ADRS)} foreign ADRs with currency conversion...')
    print('='*60)

    async with AsyncStockDataFetcher(max_workers=2) as fetcher:
        results = await fetcher.fetch_multiple_stocks(FOREIGN_ADRS, max_concurrent=2)

    successful = sum(1 for r in results.values() if 'error' not in r)
    failed = len(results) - successful

    print('\n✅ Re-fetch complete!')
    print(f'   Successful: {successful}/{len(FOREIGN_ADRS)}')
    if failed > 0:
        print(f'   Failed: {failed}')
        print('   Failed tickers:', [t for t, d in results.items() if 'error' in d])


if __name__ == '__main__':
    asyncio.run(main())

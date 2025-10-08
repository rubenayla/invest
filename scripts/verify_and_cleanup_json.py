#!/usr/bin/env python3
"""
Verify SQLite database has all stock data, then remove redundant JSON files.
"""
import sys
from pathlib import Path
import shutil

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from invest.data.stock_data_reader import StockDataReader


def main():
    print('🔍 Verifying SQLite database has all stock data...')
    print('=' * 60)

    # Check SQLite
    reader = StockDataReader()
    total = reader.get_stock_count()
    print(f'\n✅ SQLite database has {total} stocks')

    # Verify key stocks
    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    print('\nVerifying sample stocks:')
    all_ok = True
    for ticker in test_tickers:
        data = reader.get_stock_data(ticker)
        if data and data.get('info', {}).get('currentPrice'):
            price = data['info']['currentPrice']
            name = data['info'].get('longName', ticker)
            print(f'  ✅ {ticker}: ${price:.2f} ({name})')
        else:
            print(f'  ❌ {ticker}: MISSING DATA')
            all_ok = False

    if not all_ok:
        print('\n❌ SQLite data incomplete! Aborting cleanup.')
        return 1

    # Check JSON files
    cache_dir = project_root / 'data' / 'stock_cache'
    json_files = list(cache_dir.glob('*.json'))
    # Exclude cache_index.json
    json_files = [f for f in json_files if f.name != 'cache_index.json']

    print(f'\n📁 Found {len(json_files)} JSON cache files')

    # Create backup
    backup_dir = project_root / 'data' / 'stock_cache_backup'
    print(f'\n💾 Creating backup at: {backup_dir}')

    if backup_dir.exists():
        print('   Backup directory exists, removing old backup...')
        shutil.rmtree(backup_dir)

    backup_dir.mkdir(parents=True, exist_ok=True)

    # Copy all JSON files to backup
    print('   Copying JSON files to backup...')
    for json_file in json_files:
        shutil.copy2(json_file, backup_dir / json_file.name)

    # Also backup the cache index
    cache_index = cache_dir / 'cache_index.json'
    if cache_index.exists():
        shutil.copy2(cache_index, backup_dir / 'cache_index.json')

    print(f'   ✅ Backed up {len(json_files)} files')

    # Confirm deletion
    print('\n⚠️  Ready to delete JSON cache files')
    print(f'   {len(json_files)} files will be deleted')
    print(f'   Backup saved to: {backup_dir}')
    print('\nProceed with deletion? (yes/no): ', end='')

    response = input().strip().lower()

    if response != 'yes':
        print('\n❌ Deletion cancelled')
        return 0

    # Delete JSON files
    print('\n🗑️  Deleting JSON cache files...')
    deleted = 0
    for json_file in json_files:
        json_file.unlink()
        deleted += 1
        if deleted % 50 == 0:
            print(f'   Deleted {deleted}/{len(json_files)}...')

    print(f'\n✅ Deleted {deleted} JSON cache files')
    print(f'\n📦 Backup available at: {backup_dir}')
    print('   To restore: cp data/stock_cache_backup/*.json data/stock_cache/')

    return 0


if __name__ == '__main__':
    sys.exit(main())

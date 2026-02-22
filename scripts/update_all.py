#!/usr/bin/env python3
"""
Update stock data, run model predictions, and generate the dashboard.

Usage:
    uv run python scripts/update_all.py
    uv run python scripts/update_all.py --universe sp500
    uv run python scripts/update_all.py --skip-fetch --skip-nn
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import List

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / 'src'))

from invest.config.logging_config import setup_logging


def run_cmd(cmd: List[str], label: str) -> None:
    """Run a command and print timing info."""
    print(f'\n==> {label}')
    start = time.time()
    subprocess.run(cmd, check=True)
    elapsed = time.time() - start
    print(f'==> Done in {elapsed:.1f}s')


def ensure_dashboard_data() -> bool:
    """Create dashboard_data.json if it does not exist."""
    data_path = REPO_ROOT / 'dashboard' / 'dashboard_data.json'
    if data_path.exists():
        return True

    sys.path.insert(0, str(REPO_ROOT / 'src'))
    try:
        from invest.dashboard_components.data_manager import DataManager
        from invest.data.stock_data_reader import StockDataReader
    except Exception as exc:
        print(f'Could not import dashboard helpers: {exc}')
        return False

    reader = StockDataReader()
    tickers = reader.get_all_tickers()
    if not tickers:
        print('No tickers found in current_stock_data; skipping NN update.')
        return False

    manager = DataManager(output_dir=str(REPO_ROOT / 'dashboard'))
    manager.initialize_stocks(tickers)
    manager.save_data()
    print(f'Created {data_path} with {len(tickers)} stocks')
    return True


def run_gbm_predictions() -> None:
    """Run all GBM prediction variants."""
    variants = [
        ('standard', '1y'),
        ('standard', '3y'),
        ('lite', '1y'),
        ('lite', '3y'),
        ('opportunistic', '1y'),
        ('opportunistic', '3y'),
    ]
    for variant, horizon in variants:
        run_cmd(
            [
                'uv', 'run', 'python', 'scripts/run_gbm_predictions.py',
                '--variant', variant,
                '--horizon', horizon,
            ],
            f'GBM {variant} {horizon}',
        )


def main() -> int:
    setup_logging(log_file_path="logs/update_all.log")

    parser = argparse.ArgumentParser(
        description='Update data, run predictions, and regenerate the dashboard',
    )
    parser.add_argument('--universe', default='sp500', help='Universe for data fetcher')
    parser.add_argument('--max-concurrent', type=int, default=10, help='Max concurrent fetches')
    parser.add_argument('--skip-fetch', action='store_true', help='Skip data fetching step')
    parser.add_argument('--skip-gbm', action='store_true', help='Skip GBM predictions')
    parser.add_argument('--skip-nn', action='store_true', help='Skip NN predictions')
    parser.add_argument('--skip-classic', action='store_true', help='Skip classic valuations')
    parser.add_argument('--skip-dashboard', action='store_true', help='Skip dashboard generation')
    parser.add_argument('--skip-scanner', action='store_true', help='Skip opportunity scanner')
    args = parser.parse_args()

    if not args.skip_fetch:
        run_cmd(
            [
                'uv', 'run', 'python', 'scripts/data_fetcher.py',
                '--universe', args.universe,
                '--max-concurrent', str(args.max_concurrent),
            ],
            f'Fetching data ({args.universe})',
        )

    # --- Phase 2: Valuations (independent of each other) ---
    # GBM reads fundamental_history + price_history; classic reads current_stock_data.
    # Both write to valuation_results. Order between them doesn't matter.
    if not args.skip_gbm:
        run_gbm_predictions()

    # NN disabled: near-zero test correlation (2026-02-21)
    # if not args.skip_nn:
    #     if ensure_dashboard_data():
    #         run_cmd(
    #             ['uv', 'run', 'python', 'scripts/run_multi_horizon_predictions.py'],
    #             'Neural network predictions (multi-horizon)',
    #         )

    if not args.skip_classic:
        run_cmd(
            ['uv', 'run', 'python', 'scripts/run_classic_valuations.py'],
            'Classic valuations',
        )

    # --- Phase 3: Consumers (independent of each other, need Phase 2 done) ---
    # Dashboard renders valuation_results into HTML.
    # Scanner reads valuation_results for its value_score component.
    # Neither depends on the other; order between them doesn't matter.
    if not args.skip_dashboard:
        run_cmd(
            ['uv', 'run', 'python', 'scripts/dashboard.py'],
            'Dashboard generation',
        )

    if not args.skip_scanner:
        run_cmd(
            ['uv', 'run', 'python', 'scripts/run_opportunity_scan.py'],
            'Opportunity scanner',
        )

    return 0


if __name__ == '__main__':
    raise SystemExit(main())

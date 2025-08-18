#!/usr/bin/env python
"""
Run backtesting on investment strategies.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import yaml
import logging
from datetime import datetime
from pathlib import Path

from backtesting.core.engine import Backtester
from backtesting.strategies.screening import ScreeningStrategy
from backtesting.strategies.pipeline_strategy import PipelineStrategy

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description='Run investment strategy backtest')
    parser.add_argument(
        'config',
        help='Path to backtest configuration file'
    )
    parser.add_argument(
        '--output-dir',
        default='backtesting/reports',
        help='Directory for output reports'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration
    logger.info(f"Loading configuration from {args.config}")
    config = load_config(args.config)
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize backtester
    logger.info("Initializing backtester")
    backtester = Backtester(config)
    
    # Initialize strategy
    strategy_config = config.get('strategy', {})
    strategy_type = config.get('strategy_type', 'screening')
    
    if strategy_type == 'pipeline':
        strategy = PipelineStrategy(strategy_config)
        logger.info("Using real analysis pipeline strategy")
    else:
        strategy = ScreeningStrategy(strategy_config)
        logger.info("Using basic screening strategy")
    
    # Run backtest
    logger.info(f"Running backtest from {config['start_date']} to {config['end_date']}")
    results = backtester.run(strategy)
    
    # Generate output files
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_name = f"{config.get('name', 'backtest')}_{timestamp}"
    
    # Save summary
    summary_path = output_dir / f"{base_name}_summary.csv"
    results.to_csv(str(summary_path))
    logger.info(f"Summary saved to {summary_path}")
    
    # Print results
    print("\n" + "="*60)
    print("BACKTEST RESULTS")
    print("="*60)
    
    summary = results.get_summary()
    
    print(f"\nPeriod: {config['start_date']} to {config['end_date']}")
    print(f"Initial Capital: ${summary['initial_capital']:,.2f}")
    print(f"Final Value: ${summary['final_value']:,.2f}")
    print(f"\nPerformance Metrics:")
    print(f"  Total Return: {summary['total_return']:.2f}%")
    print(f"  Annualized Return: {summary['annualized_return']:.2f}%")
    print(f"  Sharpe Ratio: {summary['sharpe_ratio']:.2f}")
    print(f"  Max Drawdown: {summary['max_drawdown']:.2f}%")
    print(f"  Win Rate: {summary['win_rate']:.2f}%")
    print(f"\nTrading Activity:")
    print(f"  Number of Trades: {summary['number_of_trades']}")
    print(f"  Portfolio Turnover: {summary['portfolio_turnover']:.2f}")
    
    # Compare to benchmark if available
    if 'benchmark_return' in results.metrics:
        print(f"\nBenchmark Comparison ({config.get('benchmark', 'SPY')}):")
        print(f"  Benchmark Return: {results.metrics['benchmark_return']:.2f}%")
        print(f"  Alpha: {results.metrics.get('alpha', 0):.2f}%")
        print(f"  Beta: {results.metrics.get('beta', 0):.2f}")
        print(f"  Information Ratio: {results.metrics.get('information_ratio', 0):.2f}")
    
    print("\n" + "="*60)
    
    return results


if __name__ == '__main__':
    try:
        results = main()
    except KeyboardInterrupt:
        logger.info("Backtest interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Backtest failed: {e}", exc_info=True)
        sys.exit(1)
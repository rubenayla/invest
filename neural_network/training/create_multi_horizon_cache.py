#!/usr/bin/env python3
"""
Create training cache with REAL multi-horizon forward returns.

This script downloads historical stock data and calculates actual forward returns
for multiple time horizons (1m, 3m, 6m, 1y, 2y), not estimated values.
"""

import json
import sys
import yfinance as yf
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
import time
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.invest.valuation.neural_network_model import FeatureEngineer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MultiHorizonCacheGenerator:
    """Generate training cache with real multi-horizon forward returns."""

    def __init__(self, cache_path: str = 'training_data_cache_multi_horizon.json'):
        self.cache_path = Path(__file__).parent / cache_path
        self.feature_engineer = FeatureEngineer()

        # Time horizons in trading days (approximate)
        self.horizons = {
            '1m': 21,    # ~1 month
            '3m': 63,    # ~3 months
            '6m': 126,   # ~6 months
            '1y': 252,   # ~1 year
            '2y': 504    # ~2 years
        }

    def get_sp500_tickers(self) -> List[str]:
        """Get S&P 500 tickers (hardcoded list of common large-cap stocks)."""
        # Using a curated list of common large-cap stocks from S&P 500
        tickers = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'UNH', 'LLY',
            'V', 'JPM', 'XOM', 'JNJ', 'WMT', 'MA', 'PG', 'AVGO', 'HD', 'CVX',
            'MRK', 'ABBV', 'COST', 'PEP', 'KO', 'ADBE', 'MCD', 'CSCO', 'CRM', 'TMO',
            'ABT', 'BAC', 'NKE', 'NFLX', 'ACN', 'DHR', 'DIS', 'WFC', 'TXN', 'ORCL',
            'PM', 'QCOM', 'UPS', 'VZ', 'NEE', 'RTX', 'INTU', 'BMY', 'HON', 'UNP',
            'AMD', 'T', 'AMGN', 'LOW', 'BA', 'CAT', 'IBM', 'ELV', 'PFE', 'SPGI',
            'GS', 'DE', 'BLK', 'AXP', 'MDLZ', 'GILD', 'PLD', 'LMT', 'SYK', 'AMAT',
            'BKNG', 'ADP', 'MMC', 'TJX', 'ADI', 'CI', 'VRTX', 'C', 'MO', 'SO',
            'NOW', 'ISRG', 'REGN', 'ZTS', 'DUK', 'PGR', 'CB', 'PANW', 'GE', 'BSX',
            'SLB', 'ETN', 'CME', 'FISV', 'MCO', 'NOC', 'ITW', 'FDX', 'SCHW', 'ICE',
            'MU', 'MRVL', 'LIN', 'MDT'
        ]
        logger.info(f'Using {len(tickers)} large-cap tickers')
        return tickers

    def fetch_macro_data(self, sample_date: datetime) -> Dict[str, float]:
        """
        Fetch real historical macro data from yfinance for a given date.

        Parameters
        ----------
        sample_date : datetime
            The date to fetch macro data for

        Returns
        -------
        Dict[str, float]
            Macro indicators for the date
        """
        # Get data for a 5-day window to handle missing days
        end_date = sample_date + timedelta(days=1)
        start_date = sample_date - timedelta(days=5)

        macro_data = {}

        # VIX - Volatility Index
        try:
            vix = yf.Ticker('^VIX')
            hist = vix.history(start=start_date, end=end_date, auto_adjust=True)
            if not hist.empty:
                macro_data['vix'] = float(hist['Close'].iloc[-1])
            else:
                macro_data['vix'] = 20.0  # Default VIX
        except:
            macro_data['vix'] = 20.0

        # 10-Year Treasury Yield
        try:
            tnx = yf.Ticker('^TNX')
            hist = tnx.history(start=start_date, end=end_date, auto_adjust=True)
            if not hist.empty:
                macro_data['treasury_10y'] = float(hist['Close'].iloc[-1])
            else:
                macro_data['treasury_10y'] = 3.0  # Default 10Y
        except:
            macro_data['treasury_10y'] = 3.0

        # Dollar Index
        try:
            dxy = yf.Ticker('DX-Y.NYB')
            hist = dxy.history(start=start_date, end=end_date, auto_adjust=True)
            if not hist.empty:
                macro_data['dollar_index'] = float(hist['Close'].iloc[-1])
            else:
                macro_data['dollar_index'] = 100.0  # Default DXY
        except:
            macro_data['dollar_index'] = 100.0

        # Crude Oil
        try:
            oil = yf.Ticker('CL=F')
            hist = oil.history(start=start_date, end=end_date, auto_adjust=True)
            if not hist.empty:
                macro_data['oil_price'] = float(hist['Close'].iloc[-1])
            else:
                macro_data['oil_price'] = 70.0  # Default oil price
        except:
            macro_data['oil_price'] = 70.0

        # Gold
        try:
            gold = yf.Ticker('GC=F')
            hist = gold.history(start=start_date, end=end_date, auto_adjust=True)
            if not hist.empty:
                macro_data['gold_price'] = float(hist['Close'].iloc[-1])
            else:
                macro_data['gold_price'] = 1800.0  # Default gold price
        except:
            macro_data['gold_price'] = 1800.0

        return macro_data

    def calculate_forward_returns(self,
                                  history: pd.DataFrame,
                                  current_idx: int) -> Optional[Dict[str, float]]:
        """
        Calculate actual forward returns for all horizons from a given date.

        Parameters
        ----------
        history : pd.DataFrame
            Full historical price data
        current_idx : int
            Index of the current date

        Returns
        -------
        Dict[str, float] or None
            Forward returns for each horizon, or None if insufficient data
        """
        if current_idx >= len(history):
            return None

        current_price = history.iloc[current_idx]['Close']
        forward_returns = {}

        # Calculate return for each horizon
        for horizon_name, days_ahead in self.horizons.items():
            future_idx = current_idx + days_ahead

            if future_idx >= len(history):
                return None  # Not enough future data

            future_price = history.iloc[future_idx]['Close']

            # Calculate percentage return
            forward_return = (future_price - current_price) / current_price
            forward_returns[horizon_name] = forward_return

        return forward_returns

    def fetch_stock_data(self,
                        ticker: str,
                        start_year: int = 2004,
                        end_year: int = 2024,
                        retry_count: int = 0) -> List[Tuple]:
        """
        Fetch stock data and create samples with real multi-horizon returns.

        Includes retry logic with exponential backoff for rate limits.

        Returns list of (ticker, data_dict, forward_returns_dict) tuples.
        """
        max_retries = 6
        base_delay = 5  # Start with 5 seconds

        try:
            logger.debug(f'Fetching {ticker}...')
            stock = yf.Ticker(ticker)

            # Get historical data up to end_year
            # The loop logic below ensures we stop creating samples 2 years before end_year
            start_date = f'{start_year}-01-01'
            end_date = f'{end_year}-12-31'  # Fetch data until end_year
            history = stock.history(start=start_date, end=end_date, auto_adjust=True)

            if history.empty or len(history) < 1000:
                return []

            info = stock.info
            if not info or 'currentPrice' not in info:
                return []

            samples = []

            # Create samples from different dates
            # We need at least 2 years of history + 2 years forward
            min_history_needed = 504  # 2 years
            max_forward_needed = 504  # 2 years

            # Sample every 6 months to get diverse data points
            sample_interval = 126  # ~6 months

            for idx in range(min_history_needed, len(history) - max_forward_needed, sample_interval):
                sample_date = history.index[idx]

                # Get historical data up to this point
                hist_up_to_date = history.iloc[:idx+1].copy()

                # Calculate forward returns from this date
                forward_returns = self.calculate_forward_returns(history, idx)

                if forward_returns is None:
                    continue

                # Fetch real macro data for this sample date
                macro_data = self.fetch_macro_data(sample_date)

                # Create data dict for feature extraction
                data = {
                    'info': info,
                    'history': hist_up_to_date,
                    'macro': macro_data  # Real macro data from yfinance
                }

                samples.append((ticker, data, forward_returns))

            logger.info(f'{ticker}: Created {len(samples)} samples')
            return samples

        except Exception as e:
            error_msg = str(e).lower()

            # Check if it's a rate limit error
            if 'too many requests' in error_msg or 'rate limit' in error_msg:
                if retry_count < max_retries:
                    wait_time = base_delay * (2 ** retry_count)  # Exponential backoff
                    logger.warning(f'{ticker}: Rate limited. Waiting {wait_time}s before retry {retry_count + 1}/{max_retries}')
                    time.sleep(wait_time)
                    return self.fetch_stock_data(ticker, start_year, end_year, retry_count + 1)
                else:
                    logger.error(f'{ticker}: Max retries exceeded. Skipping.')
                    return []
            else:
                logger.warning(f'{ticker}: {e}')
                return []

    def generate_cache(self,
                      target_samples: int = 10000,
                      start_year: int = 2004,
                      end_year: int = 2024):
        """Generate training cache with real multi-horizon returns."""
        logger.info('='*60)
        logger.info('Generating Multi-Horizon Training Cache')
        logger.info('='*60)
        logger.info(f'Target samples: {target_samples}')
        logger.info(f'Data period: {start_year}-{end_year}')
        logger.info(f'Horizons: {list(self.horizons.keys())}')

        # Get S&P 500 tickers
        tickers = self.get_sp500_tickers()
        if not tickers:
            logger.error('Failed to get tickers')
            return

        all_samples = []
        failed_tickers = []

        for i, ticker in enumerate(tickers):
            if len(all_samples) >= target_samples:
                logger.info(f'Reached target of {target_samples} samples')
                break

            if (i + 1) % 10 == 0:
                logger.info(f'Progress: {i+1}/{len(tickers)} tickers, {len(all_samples)} samples')

            samples = self.fetch_stock_data(ticker, start_year, end_year)

            if samples:
                all_samples.extend(samples)
            else:
                failed_tickers.append(ticker)

            # Adaptive rate limiting - start slow, speed up if no errors
            if i < 10:
                time.sleep(1.0)  # First 10 tickers: 1 second delay
            elif i < 20:
                time.sleep(0.5)  # Next 10 tickers: 0.5 second delay
            elif failed_tickers and len(failed_tickers) > len(all_samples) * 0.1:
                # If failure rate > 10%, slow down
                time.sleep(1.0)
            else:
                time.sleep(0.2)  # Normal rate: 0.2 second delay

        logger.info(f'\nTotal samples collected: {len(all_samples)}')
        logger.info(f'Failed tickers: {len(failed_tickers)}')

        # Convert to cache format
        logger.info('\nPreparing cache data...')
        cache_samples = []

        for ticker, data, forward_returns in all_samples:
            cache_samples.append({
                'ticker': ticker,
                'data': {
                    'info': {k: v for k, v in data['info'].items()
                            if isinstance(v, (int, float, str, bool, type(None)))},
                    'history': {
                        'Close': data['history']['Close'].tolist(),
                        'Volume': data['history']['Volume'].tolist(),
                        'High': data['history']['High'].tolist(),
                        'Low': data['history']['Low'].tolist(),
                        'index': [str(d) for d in data['history'].index]
                    },
                    'macro': data['macro']
                },
                'forward_returns': forward_returns  # Real multi-horizon returns!
            })

        # Create cache
        cache = {
            'version': '2.0_multi_horizon',
            'created': datetime.now().isoformat(),
            'sample_count': len(cache_samples),
            'horizons': list(self.horizons.keys()),
            'config': {
                'start_year': start_year,
                'end_year': end_year,
                'feature_count': len(self.feature_engineer.feature_names)
            },
            'samples': cache_samples
        }

        # Save cache
        logger.info(f'\nSaving cache to {self.cache_path}...')
        with open(self.cache_path, 'w') as f:
            json.dump(cache, f)

        cache_size_mb = self.cache_path.stat().st_size / (1024 * 1024)
        logger.info(f'Cache saved: {cache_size_mb:.1f} MB')
        logger.info(f'\n✅ Multi-horizon cache generation complete!')

        # Show sample statistics
        logger.info('\nSample forward return statistics (mean ± std):')
        for horizon in self.horizons.keys():
            returns = [s['forward_returns'][horizon] * 100 for s in cache_samples]
            mean_ret = np.mean(returns)
            std_ret = np.std(returns)
            logger.info(f'  {horizon}: {mean_ret:+6.2f}% ± {std_ret:5.2f}%')


if __name__ == '__main__':
    generator = MultiHorizonCacheGenerator()
    generator.generate_cache(target_samples=10000, start_year=2004, end_year=2024)

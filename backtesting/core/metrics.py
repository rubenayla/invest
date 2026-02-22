"""
Performance metrics calculation for backtesting.
"""

import logging
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """Calculate various performance metrics for backtest results."""

    @staticmethod
    def _infer_periods_per_year(dates: pd.Series) -> float:
        """
        Infer annualization factor from observation dates.

        Returns the estimated number of observations per year based on
        the median gap between consecutive dates.
        """
        if len(dates) < 2:
            return 1.0
        diffs = pd.to_datetime(dates).diff().dropna().dt.days
        median_gap = diffs.median()
        if median_gap <= 0:
            return 252.0
        return 365.25 / median_gap

    @staticmethod
    def calculate(portfolio_values: pd.DataFrame,
                  initial_value: float,
                  benchmark_data: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Calculate comprehensive performance metrics.

        Parameters
        ----------
        portfolio_values : pd.DataFrame
            DataFrame with 'date' and 'value' columns
        initial_value : float
            Initial portfolio value
        benchmark_data : pd.DataFrame, optional
            Benchmark price data for comparison

        Returns
        -------
        Dict[str, Any]
            Dictionary of performance metrics
        """
        metrics = {}

        # Basic returns
        final_value = portfolio_values['value'].iloc[-1]
        total_return = (final_value / initial_value - 1) * 100
        metrics['total_return'] = total_return

        # Calculate period returns
        portfolio_values = portfolio_values.copy()
        portfolio_values['returns'] = portfolio_values['value'].pct_change()

        # Infer observation frequency for correct annualization
        periods_per_year = PerformanceMetrics._infer_periods_per_year(portfolio_values['date'])

        # CAGR
        days = (portfolio_values['date'].iloc[-1] - portfolio_values['date'].iloc[0]).days
        years = days / 365.25
        cagr = (((final_value / initial_value) ** (1 / years)) - 1) * 100 if years > 0 else 0
        metrics['cagr'] = cagr

        # Volatility (annualized)
        period_vol = portfolio_values['returns'].std()
        annual_vol = period_vol * np.sqrt(periods_per_year)
        metrics['volatility'] = annual_vol * 100

        # Sharpe Ratio (assuming risk-free rate of 2%)
        risk_free_rate = 0.02
        excess_return = cagr / 100 - risk_free_rate
        sharpe = excess_return / annual_vol if annual_vol > 0 else 0
        metrics['sharpe_ratio'] = sharpe

        # Maximum Drawdown
        cumulative = (1 + portfolio_values['returns']).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min() * 100
        metrics['max_drawdown'] = max_drawdown

        # Calmar Ratio (CAGR / Max Drawdown)
        calmar = cagr / abs(max_drawdown) if max_drawdown != 0 else 0
        metrics['calmar_ratio'] = calmar

        # Win Rate (periods with nonzero returns only — excludes flat periods)
        nonzero_returns = portfolio_values['returns'].dropna()
        nonzero_returns = nonzero_returns[nonzero_returns != 0]
        n_active = len(nonzero_returns)
        win_rate = (nonzero_returns > 0).sum() / n_active * 100 if n_active > 0 else 0
        metrics['win_rate'] = win_rate

        # Average Win/Loss
        wins = portfolio_values['returns'][portfolio_values['returns'] > 0]
        losses = portfolio_values['returns'][portfolio_values['returns'] < 0]

        avg_win = wins.mean() * 100 if len(wins) > 0 else 0
        avg_loss = losses.mean() * 100 if len(losses) > 0 else 0
        metrics['avg_win'] = avg_win
        metrics['avg_loss'] = avg_loss

        # Profit Factor
        total_wins = wins.sum() if len(wins) > 0 else 0
        total_losses = abs(losses.sum()) if len(losses) > 0 else 1
        profit_factor = total_wins / total_losses if total_losses > 0 else 0
        metrics['profit_factor'] = profit_factor

        # Best and Worst periods
        metrics['best_day'] = portfolio_values['returns'].max() * 100
        metrics['worst_day'] = portfolio_values['returns'].min() * 100

        # Calculate monthly returns
        portfolio_values['month'] = pd.to_datetime(portfolio_values['date']).dt.to_period('M')
        monthly_returns = portfolio_values.groupby('month')['returns'].apply(
            lambda x: (1 + x).prod() - 1
        )

        metrics['best_month'] = monthly_returns.max() * 100
        metrics['worst_month'] = monthly_returns.min() * 100

        # Sortino Ratio (using downside deviation)
        downside_returns = portfolio_values['returns'][portfolio_values['returns'] < 0]
        downside_std = downside_returns.std() * np.sqrt(periods_per_year)
        sortino = excess_return / downside_std if downside_std > 0 else 0
        metrics['sortino_ratio'] = sortino

        # Portfolio Turnover (estimated from value changes)
        # Exclude final liquidation row if flagged by the engine
        if 'is_liquidation' in portfolio_values.columns:
            turnover_mask = ~portfolio_values['is_liquidation'].fillna(False).astype(bool)
            pv_for_turnover = portfolio_values.loc[turnover_mask, 'value']
        else:
            pv_for_turnover = portfolio_values['value']
        value_changes = pv_for_turnover.diff().abs()
        avg_value = pv_for_turnover.mean()
        turnover = value_changes.sum() / (avg_value * years) if years > 0 else 0
        metrics['turnover'] = turnover

        # Benchmark comparison if provided
        if benchmark_data is not None:
            benchmark_metrics = PerformanceMetrics._calculate_benchmark_metrics(
                portfolio_values, benchmark_data, initial_value
            )
            metrics.update(benchmark_metrics)

        return metrics

    @staticmethod
    def _calculate_benchmark_metrics(portfolio_values: pd.DataFrame,
                                      benchmark_data: pd.DataFrame,
                                      initial_value: float) -> Dict[str, Any]:
        """Calculate metrics relative to benchmark."""
        metrics = {}

        # Align dates
        start_date = portfolio_values['date'].iloc[0]
        end_date = portfolio_values['date'].iloc[-1]

        # Handle both Series and DataFrame for benchmark data
        if isinstance(benchmark_data, pd.DataFrame):
            if 'Close' in benchmark_data.columns:
                benchmark_series = benchmark_data['Close']
            else:
                # Take the first column if 'Close' not available
                benchmark_series = benchmark_data.iloc[:, 0]
        else:
            benchmark_series = benchmark_data

        benchmark_period = benchmark_series[
            (benchmark_series.index >= start_date) &
            (benchmark_series.index <= end_date)
        ]

        if len(benchmark_period) > 0:
            # Benchmark return
            benchmark_return = (benchmark_period.iloc[-1] / benchmark_period.iloc[0] - 1) * 100
            metrics['benchmark_return'] = benchmark_return

            # Alpha (excess return over benchmark)
            portfolio_return = (portfolio_values['value'].iloc[-1] / initial_value - 1) * 100
            alpha = portfolio_return - benchmark_return
            metrics['alpha'] = alpha

            # Beta (correlation with benchmark)
            # Resample both to common (daily) frequency to avoid misalignment
            try:
                # Build daily portfolio values, forward-fill sparse rebalance dates
                portfolio_vals = portfolio_values.set_index('date')['value']
                portfolio_vals.index = pd.to_datetime(portfolio_vals.index)
                portfolio_vals = portfolio_vals[~portfolio_vals.index.duplicated(keep='last')]
                portfolio_vals = portfolio_vals.resample('D').ffill().dropna()
                portfolio_daily = portfolio_vals.pct_change().dropna()

                benchmark_series_idx = benchmark_period.copy()
                benchmark_series_idx.index = pd.to_datetime(benchmark_series_idx.index)
                benchmark_series_idx = benchmark_series_idx[~benchmark_series_idx.index.duplicated(keep='last')]
                benchmark_daily = benchmark_series_idx.resample('D').ffill().dropna().pct_change().dropna()

                # Ensure both are Series, not DataFrames
                if isinstance(portfolio_daily, pd.DataFrame):
                    portfolio_daily = portfolio_daily.iloc[:, 0]
                if isinstance(benchmark_daily, pd.DataFrame):
                    benchmark_daily = benchmark_daily.iloc[:, 0]

                # Create aligned DataFrame on common dates
                aligned_data = pd.concat([portfolio_daily, benchmark_daily], axis=1, join='inner')
                aligned_data.columns = ['portfolio', 'benchmark']
                aligned = aligned_data.dropna()

            except Exception as e:
                logger.warning(f'Could not align portfolio and benchmark data: {e}')
                aligned = pd.DataFrame()  # Empty DataFrame to skip correlation calculations

            if len(aligned) > 1:
                covariance = aligned.cov().iloc[0, 1]
                benchmark_variance = aligned['benchmark'].var()
                beta = covariance / benchmark_variance if benchmark_variance > 0 else 0
                metrics['beta'] = beta

                # Information Ratio
                periods_per_year = PerformanceMetrics._infer_periods_per_year(
                    pd.Series(aligned.index)
                )
                tracking_error = (aligned['portfolio'] - aligned['benchmark']).std() * np.sqrt(periods_per_year)
                info_ratio = (alpha / 100) / tracking_error if tracking_error > 0 else 0
                metrics['information_ratio'] = info_ratio

        return metrics

    @staticmethod
    def calculate_rolling_metrics(portfolio_values: pd.DataFrame,
                                   window: int = 252) -> pd.DataFrame:
        """
        Calculate rolling performance metrics.

        Parameters
        ----------
        portfolio_values : pd.DataFrame
            Portfolio value history
        window : int
            Rolling window size in days

        Returns
        -------
        pd.DataFrame
            DataFrame with rolling metrics
        """
        portfolio_values = portfolio_values.copy()
        portfolio_values['returns'] = portfolio_values['value'].pct_change()

        # Infer observation frequency for correct annualization
        periods_per_year = PerformanceMetrics._infer_periods_per_year(portfolio_values['date'])

        rolling_metrics = pd.DataFrame(index=portfolio_values.index)
        rolling_metrics['date'] = portfolio_values['date']

        # Rolling returns
        rolling_metrics['rolling_return'] = (
            portfolio_values['value'].pct_change(window) * 100
        )

        # Rolling volatility
        rolling_metrics['rolling_volatility'] = (
            portfolio_values['returns'].rolling(window).std() * np.sqrt(periods_per_year) * 100
        )

        # Rolling Sharpe
        risk_free_rate = 0.02 / periods_per_year  # Per-period risk-free rate
        excess_returns = portfolio_values['returns'] - risk_free_rate

        rolling_metrics['rolling_sharpe'] = (
            excess_returns.rolling(window).mean() /
            portfolio_values['returns'].rolling(window).std() * np.sqrt(periods_per_year)
        )

        # Rolling max drawdown
        cumulative = (1 + portfolio_values['returns']).cumprod()
        running_max = cumulative.rolling(window, min_periods=1).max()
        drawdown = (cumulative - running_max) / running_max
        rolling_metrics['rolling_max_drawdown'] = drawdown * 100

        return rolling_metrics

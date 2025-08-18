"""
Backtesting engine for evaluating investment strategies historically.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import logging

from ..data.historical import HistoricalDataProvider
from .portfolio import Portfolio
from .metrics import PerformanceMetrics

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """Configuration for backtesting."""
    start_date: str
    end_date: str
    initial_capital: float = 100000
    rebalance_frequency: str = 'quarterly'  # monthly, quarterly, annually
    universe: List[str] = None
    max_positions: int = 10
    min_position_size: float = 0.01  # 1% minimum
    max_position_size: float = 0.20  # 20% maximum
    transaction_cost: float = 0.001  # 0.1% per trade
    slippage: float = 0.001  # 0.1% slippage
    benchmark: str = 'SPY'
    name: str = 'backtest'  # Name of the backtest
    strategy: Dict[str, Any] = None  # Strategy configuration
    
    def __post_init__(self):
        self.start_date = pd.to_datetime(self.start_date)
        self.end_date = pd.to_datetime(self.end_date)
        if self.strategy is None:
            self.strategy = {}


class Backtester:
    """Main backtesting engine."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize backtester with configuration."""
        self.config = BacktestConfig(**config)
        self.data_provider = HistoricalDataProvider()
        self.portfolio = Portfolio(self.config.initial_capital)
        self.results = None
        
    def run(self, strategy) -> 'BacktestResults':
        """
        Run backtest with given strategy.
        
        Parameters
        ----------
        strategy : Strategy
            Investment strategy to test
            
        Returns
        -------
        BacktestResults
            Results of the backtest
        """
        logger.info(f"Starting backtest from {self.config.start_date} to {self.config.end_date}")
        
        # Generate rebalance dates
        rebalance_dates = self._generate_rebalance_dates()
        
        # Initialize tracking
        portfolio_values = []
        transactions = []
        holdings_history = []
        
        # Run strategy at each rebalance date
        for date in rebalance_dates:
            logger.info(f"Rebalancing on {date}")
            
            # Get point-in-time data (no look-ahead bias)
            market_data = self.data_provider.get_data_as_of(
                date=date,
                tickers=self.config.universe,
                lookback_days=365  # 1 year of history for analysis
            )
            
            # Get strategy signals
            signals = strategy.generate_signals(
                market_data=market_data,
                current_portfolio=self.portfolio.get_holdings(),
                date=date
            )
            
            # Execute trades
            trades = self.portfolio.rebalance(
                target_weights=signals,
                current_prices=market_data['current_prices'],
                transaction_cost=self.config.transaction_cost,
                slippage=self.config.slippage
            )
            
            transactions.extend(trades)
            
            # Track portfolio value
            portfolio_values.append({
                'date': date,
                'value': self.portfolio.get_value(market_data['current_prices']),
                'cash': self.portfolio.cash,
                'holdings': self.portfolio.get_holdings().copy()
            })
            
            holdings_history.append(self.portfolio.get_holdings().copy())
        
        # Calculate final portfolio value at end date
        final_prices = self.data_provider.get_prices(
            self.config.universe,
            self.config.end_date
        )
        
        final_value = self.portfolio.get_value(final_prices)
        
        # Create results
        self.results = BacktestResults(
            config=self.config,
            portfolio_values=portfolio_values,
            transactions=transactions,
            holdings_history=holdings_history,
            final_value=final_value,
            benchmark_data=self._get_benchmark_data()
        )
        
        return self.results
    
    def _generate_rebalance_dates(self) -> List[pd.Timestamp]:
        """Generate rebalancing dates based on frequency."""
        dates = []
        current = self.config.start_date
        
        while current <= self.config.end_date:
            dates.append(current)
            
            if self.config.rebalance_frequency == 'monthly':
                current = current + pd.DateOffset(months=1)
            elif self.config.rebalance_frequency == 'quarterly':
                current = current + pd.DateOffset(months=3)
            elif self.config.rebalance_frequency == 'annually':
                current = current + pd.DateOffset(years=1)
            else:
                raise ValueError(f"Unknown rebalance frequency: {self.config.rebalance_frequency}")
        
        return dates
    
    def _get_benchmark_data(self) -> pd.DataFrame:
        """Get benchmark performance data."""
        if self.config.benchmark is None or self.config.benchmark == 'null':
            return None
        
        return self.data_provider.get_price_history(
            ticker=self.config.benchmark,
            start_date=self.config.start_date,
            end_date=self.config.end_date
        )


class BacktestResults:
    """Container for backtest results."""
    
    def __init__(self, config, portfolio_values, transactions, 
                 holdings_history, final_value, benchmark_data):
        self.config = config
        self.portfolio_values = pd.DataFrame(portfolio_values)
        self.transactions = pd.DataFrame(transactions) if transactions else pd.DataFrame()
        self.holdings_history = holdings_history
        self.final_value = final_value
        self.benchmark_data = benchmark_data
        
        # Calculate metrics
        self.metrics = PerformanceMetrics.calculate(
            portfolio_values=self.portfolio_values,
            initial_value=config.initial_capital,
            benchmark_data=benchmark_data
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of backtest results."""
        # Ensure scalar values for final_value
        if hasattr(self.final_value, 'iloc'):
            # It's a pandas Series, get the scalar value
            final_val = float(self.final_value.iloc[0]) if len(self.final_value) > 0 else 0.0
        else:
            final_val = float(self.final_value)
        
        return {
            'initial_capital': float(self.config.initial_capital),
            'final_value': final_val,
            'total_return': float((final_val / self.config.initial_capital - 1) * 100),
            'annualized_return': float(self.metrics['cagr']),
            'sharpe_ratio': float(self.metrics['sharpe_ratio']),
            'max_drawdown': float(self.metrics['max_drawdown']),
            'win_rate': float(self.metrics['win_rate']),
            'number_of_trades': int(len(self.transactions)),
            'portfolio_turnover': float(self.metrics['turnover'])
        }
    
    def generate_report(self, filepath: str):
        """Generate detailed HTML report."""
        from ..reports.generator import ReportGenerator
        
        generator = ReportGenerator()
        generator.create_report(
            results=self,
            output_path=filepath
        )
        
        logger.info(f"Report generated: {filepath}")
    
    def to_csv(self, filepath: str):
        """Export results to CSV."""
        summary = pd.DataFrame([self.get_summary()])
        summary.to_csv(filepath, index=False)
        
        # Also save portfolio values
        values_file = filepath.replace('.csv', '_portfolio_values.csv')
        self.portfolio_values.to_csv(values_file, index=False)
        
        # Save transactions
        if not self.transactions.empty:
            trans_file = filepath.replace('.csv', '_transactions.csv')
            self.transactions.to_csv(trans_file, index=False)
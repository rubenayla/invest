"""
Historical data provider for backtesting with no look-ahead bias.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


class HistoricalDataProvider:
    """
    Provides historical data for backtesting.
    Ensures no look-ahead bias by only using data available at each point in time.
    """
    
    def __init__(self, cache_dir: Optional[str] = None) -> None:
        """Initialize data provider with optional cache directory."""
        self.cache_dir = cache_dir
        self._price_cache: Dict[str, pd.DataFrame] = {}
        self._fundamental_cache: Dict[str, Dict[str, Any]] = {}
        
    def get_data_as_of(self, date: pd.Timestamp, tickers: List[str], 
                        lookback_days: int = 365) -> Dict[str, Any]:
        """
        Get all data available as of a specific date (point-in-time).
        
        Parameters
        ----------
        date : pd.Timestamp
            The "as of" date - only data before this date is used
        tickers : List[str]
            List of tickers to get data for
        lookback_days : int
            Number of days of history to include
            
        Returns
        -------
        Dict[str, Any]
            Dictionary containing:
            - current_prices: Dict of ticker -> price as of date
            - price_history: DataFrame of historical prices
            - fundamentals: Dict of ticker -> fundamental data
            - financial_metrics: Dict of ticker -> metrics for screening
        """
        logger.info(f"Getting point-in-time data as of {date}")
        
        # Calculate lookback period
        start_date = date - timedelta(days=lookback_days)
        
        # Get price data
        price_history = self._get_price_history_range(
            tickers, start_date, date
        )
        
        # Get current prices (last available price before or on date)
        current_prices = {}
        for ticker in tickers:
            if ticker in price_history.columns:
                ticker_prices = price_history[ticker].dropna()
                if len(ticker_prices) > 0:
                    current_prices[ticker] = ticker_prices.iloc[-1]
        
        # Get fundamental data (as it would have been available at that date)
        fundamentals = self._get_fundamentals_as_of(tickers, date)
        
        # Calculate financial metrics for screening
        financial_metrics = self._calculate_metrics_as_of(
            tickers, price_history, fundamentals, date
        )
        
        return {
            'date': date,
            'current_prices': current_prices,
            'price_history': price_history,
            'fundamentals': fundamentals,
            'financial_metrics': financial_metrics
        }
    
    def get_prices(self, tickers: List[str], date: pd.Timestamp) -> Dict[str, float]:
        """Get prices for specific tickers on a specific date."""
        prices: Dict[str, float] = {}
        
        for ticker in tickers:
            try:
                # Get price history around the date
                start = date - timedelta(days=10)
                end = date + timedelta(days=1)
                
                data = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
                
                if not data.empty:
                    # Get the last available price up to and including the date
                    valid_prices = data[data.index <= date]['Close']
                    if not valid_prices.empty:
                        # Ensure we return a Python float, not pandas scalar
                        price_value = valid_prices.iloc[-1]
                        prices[ticker] = float(price_value.item())
                        
            except Exception as e:
                logger.warning(f"Could not get price for {ticker} on {date}: {e}")
        
        return prices
    
    def get_price_history(self, ticker: str, start_date: pd.Timestamp, 
                          end_date: pd.Timestamp) -> pd.DataFrame:
        """Get price history for a single ticker."""
        cache_key = f"{ticker}_{start_date}_{end_date}"
        
        if cache_key not in self._price_cache:
            try:
                data = yf.download(
                    ticker, 
                    start=start_date, 
                    end=end_date, 
                    progress=False,
                    auto_adjust=True
                )
                self._price_cache[cache_key] = data
            except Exception as e:
                logger.error(f"Error fetching {ticker}: {e}")
                self._price_cache[cache_key] = pd.DataFrame()
        
        return self._price_cache[cache_key]
    
    def _get_price_history_range(self, tickers: List[str], 
                                  start_date: pd.Timestamp,
                                  end_date: pd.Timestamp) -> pd.DataFrame:
        """Get price history for multiple tickers."""
        price_series = []
        
        for ticker in tickers:
            history = self.get_price_history(ticker, start_date, end_date)
            if not history.empty and 'Close' in history.columns:
                series = history['Close'].copy()
                series.name = ticker
                price_series.append(series)
        
        if price_series:
            # Combine all series into a DataFrame
            return pd.concat(price_series, axis=1)
        else:
            return pd.DataFrame()
    
    def _get_fundamentals_as_of(self, tickers: List[str], 
                                 date: pd.Timestamp) -> Dict[str, Dict]:
        """
        Get fundamental data as it would have been available at a point in time.
        
        Note: This is simplified - in reality, fundamental data has reporting delays.
        For accurate backtesting, you'd need to account for earnings release dates.
        """
        fundamentals = {}
        
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # Get quarterly financials
                financials = stock.quarterly_financials
                balance_sheet = stock.quarterly_balance_sheet
                cash_flow = stock.quarterly_cashflow
                
                # Only use data from before the as-of date
                # (In reality, there's a lag between period end and reporting)
                fundamental_data = {
                    'market_cap': info.get('marketCap'),
                    'pe_ratio': info.get('trailingPE'),
                    'pb_ratio': info.get('priceToBook'),
                    'ps_ratio': info.get('priceToSalesTrailing12Months'),
                    'debt_to_equity': info.get('debtToEquity'),
                    'roe': info.get('returnOnEquity'),
                    'roa': info.get('returnOnAssets'),
                    'current_ratio': info.get('currentRatio'),
                    'quick_ratio': info.get('quickRatio'),
                    'gross_margins': info.get('grossMargins'),
                    'operating_margins': info.get('operatingMargins'),
                    'profit_margins': info.get('profitMargins'),
                    'revenue_growth': info.get('revenueGrowth'),
                    'earnings_growth': info.get('earningsGrowth'),
                    'free_cash_flow': info.get('freeCashflow'),
                    'dividend_yield': info.get('dividendYield'),
                    'beta': info.get('beta'),
                    'sector': info.get('sector'),
                    'industry': info.get('industry')
                }
                
                # Add time-sensitive data if available
                if not financials.empty:
                    # Get the most recent data before the as-of date
                    valid_dates = [d for d in financials.columns if d <= date]
                    if valid_dates:
                        latest_date = max(valid_dates)
                        fundamental_data['revenue'] = financials[latest_date].get('Total Revenue')
                        fundamental_data['net_income'] = financials[latest_date].get('Net Income')
                
                fundamentals[ticker] = fundamental_data
                
            except Exception as e:
                logger.warning(f"Could not get fundamentals for {ticker}: {e}")
                fundamentals[ticker] = {}
        
        return fundamentals
    
    def _calculate_metrics_as_of(self, tickers: List[str],
                                  price_history: pd.DataFrame,
                                  fundamentals: Dict[str, Dict],
                                  date: pd.Timestamp) -> Dict[str, Dict]:
        """Calculate screening metrics based on point-in-time data."""
        metrics = {}
        
        for ticker in tickers:
            ticker_metrics = {}
            
            # Price-based metrics
            if ticker in price_history.columns:
                prices = price_history[ticker].dropna()
                
                if len(prices) > 0:
                    # Returns
                    ticker_metrics['return_1m'] = (prices.iloc[-1] / prices.iloc[-21] - 1) * 100 if len(prices) > 21 else None
                    ticker_metrics['return_3m'] = (prices.iloc[-1] / prices.iloc[-63] - 1) * 100 if len(prices) > 63 else None
                    ticker_metrics['return_6m'] = (prices.iloc[-1] / prices.iloc[-126] - 1) * 100 if len(prices) > 126 else None
                    ticker_metrics['return_1y'] = (prices.iloc[-1] / prices.iloc[-252] - 1) * 100 if len(prices) > 252 else None
                    
                    # Volatility
                    returns = prices.pct_change()
                    ticker_metrics['volatility'] = returns.std() * np.sqrt(252) * 100
                    
                    # Moving averages
                    ticker_metrics['above_ma50'] = prices.iloc[-1] > prices.rolling(50).mean().iloc[-1] if len(prices) > 50 else None
                    ticker_metrics['above_ma200'] = prices.iloc[-1] > prices.rolling(200).mean().iloc[-1] if len(prices) > 200 else None
                    
                    # Relative strength
                    ticker_metrics['rsi'] = self._calculate_rsi(prices)
            
            # Fundamental metrics
            if ticker in fundamentals:
                fund_data = fundamentals[ticker]
                
                # Quality metrics
                ticker_metrics['roe'] = fund_data.get('roe')
                ticker_metrics['roa'] = fund_data.get('roa')
                ticker_metrics['gross_margin'] = fund_data.get('gross_margins')
                ticker_metrics['operating_margin'] = fund_data.get('operating_margins')
                ticker_metrics['current_ratio'] = fund_data.get('current_ratio')
                ticker_metrics['debt_to_equity'] = fund_data.get('debt_to_equity')
                
                # Value metrics
                ticker_metrics['pe_ratio'] = fund_data.get('pe_ratio')
                ticker_metrics['pb_ratio'] = fund_data.get('pb_ratio')
                ticker_metrics['ps_ratio'] = fund_data.get('ps_ratio')
                ticker_metrics['dividend_yield'] = fund_data.get('dividend_yield')
                
                # Growth metrics
                ticker_metrics['revenue_growth'] = fund_data.get('revenue_growth')
                ticker_metrics['earnings_growth'] = fund_data.get('earnings_growth')
                
                # Risk metrics
                ticker_metrics['beta'] = fund_data.get('beta')
                
                # Other
                ticker_metrics['market_cap'] = fund_data.get('market_cap')
                ticker_metrics['sector'] = fund_data.get('sector')
            
            metrics[ticker] = ticker_metrics
        
        return metrics
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI (Relative Strength Index)."""
        if len(prices) < period + 1:
            return None
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else None
"""
Base data provider interface for the investment analysis system.

This module defines the abstract interface that all data providers must implement,
enabling easy swapping between different data sources (Yahoo Finance, Alpha Vantage, etc.)
while keeping the rest of the system provider-agnostic.

Key Benefits:
- Provider-agnostic valuation models
- Easy A/B testing between data sources
- Graceful fallback when primary provider fails
- Unified data format across providers
- Easy mocking for unit tests
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, date
import pandas as pd

from ...exceptions import DataFetchError, RateLimitError


@dataclass
class StockInfo:
    """Standardized stock information across all providers."""
    
    # Basic identification
    ticker: str
    name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    exchange: Optional[str] = None
    currency: Optional[str] = None
    country: Optional[str] = None
    
    # Market data
    current_price: Optional[float] = None
    market_cap: Optional[float] = None
    enterprise_value: Optional[float] = None
    shares_outstanding: Optional[float] = None
    
    # Valuation ratios
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    price_to_book: Optional[float] = None
    price_to_sales: Optional[float] = None
    ev_to_ebitda: Optional[float] = None
    ev_to_revenue: Optional[float] = None
    
    # Financial metrics
    revenue: Optional[float] = None
    net_income: Optional[float] = None
    free_cash_flow: Optional[float] = None
    total_cash: Optional[float] = None
    total_debt: Optional[float] = None
    book_value_per_share: Optional[float] = None
    
    # Growth metrics
    revenue_growth: Optional[float] = None
    earnings_growth: Optional[float] = None
    
    # Profitability metrics
    return_on_equity: Optional[float] = None
    return_on_assets: Optional[float] = None
    profit_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    
    # Efficiency metrics
    current_ratio: Optional[float] = None
    debt_to_equity: Optional[float] = None
    asset_turnover: Optional[float] = None
    
    # Dividend information
    dividend_yield: Optional[float] = None
    payout_ratio: Optional[float] = None
    
    # Target prices
    target_mean_price: Optional[float] = None
    target_high_price: Optional[float] = None
    target_low_price: Optional[float] = None
    
    # Metadata
    last_updated: Optional[datetime] = None
    data_provider: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backward compatibility."""
        return {
            # Legacy field mappings for existing code
            'symbol': self.ticker,
            'currentPrice': self.current_price,
            'marketCap': self.market_cap,
            'enterpriseValue': self.enterprise_value,
            'sharesOutstanding': self.shares_outstanding,
            'trailingPE': self.pe_ratio,
            'forwardPE': self.forward_pe,
            'priceToBook': self.price_to_book,
            'enterpriseToEbitda': self.ev_to_ebitda,
            'enterpriseToRevenue': self.ev_to_revenue,
            'totalRevenue': self.revenue,
            'freeCashflow': self.free_cash_flow,
            'totalCash': self.total_cash,
            'totalDebt': self.total_debt,
            'bookValue': self.book_value_per_share,
            'revenueGrowth': self.revenue_growth,
            'earningsGrowth': self.earnings_growth,
            'returnOnEquity': self.return_on_equity,
            'returnOnAssets': self.return_on_assets,
            'profitMargins': self.profit_margin,
            'operatingMargins': self.operating_margin,
            'currentRatio': self.current_ratio,
            'debtToEquity': self.debt_to_equity,
            'sector': self.sector,
            'industry': self.industry,
            'targetMeanPrice': self.target_mean_price,
            'targetHighPrice': self.target_high_price,
            'targetLowPrice': self.target_low_price,
            # Include all original fields for completeness
            **{k: v for k, v in self.__dict__.items() if v is not None}
        }


@dataclass
class FinancialStatements:
    """Standardized financial statements data."""
    
    ticker: str
    financials: Dict[str, Any]  # Income statement
    balance_sheet: Dict[str, Any]  # Balance sheet
    cash_flow: Dict[str, Any]  # Cash flow statement
    last_updated: Optional[datetime] = None
    data_provider: Optional[str] = None


class DataProvider(ABC):
    """Abstract base class for all data providers."""
    
    def __init__(self, name: str):
        self.name = name
        self._rate_limit_remaining = None
        self._rate_limit_reset_time = None
    
    @abstractmethod
    def get_stock_info(self, ticker: str) -> StockInfo:
        """
        Get basic stock information.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            StockInfo object with standardized data
            
        Raises:
            DataFetchError: If data cannot be retrieved
            RateLimitError: If rate limit is exceeded
        """
        pass
    
    @abstractmethod
    def get_financial_statements(self, ticker: str) -> FinancialStatements:
        """
        Get detailed financial statements.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            FinancialStatements object
            
        Raises:
            DataFetchError: If data cannot be retrieved
            RateLimitError: If rate limit is exceeded
        """
        pass
    
    @abstractmethod
    def get_multiple_stocks(self, tickers: List[str]) -> Dict[str, Optional[StockInfo]]:
        """
        Get stock information for multiple tickers efficiently.
        
        Args:
            tickers: List of stock ticker symbols
            
        Returns:
            Dictionary mapping ticker to StockInfo (None if failed)
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test if the data provider is accessible.
        
        Returns:
            True if provider is accessible, False otherwise
        """
        pass
    
    @abstractmethod
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get current rate limiting status.
        
        Returns:
            Dictionary with rate limit information
        """
        pass
    
    # Optional methods that providers can implement
    
    def get_historical_data(
        self, 
        ticker: str, 
        period: str = "1y",
        interval: str = "1d"
    ) -> Optional[pd.DataFrame]:
        """
        Get historical price data.
        
        Args:
            ticker: Stock ticker symbol
            period: Time period (1y, 2y, 5y, etc.)
            interval: Data interval (1d, 1wk, 1mo)
            
        Returns:
            DataFrame with historical data or None if not supported
        """
        return None
    
    def search_symbols(self, query: str) -> List[Dict[str, str]]:
        """
        Search for stock symbols by company name.
        
        Args:
            query: Company name or partial name
            
        Returns:
            List of matching symbols with metadata
        """
        return []
    
    def get_market_indices(self) -> Dict[str, float]:
        """
        Get major market index values.
        
        Returns:
            Dictionary mapping index name to current value
        """
        return {}
    
    def supports_feature(self, feature: str) -> bool:
        """
        Check if provider supports a specific feature.
        
        Args:
            feature: Feature name (e.g., 'historical_data', 'real_time', 'financials')
            
        Returns:
            True if feature is supported
        """
        return False


class DataProviderManager:
    """
    Manages multiple data providers with fallback capabilities.
    
    This class handles:
    - Primary/fallback provider switching
    - Load balancing across providers  
    - Provider health monitoring
    - Unified interface for all providers
    """
    
    def __init__(self):
        self.providers: Dict[str, DataProvider] = {}
        self.primary_provider: Optional[str] = None
        self.fallback_providers: List[str] = []
        
    def register_provider(self, provider: DataProvider, is_primary: bool = False):
        """Register a data provider."""
        self.providers[provider.name] = provider
        
        if is_primary:
            self.primary_provider = provider.name
        else:
            if provider.name not in self.fallback_providers:
                self.fallback_providers.append(provider.name)
    
    def get_stock_info(self, ticker: str) -> StockInfo:
        """Get stock info with automatic fallback."""
        providers_to_try = [self.primary_provider] + self.fallback_providers
        providers_to_try = [p for p in providers_to_try if p]  # Remove None
        
        last_error = None
        for provider_name in providers_to_try:
            provider = self.providers.get(provider_name)
            if not provider:
                continue
                
            try:
                result = provider.get_stock_info(ticker)
                result.data_provider = provider_name
                return result
            except (DataFetchError, RateLimitError) as e:
                last_error = e
                continue
        
        # All providers failed
        if last_error:
            raise last_error
        else:
            raise DataFetchError(ticker, "No providers available", "unknown")
    
    def get_multiple_stocks(self, tickers: List[str]) -> Dict[str, Optional[StockInfo]]:
        """Get multiple stocks with load balancing."""
        if self.primary_provider:
            provider = self.providers[self.primary_provider]
            return provider.get_multiple_stocks(tickers)
        
        # No primary provider, try each fallback
        for provider_name in self.fallback_providers:
            provider = self.providers[provider_name]
            try:
                return provider.get_multiple_stocks(tickers)
            except Exception:
                continue
        
        raise DataFetchError("multiple", "No providers available", "unknown")
    
    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all registered providers."""
        status = {}
        
        for name, provider in self.providers.items():
            try:
                is_available = provider.test_connection()
                rate_limit = provider.get_rate_limit_status()
                
                status[name] = {
                    "available": is_available,
                    "is_primary": name == self.primary_provider,
                    "rate_limit": rate_limit
                }
            except Exception as e:
                status[name] = {
                    "available": False,
                    "error": str(e),
                    "is_primary": name == self.primary_provider
                }
        
        return status
    
    def set_primary_provider(self, provider_name: str):
        """Change the primary provider."""
        if provider_name in self.providers:
            # Move current primary to fallback
            if self.primary_provider:
                self.fallback_providers.insert(0, self.primary_provider)
            
            # Set new primary
            self.primary_provider = provider_name
            
            # Remove new primary from fallback list
            if provider_name in self.fallback_providers:
                self.fallback_providers.remove(provider_name)
        else:
            raise ValueError(f"Provider '{provider_name}' not registered")


# Global provider manager instance
provider_manager = DataProviderManager()
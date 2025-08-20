"""
Data provider system for the investment analysis framework.

This package provides a unified interface for accessing financial data from
multiple sources (Yahoo Finance, Alpha Vantage, etc.) with automatic fallback
and provider abstraction.

Usage:
    from src.invest.data.providers import get_provider_manager, setup_default_providers
    
    # Setup providers
    setup_default_providers()
    
    # Get data through unified interface
    manager = get_provider_manager()
    stock_info = manager.get_stock_info("AAPL")
    
    # Or use provider directly
    from src.invest.data.providers.yahoo_finance import create_yahoo_finance_provider
    provider = create_yahoo_finance_provider()
    stock_info = provider.get_stock_info("AAPL")
"""

from .base import DataProvider, StockInfo, FinancialStatements, DataProviderManager, provider_manager
from .yahoo_finance import YahooFinanceProvider, create_yahoo_finance_provider
from .mock_provider import MockDataProvider, create_mock_provider

from ...config.logging_config import get_logger

logger = get_logger(__name__)


def setup_default_providers(use_mock: bool = False, mock_failure_rate: float = 0.0):
    """
    Setup default data providers.
    
    Args:
        use_mock: If True, use mock provider instead of real APIs (for testing)
        mock_failure_rate: Failure rate for mock provider (0.0 to 1.0)
    """
    logger.info("Setting up data providers...")
    
    if use_mock:
        # Setup mock provider for testing
        mock_provider = create_mock_provider(
            simulate_failures=mock_failure_rate > 0,
            failure_rate=mock_failure_rate
        )
        provider_manager.register_provider(mock_provider, is_primary=True)
        logger.info("Mock provider registered as primary")
    else:
        # Setup Yahoo Finance as primary provider
        yahoo_provider = create_yahoo_finance_provider()
        provider_manager.register_provider(yahoo_provider, is_primary=True)
        logger.info("Yahoo Finance provider registered as primary")
        
        # Could add additional providers as fallbacks here:
        # alpha_vantage_provider = create_alpha_vantage_provider()  
        # provider_manager.register_provider(alpha_vantage_provider, is_primary=False)
    
    # Log provider status
    status = provider_manager.get_provider_status()
    for provider_name, provider_status in status.items():
        if provider_status.get('available'):
            logger.info(f"Provider {provider_name}: Available ({'primary' if provider_status['is_primary'] else 'fallback'})")
        else:
            logger.warning(f"Provider {provider_name}: Unavailable - {provider_status.get('error', 'Unknown error')}")


def get_provider_manager() -> DataProviderManager:
    """Get the global provider manager instance."""
    return provider_manager


def get_stock_info(ticker: str) -> StockInfo:
    """Convenience function to get stock info through provider manager."""
    return provider_manager.get_stock_info(ticker)


def get_multiple_stocks(tickers: list) -> dict:
    """Convenience function to get multiple stocks through provider manager."""
    return provider_manager.get_multiple_stocks(tickers)


# Auto-setup providers when module is imported (can be overridden)
def _auto_setup():
    """Automatically setup providers if none are registered."""
    if not provider_manager.providers:
        try:
            setup_default_providers(use_mock=False)
        except Exception as e:
            logger.warning(f"Failed to setup default providers, using mock: {e}")
            setup_default_providers(use_mock=True, mock_failure_rate=0.1)


# Uncomment to enable auto-setup on import
# _auto_setup()

__all__ = [
    'DataProvider',
    'StockInfo', 
    'FinancialStatements',
    'DataProviderManager',
    'YahooFinanceProvider',
    'MockDataProvider',
    'setup_default_providers',
    'get_provider_manager',
    'get_stock_info',
    'get_multiple_stocks',
    'create_yahoo_finance_provider',
    'create_mock_provider',
]
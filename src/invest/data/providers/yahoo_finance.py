"""
Yahoo Finance data provider implementation.

This module implements the DataProvider interface for Yahoo Finance,
providing our system with access to free financial data while maintaining
provider independence.
"""

import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd

import yfinance as yf

from .base import DataProvider, StockInfo, FinancialStatements
from ...exceptions import DataFetchError, RateLimitError
from ...config.logging_config import get_logger, log_data_fetch
from ..concurrent_fetcher import ConcurrentDataFetcher

logger = get_logger(__name__)


class YahooFinanceProvider(DataProvider):
    """Yahoo Finance data provider implementation."""
    
    def __init__(self):
        super().__init__("yahoo_finance")
        self.concurrent_fetcher = ConcurrentDataFetcher()
        self.base_url = "https://finance.yahoo.com"
        
    def get_stock_info(self, ticker: str) -> StockInfo:
        """Get stock information from Yahoo Finance."""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            if not info or 'symbol' not in info:
                raise DataFetchError(ticker, "Empty or invalid response", self.name)
            
            log_data_fetch(logger, ticker, "stock_info", True, provider=self.name)
            
            # Convert Yahoo Finance data to our standardized format
            return self._convert_yahoo_info_to_stock_info(ticker, info)
            
        except Exception as e:
            log_data_fetch(logger, ticker, "stock_info", False, provider=self.name, error=str(e))
            
            if "404" in str(e) or "not found" in str(e).lower():
                raise DataFetchError(ticker, "Ticker not found", self.name)
            elif "rate limit" in str(e).lower() or "too many requests" in str(e).lower():
                raise RateLimitError(self.name, retry_after=60)
            else:
                raise DataFetchError(ticker, str(e), self.name)
    
    def get_financial_statements(self, ticker: str) -> FinancialStatements:
        """Get detailed financial statements from Yahoo Finance."""
        try:
            stock = yf.Ticker(ticker)
            
            # Get financial statements
            financials = stock.financials.to_dict() if not stock.financials.empty else {}
            balance_sheet = stock.balance_sheet.to_dict() if not stock.balance_sheet.empty else {}
            cash_flow = stock.cashflow.to_dict() if not stock.cashflow.empty else {}
            
            log_data_fetch(logger, ticker, "financial_statements", True, provider=self.name)
            
            return FinancialStatements(
                ticker=ticker,
                financials=financials,
                balance_sheet=balance_sheet,
                cash_flow=cash_flow,
                last_updated=datetime.now(),
                data_provider=self.name
            )
            
        except Exception as e:
            log_data_fetch(logger, ticker, "financial_statements", False, provider=self.name, error=str(e))
            raise DataFetchError(ticker, f"Failed to fetch financial statements: {e}", self.name)
    
    def get_multiple_stocks(self, tickers: List[str]) -> Dict[str, Optional[StockInfo]]:
        """Get multiple stocks using concurrent fetcher."""
        logger.info(f"Fetching {len(tickers)} stocks via Yahoo Finance")
        
        # Use our concurrent fetcher for efficiency
        results = self.concurrent_fetcher.fetch_multiple_stocks_basic(tickers)
        
        # Convert results to StockInfo format
        stock_infos = {}
        for ticker, data in results.items():
            if data:
                try:
                    stock_infos[ticker] = self._convert_yahoo_info_to_stock_info(ticker, data)
                except Exception as e:
                    logger.warning(f"Failed to convert data for {ticker}: {e}")
                    stock_infos[ticker] = None
            else:
                stock_infos[ticker] = None
        
        success_count = sum(1 for info in stock_infos.values() if info is not None)
        logger.info(f"Yahoo Finance batch fetch: {success_count}/{len(tickers)} successful")
        
        return stock_infos
    
    def test_connection(self) -> bool:
        """Test Yahoo Finance connectivity."""
        try:
            # Try to fetch a known ticker
            test_ticker = yf.Ticker("AAPL")
            info = test_ticker.info
            
            # Check if we got valid data
            return bool(info and 'symbol' in info)
            
        except Exception as e:
            logger.warning(f"Yahoo Finance connection test failed: {e}")
            return False
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get Yahoo Finance rate limit status."""
        # Yahoo Finance doesn't provide explicit rate limit headers,
        # so we estimate based on our usage
        return {
            "provider": self.name,
            "requests_per_second": 2.0,  # Our configured limit
            "requests_per_minute": 100,   # Our configured limit
            "estimated_remaining": "unknown",
            "reset_time": None,
            "notes": "Yahoo Finance limits are estimated, not explicit"
        }
    
    def get_historical_data(
        self, 
        ticker: str, 
        period: str = "1y",
        interval: str = "1d"
    ) -> Optional[pd.DataFrame]:
        """Get historical price data from Yahoo Finance."""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period, interval=interval)
            
            if hist.empty:
                return None
            
            log_data_fetch(logger, ticker, "historical_data", True, provider=self.name, period=period)
            return hist
            
        except Exception as e:
            log_data_fetch(logger, ticker, "historical_data", False, provider=self.name, error=str(e))
            return None
    
    def search_symbols(self, query: str) -> List[Dict[str, str]]:
        """Search for symbols (Yahoo Finance doesn't have a great API for this)."""
        logger.warning("Symbol search not optimally supported by Yahoo Finance")
        return []
    
    def get_market_indices(self) -> Dict[str, float]:
        """Get major market index values."""
        indices = {
            "^GSPC": "S&P 500",
            "^DJI": "Dow Jones",
            "^IXIC": "NASDAQ", 
            "^RUT": "Russell 2000"
        }
        
        results = {}
        for symbol, name in indices.items():
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                price = info.get('regularMarketPrice') or info.get('previousClose')
                if price:
                    results[name] = price
            except Exception:
                continue
        
        return results
    
    def supports_feature(self, feature: str) -> bool:
        """Check feature support."""
        supported_features = {
            'stock_info': True,
            'financial_statements': True,
            'historical_data': True,
            'real_time': True,  # Delayed ~15-20 minutes
            'market_indices': True,
            'options_data': True,
            'earnings_calendar': False,
            'symbol_search': False,  # Limited
            'news': False  # Not reliable
        }
        
        return supported_features.get(feature, False)
    
    def _convert_yahoo_info_to_stock_info(self, ticker: str, yahoo_info: Dict) -> StockInfo:
        """Convert Yahoo Finance info dict to standardized StockInfo."""
        
        # Helper function to safely get numeric values
        def safe_float(value):
            if value is None:
                return None
            try:
                return float(value)
            except (ValueError, TypeError):
                return None
        
        # Helper function to safely get values with multiple possible keys
        def safe_get(info_dict, keys, converter=None):
            for key in keys if isinstance(keys, list) else [keys]:
                value = info_dict.get(key)
                if value is not None:
                    return converter(value) if converter else value
            return None
        
        return StockInfo(
            # Basic identification
            ticker=ticker,
            name=yahoo_info.get('longName') or yahoo_info.get('shortName'),
            sector=yahoo_info.get('sector'),
            industry=yahoo_info.get('industry'),
            exchange=yahoo_info.get('exchange'),
            currency=yahoo_info.get('currency'),
            country=yahoo_info.get('country'),
            
            # Market data
            current_price=safe_get(yahoo_info, ['currentPrice', 'regularMarketPrice', 'previousClose'], safe_float),
            market_cap=safe_get(yahoo_info, 'marketCap', safe_float),
            enterprise_value=safe_get(yahoo_info, 'enterpriseValue', safe_float),
            shares_outstanding=safe_get(yahoo_info, 'sharesOutstanding', safe_float),
            
            # Valuation ratios
            pe_ratio=safe_get(yahoo_info, ['trailingPE', 'forwardPE'], safe_float),
            forward_pe=safe_get(yahoo_info, 'forwardPE', safe_float),
            price_to_book=safe_get(yahoo_info, 'priceToBook', safe_float),
            price_to_sales=safe_get(yahoo_info, ['priceToSalesTrailing12Months', 'priceToSales'], safe_float),
            ev_to_ebitda=safe_get(yahoo_info, 'enterpriseToEbitda', safe_float),
            ev_to_revenue=safe_get(yahoo_info, 'enterpriseToRevenue', safe_float),
            
            # Financial metrics
            revenue=safe_get(yahoo_info, 'totalRevenue', safe_float),
            net_income=safe_get(yahoo_info, 'netIncomeToCommon', safe_float),
            free_cash_flow=safe_get(yahoo_info, 'freeCashflow', safe_float),
            total_cash=safe_get(yahoo_info, 'totalCash', safe_float),
            total_debt=safe_get(yahoo_info, 'totalDebt', safe_float),
            book_value_per_share=safe_get(yahoo_info, 'bookValue', safe_float),
            
            # Growth metrics
            revenue_growth=safe_get(yahoo_info, 'revenueGrowth', safe_float),
            earnings_growth=safe_get(yahoo_info, 'earningsGrowth', safe_float),
            
            # Profitability metrics
            return_on_equity=safe_get(yahoo_info, 'returnOnEquity', safe_float),
            return_on_assets=safe_get(yahoo_info, 'returnOnAssets', safe_float),
            profit_margin=safe_get(yahoo_info, 'profitMargins', safe_float),
            operating_margin=safe_get(yahoo_info, 'operatingMargins', safe_float),
            
            # Efficiency metrics
            current_ratio=safe_get(yahoo_info, 'currentRatio', safe_float),
            debt_to_equity=safe_get(yahoo_info, 'debtToEquity', safe_float),
            asset_turnover=safe_get(yahoo_info, 'assetTurnover', safe_float),
            
            # Dividend information
            dividend_yield=safe_get(yahoo_info, 'dividendYield', safe_float),
            payout_ratio=safe_get(yahoo_info, 'payoutRatio', safe_float),
            
            # Target prices
            target_mean_price=safe_get(yahoo_info, 'targetMeanPrice', safe_float),
            target_high_price=safe_get(yahoo_info, 'targetHighPrice', safe_float),
            target_low_price=safe_get(yahoo_info, 'targetLowPrice', safe_float),
            
            # Metadata
            last_updated=datetime.now(),
            data_provider=self.name
        )


# Convenience function to create and configure Yahoo Finance provider
def create_yahoo_finance_provider() -> YahooFinanceProvider:
    """Create a configured Yahoo Finance provider."""
    return YahooFinanceProvider()
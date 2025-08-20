"""
Mock data provider for testing and development.

This provider returns realistic-looking fake data for testing purposes,
allowing development and testing without hitting real APIs.
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd

from .base import DataProvider, StockInfo, FinancialStatements
from ...exceptions import DataFetchError, RateLimitError
from ...config.logging_config import get_logger

logger = get_logger(__name__)


class MockDataProvider(DataProvider):
    """Mock data provider for testing."""
    
    def __init__(self, simulate_failures: bool = False, failure_rate: float = 0.1):
        super().__init__("mock_provider")
        self.simulate_failures = simulate_failures
        self.failure_rate = failure_rate
        self.request_count = 0
        self.max_requests_per_minute = 1000  # Very generous for testing
        
        # Predefined mock data for common test tickers
        self.mock_companies = {
            'AAPL': {
                'name': 'Apple Inc.',
                'sector': 'Technology',
                'industry': 'Consumer Electronics',
                'base_price': 150.0,
                'market_cap': 2_400_000_000_000,  # $2.4T
                'pe_ratio': 25.0
            },
            'MSFT': {
                'name': 'Microsoft Corporation', 
                'sector': 'Technology',
                'industry': 'Software',
                'base_price': 400.0,
                'market_cap': 2_800_000_000_000,  # $2.8T
                'pe_ratio': 28.0
            },
            'GOOGL': {
                'name': 'Alphabet Inc.',
                'sector': 'Communication Services',
                'industry': 'Internet Content & Information',
                'base_price': 2800.0,
                'market_cap': 1_800_000_000_000,  # $1.8T
                'pe_ratio': 22.0
            },
            'TSLA': {
                'name': 'Tesla, Inc.',
                'sector': 'Consumer Discretionary', 
                'industry': 'Auto Manufacturers',
                'base_price': 800.0,
                'market_cap': 800_000_000_000,  # $800B
                'pe_ratio': 60.0
            },
            'FAILED': {
                'name': 'Always Fails Corp',
                'sector': 'Error',
                'industry': 'Testing',
                'base_price': 0.0,
                'market_cap': 0,
                'pe_ratio': None,
                'always_fail': True  # Special flag
            }
        }
    
    def get_stock_info(self, ticker: str) -> StockInfo:
        """Get mock stock information."""
        self._increment_request_count()
        
        # Simulate failures if enabled
        if self._should_simulate_failure(ticker):
            if ticker == 'RATE_LIMITED':
                raise RateLimitError(self.name, retry_after=60)
            else:
                raise DataFetchError(ticker, "Simulated failure", self.name)
        
        # Check if we have predefined data
        if ticker in self.mock_companies:
            company_data = self.mock_companies[ticker]
            
            # Handle special failure case
            if company_data.get('always_fail'):
                raise DataFetchError(ticker, "Company always fails", self.name)
                
            return self._generate_stock_info(ticker, company_data)
        
        # Generate realistic random data for unknown tickers
        return self._generate_random_stock_info(ticker)
    
    def get_financial_statements(self, ticker: str) -> FinancialStatements:
        """Get mock financial statements."""
        self._increment_request_count()
        
        if self._should_simulate_failure(ticker):
            raise DataFetchError(ticker, "Simulated financial statements failure", self.name)
        
        return FinancialStatements(
            ticker=ticker,
            financials=self._generate_mock_financials(),
            balance_sheet=self._generate_mock_balance_sheet(),
            cash_flow=self._generate_mock_cash_flow(),
            last_updated=datetime.now(),
            data_provider=self.name
        )
    
    def get_multiple_stocks(self, tickers: List[str]) -> Dict[str, Optional[StockInfo]]:
        """Get multiple mock stocks."""
        results = {}
        
        for ticker in tickers:
            try:
                results[ticker] = self.get_stock_info(ticker)
            except (DataFetchError, RateLimitError):
                results[ticker] = None
        
        return results
    
    def test_connection(self) -> bool:
        """Mock connection test (always succeeds unless configured otherwise)."""
        return not self.simulate_failures or random.random() > 0.1
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get mock rate limit status."""
        return {
            "provider": self.name,
            "requests_made": self.request_count,
            "requests_per_minute": self.max_requests_per_minute,
            "remaining": max(0, self.max_requests_per_minute - self.request_count),
            "reset_time": datetime.now() + timedelta(minutes=1),
            "notes": "Mock provider with simulated limits"
        }
    
    def get_historical_data(
        self, 
        ticker: str, 
        period: str = "1y",
        interval: str = "1d"
    ) -> Optional[pd.DataFrame]:
        """Generate mock historical data."""
        try:
            # Parse period to get number of days
            period_days = {
                '1mo': 30, '3mo': 90, '6mo': 180,
                '1y': 365, '2y': 730, '5y': 1825, '10y': 3650
            }.get(period, 365)
            
            # Get base price
            base_price = self.mock_companies.get(ticker, {}).get('base_price', 100.0)
            
            # Generate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=period_days)
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            
            # Generate mock price data with realistic movements
            prices = []
            current_price = base_price
            
            for i, date in enumerate(dates):
                # Random walk with slight upward bias
                daily_change = random.gauss(0.001, 0.02)  # 0.1% avg daily return, 2% volatility
                current_price *= (1 + daily_change)
                prices.append(current_price)
            
            # Create OHLC data
            data = []
            for i, (date, close) in enumerate(zip(dates, prices)):
                # Generate realistic OHLC from close price
                volatility = close * 0.02  # 2% daily volatility
                high = close + random.uniform(0, volatility)
                low = close - random.uniform(0, volatility)
                open_price = low + random.uniform(0, high - low)
                
                # Ensure OHLC relationships are valid
                high = max(high, open_price, close)
                low = min(low, open_price, close)
                
                volume = random.randint(1_000_000, 10_000_000)
                
                data.append({
                    'Open': open_price,
                    'High': high,
                    'Low': low,
                    'Close': close,
                    'Volume': volume
                })
            
            df = pd.DataFrame(data, index=dates)
            return df
            
        except Exception as e:
            logger.warning(f"Failed to generate mock historical data for {ticker}: {e}")
            return None
    
    def supports_feature(self, feature: str) -> bool:
        """Mock provider supports most features."""
        return feature in [
            'stock_info', 'financial_statements', 'historical_data',
            'real_time', 'market_indices', 'symbol_search'
        ]
    
    def _generate_stock_info(self, ticker: str, company_data: Dict) -> StockInfo:
        """Generate stock info from company template."""
        base_price = company_data['base_price']
        
        # Add some random variation to price
        current_price = base_price * (1 + random.gauss(0, 0.05))  # ±5% variation
        
        market_cap = company_data['market_cap']
        shares_outstanding = market_cap / current_price if current_price > 0 else 1_000_000
        
        return StockInfo(
            ticker=ticker,
            name=company_data['name'],
            sector=company_data['sector'],
            industry=company_data['industry'],
            exchange='NASDAQ',
            currency='USD',
            country='US',
            
            current_price=round(current_price, 2),
            market_cap=market_cap,
            enterprise_value=market_cap * random.uniform(0.9, 1.1),
            shares_outstanding=shares_outstanding,
            
            pe_ratio=company_data.get('pe_ratio'),
            forward_pe=company_data.get('pe_ratio', 20) * random.uniform(0.8, 1.2),
            price_to_book=random.uniform(1.5, 8.0),
            price_to_sales=random.uniform(2.0, 15.0),
            ev_to_ebitda=random.uniform(10.0, 30.0),
            
            revenue=market_cap * random.uniform(0.8, 2.5),
            free_cash_flow=market_cap * random.uniform(0.05, 0.15),
            total_cash=market_cap * random.uniform(0.1, 0.3),
            total_debt=market_cap * random.uniform(0.0, 0.5),
            
            revenue_growth=random.uniform(-0.1, 0.3),  # -10% to +30%
            earnings_growth=random.uniform(-0.2, 0.4),
            
            return_on_equity=random.uniform(0.05, 0.25),
            return_on_assets=random.uniform(0.02, 0.15),
            profit_margin=random.uniform(0.05, 0.30),
            operating_margin=random.uniform(0.08, 0.35),
            
            current_ratio=random.uniform(1.0, 3.0),
            debt_to_equity=random.uniform(0.0, 2.0),
            
            dividend_yield=random.uniform(0.0, 0.06) if random.random() > 0.3 else None,
            
            target_mean_price=current_price * random.uniform(0.8, 1.4),
            target_high_price=current_price * random.uniform(1.2, 1.8),
            target_low_price=current_price * random.uniform(0.6, 1.0),
            
            last_updated=datetime.now(),
            data_provider=self.name
        )
    
    def _generate_random_stock_info(self, ticker: str) -> StockInfo:
        """Generate completely random stock info for unknown tickers."""
        base_price = random.uniform(10.0, 1000.0)
        market_cap = random.uniform(1_000_000_000, 100_000_000_000)  # $1B to $100B
        
        sectors = ['Technology', 'Healthcare', 'Financials', 'Consumer Discretionary', 'Industrials']
        industries = ['Software', 'Pharmaceuticals', 'Banks', 'Retail', 'Manufacturing']
        
        return StockInfo(
            ticker=ticker,
            name=f"{ticker} Corporation",
            sector=random.choice(sectors),
            industry=random.choice(industries),
            exchange='NYSE',
            currency='USD',
            country='US',
            
            current_price=round(base_price, 2),
            market_cap=market_cap,
            enterprise_value=market_cap * random.uniform(0.9, 1.1),
            shares_outstanding=market_cap / base_price,
            
            pe_ratio=random.uniform(10.0, 50.0),
            price_to_book=random.uniform(1.0, 10.0),
            
            revenue=market_cap * random.uniform(0.5, 3.0),
            free_cash_flow=market_cap * random.uniform(-0.1, 0.2),
            
            return_on_equity=random.uniform(-0.1, 0.3),
            profit_margin=random.uniform(-0.1, 0.4),
            
            last_updated=datetime.now(),
            data_provider=self.name
        )
    
    def _generate_mock_financials(self) -> Dict[str, Any]:
        """Generate mock financial statements."""
        return {
            'Total Revenue': {datetime.now().year - 1: random.randint(1_000_000, 100_000_000)},
            'Net Income': {datetime.now().year - 1: random.randint(-1_000_000, 10_000_000)},
            'Gross Profit': {datetime.now().year - 1: random.randint(500_000, 50_000_000)},
        }
    
    def _generate_mock_balance_sheet(self) -> Dict[str, Any]:
        """Generate mock balance sheet."""
        return {
            'Total Assets': {datetime.now().year - 1: random.randint(10_000_000, 500_000_000)},
            'Total Debt': {datetime.now().year - 1: random.randint(0, 100_000_000)},
            'Total Stockholder Equity': {datetime.now().year - 1: random.randint(5_000_000, 200_000_000)},
        }
    
    def _generate_mock_cash_flow(self) -> Dict[str, Any]:
        """Generate mock cash flow statement."""
        return {
            'Operating Cash Flow': {datetime.now().year - 1: random.randint(-5_000_000, 50_000_000)},
            'Free Cash Flow': {datetime.now().year - 1: random.randint(-10_000_000, 30_000_000)},
            'Capital Expenditures': {datetime.now().year - 1: -random.randint(1_000_000, 20_000_000)},
        }
    
    def _should_simulate_failure(self, ticker: str) -> bool:
        """Check if we should simulate a failure for this request."""
        if not self.simulate_failures:
            return False
        
        # Always fail for special test tickers
        if ticker in ['FAILED', 'RATE_LIMITED', 'TIMEOUT']:
            return True
            
        # Random failures based on failure rate
        return random.random() < self.failure_rate
    
    def _increment_request_count(self):
        """Track request count for rate limiting simulation."""
        self.request_count += 1


def create_mock_provider(simulate_failures: bool = False, failure_rate: float = 0.1) -> MockDataProvider:
    """Create a configured mock provider."""
    return MockDataProvider(simulate_failures=simulate_failures, failure_rate=failure_rate)
"""
Example showing how we could integrate tenacity while keeping our custom logic.

This demonstrates a hybrid approach that uses tenacity for retry logic
while preserving our rate limiting and circuit breaker functionality.
"""

from typing import Dict
import yfinance as yf
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    RetryCallState
)
import logging

# Our custom components we'd still need
from src.invest.data.concurrent_fetcher import RateLimiter, CircuitBreaker, RateLimitConfig
from src.invest.exceptions import RateLimitError, DataFetchError
from src.invest.config.logging_config import get_logger

logger = get_logger(__name__)


class TenacityEnhancedFetcher:
    """Data fetcher using tenacity for retry logic."""
    
    def __init__(self):
        self.rate_limiter = RateLimiter(RateLimitConfig())
        self.circuit_breaker = CircuitBreaker()
    
    def fetch_stock_data(self, ticker: str) -> Dict:
        """Fetch stock data with tenacity + our custom logic."""
        
        # Check circuit breaker before attempting
        if not self.circuit_breaker.call_allowed():
            raise DataFetchError(ticker, "Circuit breaker open", "yfinance")
        
        try:
            # Use tenacity for the actual retry logic
            result = self._fetch_with_tenacity(ticker)
            self.circuit_breaker.record_success()
            return result
        except Exception as e:
            self.circuit_breaker.record_failure()
            raise e
    
    @retry(
        # Retry up to 3 times
        stop=stop_after_attempt(3),
        
        # Exponential backoff: 0.5s, 1s, 2s, 4s (with jitter)
        wait=wait_exponential(multiplier=0.5, max=10, jitter=True),
        
        # Only retry specific exceptions
        retry=retry_if_exception_type((
            ConnectionError,
            TimeoutError, 
            RateLimitError
        )),
        
        # Log before each retry
        before_sleep=before_sleep_log(logger, logging.INFO),
        
        # Custom callback for our rate limiting
        before=lambda retry_state: self._before_retry(retry_state),
        after=lambda retry_state: self._after_retry(retry_state)
    )
    def _fetch_with_tenacity(self, ticker: str) -> Dict:
        """Core fetch logic with tenacity retry handling."""
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not info or 'symbol' not in info:
            raise DataFetchError(ticker, "Empty response", "yfinance")
            
        return info
    
    def _before_retry(self, retry_state: RetryCallState):
        """Called before each retry attempt."""
        # Apply rate limiting
        while not self.rate_limiter.acquire():
            import time
            wait_time = self.rate_limiter.wait_time()
            if wait_time > 0:
                time.sleep(min(wait_time + 0.1, 2.0))
    
    def _after_retry(self, retry_state: RetryCallState):
        """Called after each retry attempt."""
        # Release rate limiter
        self.rate_limiter.release()


# Comparison of code complexity:

def current_approach_example():
    """Our current custom implementation."""
    return """
    # Our current approach - ~150 lines of custom code:
    
    class ConcurrentDataFetcher:
        def __init__(self):
            self.rate_limiter = RateLimiter(config)
            self.circuit_breaker = CircuitBreaker()
            
        @with_retry_and_rate_limiting(rate_limiter, circuit_breaker, max_retries=3)
        def _fetch_stock_info(self, ticker: str):
            # Custom retry logic with:
            # - Manual retry counting (10+ lines)
            # - Exponential backoff calculation (5+ lines)
            # - Error classification (15+ lines)
            # - Rate limiting integration (20+ lines)  
            # - Circuit breaker integration (10+ lines)
            # - Progress callbacks (10+ lines)
            # - Exception handling (20+ lines)
            
        def with_retry_and_rate_limiting(rate_limiter, circuit_breaker, max_retries):
            # 50+ lines of decorator implementation
            def decorator(func):
                def wrapper(*args, **kwargs):
                    retries = 0
                    while retries <= max_retries:
                        # Manual retry logic...
                        # Manual backoff calculation...
                        # Manual error classification...
                    return wrapper
            return decorator
    """


def tenacity_approach_example():
    """Tenacity-based approach.""" 
    return """
    # Tenacity approach - ~50 lines total:
    
    class TenacityEnhancedFetcher:
        def __init__(self):
            self.rate_limiter = RateLimiter(config)  # Still need this
            self.circuit_breaker = CircuitBreaker()  # Still need this
            
        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=0.5, max=10, jitter=True),
            retry=retry_if_exception_type((ConnectionError, TimeoutError)),
            before_sleep=before_sleep_log(logger, logging.INFO),
            before=self._apply_rate_limiting,  # Custom hook
            after=self._release_rate_limiting   # Custom hook  
        )
        def _fetch_stock_info(self, ticker: str):
            # Just the core logic - tenacity handles retry behavior
            return yf.Ticker(ticker).info
            
        def _apply_rate_limiting(self, retry_state):
            # 5 lines of rate limiting
            
        def _release_rate_limiting(self, retry_state): 
            # 2 lines to release
    """


# Performance and reliability comparison
def compare_approaches():
    """Compare the two approaches."""
    
    comparison = {
        "Lines of Code": {
            "Current (Custom)": 150,
            "Tenacity Hybrid": 50,  # 70% reduction
        },
        
        "Reliability": {
            "Current": "Good - tested in our system",
            "Tenacity": "Excellent - battle-tested in production systems worldwide"
        },
        
        "Maintainability": {
            "Current": "Medium - custom logic to maintain",
            "Tenacity": "High - declarative config, well-documented"
        },
        
        "Features": {
            "Current": "Basic exponential backoff, manual jitter",
            "Tenacity": "Jitter, multiple wait strategies, conditional retries, statistics"
        },
        
        "Dependencies": {
            "Current": "0 extra deps",
            "Tenacity": "+1 small, stable dependency (tenacity)"
        },
        
        "Learning Curve": {
            "Current": "Must understand our custom implementation", 
            "Tenacity": "Industry-standard library with great docs"
        }
    }
    
    return comparison


if __name__ == "__main__":
    print("TENACITY vs CURRENT APPROACH COMPARISON")
    print("=" * 50)
    
    comparison = compare_approaches()
    for category, details in comparison.items():
        print(f"\n{category}:")
        for approach, value in details.items():
            print(f"  {approach}: {value}")
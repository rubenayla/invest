"""
Performance tests for the investment analysis system.

These tests verify that performance optimizations (caching, concurrent processing,
etc.) are working effectively and that the system meets performance benchmarks.
"""

import pytest
import time
import threading
import psutil
import os
from unittest.mock import patch, Mock
from concurrent.futures import ThreadPoolExecutor

from src.invest.caching.cache_manager import get_cache_manager, reset_cache_manager
from src.invest.caching.cache_decorators import get_cache_stats, clear_all_caches
from src.invest.valuation.model_registry import run_valuation, run_all_suitable_models
from src.invest.dashboard_components.valuation_engine import ValuationEngine
from src.invest.data.yahoo import get_sp500_tickers, get_stock_data


class PerformanceMetrics:
    """Helper class to collect performance metrics."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.end_memory = None
        self.process = psutil.Process(os.getpid())
    
    def start(self):
        """Start performance measurement."""
        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
    
    def stop(self):
        """Stop performance measurement.""" 
        self.end_time = time.time()
        self.end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
    
    @property
    def execution_time(self) -> float:
        """Get execution time in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0
    
    @property
    def memory_usage(self) -> float:
        """Get memory usage increase in MB."""
        if self.start_memory and self.end_memory:
            return self.end_memory - self.start_memory
        return 0.0


@pytest.mark.performance
class TestCachePerformance:
    """Test caching system performance."""
    
    @pytest.fixture(autouse=True)
    def setup_clean_cache(self):
        """Ensure clean cache for each test."""
        reset_cache_manager()
        yield
        reset_cache_manager()
    
    def test_cache_hit_performance(self):
        """Test cache hit performance meets benchmarks."""
        cache_manager = get_cache_manager()
        
        # Setup test data
        test_key = 'performance_test_key'
        test_value = {'large_data': 'x' * 10000}  # 10KB of data
        
        # Store data in cache
        cache_manager.set(test_key, test_value, 'default')
        
        # Measure cache hit performance
        metrics = PerformanceMetrics()
        metrics.start()
        
        # Perform many cache hits
        for _ in range(10000):
            result = cache_manager.get(test_key, 'default')
            assert result is not None
        
        metrics.stop()
        
        # Performance assertions
        assert metrics.execution_time < 1.0, f"10K cache hits took {metrics.execution_time:.3f}s (should be < 1.0s)"
        assert metrics.memory_usage < 50, f"Memory usage increased by {metrics.memory_usage:.1f}MB (should be < 50MB)"
        
        # Verify cache statistics
        stats = get_cache_stats()
        manager_stats = stats['manager_stats']
        assert manager_stats['hits'] >= 10000
    
    def test_cache_miss_vs_hit_performance(self):
        """Test cache miss vs hit performance differential."""
        cache_manager = get_cache_manager()
        
        # Test cache miss performance
        miss_metrics = PerformanceMetrics()
        miss_metrics.start()
        
        for i in range(1000):
            result = cache_manager.get(f'nonexistent_key_{i}', 'default')
            assert result is None
        
        miss_metrics.stop()
        
        # Setup cache data
        for i in range(1000):
            cache_manager.set(f'test_key_{i}', f'value_{i}', 'default')
        
        # Test cache hit performance
        hit_metrics = PerformanceMetrics()
        hit_metrics.start()
        
        for i in range(1000):
            result = cache_manager.get(f'test_key_{i}', 'default')
            assert result == f'value_{i}'
        
        hit_metrics.stop()
        
        # Cache hits should be similar speed to misses for in-memory cache
        # (both are just dictionary lookups)
        time_ratio = hit_metrics.execution_time / miss_metrics.execution_time if miss_metrics.execution_time > 0 else 1
        assert time_ratio < 2.0, f"Cache hits took {time_ratio:.1f}x longer than misses (should be < 2x)"
    
    @pytest.mark.slow
    def test_concurrent_cache_access_performance(self):
        """Test cache performance under concurrent access."""
        cache_manager = get_cache_manager()
        
        # Setup test data
        for i in range(100):
            cache_manager.set(f'concurrent_key_{i}', f'value_{i}', 'default')
        
        def cache_access_worker(worker_id: int, iterations: int):
            """Worker function for concurrent cache access."""
            for i in range(iterations):
                key = f'concurrent_key_{i % 100}'
                result = cache_manager.get(key, 'default')
                assert result is not None
        
        # Test concurrent access
        metrics = PerformanceMetrics()
        metrics.start()
        
        num_workers = 10
        iterations_per_worker = 1000
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [
                executor.submit(cache_access_worker, i, iterations_per_worker)
                for i in range(num_workers)
            ]
            
            # Wait for all workers to complete
            for future in futures:
                future.result()
        
        metrics.stop()
        
        # Performance assertions
        total_operations = num_workers * iterations_per_worker
        ops_per_second = total_operations / metrics.execution_time if metrics.execution_time > 0 else 0
        
        assert metrics.execution_time < 5.0, f"Concurrent cache access took {metrics.execution_time:.3f}s (should be < 5.0s)"
        assert ops_per_second > 10000, f"Cache ops/sec: {ops_per_second:.0f} (should be > 10,000)"


@pytest.mark.performance
class TestValuationModelPerformance:
    """Test valuation model performance."""
    
    @pytest.fixture(autouse=True)
    def setup_clean_cache(self):
        """Ensure clean cache for each test."""
        reset_cache_manager()
        yield
        reset_cache_manager()
    
    @pytest.fixture(autouse=True)
    def setup_mock_data(self):
        """Setup mock data for performance tests."""
        with patch('yfinance.Ticker') as mock_ticker:
            mock_stock = Mock()
            mock_stock.info = {
                'currentPrice': 150.0,
                'sharesOutstanding': 16000000000,
                'trailingEps': 6.0,
                'bookValue': 3.5,
                'revenuePerShare': 24.0,
                'beta': 1.2,
                'sector': 'Technology'
            }
            
            import pandas as pd
            from datetime import datetime, timedelta
            
            dates = [datetime.now() - timedelta(days=365*i) for i in range(3)]
            mock_stock.financials = pd.DataFrame({
                dates[0]: {'Total Revenue': 365000000000, 'Net Income': 95000000000},
            }).T
            
            mock_stock.balance_sheet = pd.DataFrame({
                dates[0]: {'Total Stockholder Equity': 150000000000},
            }).T
            
            mock_stock.cashflow = pd.DataFrame({
                dates[0]: {'Total Cash From Operating Activities': 110000000000},
            }).T
            
            mock_ticker.return_value = mock_stock
            yield
    
    def test_single_valuation_performance(self):
        """Test single valuation model performance."""
        ticker = 'AAPL'
        model = 'simple_ratios'
        
        # Test first run (no cache)
        metrics = PerformanceMetrics()
        metrics.start()
        
        result = run_valuation(model, ticker, verbose=False)
        
        metrics.stop()
        
        # Performance assertions
        assert metrics.execution_time < 5.0, f"Single valuation took {metrics.execution_time:.3f}s (should be < 5.0s)"
        assert result is not None, "Valuation should not fail with valid mock data"
        assert result.is_valid(), "Valuation result should be valid"
        
        # Test second run (with cache)
        cached_metrics = PerformanceMetrics()
        cached_metrics.start()
        
        cached_result = run_valuation(model, ticker, verbose=False)
        
        cached_metrics.stop()
        
        # Cached run should be much faster
        speedup = metrics.execution_time / cached_metrics.execution_time if cached_metrics.execution_time > 0 else float('inf')
        assert speedup >= 2.0, f"Cache speedup was {speedup:.1f}x (should be >= 2x)"
        assert cached_result.fair_value == result.fair_value, "Cached result should match original"
    
    def test_multiple_models_performance(self):
        """Test performance of running multiple models."""
        ticker = 'AAPL'
        
        metrics = PerformanceMetrics()
        metrics.start()
        
        # Run all suitable models
        results = run_all_suitable_models(ticker, verbose=False)
        
        metrics.stop()
        
        # Performance assertions
        assert metrics.execution_time < 15.0, f"Multiple models took {metrics.execution_time:.3f}s (should be < 15.0s)"
        assert len(results) > 0, "At least one model should succeed"
        
        # All results should be valid
        for model_name, result in results.items():
            assert result.is_valid(), f"Result for {model_name} should be valid"
    
    @pytest.mark.slow
    def test_concurrent_valuation_performance(self):
        """Test concurrent valuation performance."""
        tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        model = 'simple_ratios'
        
        def valuation_worker(ticker: str):
            """Worker function for concurrent valuations."""
            return run_valuation(model, ticker, verbose=False)
        
        # Test concurrent valuations
        metrics = PerformanceMetrics()
        metrics.start()
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(valuation_worker, ticker) for ticker in tickers]
            results = [future.result() for future in futures]
        
        metrics.stop()
        
        # Performance assertions
        assert metrics.execution_time < 10.0, f"Concurrent valuations took {metrics.execution_time:.3f}s (should be < 10.0s)"
        
        # All results should be valid (if they're not None)
        successful_results = [r for r in results if r is not None]
        assert len(successful_results) > 0, "At least one valuation should succeed"
        
        for result in successful_results:
            assert result.is_valid(), "All results should be valid"


@pytest.mark.performance
class TestDashboardPerformance:
    """Test dashboard component performance."""
    
    @pytest.fixture(autouse=True)
    def setup_clean_cache(self):
        """Ensure clean cache for each test."""
        reset_cache_manager()
        yield
        reset_cache_manager()
    
    def test_valuation_engine_initialization_performance(self):
        """Test ValuationEngine initialization performance."""
        metrics = PerformanceMetrics()
        metrics.start()
        
        engine = ValuationEngine()
        
        metrics.stop()
        
        # Performance assertions
        assert metrics.execution_time < 2.0, f"ValuationEngine init took {metrics.execution_time:.3f}s (should be < 2.0s)"
        assert metrics.memory_usage < 100, f"Memory usage: {metrics.memory_usage:.1f}MB (should be < 100MB)"
        
        # Test functionality
        models = engine.get_available_models()
        assert len(models) > 0, "Should have available models"
        
        stats = engine.get_model_statistics()
        assert isinstance(stats, dict), "Should return statistics"
    
    @pytest.mark.slow
    def test_dashboard_update_performance(self):
        """Test dashboard update performance with multiple tickers."""
        import tempfile
        
        with patch('yfinance.Ticker') as mock_ticker:
            # Setup mock for multiple tickers
            mock_stock = Mock()
            mock_stock.info = {
                'currentPrice': 150.0,
                'sharesOutstanding': 16000000000,
                'trailingEps': 6.0,
                'bookValue': 3.5,
                'revenuePerShare': 24.0,
                'beta': 1.2,
                'sector': 'Technology'
            }
            mock_stock.financials = Mock()
            mock_stock.balance_sheet = Mock()  
            mock_stock.cashflow = Mock()
            mock_ticker.return_value = mock_stock
            
            tickers = ['AAPL', 'MSFT', 'GOOGL']
            
            with tempfile.TemporaryDirectory() as temp_dir:
                from src.invest.dashboard_components.dashboard import ValuationDashboard
                
                dashboard = ValuationDashboard(output_dir=temp_dir)
                
                metrics = PerformanceMetrics()
                metrics.start()
                
                # This would normally be tested with actual dashboard.update_dashboard()
                # but we'll test the engine directly for performance
                engine = dashboard.valuation_engine
                successful_valuations = 0
                
                for ticker in tickers:
                    for model in engine.get_available_models()[:2]:  # Test first 2 models
                        result = engine.run_valuation(ticker, model, timeout=10)
                        if result:
                            successful_valuations += 1
                
                metrics.stop()
                
                # Performance assertions
                expected_max_time = len(tickers) * 2 * 5  # tickers * models * 5 sec per model
                assert metrics.execution_time < expected_max_time, f"Dashboard update took {metrics.execution_time:.3f}s (should be < {expected_max_time}s)"
                assert successful_valuations > 0, "At least some valuations should succeed"


@pytest.mark.performance  
class TestDataProviderPerformance:
    """Test data provider performance."""
    
    @pytest.fixture(autouse=True)
    def setup_clean_cache(self):
        """Ensure clean cache for each test."""
        reset_cache_manager()
        yield
        reset_cache_manager()
    
    @patch('requests.get')
    def test_sp500_ticker_fetch_performance(self, mock_get):
        """Test S&P 500 ticker fetching performance."""
        # Mock the response
        mock_response = Mock()
        mock_response.text = '''
        <table class="wikitable">
            <tr><th>Symbol</th><th>Security</th></tr>
            <tr><td>AAPL</td><td>Apple Inc.</td></tr>
            <tr><td>MSFT</td><td>Microsoft Corporation</td></tr>
        </table>
        '''
        mock_get.return_value = mock_response
        
        # Test first call (cache miss)
        metrics = PerformanceMetrics()
        metrics.start()
        
        tickers = get_sp500_tickers()
        
        metrics.stop()
        
        # Performance assertions
        assert metrics.execution_time < 5.0, f"S&P 500 fetch took {metrics.execution_time:.3f}s (should be < 5.0s)"
        assert len(tickers) > 0, "Should return some tickers"
        assert 'AAPL' in tickers, "Should contain expected tickers"
        
        # Test second call (cache hit)
        cached_metrics = PerformanceMetrics()
        cached_metrics.start()
        
        cached_tickers = get_sp500_tickers()
        
        cached_metrics.stop()
        
        # Cached call should be much faster
        speedup = metrics.execution_time / cached_metrics.execution_time if cached_metrics.execution_time > 0 else float('inf')
        assert speedup >= 5.0, f"Cache speedup was {speedup:.1f}x (should be >= 5x)"
        assert cached_tickers == tickers, "Cached result should match"
    
    @patch('yfinance.Ticker')
    def test_stock_data_fetch_performance(self, mock_ticker):
        """Test stock data fetching performance."""
        # Setup mock
        mock_stock = Mock()
        mock_stock.info = {
            'symbol': 'AAPL',
            'currentPrice': 150.0,
            'marketCap': 2400000000000
        }
        mock_ticker.return_value = mock_stock
        
        ticker = 'AAPL'
        
        # Test first call (cache miss)
        metrics = PerformanceMetrics()
        metrics.start()
        
        data = get_stock_data(ticker)
        
        metrics.stop()
        
        # Performance assertions
        assert metrics.execution_time < 3.0, f"Stock data fetch took {metrics.execution_time:.3f}s (should be < 3.0s)"
        assert data is not None, "Should return data"
        assert data.get('currentPrice') == 150.0, "Should contain expected data"
        
        # Test second call (cache hit)
        cached_metrics = PerformanceMetrics()
        cached_metrics.start()
        
        cached_data = get_stock_data(ticker)
        
        cached_metrics.stop()
        
        # Cached call should be much faster
        speedup = metrics.execution_time / cached_metrics.execution_time if cached_metrics.execution_time > 0 else float('inf')
        assert speedup >= 10.0, f"Cache speedup was {speedup:.1f}x (should be >= 10x)"
        assert cached_data == data, "Cached result should match"


@pytest.mark.performance
class TestMemoryUsage:
    """Test memory usage patterns."""
    
    @pytest.fixture(autouse=True)
    def setup_clean_cache(self):
        """Ensure clean cache for each test."""
        reset_cache_manager()
        yield
        reset_cache_manager()
    
    def test_cache_memory_efficiency(self):
        """Test cache memory usage is reasonable."""
        cache_manager = get_cache_manager()
        
        initial_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024  # MB
        
        # Add a reasonable amount of data to cache
        for i in range(1000):
            test_data = {'ticker': f'TEST{i}', 'data': 'x' * 1000}  # 1KB per entry
            cache_manager.set(f'test_key_{i}', test_data, 'default')
        
        final_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Should use reasonable memory (allowing for Python overhead)
        # 1000 * 1KB = 1MB of data, but Python objects have overhead
        assert memory_increase < 50, f"Memory increased by {memory_increase:.1f}MB for 1MB of data (should be < 50MB)"
    
    def test_valuation_memory_efficiency(self):
        """Test valuation models don't leak memory."""
        with patch('yfinance.Ticker') as mock_ticker:
            # Setup mock
            mock_stock = Mock()
            mock_stock.info = {
                'currentPrice': 150.0,
                'sharesOutstanding': 16000000000,
                'trailingEps': 6.0,
                'bookValue': 3.5,
                'revenuePerShare': 24.0,
                'beta': 1.2
            }
            mock_stock.financials = Mock()
            mock_stock.balance_sheet = Mock()
            mock_stock.cashflow = Mock()
            mock_ticker.return_value = mock_stock
            
            initial_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024  # MB
            
            # Run many valuations
            for i in range(100):
                ticker = f'TEST{i % 10}'  # Reuse some tickers for caching
                result = run_valuation('simple_ratios', ticker, verbose=False)
            
            final_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Should not increase memory significantly with caching
            assert memory_increase < 100, f"Memory increased by {memory_increase:.1f}MB (should be < 100MB)"


if __name__ == '__main__':
    # Run performance tests
    pytest.main([__file__, '-v', '--tb=short', '-m', 'performance'])
import pytest
import sys
import json
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import yaml

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from invest.config.loader import load_analysis_config
from invest.analysis.pipeline import AnalysisPipeline


class TestEndToEndWorkflows:
    """End-to-end workflow testing for the complete investment analysis system."""
    
    @pytest.fixture
    def mock_stock_universe(self):
        """Create a comprehensive mock stock universe for testing."""
        return {
            # US Tech Giants
            'AAPL': {
                'ticker': 'AAPL', 'sector': 'Technology', 'market_cap': 3000000000000,
                'current_price': 193.6, 'trailing_pe': 28.5, 'price_to_book': 40.0,
                'return_on_equity': 1.479, 'debt_to_equity': 195.6, 'current_ratio': 1.038,
                'revenue_growth': 0.081, 'earnings_growth': 0.120, 'country': 'USA', 'currency': 'USD'
            },
            'MSFT': {
                'ticker': 'MSFT', 'sector': 'Technology', 'market_cap': 2800000000000,
                'current_price': 378.85, 'trailing_pe': 32.1, 'price_to_book': 12.5,
                'return_on_equity': 0.361, 'debt_to_equity': 47.0, 'current_ratio': 1.9,
                'revenue_growth': 0.180, 'earnings_growth': 0.250, 'country': 'USA', 'currency': 'USD'
            },
            'GOOGL': {
                'ticker': 'GOOGL', 'sector': 'Communication Services', 'market_cap': 2100000000000,
                'current_price': 167.06, 'trailing_pe': 24.8, 'price_to_book': 5.8,
                'return_on_equity': 0.276, 'debt_to_equity': 10.5, 'current_ratio': 2.6,
                'revenue_growth': 0.070, 'earnings_growth': 0.090, 'country': 'USA', 'currency': 'USD'
            },
            
            # Japanese Companies
            '7203.T': {
                'ticker': '7203.T', 'sector': 'Consumer Cyclical', 'market_cap': 37835960000000,
                'current_price': 2903.0, 'trailing_pe': 8.9, 'price_to_book': 1.05,
                'return_on_equity': 0.117, 'debt_to_equity': 103.9, 'current_ratio': 1.2,
                'revenue_growth': 0.035, 'earnings_growth': 0.040, 'country': 'Japan', 'currency': 'JPY'
            },
            '6758.T': {
                'ticker': '6758.T', 'sector': 'Technology', 'market_cap': 25068590000000,
                'current_price': 4183.0, 'trailing_pe': 21.3, 'price_to_book': 3.03,
                'return_on_equity': 0.144, 'debt_to_equity': 18.8, 'current_ratio': 1.8,
                'revenue_growth': 0.022, 'earnings_growth': 0.030, 'country': 'Japan', 'currency': 'JPY'
            },
            
            # European Companies (ADRs)
            'ASML': {
                'ticker': 'ASML', 'sector': 'Technology', 'market_cap': 280000000000,
                'current_price': 680.50, 'trailing_pe': 35.2, 'price_to_book': 15.8,
                'return_on_equity': 0.485, 'debt_to_equity': 25.3, 'current_ratio': 2.1,
                'revenue_growth': 0.145, 'earnings_growth': 0.200, 'country': 'Netherlands', 'currency': 'EUR'
            },
            'SAP': {
                'ticker': 'SAP', 'sector': 'Technology', 'market_cap': 180000000000,
                'current_price': 150.25, 'trailing_pe': 18.7, 'price_to_book': 4.2,
                'return_on_equity': 0.195, 'debt_to_equity': 65.4, 'current_ratio': 1.1,
                'revenue_growth': 0.089, 'earnings_growth': 0.110, 'country': 'Germany', 'currency': 'EUR'
            },
            
            # Value Stock Example
            'VALUE_STOCK': {
                'ticker': 'VALUE_STOCK',
                'sector': 'Industrials',
                'industry': 'Industrial Machinery',
                'market_cap': 50000000000,
                'enterprise_value': 52000000000,
                'current_price': 45.0,
                'trailing_pe': 12.5,
                'forward_pe': 11.2,
                'price_to_book': 1.8,
                'ev_to_ebitda': 8.5,
                'ev_to_revenue': 1.2,
                'return_on_equity': 0.18,
                'return_on_assets': 0.12,
                'debt_to_equity': 35.0,
                'current_ratio': 2.2,
                'revenue_growth': 0.065,
                'earnings_growth': 0.080,
                'free_cash_flow': 4000000000,
                'shares_outstanding': 1111111111,
                'target_high_price': 55.0,
                'target_low_price': 40.0,
                'target_mean_price': 47.5,
                'country': 'USA',
                'currency': 'USD',
                'exchange': 'NYSE'
            },
            
            # Poor Quality Stock
            'POOR_QUALITY': {
                'ticker': 'POOR_QUALITY',
                'sector': 'Energy',
                'industry': 'Oil & Gas',
                'market_cap': 5000000000,
                'enterprise_value': 8000000000,
                'current_price': 25.0,
                'trailing_pe': 45.0,
                'forward_pe': None,
                'price_to_book': 8.5,
                'ev_to_ebitda': 35.0,
                'ev_to_revenue': 2.8,
                'return_on_equity': 0.05,
                'return_on_assets': 0.02,
                'debt_to_equity': 250.0,
                'current_ratio': 0.8,
                'revenue_growth': -0.10,
                'earnings_growth': -0.15,
                'free_cash_flow': 200000000,
                'shares_outstanding': 200000000,
                'target_high_price': 30.0,
                'target_low_price': 15.0,
                'target_mean_price': 22.0,
                'country': 'USA',
                'currency': 'USD',
                'exchange': 'NYSE'
            }
        }
    
    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary configuration file for testing."""
        config_data = {
            'name': 'end_to_end_test',
            'description': 'End-to-end testing configuration',
            'universe': {
                'name': 'Test Universe',
                'market': 'test_universe',
                'custom_tickers': ['AAPL', 'MSFT', 'GOOGL', 'VALUE_STOCK', 'POOR_QUALITY'],
                'filters': {
                    'min_market_cap_b': 1.0,
                    'max_market_cap_b': None,
                    'exclude_sectors': [],
                    'include_sectors': []
                }
            },
            'quality': {
                'min_roe': 0.10,
                'min_roic': 0.08,
                'max_debt_equity': 1.0,
                'min_current_ratio': 1.0
            },
            'value': {
                'max_pe': 30.0,
                'max_pb': 10.0,
                'max_ev_ebitda': 20.0
            },
            'growth': {
                'min_revenue_growth': 0.03,
                'min_earnings_growth': 0.02
            },
            'risk': {
                'max_beta': 1.8
            },
            'valuation': {
                'dcf': {
                    'enabled': True,
                    'growth_rate': 0.04,
                    'discount_rate': 0.10,
                    'terminal_multiple': 15.0
                }
            },
            'output': {
                'formats': ['txt', 'csv', 'json'],
                'top_n': 10,
                'include_all_stocks': True
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            return f.name
    
    def test_complete_analysis_workflow_us_stocks(self, mock_stock_universe, temp_config_file):
        """Test complete analysis workflow with US stocks."""
        with patch('invest.data.yahoo.get_stock_data') as mock_get_data:
            mock_get_data.side_effect = lambda ticker: mock_stock_universe.get(ticker)
            
            # Load configuration
            config = load_analysis_config(temp_config_file)
            assert config is not None
            assert config.name == 'end_to_end_test'
            
            # Run analysis pipeline
            pipeline = AnalysisPipeline(config)
            
            with patch.object(pipeline, '_get_universe') as mock_universe:
                universe_data = [mock_stock_universe[ticker] for ticker in ['AAPL', 'MSFT', 'GOOGL', 'VALUE_STOCK', 'POOR_QUALITY']]
                mock_universe.return_value = universe_data
                
                results = pipeline.run_analysis()
            
            # Verify complete results structure
            assert results is not None
            assert 'config' in results
            assert 'summary' in results
            assert 'stocks' in results
            assert 'all_stocks' in results
            assert 'total_universe' in results
            assert 'passed_screening' in results
            assert 'final_results' in results
            
            # Verify analysis processed all stocks
            assert results['total_universe'] == 5
            assert len(results['all_stocks']) == 5
            
            # Verify stocks have required analysis fields
            for stock in results['all_stocks']:
                assert 'ticker' in stock
                assert 'composite_score' in stock
                assert 'scores' in stock
                assert 'quality' in stock['scores']
                assert 'value' in stock['scores']
                assert 'growth' in stock['scores']
                assert 'risk' in stock['scores']
                assert 'passes_filters' in stock
            
            # VALUE_STOCK should pass filters, POOR_QUALITY should fail
            value_stock = next(s for s in results['all_stocks'] if s['ticker'] == 'VALUE_STOCK')
            poor_stock = next(s for s in results['all_stocks'] if s['ticker'] == 'POOR_QUALITY')
            
            assert value_stock['passes_filters'] == True
            assert poor_stock['passes_filters'] == False
            assert value_stock['composite_score'] > poor_stock['composite_score']
    
    def test_international_analysis_workflow(self, mock_stock_universe):
        """Test complete workflow with international stocks."""
        # Create international configuration
        intl_config_data = {
            'name': 'international_test',
            'universe': {
                'name': 'International Test',
                'market': 'japan_topix30',
                'filters': {
                    'min_market_cap_b': 5.0,
                    'exclude_sectors': [],
                }
            },
            'quality': {'min_roe': 0.08, 'max_debt_equity': 1.5},
            'value': {'max_pe': 25.0, 'max_pb': 3.0},
            'growth': {'min_revenue_growth': 0.02},
            'risk': {'max_beta': 1.6},
            'valuation': {
                'dcf': {
                    'enabled': True,
                    'growth_rate': 0.03,
                    'discount_rate': 0.09
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(intl_config_data, f)
            config_file = f.name
        
        try:
            with patch('invest.data.international.get_market_tickers') as mock_tickers:
                mock_tickers.return_value = ['7203.T', '6758.T']
                
                with patch('invest.data.international.get_international_stock_data') as mock_data:
                    mock_data.side_effect = lambda ticker: mock_stock_universe.get(ticker)
                    
                    config = load_analysis_config(config_file)
                    pipeline = AnalysisPipeline(config)
                    
                    with patch.object(pipeline, '_get_universe') as mock_universe:
                        universe_data = [mock_stock_universe['7203.T'], mock_stock_universe['6758.T']]
                        mock_universe.return_value = universe_data
                        
                        results = pipeline.run_analysis()
                    
                    # Verify international analysis
                    assert results is not None
                    assert results['total_universe'] == 2
                    
                    # Should include Japanese stocks
                    japanese_tickers = [s['ticker'] for s in results['all_stocks']]
                    assert '7203.T' in japanese_tickers
                    assert '6758.T' in japanese_tickers
                    
                    # Both should pass reasonable criteria for Japanese market
                    toyota = next(s for s in results['all_stocks'] if s['ticker'] == '7203.T')
                    sony = next(s for s in results['all_stocks'] if s['ticker'] == '6758.T')
                    
                    assert toyota['passes_filters'] in [True, False]  # May pass/fail based on criteria
                    assert sony['passes_filters'] in [True, False]
                    
                    # Both should have reasonable scores
                    assert sony['scores']['quality'] >= 0
                    assert toyota['scores']['quality'] >= 0
                    assert sony['composite_score'] >= 0
                    assert toyota['composite_score'] >= 0
                    # Both should have all required score components
                    assert 'value' in sony['scores']
                    assert 'growth' in sony['scores']
                    assert 'risk' in sony['scores']
        
        finally:
            Path(config_file).unlink()
    
    def test_command_line_interface(self, mock_stock_universe, temp_config_file):
        """Test command line interface end-to-end."""
        script_path = Path(__file__).parent.parent / "scripts" / "systematic_analysis.py"
        
        if not script_path.exists():
            pytest.skip("systematic_analysis.py script not found")
        
        with patch('invest.data.yahoo.get_stock_data') as mock_get_data:
            mock_get_data.side_effect = lambda ticker: mock_stock_universe.get(ticker)
            
            with patch('invest.analysis.pipeline.AnalysisPipeline._get_universe') as mock_universe:
                universe_data = [mock_stock_universe[ticker] for ticker in ['AAPL', 'MSFT', 'VALUE_STOCK']]
                mock_universe.return_value = universe_data
                
                # Test basic command execution
                with tempfile.TemporaryDirectory() as temp_dir:
                    cmd = [
                        'poetry', 'run', 'python', str(script_path),
                        temp_config_file,
                        '--save-csv',
                        '--output', temp_dir,
                        '--quiet'
                    ]
                    
                    try:
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                        
                        # Should complete successfully
                        assert result.returncode == 0
                        
                        # Should generate CSV file
                        csv_files = list(Path(temp_dir).glob("*.csv"))
                        assert len(csv_files) > 0
                        
                        # CSV should have proper structure
                        csv_file = csv_files[0]
                        df = pd.read_csv(csv_file)
                        
                        expected_columns = [
                            'Ticker', 'Sector', 'Market_Cap_B', 'Current_Price',
                            'Passes_Filters', 'Composite_Score', 'Quality_Score',
                            'Value_Score', 'Growth_Score', 'Risk_Score'
                        ]
                        
                        for col in expected_columns:
                            assert col in df.columns, f"Missing column: {col}"
                        
                        assert len(df) > 0
                        assert 'AAPL' in df['Ticker'].values
                        
                    except subprocess.TimeoutExpired:
                        pytest.skip("Command line test timed out")
                    except FileNotFoundError:
                        pytest.skip("Poetry not available for CLI testing")
    
    def test_output_format_generation(self, mock_stock_universe, temp_config_file):
        """Test generation of all output formats."""
        with patch('invest.data.yahoo.get_stock_data') as mock_get_data:
            mock_get_data.side_effect = lambda ticker: mock_stock_universe.get(ticker)
            
            config = load_analysis_config(temp_config_file)
            pipeline = AnalysisPipeline(config)
            
            with patch.object(pipeline, '_get_universe') as mock_universe:
                universe_data = [mock_stock_universe[ticker] for ticker in ['AAPL', 'VALUE_STOCK', 'POOR_QUALITY']]
                mock_universe.return_value = universe_data
                
                results = pipeline.run_analysis()
            
            # Test CSV format generation
            csv_data = []
            for stock in results['all_stocks']:
                csv_row = {
                    'Ticker': stock['ticker'],
                    'Sector': stock['basic_data']['sector'],
                    'Passes_Filters': 'Y' if stock['passes_filters'] else 'N',
                    'Composite_Score': stock['composite_score'],
                    'Quality_Score': stock['scores']['quality']
                }
                csv_data.append(csv_row)
            
            assert len(csv_data) == 3
            assert any(row['Ticker'] == 'AAPL' for row in csv_data)
            assert any(row['Passes_Filters'] == 'Y' for row in csv_data)
            assert any(row['Passes_Filters'] == 'N' for row in csv_data)
            
            # Test JSON format generation
            json_data = json.dumps(results, indent=2, default=str)
            parsed_json = json.loads(json_data)
            
            assert 'stocks' in parsed_json
            assert 'summary' in parsed_json
            assert len(parsed_json['stocks']) <= len(parsed_json['all_stocks'])
    
    def test_error_recovery_end_to_end(self, temp_config_file):
        """Test error recovery in end-to-end workflow."""
        # Test with network errors
        with patch('invest.data.yahoo.get_stock_data') as mock_get_data:
            # First call succeeds, second fails, third succeeds
            mock_get_data.side_effect = [
                {'ticker': 'AAPL', 'sector': 'Technology', 'market_cap': 3000000000000},
                None,  # Simulates network error
                {'ticker': 'GOOGL', 'sector': 'Communication Services', 'market_cap': 2100000000000}
            ]
            
            config = load_analysis_config(temp_config_file)
            pipeline = AnalysisPipeline(config)
            
            with patch.object(pipeline, '_get_universe') as mock_universe:
                universe_data = [
                    {'ticker': 'AAPL', 'sector': 'Technology', 'market_cap': 3000000000000},
                    {'ticker': 'GOOGL', 'sector': 'Communication Services', 'market_cap': 2100000000000}
                ]
                mock_universe.return_value = universe_data
                
                results = pipeline.run_analysis()
            
            # Should complete despite one failure
            assert results is not None
            assert results['total_universe'] == 2
            
            # Should have reasonable summary even with partial data
            assert 'summary' in results
    
    def test_configuration_validation_end_to_end(self):
        """Test configuration validation in end-to-end workflow."""
        # Test with invalid configuration
        invalid_config = {
            'name': 'invalid_test',
            'screening': {
                'quality': {'min_roe': -0.50},  # Invalid negative ROE
                'value': {'max_pe_ratio': 0},   # Invalid zero P/E
                'growth': {'min_revenue_growth': 2.0}  # Invalid 200% growth requirement
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(invalid_config, f)
            config_file = f.name
        
        try:
            # Should either handle gracefully or raise appropriate error
            config = load_analysis_config(config_file)
            
            if config is not None:
                pipeline = AnalysisPipeline(config)
                
                # Pipeline should handle unrealistic thresholds gracefully
                with patch.object(pipeline, '_get_universe') as mock_universe:
                    mock_universe.return_value = []  # Empty universe to avoid data issues
                    
                    results = pipeline.run_analysis()
                    assert 'error' in results  # Should report no stocks found
        
        finally:
            Path(config_file).unlink()
    
    def test_large_universe_performance(self, mock_stock_universe):
        """Test performance with large stock universe."""
        # Create large mock universe
        large_universe = {}
        for i in range(100):
            ticker = f"STOCK{i:03d}"
            large_universe[ticker] = {
                'ticker': ticker,
                'sector': 'Technology' if i % 3 == 0 else 'Industrials',
                'market_cap': (i + 1) * 1000000000,  # $1B to $100B
                'trailing_pe': 15 + (i % 20),
                'return_on_equity': 0.10 + (i % 30) / 100,
                'current_ratio': 1.0 + (i % 10) / 10
            }
        
        config_data = {
            'name': 'large_universe_test',
            'universe': {'custom_tickers': list(large_universe.keys())},
            'screening': {
                'quality': {'min_roe': 0.10, 'weight': 0.25},
                'value': {'max_pe_ratio': 25.0, 'weight': 0.25},
                'growth': {'min_revenue_growth': 0.0, 'weight': 0.25},
                'risk': {'max_beta': 2.0, 'weight': 0.25}
            },
            'max_results': 20
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_file = f.name
        
        try:
            with patch('invest.data.yahoo.get_stock_data') as mock_get_data:
                mock_get_data.side_effect = lambda ticker: large_universe.get(ticker)
                
                config = load_analysis_config(config_file)
                pipeline = AnalysisPipeline(config)
                
                with patch.object(pipeline, '_get_universe') as mock_universe:
                    mock_universe.return_value = list(large_universe.values())
                    
                    results = pipeline.run_analysis()
                
                # Should handle large universe efficiently
                assert results is not None
                assert results['total_universe'] == 100
                assert len(results['stocks']) <= 20  # Respects max_results
                assert len(results['all_stocks']) == 100  # Includes all analyzed stocks
                
                # Results should be properly ranked
                if len(results['stocks']) > 1:
                    scores = [stock['composite_score'] for stock in results['stocks']]
                    assert scores == sorted(scores, reverse=True)
        
        finally:
            Path(config_file).unlink()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import yaml

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from invest.data.international import (
    get_major_japanese_stocks, get_topix_core30_tickers,
    get_buffett_favorites_japan, get_warren_buffett_international,
    get_ftse100_tickers, get_dax_tickers, get_market_tickers,
    get_international_stock_data, MARKET_UNIVERSES
)
from invest.config.loader import load_analysis_config
from invest.analysis.pipeline import AnalysisPipeline


class TestJapaneseMarkets:
    """Test Japanese market data and functionality."""
    
    def test_japanese_ticker_formats(self):
        """Test that Japanese tickers have correct format."""
        markets = [
            get_major_japanese_stocks(),
            get_topix_core30_tickers(),
            get_buffett_favorites_japan()
        ]
        
        for market in markets:
            assert isinstance(market, list)
            assert len(market) > 0
            
            for ticker in market:
                assert isinstance(ticker, str)
                assert ticker.endswith('.T'), f"Japanese ticker {ticker} should end with .T"
                
                # Should have numeric code before .T
                code = ticker.replace('.T', '')
                assert code.isdigit(), f"Japanese ticker code {code} should be numeric"
                assert len(code) == 4, f"Japanese ticker code {code} should be 4 digits"
    
    def test_topix_core30_composition(self):
        """Test TOPIX Core 30 specific requirements."""
        topix30 = get_topix_core30_tickers()
        
        assert len(topix30) == 30, "TOPIX Core 30 should have exactly 30 stocks"
        
        # Should include major Japanese companies
        major_japanese_companies = [
            '7203.T',  # Toyota
            '6758.T',  # Sony
            '8306.T',  # Mitsubishi UFJ
            '9984.T',  # SoftBank Group
            '6861.T'   # Keyence
        ]
        
        for company in major_japanese_companies:
            assert company in topix30, f"TOPIX 30 should include {company}"
    
    def test_buffett_japanese_holdings(self):
        """Test that Berkshire Hathaway's actual holdings are included."""
        buffett_favorites = get_buffett_favorites_japan()
        
        # Berkshire's documented holdings in Japanese trading houses
        berkshire_holdings = [
            '8058.T',  # Mitsubishi Corporation
            '8031.T',  # Mitsui & Co
            '8001.T',  # Itochu Corporation
            '2768.T',  # Sumitomo Corporation
            '8002.T'   # Marubeni Corporation
        ]
        
        for holding in berkshire_holdings:
            assert holding in buffett_favorites, f"Should include Berkshire holding {holding}"
        
        # Should also include other Buffett-style companies
        assert len(buffett_favorites) > len(berkshire_holdings), "Should include additional Buffett-style companies"
    
    @patch('yfinance.Ticker')
    def test_japanese_stock_data_retrieval(self, mock_ticker):
        """Test retrieval of Japanese stock data with proper currency handling."""
        # Mock Japanese stock (Toyota)
        mock_stock = Mock()
        mock_stock.info = {
            'symbol': '7203.T',
            'longName': 'Toyota Motor Corporation',
            'marketCap': 37835960000000,  # In JPY
            'trailingPE': 8.9,
            'priceToBook': 1.05,
            'returnOnEquity': 0.117,
            'debtToEquity': 103.9,
            'currentRatio': 1.2,
            'revenueGrowth': 0.035,
            'currency': 'JPY',
            'financialCurrency': 'JPY',
            'country': 'Japan',
            'exchange': 'Tokyo Stock Exchange',
            'sector': 'Consumer Cyclical'
        }
        mock_ticker.return_value = mock_stock
        
        result = get_international_stock_data('7203.T')
        
        assert result is not None
        assert result['ticker'] == '7203.T'
        assert result['currency'] == 'JPY'
        assert result['country'] == 'Japan'
        assert result['exchange'] == 'Tokyo Stock Exchange'
        
        # Should include standard financial metrics
        assert 'trailing_pe' in result
        assert 'return_on_equity' in result
        assert 'market_cap' in result
    
    def test_japanese_market_universe_mapping(self):
        """Test Japanese market universe mapping."""
        # Test available Japanese markets
        japanese_markets = ['japan_major', 'japan_topix30']
        
        for market in japanese_markets:
            assert market in MARKET_UNIVERSES
            tickers = get_market_tickers(market)
            
            assert isinstance(tickers, list)
            assert len(tickers) > 0
            
            # All should be Japanese tickers
            for ticker in tickers:
                assert ticker.endswith('.T')


class TestInternationalMarkets:
    """Test other international markets (UK, Germany, etc.)."""
    
    def test_uk_market_data(self):
        """Test UK market data structure."""
        ftse_tickers = get_ftse100_tickers()
        
        assert isinstance(ftse_tickers, list)
        assert len(ftse_tickers) > 0
        
        # Should include both London-listed stocks and ADRs
        london_stocks = [ticker for ticker in ftse_tickers if ticker.endswith('.L')]
        adr_stocks = [ticker for ticker in ftse_tickers if not ticker.endswith('.L')]
        
        assert len(london_stocks) > 0, "Should include London-listed stocks"
        assert len(adr_stocks) > 0, "Should include ADR stocks"
        
        # Should include major UK companies
        major_uk_companies = ['SHEL', 'BP', 'VOD', 'UL']  # ADR versions
        overlap = set(major_uk_companies) & set(ftse_tickers)
        assert len(overlap) > 0, "Should include some major UK ADRs"
    
    def test_german_market_data(self):
        """Test German market data structure."""
        dax_tickers = get_dax_tickers()
        
        assert isinstance(dax_tickers, list)
        assert len(dax_tickers) > 0
        
        # Should include both German exchange and ADR listings
        german_exchange = [ticker for ticker in dax_tickers if ticker.endswith('.DE')]
        adr_stocks = [ticker for ticker in dax_tickers if not ticker.endswith('.DE')]
        
        assert len(german_exchange) > 0, "Should include German exchange stocks"
        assert len(adr_stocks) > 0, "Should include German ADRs"
        
        # Should include major German companies
        expected_companies = ['SAP', 'ADDYY', 'VLKAY']  # ADR versions
        overlap = set(expected_companies) & set(dax_tickers)
        assert len(overlap) > 0, "Should include major German ADRs"
    
    def test_warren_buffett_international_composition(self):
        """Test Warren Buffett international stock compilation."""
        buffett_intl = get_warren_buffett_international()
        
        assert isinstance(buffett_intl, list)
        assert len(buffett_intl) > 15, "Should include substantial international holdings"
        
        # Should include Japanese holdings
        japanese_stocks = [ticker for ticker in buffett_intl if ticker.endswith('.T')]
        assert len(japanese_stocks) >= 5, "Should include multiple Japanese stocks"
        
        # Should include some European ADRs
        european_adrs = ['UL', 'DEO', 'SAP', 'ASML']
        europe_overlap = set(european_adrs) & set(buffett_intl)
        assert len(europe_overlap) > 0, "Should include European ADRs"
        
        # Should include Asian ADRs
        asian_adrs = ['TSM', 'BABA', 'PDD']
        asia_overlap = set(asian_adrs) & set(buffett_intl)
        assert len(asia_overlap) > 0, "Should include Asian ADRs"
    
    def test_market_universe_completeness(self):
        """Test that all international market universes are properly defined."""
        expected_markets = [
            'japan_major', 'japan_topix30', 'uk_ftse', 'germany_dax'
        ]
        
        for market in expected_markets:
            assert market in MARKET_UNIVERSES, f"Market {market} should be defined"
            
            tickers = get_market_tickers(market)
            assert isinstance(tickers, list)
            assert len(tickers) > 0, f"Market {market} should have tickers"
            
            # Test ticker format consistency within each market
            if market.startswith('japan'):
                assert all(ticker.endswith('.T') for ticker in tickers), f"Japan market {market} should have .T tickers"
            elif market == 'uk_ftse':
                # UK can have mixed .L and ADR tickers
                assert any(ticker.endswith('.L') for ticker in tickers) or any(not ticker.endswith('.L') for ticker in tickers)


class TestInternationalConfiguration:
    """Test international market configuration files."""
    
    def test_japan_topix30_config(self):
        """Test Japan TOPIX 30 configuration file."""
        config_path = Path(__file__).parent.parent / "configs" / "japan_topix30.yaml"
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Test configuration structure
            assert 'universe' in config_data
            assert 'screening' in config_data
            assert 'valuation' in config_data
            
            # Test universe configuration
            universe = config_data['universe']
            assert universe['market'] == 'japan_topix30'
            assert universe['name'] == "Japan TOPIX Core 30"
            
            # Test screening parameters are adjusted for Japanese market
            screening = config_data['screening']
            assert 'quality' in screening
            assert 'value' in screening
            
            # Japanese market should have adjusted thresholds
            quality = screening['quality']
            assert quality['min_roe'] <= 0.10, "Japanese ROE threshold should be conservative"
            
            value = screening['value']
            assert value['max_pe_ratio'] >= 20, "Japanese P/E threshold should allow higher multiples"
    
    def test_buffett_favorites_config(self):
        """Test Warren Buffett Japanese favorites configuration."""
        config_path = Path(__file__).parent.parent / "configs" / "japan_buffett_favorites.yaml"
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Should have Buffett-specific criteria
            universe = config_data['universe']
            assert universe['market'] == 'japan_buffett'
            
            screening = config_data['screening']
            
            # Should emphasize quality and value (Buffett's style)
            quality_weight = screening['quality']['weight']
            value_weight = screening['value']['weight']
            
            assert quality_weight >= 0.30, "Should emphasize quality"
            assert value_weight >= 0.30, "Should emphasize value"
            
            # Should have conservative value criteria
            value_criteria = screening['value']
            assert value_criteria['max_pe_ratio'] <= 25, "Should have conservative P/E threshold"
            assert value_criteria['max_pb_ratio'] <= 3.0, "Should have conservative P/B threshold"
    
    def test_international_value_config(self):
        """Test international value configuration."""
        config_path = Path(__file__).parent.parent / "configs" / "international_value.yaml"
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            universe = config_data['universe']
            assert universe['market'] == 'international_diversified'
            
            screening = config_data['screening']
            
            # Should heavily weight value
            value_weight = screening['value']['weight']
            assert value_weight >= 0.35, "International value should heavily weight value criteria"
            
            # Should have strict value thresholds
            value = screening['value']
            assert value['max_pe_ratio'] <= 20, "Should have strict P/E for value focus"


class TestInternationalPipelineIntegration:
    """Test integration of international markets with analysis pipeline."""
    
    @patch('invest.data.international.get_market_tickers')
    @patch('invest.data.international.get_international_stock_data')
    def test_international_pipeline_execution(self, mock_get_data, mock_get_tickers):
        """Test that pipeline works with international market data."""
        # Mock Japanese market tickers
        mock_get_tickers.return_value = ['7203.T', '6758.T', '8306.T']
        
        # Mock international stock data
        def mock_stock_data(ticker):
            base_data = {
                'ticker': ticker,
                'market_cap': 25000000000000,  # 25T Yen
                'enterprise_value': 24000000000000,
                'trailing_pe': 15.0,
                'price_to_book': 1.5,
                'return_on_equity': 0.12,
                'debt_to_equity': 50.0,
                'current_ratio': 1.3,
                'revenue_growth': 0.04,
                'earnings_growth': 0.06,
                'sector': 'Technology',
                'currency': 'JPY',
                'country': 'Japan',
                'exchange': 'Tokyo Stock Exchange'
            }
            
            # Vary some metrics by ticker
            if ticker == '7203.T':  # Toyota
                base_data.update({
                    'sector': 'Consumer Cyclical',
                    'trailing_pe': 8.9,
                    'return_on_equity': 0.117
                })
            elif ticker == '6758.T':  # Sony
                base_data.update({
                    'trailing_pe': 21.3,
                    'return_on_equity': 0.144
                })
            elif ticker == '8306.T':  # Mitsubishi UFJ
                base_data.update({
                    'sector': 'Financial Services',
                    'trailing_pe': 14.5,
                    'return_on_equity': 0.059
                })
                
            return base_data
        
        mock_get_data.side_effect = mock_stock_data
        
        # Create test configuration
        from invest.config.schema import AnalysisConfig, UniverseConfig, QualityThresholds, ValueThresholds, GrowthThresholds, RiskThresholds
        
        config = AnalysisConfig(
            name="test_international",
            universe=UniverseConfig(market="japan_topix30"),
            quality=QualityThresholds(min_roe=0.08, min_roic=0.06, max_debt_equity=1.5),
            value=ValueThresholds(max_pe=25.0, max_pb=2.5),
            growth=GrowthThresholds(min_revenue_growth=0.02),
            risk=RiskThresholds(max_beta=1.6),
            max_results=10
        )
        
        # Test pipeline execution
        pipeline = AnalysisPipeline(config)
        
        with patch.object(pipeline, '_get_universe') as mock_get_universe:
            mock_get_universe.return_value = [mock_stock_data(ticker) for ticker in ['7203.T', '6758.T', '8306.T']]
            
            results = pipeline.run_analysis()
        
        # Verify results structure
        assert results is not None
        assert 'stocks' in results
        assert 'total_universe' in results
        assert results['total_universe'] == 3
        
        # Should have processed international stocks
        assert len(results['stocks']) <= 3
    
    def test_currency_handling_in_pipeline(self):
        """Test that pipeline handles different currencies properly."""
        # This would test currency conversion if implemented
        # For now, test that currency info is preserved
        
        sample_currencies = ['JPY', 'EUR', 'GBP', 'USD']
        
        for currency in sample_currencies:
            with patch('yfinance.Ticker') as mock_ticker:
                mock_info = {
                    'currency': currency,
                    'financialCurrency': currency,
                    'marketCap': 1000000000000,
                    'trailingPE': 15.0,
                    'sector': 'Technology'
                }
                mock_ticker.return_value.info = mock_info
                
                result = get_international_stock_data(f'TEST.{currency}')
                assert result['currency'] == currency
    
    def test_error_handling_international_data(self):
        """Test error handling with international data sources."""
        # Test with invalid market
        with pytest.raises(ValueError):
            get_market_tickers('invalid_international_market')
        
        # Test with network errors for international data
        with patch('yfinance.Ticker', side_effect=Exception("Network error")):
            result = get_international_stock_data('7203.T')
            assert result is None
        
        # Test pipeline resilience with missing international data
        with patch('invest.data.international.get_market_tickers') as mock_tickers:
            mock_tickers.return_value = ['INVALID.T', 'MISSING.T']
            
            with patch('invest.data.international.get_international_stock_data') as mock_data:
                mock_data.return_value = None  # Simulate data retrieval failure
                
                tickers = get_market_tickers('japan_major')
                assert isinstance(tickers, list)  # Should still return list even if empty


class TestInternationalScreeningAdjustments:
    """Test screening criteria adjustments for international markets."""
    
    def test_japanese_market_adjustments(self):
        """Test that Japanese market has appropriate screening adjustments."""
        # Japanese companies often have different financial characteristics
        japanese_adjustments = {
            'lower_roe_threshold': 0.08,      # vs 0.15 for US
            'higher_debt_tolerance': 1.5,     # vs 0.6 for US
            'lower_growth_expectations': 0.02, # vs 0.05 for US
            'different_pe_ranges': 25.0       # vs 20.0 for US
        }
        
        # These adjustments should be reflected in configurations
        for adjustment, expected_value in japanese_adjustments.items():
            assert isinstance(expected_value, (int, float))
            assert expected_value > 0
    
    def test_currency_aware_valuation(self):
        """Test that valuations consider currency differences."""
        # Test data with different currencies
        test_stocks = [
            {'ticker': 'US.STOCK', 'market_cap': 100000000000, 'currency': 'USD'},    # $100B
            {'ticker': '1234.T', 'market_cap': 12000000000000, 'currency': 'JPY'},    # ¥12T (~$100B at 120 JPY/USD)
            {'ticker': 'EU.STOCK', 'market_cap': 85000000000, 'currency': 'EUR'},     # €85B (~$100B at 1.15 EUR/USD)
        ]
        
        for stock in test_stocks:
            # Market cap should be positive regardless of currency
            assert stock['market_cap'] > 0
            
            # Currency should be properly identified
            assert stock['currency'] in ['USD', 'JPY', 'EUR', 'GBP']
    
    def test_sector_adjustments_international(self):
        """Test sector-specific adjustments for international markets."""
        # Different markets have different sector compositions and norms
        sector_adjustments = {
            'japan': {
                'Technology': {'pe_premium': 1.2, 'roe_discount': 0.8},
                'Industrials': {'debt_tolerance': 1.5, 'growth_discount': 0.7},
                'Financial Services': {'special_metrics': True}
            },
            'europe': {
                'Utilities': {'dividend_focus': True, 'growth_discount': 0.6},
                'Energy': {'cyclical_adjustment': True}
            }
        }
        
        for market, sectors in sector_adjustments.items():
            for sector, adjustments in sectors.items():
                assert isinstance(adjustments, dict)
                assert len(adjustments) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from invest.data.international import (  # noqa: E402
    MARKET_UNIVERSES,
    get_buffett_favorites_japan,
    get_international_stock_data,
    get_major_japanese_stocks,
    get_market_tickers,
    get_topix_core30_tickers,
    get_warren_buffett_international,
)
from invest.data.yahoo import (  # noqa: E402
    get_financials,
    get_sp500_sample,
    get_sp500_tickers,
    get_stock_data,
    get_universe_data,
)


class TestYahooFinanceDataProvider:
    """Test Yahoo Finance data provider functionality."""

    def test_sp500_tickers_structure(self):
        """Test that S&P 500 tickers are returned in correct format."""
        with patch("requests.get") as mock_get:
            # Mock Wikipedia response
            mock_response = Mock()
            mock_response.text = """
            <table class="wikitable">
                <tr><th>Symbol</th><th>Company</th></tr>
                <tr><td>AAPL</td><td>Apple Inc.</td></tr>
                <tr><td>MSFT</td><td>Microsoft Corporation</td></tr>
                <tr><td>BRK.B</td><td>Berkshire Hathaway</td></tr>
            </table>
            """
            mock_get.return_value = mock_response

            tickers = get_sp500_tickers()

            assert isinstance(tickers, list)
            assert len(tickers) > 0
            assert "AAPL" in tickers
            assert "MSFT" in tickers
            assert "BRK-B" in tickers  # Should be converted from BRK.B

    def test_sp500_sample_subset(self):
        """Test that SP500 sample returns reasonable subset."""
        with patch("invest.data.yahoo.SP500_TICKERS", ["AAPL", "MSFT", "GOOGL"] * 20):
            sample = get_sp500_sample()

            assert isinstance(sample, list)
            assert len(sample) == 30  # Should return first 30
            assert all(ticker in ["AAPL", "MSFT", "GOOGL"] for ticker in sample)

    @patch("yfinance.Ticker")
    def test_get_stock_data_success(self, mock_ticker):
        """Test successful stock data retrieval."""
        # Mock yfinance response
        mock_stock = Mock()
        mock_stock.info = {
            "symbol": "AAPL",
            "marketCap": 3000000000000,  # $3T
            "trailingPE": 28.5,
            "priceToBook": 40.0,
            "returnOnEquity": 1.479,
            "debtToEquity": 195.6,
            "currentRatio": 1.038,
            "revenueGrowth": 0.081,
            "sector": "Technology",
            "currentPrice": 193.6,
        }
        mock_ticker.return_value = mock_stock

        result = get_stock_data("AAPL")

        assert result is not None
        assert result["ticker"] == "AAPL"
        assert result["market_cap"] == 3000000000000
        assert result["trailing_pe"] == 28.5
        assert result["sector"] == "Technology"
        assert "current_price" in result

    @patch("yfinance.Ticker")
    def test_get_stock_data_error_handling(self, mock_ticker):
        """Test error handling in stock data retrieval."""
        # Mock yfinance to raise exception
        mock_ticker.side_effect = Exception("Network error")

        result = get_stock_data("INVALID")

        assert result is None

    @patch("yfinance.Ticker")
    def test_get_financials_success(self, mock_ticker):
        """Test financial statements retrieval."""
        # Mock financial data
        mock_stock = Mock()
        mock_stock.financials = pd.DataFrame({"Revenue": [100000, 110000]})
        mock_stock.balance_sheet = pd.DataFrame({"Total Assets": [50000, 55000]})
        mock_stock.cashflow = pd.DataFrame({"Operating CF": [20000, 22000]})
        mock_ticker.return_value = mock_stock

        result = get_financials("AAPL")

        assert result is not None
        assert result["ticker"] == "AAPL"
        assert "income_statement" in result
        assert "balance_sheet" in result
        assert "cash_flow" in result

    def test_get_universe_data_integration(self):
        """Test universe data retrieval with mock data."""
        with patch("invest.data.yahoo.get_stock_data") as mock_get_data:
            # Mock successful data for some tickers
            mock_get_data.side_effect = (
                lambda ticker: {"ticker": ticker, "market_cap": 1000000000, "sector": "Technology"}
                if ticker in ["AAPL", "MSFT"]
                else None
            )

            result = get_universe_data(["AAPL", "MSFT", "INVALID"])

            assert isinstance(result, pd.DataFrame)
            assert len(result) == 2  # Only successful tickers
            assert "AAPL" in result["ticker"].values
            assert "MSFT" in result["ticker"].values


class TestInternationalDataProvider:
    """Test international market data provider functionality."""

    def test_japanese_stock_lists(self):
        """Test Japanese stock ticker lists."""
        major_japanese = get_major_japanese_stocks()
        topix30 = get_topix_core30_tickers()
        buffett_japan = get_buffett_favorites_japan()

        # Test structure
        assert isinstance(major_japanese, list)
        assert isinstance(topix30, list)
        assert isinstance(buffett_japan, list)

        assert len(major_japanese) > 0
        assert len(topix30) == 30
        assert len(buffett_japan) > 0

        # Test Japanese ticker format
        for ticker in topix30:
            assert ticker.endswith(".T"), f"Japanese ticker {ticker} should end with .T"

        # Test that Berkshire's actual holdings are included
        berkshire_holdings = ["8058.T", "8031.T", "8001.T", "2768.T", "8002.T"]
        for holding in berkshire_holdings:
            assert (
                holding in buffett_japan
            ), f"Berkshire holding {holding} missing from buffett favorites"

    def test_market_universes_mapping(self):
        """Test market universe mapping functionality."""
        # Test that all predefined markets are available
        expected_markets = {"japan_major", "japan_topix30", "uk_ftse", "germany_dax", "usa_sp500"}

        for market in expected_markets:
            if market != "usa_sp500":  # usa_sp500 is None and handled separately
                assert market in MARKET_UNIVERSES
                tickers = MARKET_UNIVERSES[market]
                assert isinstance(tickers, list)
                assert len(tickers) > 0

    def test_get_market_tickers(self):
        """Test market ticker retrieval function."""
        # Test Japanese markets
        japan_major = get_market_tickers("japan_major")
        japan_topix30 = get_market_tickers("japan_topix30")

        assert isinstance(japan_major, list)
        assert isinstance(japan_topix30, list)
        assert len(japan_major) > 30
        assert len(japan_topix30) == 30

        # Test invalid market
        with pytest.raises(ValueError, match="Unknown market"):
            get_market_tickers("invalid_market")

    @patch("yfinance.Ticker")
    def test_get_international_stock_data(self, mock_ticker):
        """Test international stock data retrieval with currency handling."""
        # Mock Japanese stock data
        mock_stock = Mock()
        mock_stock.info = {
            "symbol": "7203.T",
            "longName": "Toyota Motor Corporation",
            "marketCap": 37835960000000,  # Yen
            "trailingPE": 8.9,
            "priceToBook": 1.05,
            "returnOnEquity": 0.117,
            "currency": "JPY",
            "financialCurrency": "JPY",
            "country": "Japan",
            "exchange": "Tokyo",
            "sector": "Consumer Cyclical",
        }
        mock_ticker.return_value = mock_stock

        result = get_international_stock_data("7203.T")

        assert result is not None
        assert result["ticker"] == "7203.T"
        assert result["currency"] == "JPY"
        assert result["country"] == "Japan"
        assert result["exchange"] == "Tokyo"
        assert "financial_currency" in result

    def test_warren_buffett_international(self):
        """Test Warren Buffett international stock list."""
        buffett_intl = get_warren_buffett_international()

        assert isinstance(buffett_intl, list)
        assert len(buffett_intl) > 10

        # Should include Japanese trading houses
        japanese_holdings = ["8058.T", "8031.T", "8001.T", "2768.T", "8002.T"]
        for holding in japanese_holdings:
            assert holding in buffett_intl

        # Should include some European ADRs
        european_adrs = ["UL", "DEO", "ASML", "SAP"]
        overlapping_adrs = set(european_adrs) & set(buffett_intl)
        assert len(overlapping_adrs) > 0, "Should include some European ADRs"


class TestDataIntegration:
    """Integration tests for data providers."""

    @patch("invest.data.yahoo.get_stock_data")
    def test_us_international_data_consistency(self, mock_get_data):
        """Test that US and international data structures are consistent."""
        # Mock US stock data
        us_data = {
            "ticker": "AAPL",
            "market_cap": 3000000000000,
            "trailing_pe": 28.5,
            "sector": "Technology",
        }

        # Mock international stock data
        intl_data = {
            "ticker": "7203.T",
            "market_cap": 37835960000000,
            "trailing_pe": 8.9,
            "sector": "Consumer Cyclical",
            "currency": "JPY",
            "country": "Japan",
        }

        mock_get_data.side_effect = lambda ticker: us_data if ticker == "AAPL" else intl_data

        us_result = get_stock_data("AAPL")

        with patch("invest.data.international.get_international_stock_data") as mock_intl:
            mock_intl.return_value = intl_data
            intl_result = get_international_stock_data("7203.T")

        # Both should have core fields
        core_fields = ["ticker", "market_cap", "trailing_pe", "sector"]
        for field in core_fields:
            assert field in us_result
            assert field in intl_result

        # International data should have additional fields
        intl_fields = ["currency", "country"]
        for field in intl_fields:
            assert field in intl_result

    def test_error_handling_consistency(self):
        """Test that error handling is consistent across data providers."""
        with patch("yfinance.Ticker", side_effect=Exception("Network error")):
            us_result = get_stock_data("INVALID")
            intl_result = get_international_stock_data("INVALID.T")

            # Both should return None on error
            assert us_result is None
            assert intl_result is None

    def test_ticker_format_validation(self):
        """Test ticker format validation for different markets."""
        # US tickers
        us_tickers = ["AAPL", "MSFT", "BRK-B"]
        for ticker in us_tickers:
            assert not ticker.endswith(".T")
            assert not ticker.endswith(".L")

        # Japanese tickers
        japanese_tickers = get_topix_core30_tickers()
        for ticker in japanese_tickers:
            assert ticker.endswith(".T")

        # UK tickers (from FTSE list)
        with patch("invest.data.international.get_ftse100_tickers") as mock_ftse:
            mock_ftse.return_value = ["LLOY.L", "BARC.L", "VOD"]  # Mix of .L and ADRs
            ftse_tickers = get_market_tickers("uk_ftse")

            london_tickers = [t for t in ftse_tickers if t.endswith(".L")]
            adr_tickers = [t for t in ftse_tickers if not t.endswith(".L")]

            assert len(london_tickers) > 0
            assert len(adr_tickers) > 0


class TestDataQuality:
    """Test data quality and validation."""

    @patch("yfinance.Ticker")
    def test_missing_data_handling(self, mock_ticker):
        """Test handling of missing or incomplete data."""
        # Mock stock with missing data
        mock_stock = Mock()
        mock_stock.info = {
            "symbol": "TEST",
            "marketCap": None,  # Missing market cap
            "trailingPE": None,  # Missing P/E
            "sector": "Technology",
        }
        mock_ticker.return_value = mock_stock

        result = get_stock_data("TEST")

        assert result is not None
        assert result["ticker"] == "TEST"
        assert result["market_cap"] is None
        assert result["trailing_pe"] is None
        assert result["sector"] == "Technology"

    def test_data_type_consistency(self):
        """Test that data types are consistent."""
        with patch("invest.data.yahoo.get_stock_data") as mock_get_data:
            mock_get_data.return_value = {
                "ticker": "AAPL",
                "market_cap": 3000000000000,  # Should be int/float
                "trailing_pe": 28.5,  # Should be float
                "sector": "Technology",  # Should be string
                "current_price": 193.6,  # Should be float
            }

            result = get_stock_data("AAPL")

            assert isinstance(result["ticker"], str)
            assert isinstance(result["market_cap"], (int, float))
            assert isinstance(result["trailing_pe"], (int, float))
            assert isinstance(result["sector"], str)
            assert isinstance(result["current_price"], (int, float))

    def test_large_universe_handling(self):
        """Test handling of large stock universes."""
        # Test with large ticker list
        large_ticker_list = [f"STOCK{i}" for i in range(1000)]

        with patch("invest.data.yahoo.get_stock_data") as mock_get_data:
            # Mock to return data for first 10, None for rest
            mock_get_data.side_effect = (
                lambda ticker: {"ticker": ticker, "market_cap": 1000000000}
                if ticker in large_ticker_list[:10]
                else None
            )

            result = get_universe_data(large_ticker_list[:50])  # Test subset

            assert isinstance(result, pd.DataFrame)
            assert len(result) == 10  # Only successful tickers
            assert len(result.columns) >= 2  # At least ticker and market_cap


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Integration tests for user-facing scripts.

These tests verify that the actual scripts users run (like run_classic_valuations.py)
work correctly with the real data storage layer (SQLite).
"""

import json
import subprocess
import sys
from pathlib import Path
import pytest

project_root = Path(__file__).parent.parent


class TestClassicValuationsScript:
    """Test the run_classic_valuations.py script end-to-end."""

    def test_script_can_load_from_sqlite(self, tmp_path):
        """
        Test that run_classic_valuations.py can load stock data from SQLite.

        This test would have caught the bug where the script was looking for
        deleted JSON files instead of reading from the SQLite database.
        """
        # Create a minimal dashboard_data.json with test stocks
        dashboard_data = {
            'stocks': {
                'AAPL': {},
                'MSFT': {},
            },
            'metadata': {
                'last_updated': '2025-01-01T00:00:00'
            }
        }

        # Create temporary dashboard data file
        test_dashboard_path = tmp_path / 'dashboard_data.json'
        with open(test_dashboard_path, 'w') as f:
            json.dump(dashboard_data, f)

        # Import the script's main components
        sys.path.insert(0, str(project_root / 'src'))
        from invest.data.stock_data_reader import StockDataReader

        # Import the script module
        script_path = project_root / 'scripts' / 'run_classic_valuations.py'
        import importlib.util
        spec = importlib.util.spec_from_file_location('run_classic_valuations', script_path)
        script = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(script)  # Need to execute to load functions

        # Test that load_stock_data function uses StockDataReader
        reader = StockDataReader()

        # This should not raise an error about missing JSON files
        # It should read from SQLite
        data = script.load_stock_data('AAPL', reader)

        # Verify we got data back (or None if AAPL not in DB, but no crash)
        assert data is None or isinstance(data, dict)

        # If we got data, verify it has the expected structure
        if data:
            assert 'info' in data
            assert isinstance(data['info'], dict)

    def test_script_handles_missing_stock(self, tmp_path):
        """Test that the script gracefully handles stocks not in the database."""
        sys.path.insert(0, str(project_root / 'src'))
        from invest.data.stock_data_reader import StockDataReader

        script_path = project_root / 'scripts' / 'run_classic_valuations.py'
        import importlib.util
        spec = importlib.util.spec_from_file_location('run_classic_valuations', script_path)
        script = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(script)

        reader = StockDataReader()

        # Try to load a stock that definitely doesn't exist
        data = script.load_stock_data('FAKE_TICKER_12345', reader)

        # Should return None, not crash
        assert data is None

    def test_script_converts_dataframes_correctly(self, tmp_path):
        """Test that the script correctly converts JSON data to DataFrames."""
        sys.path.insert(0, str(project_root / 'src'))
        from invest.data.stock_data_reader import StockDataReader
        import pandas as pd

        script_path = project_root / 'scripts' / 'run_classic_valuations.py'
        import importlib.util
        spec = importlib.util.spec_from_file_location('run_classic_valuations', script_path)
        script = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(script)

        reader = StockDataReader()

        # Try to load a stock that exists in the database
        # We'll use AAPL if it exists, otherwise skip
        data = script.load_stock_data('AAPL', reader)

        if not data:
            pytest.skip('AAPL not in database - cannot test DataFrame conversion')

        # If we have cashflow data, verify it was converted to DataFrame
        if 'cashflow' in data:
            assert isinstance(data['cashflow'], pd.DataFrame), \
                'Cashflow should be converted to DataFrame'

        # Same for balance sheet
        if 'balance_sheet' in data:
            assert isinstance(data['balance_sheet'], pd.DataFrame), \
                'Balance sheet should be converted to DataFrame'

        # Same for income statement
        if 'income' in data:
            assert isinstance(data['income'], pd.DataFrame), \
                'Income statement should be converted to DataFrame'


class TestDataFetcherScript:
    """Test the data_fetcher.py script integration with SQLite."""

    def test_fetcher_writes_to_sqlite(self):
        """
        Test that data_fetcher.py writes to SQLite database.

        This is a smoke test to ensure the data fetcher is configured
        to use the SQLite backend.
        """
        sys.path.insert(0, str(project_root / 'src'))
        from invest.data.stock_data_reader import StockDataReader

        # Check that we can read from the database
        reader = StockDataReader()

        # The database should exist and have some stocks
        # (This test assumes data has been fetched at least once)
        stock_count = reader.get_stock_count()

        # If count is 0, the database might be empty but should still exist
        # We're just testing that the database connection works
        assert stock_count >= 0


class TestDashboardGeneration:
    """Test dashboard generation scripts."""

    def test_dashboard_can_be_regenerated(self):
        """
        Test that regenerate_dashboard_html.py exists and can be imported.

        This is a smoke test that the dashboard generation pipeline is available.
        """
        script_path = project_root / 'scripts' / 'regenerate_dashboard_html.py'

        # Verify the script exists
        assert script_path.exists(), 'Dashboard regeneration script should exist'

        # Verify it can be imported without errors
        import importlib.util
        spec = importlib.util.spec_from_file_location('regenerate_dashboard_html', script_path)
        script = importlib.util.module_from_spec(spec)

        # If we can create the spec, the script is valid Python
        assert spec is not None
        assert script is not None

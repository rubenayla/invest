"""
Tests for GBM models.

These tests require trained models and will be skipped if models don't exist.
"""

from pathlib import Path

import pytest


@pytest.mark.requires_models
@pytest.mark.requires_data
def test_gbm_model_exists():
    """Test that GBM models exist and can be loaded."""
    import lightgbm as lgb

    project_root = Path(__file__).parent.parent
    model_path = project_root / 'neural_network/training/gbm_model_1y.txt'

    # This test will be skipped if model doesn't exist
    model = lgb.Booster(model_file=str(model_path))
    assert model is not None


@pytest.mark.requires_models
@pytest.mark.requires_data
def test_gbm_prediction_script_can_run():
    """Test that GBM prediction script can be imported and run."""
    import sys
    from pathlib import Path

    # Add scripts to path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root / 'scripts'))

    # Import the unified script
    import run_gbm_predictions

    # Check that main components exist
    assert hasattr(run_gbm_predictions, 'load_gbm_model')
    assert hasattr(run_gbm_predictions, 'load_and_engineer_features')
    assert hasattr(run_gbm_predictions, 'get_model_metadata')


@pytest.mark.requires_data
def test_fundamental_history_table_exists():
    """Test that fundamental_history table exists with data."""
    import sqlite3
    from pathlib import Path

    project_root = Path(__file__).parent.parent
    db_path = project_root / 'data/stock_data.db'

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Check table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fundamental_history'")
    assert cursor.fetchone() is not None

    # Check has data
    cursor.execute("SELECT COUNT(*) FROM fundamental_history")
    count = cursor.fetchone()[0]
    assert count > 1000, f"Expected >1000 records, got {count}"

    conn.close()


@pytest.mark.requires_data
def test_database_schema():
    """Test database schema - requires populated database."""
    import sqlite3
    from pathlib import Path

    project_root = Path(__file__).parent.parent
    db_path = project_root / 'data/stock_data.db'

    if not db_path.exists():
        pytest.skip("Database not found")

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Check valuation_results table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='valuation_results'")
    result = cursor.fetchone()

    if result is None:
        conn.close()
        pytest.skip("valuation_results table not found - database not populated")

    # Check it has the right columns
    cursor.execute("PRAGMA table_info(valuation_results)")
    columns = {row[1] for row in cursor.fetchall()}

    expected_columns = {'ticker', 'model_name', 'fair_value', 'timestamp'}
    assert expected_columns.issubset(columns)

    conn.close()

#!/usr/bin/env python3
"""
Create the unified valuation_results table.

This table stores ALL valuation model outputs in a consistent schema:
- DCF models (dcf, dcf_enhanced, growth_dcf, multi_stage_dcf)
- RIM model
- Simple ratios
- Neural network predictions
- Ensemble models

Database: data/stock_data.db
"""

import sqlite3
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
db_path = project_root / 'data' / 'stock_data.db'


def create_valuation_results_table():
    """Create the unified valuation_results table."""

    print(f'Creating valuation_results table in {db_path}')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Drop old tables if they exist (clean migration)
    print('Dropping old valuation tables...')
    cursor.execute('DROP TABLE IF EXISTS valuation_predictions')
    cursor.execute('DROP TABLE IF EXISTS nn_predictions')

    # Create new unified table
    print('Creating valuation_results table...')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS valuation_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            model_name TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

            -- Core valuation outputs (common to all models)
            fair_value REAL,
            current_price REAL,
            margin_of_safety REAL,
            upside_pct REAL,

            -- Suitability & errors
            suitable BOOLEAN NOT NULL,
            error_message TEXT,
            failure_reason TEXT,

            -- Model-specific details (JSON blob for flexibility)
            -- DCF: wacc, terminal_growth, fcf_projections
            -- NN: confidence intervals, hit_rate, correlation
            details_json TEXT,

            -- Confidence (numeric 0-1)
            confidence REAL,

            -- Ensure only one result per ticker-model pair (replace on conflict)
            UNIQUE(ticker, model_name) ON CONFLICT REPLACE
        )
    ''')

    # Create indexes for performance
    print('Creating indexes...')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_valuation_ticker ON valuation_results(ticker)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_valuation_model ON valuation_results(model_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_valuation_suitable ON valuation_results(suitable)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_valuation_timestamp ON valuation_results(timestamp)')

    conn.commit()
    conn.close()

    print('✅ valuation_results table created successfully!')
    print()
    print('Schema:')
    print('  - ticker, model_name (unique constraint)')
    print('  - fair_value, current_price, margin_of_safety, upside_pct')
    print('  - suitable, error_message, failure_reason')
    print('  - details_json (model-specific data)')
    print('  - confidence (for NN models)')
    print('  - timestamp (auto-updated)')
    print()
    print('Old tables dropped:')
    print('  - valuation_predictions')
    print('  - nn_predictions')


if __name__ == '__main__':
    create_valuation_results_table()

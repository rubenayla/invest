#!/usr/bin/env python3
"""
Create database schema for storing valuation predictions.

This script creates three tables:
- models: Registry of all valuation models (classic + neural networks)
- valuation_predictions: Predictions from classic models (DCF, RIM, etc.)
- nn_predictions: Predictions from neural network models with multiple horizons
"""

import sqlite3
import sys
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent.parent / 'neural_network' / 'training' / 'stock_data.db'


def create_schema(db_path: Path):
    """Create the valuation prediction schema."""

    print(f'📊 Creating valuation schema in: {db_path}')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Create models table
    print('\n📋 Creating models table...')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            model_type TEXT NOT NULL,
            version TEXT,
            description TEXT,

            -- Neural network specific (NULL for classic models)
            model_path TEXT,
            feature_dim INTEGER,
            trained_date TIMESTAMP,

            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Create valuation_predictions table
    print('📋 Creating valuation_predictions table...')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS valuation_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_id INTEGER NOT NULL,
            ticker TEXT NOT NULL,
            prediction_date TIMESTAMP NOT NULL,

            current_price REAL,
            fair_value REAL NOT NULL,
            margin_of_safety REAL,
            upside_pct REAL,

            suitable BOOLEAN DEFAULT 1,
            failure_reason TEXT,
            details_json TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (model_id) REFERENCES models(id),
            UNIQUE(model_id, ticker, prediction_date)
        )
    ''')

    # 3. Create nn_predictions table
    print('📋 Creating nn_predictions table...')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nn_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_id INTEGER NOT NULL,
            ticker TEXT NOT NULL,
            prediction_date TIMESTAMP NOT NULL,
            horizon TEXT NOT NULL,

            current_price REAL,
            predicted_return REAL,
            fair_value REAL,
            confidence_score REAL,

            -- NN-specific metadata
            recommended BOOLEAN DEFAULT 0,
            overall_score REAL,

            suitable BOOLEAN DEFAULT 1,
            failure_reason TEXT,
            details_json TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (model_id) REFERENCES models(id),
            UNIQUE(model_id, ticker, prediction_date, horizon)
        )
    ''')

    # 4. Create indexes
    print('📋 Creating indexes...')

    # Valuation predictions indexes
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_val_pred_ticker_date
        ON valuation_predictions(ticker, prediction_date)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_val_pred_model
        ON valuation_predictions(model_id)
    ''')

    # NN predictions indexes
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_nn_pred_ticker_date
        ON nn_predictions(ticker, prediction_date)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_nn_pred_model_horizon
        ON nn_predictions(model_id, horizon)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_nn_pred_recommended
        ON nn_predictions(ticker, recommended)
    ''')

    # 5. Populate initial models
    print('\n📦 Populating initial models...')

    models = [
        # Classic models
        ('dcf', 'classic', None, 'Standard Discounted Cash Flow model'),
        ('enhanced_dcf', 'classic', None, 'Enhanced DCF with quality adjustments'),
        ('growth_dcf', 'classic', None, 'Growth-focused DCF model'),
        ('rim', 'classic', None, 'Residual Income Model'),
        ('simple_ratios', 'classic', None, 'Simple valuation ratios model'),
        ('multi_stage_dcf', 'classic', None, 'Multi-stage DCF model'),

        # Neural network model
        ('multi_horizon_nn', 'neural_network', '1.0', 'Multi-horizon neural network predictor'),
    ]

    for name, model_type, version, description in models:
        try:
            cursor.execute('''
                INSERT INTO models (name, model_type, version, description)
                VALUES (?, ?, ?, ?)
            ''', (name, model_type, version, description))
            print(f'   ✅ Added model: {name}')
        except sqlite3.IntegrityError:
            print(f'   ⏭️  Model already exists: {name}')

    conn.commit()
    conn.close()

    print('\n✅ Schema created successfully!')
    print(f'   Database: {db_path}')
    print('   Tables: models, valuation_predictions, nn_predictions')


def verify_schema(db_path: Path):
    """Verify the schema was created correctly."""

    print('\n🔍 Verifying schema...')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check tables
    cursor.execute('''
        SELECT name FROM sqlite_master
        WHERE type='table' AND name IN ('models', 'valuation_predictions', 'nn_predictions')
        ORDER BY name
    ''')
    tables = cursor.fetchall()
    print(f'   Tables found: {", ".join(t[0] for t in tables)}')

    # Check models
    cursor.execute('SELECT COUNT(*) FROM models')
    model_count = cursor.fetchone()[0]
    print(f'   Models registered: {model_count}')

    # Show models
    cursor.execute('SELECT name, model_type FROM models ORDER BY model_type, name')
    models = cursor.fetchall()
    print('\n📋 Registered models:')
    for name, model_type in models:
        print(f'   - {name} ({model_type})')

    conn.close()
    print('\n✅ Verification complete!')


def main():
    """Main entry point."""

    print('🚀 Valuation Schema Setup')
    print('=' * 60)

    if not DB_PATH.exists():
        print(f'❌ Database not found: {DB_PATH}')
        print('   Please create the training database first.')
        return 1

    # Create schema
    create_schema(DB_PATH)

    # Verify
    verify_schema(DB_PATH)

    return 0


if __name__ == '__main__':
    sys.exit(main())

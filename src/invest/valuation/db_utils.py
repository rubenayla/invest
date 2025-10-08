"""
Database utilities for saving valuation predictions.

This module provides helper functions for saving both classic and neural network
valuation predictions to the database.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Default database path
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent.parent / 'neural_network' / 'training' / 'stock_data.db'


def get_db_connection(db_path: Path = None) -> sqlite3.Connection:
    """Get database connection."""
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    return sqlite3.connect(db_path)


def get_model_id(conn: sqlite3.Connection, model_name: str) -> Optional[int]:
    """Get model_id from database."""
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM models WHERE name = ?', (model_name,))
    result = cursor.fetchone()
    return result[0] if result else None


def save_classic_prediction(
    conn: sqlite3.Connection,
    model_name: str,
    ticker: str,
    fair_value: float,
    current_price: float,
    margin_of_safety: Optional[float] = None,
    upside_pct: Optional[float] = None,
    suitable: bool = True,
    failure_reason: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    prediction_date: Optional[datetime] = None
) -> None:
    """
    Save classic valuation prediction to database.

    Parameters
    ----------
    conn : sqlite3.Connection
        Database connection
    model_name : str
        Model name (e.g., 'dcf', 'rim', 'simple_ratios')
    ticker : str
        Stock ticker symbol
    fair_value : float
        Calculated fair value per share
    current_price : float
        Current stock price
    margin_of_safety : float, optional
        Margin of safety percentage
    upside_pct : float, optional
        Upside percentage
    suitable : bool
        Whether the model is suitable for this stock
    failure_reason : str, optional
        Reason for failure if suitable=False
    details : dict, optional
        Additional model-specific details
    prediction_date : datetime, optional
        Date of prediction (defaults to now)
    """
    if prediction_date is None:
        prediction_date = datetime.now()

    # Get model_id
    model_id = get_model_id(conn, model_name)
    if model_id is None:
        raise ValueError(f'Model {model_name} not found in database. Run create_valuation_schema.py first.')

    # Calculate margin_of_safety if not provided
    if margin_of_safety is None and current_price and current_price > 0:
        margin_of_safety = (fair_value - current_price) / current_price

    # Calculate upside if not provided
    if upside_pct is None and current_price and current_price > 0:
        upside_pct = ((fair_value / current_price) - 1) * 100

    # Prepare details JSON
    details_json = json.dumps(details) if details else None

    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO valuation_predictions (
                model_id, ticker, prediction_date,
                current_price, fair_value, margin_of_safety, upside_pct,
                suitable, failure_reason, details_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            model_id, ticker, prediction_date,
            current_price, fair_value, margin_of_safety, upside_pct,
            suitable, failure_reason, details_json
        ))
        conn.commit()
    except Exception as e:
        raise RuntimeError(f'Failed to save prediction for {ticker} ({model_name}): {e}')


def save_nn_prediction(
    conn: sqlite3.Connection,
    model_name: str,
    ticker: str,
    horizons: Dict[str, Dict[str, float]],
    recommended_horizon: str,
    current_price: float,
    overall_score: float,
    suitable: bool = True,
    failure_reason: Optional[str] = None,
    prediction_date: Optional[datetime] = None
) -> None:
    """
    Save neural network prediction to database.

    Parameters
    ----------
    conn : sqlite3.Connection
        Database connection
    model_name : str
        Model name (e.g., 'multi_horizon_nn')
    ticker : str
        Stock ticker symbol
    horizons : dict
        Dict of horizon -> {predicted_return, fair_value, confidence_score}
    recommended_horizon : str
        Recommended horizon (e.g., '3m')
    current_price : float
        Current stock price
    overall_score : float
        Overall prediction score
    suitable : bool
        Whether the model is suitable for this stock
    failure_reason : str, optional
        Reason for failure if suitable=False
    prediction_date : datetime, optional
        Date of prediction (defaults to now)
    """
    if prediction_date is None:
        prediction_date = datetime.now()

    # Get model_id
    model_id = get_model_id(conn, model_name)
    if model_id is None:
        raise ValueError(f'Model {model_name} not found in database. Run create_valuation_schema.py first.')

    cursor = conn.cursor()

    for horizon, values in horizons.items():
        predicted_return = values.get('predicted_return', 0.0)
        fair_value = values.get('fair_value', 0.0)
        confidence_score = values.get('confidence_score', 0.0)
        is_recommended = (horizon == recommended_horizon)

        details = {
            'prediction': predicted_return,
            'fair_value': fair_value,
            'confidence': confidence_score,
            'overall_score': overall_score
        }

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO nn_predictions (
                    model_id, ticker, prediction_date, horizon,
                    current_price, predicted_return, fair_value, confidence_score,
                    recommended, overall_score, suitable, failure_reason, details_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                model_id, ticker, prediction_date, horizon,
                current_price, predicted_return, fair_value, confidence_score,
                is_recommended, overall_score, suitable, failure_reason, json.dumps(details)
            ))
        except Exception as e:
            raise RuntimeError(f'Failed to save NN prediction for {ticker} horizon {horizon}: {e}')

    conn.commit()


def get_latest_predictions(
    conn: sqlite3.Connection,
    ticker: str,
    model_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get latest predictions for a ticker.

    Parameters
    ----------
    conn : sqlite3.Connection
        Database connection
    ticker : str
        Stock ticker symbol
    model_name : str, optional
        Specific model name to query (if None, returns all models)

    Returns
    -------
    dict
        Dictionary of predictions by model
    """
    cursor = conn.cursor()

    results = {}

    # Get classic predictions
    if model_name is None or model_name in ['dcf', 'rim', 'simple_ratios', 'enhanced_dcf', 'growth_dcf', 'multi_stage_dcf']:
        query = '''
            SELECT m.name, v.fair_value, v.margin_of_safety, v.upside_pct,
                   v.suitable, v.failure_reason, v.details_json, v.prediction_date
            FROM valuation_predictions v
            JOIN models m ON v.model_id = m.id
            WHERE v.ticker = ?
        '''
        params = [ticker]

        if model_name:
            query += ' AND m.name = ?'
            params.append(model_name)

        query += ' ORDER BY v.prediction_date DESC'

        cursor.execute(query, params)
        for row in cursor.fetchall():
            name, fair_value, margin, upside, suitable, reason, details_json, date = row
            results[name] = {
                'fair_value': fair_value,
                'margin_of_safety': margin,
                'upside_pct': upside,
                'suitable': bool(suitable),
                'failure_reason': reason,
                'details': json.loads(details_json) if details_json else {},
                'prediction_date': date
            }

    # Get NN predictions (recommended horizon only for summary)
    if model_name is None or model_name == 'multi_horizon_nn':
        query = '''
            SELECT m.name, n.fair_value, n.confidence_score, n.horizon,
                   n.suitable, n.failure_reason, n.details_json, n.prediction_date
            FROM nn_predictions n
            JOIN models m ON n.model_id = m.id
            WHERE n.ticker = ? AND n.recommended = 1
        '''
        params = [ticker]

        if model_name:
            query += ' AND m.name = ?'
            params.append(model_name)

        query += ' ORDER BY n.prediction_date DESC LIMIT 1'

        cursor.execute(query, params)
        row = cursor.fetchone()
        if row:
            name, fair_value, confidence, horizon, suitable, reason, details_json, date = row
            results[name] = {
                'fair_value': fair_value,
                'confidence_score': confidence,
                'recommended_horizon': horizon,
                'suitable': bool(suitable),
                'failure_reason': reason,
                'details': json.loads(details_json) if details_json else {},
                'prediction_date': date
            }

    return results

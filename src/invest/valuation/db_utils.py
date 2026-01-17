"""
Database utilities for saving valuation predictions.

This module stores predictions in the valuation_results table, which is the
database source of truth for all model outputs.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Default database path
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent.parent / 'data' / 'stock_data.db'


def get_db_connection(db_path: Path = None) -> sqlite3.Connection:
    """Get database connection."""
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    return sqlite3.connect(db_path)


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
    prediction_date: Optional[datetime] = None,
    confidence: Optional[float] = None,
    error_message: Optional[str] = None
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
    confidence : float, optional
        Optional confidence score
    error_message : str, optional
        Error message for unsuitable predictions
    """
    if prediction_date is None:
        prediction_date = datetime.now()

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
            INSERT OR REPLACE INTO valuation_results (
                ticker, model_name, timestamp,
                fair_value, current_price, margin_of_safety, upside_pct,
                suitable, error_message, failure_reason, details_json, confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ticker,
            model_name,
            prediction_date,
            fair_value,
            current_price,
            margin_of_safety,
            upside_pct,
            suitable,
            error_message,
            failure_reason,
            details_json,
            confidence
        ))
        conn.commit()
    except Exception as e:
        raise RuntimeError(f'Failed to save prediction for {ticker} ({model_name}): {e}')


def save_nn_prediction(
    conn: sqlite3.Connection,
    model_name: str,
    ticker: str,
    fair_value: float,
    current_price: float,
    margin_of_safety: float,
    upside_pct: float,
    confidence: Optional[float] = None,
    details: Optional[Dict[str, Any]] = None,
    suitable: bool = True,
    error_message: Optional[str] = None,
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
    fair_value : float
        Recommended fair value per share
    current_price : float
        Current stock price
    margin_of_safety : float
        Margin of safety ratio
    upside_pct : float
        Upside percentage
    confidence : float, optional
        Overall confidence score
    details : dict, optional
        Additional NN prediction details
    suitable : bool
        Whether the model is suitable for this stock
    error_message : str, optional
        Error message for unsuitable predictions
    failure_reason : str, optional
        Reason for failure if suitable=False
    prediction_date : datetime, optional
        Date of prediction (defaults to now)
    """
    if prediction_date is None:
        prediction_date = datetime.now()
    details_json = json.dumps(details) if details else None

    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO valuation_results (
                ticker, model_name, timestamp,
                fair_value, current_price, margin_of_safety, upside_pct,
                suitable, error_message, failure_reason, details_json, confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ticker,
            model_name,
            prediction_date,
            fair_value,
            current_price,
            margin_of_safety,
            upside_pct,
            suitable,
            error_message,
            failure_reason,
            details_json,
            confidence
        ))
        conn.commit()
    except Exception as e:
        raise RuntimeError(f'Failed to save NN prediction for {ticker} ({model_name}): {e}')


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

    query = '''
        SELECT model_name, fair_value, margin_of_safety, upside_pct,
               suitable, error_message, failure_reason, details_json,
               confidence, timestamp
        FROM valuation_results
        WHERE ticker = ?
    '''
    params = [ticker]

    if model_name:
        query += ' AND model_name = ?'
        params.append(model_name)

    query += ' ORDER BY timestamp DESC'

    cursor.execute(query, params)
    for row in cursor.fetchall():
        name, fair_value, margin, upside, suitable, error_message, reason, details_json, confidence, timestamp = row
        if name in results:
            continue
        results[name] = {
            'fair_value': fair_value,
            'margin_of_safety': margin,
            'upside_pct': upside,
            'confidence': confidence,
            'suitable': bool(suitable),
            'error_message': error_message,
            'failure_reason': reason,
            'details': json.loads(details_json) if details_json else {},
            'timestamp': timestamp
        }

    return results

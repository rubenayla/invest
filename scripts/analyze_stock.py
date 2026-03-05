#!/usr/bin/env python3
import json
import sqlite3
import sys
from pathlib import Path
from typing import Optional, List

import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from invest.data.stock_data_reader import StockDataReader
from invest.valuation.base import ModelNotSuitableError
from invest.valuation.model_registry import ModelRegistry

# Reuse models from run_classic_valuations.py
MODELS_TO_RUN = [
    ('dcf', 'dcf'),
    ('dcf_enhanced', 'dcf_enhanced'),
    ('rim', 'rim'),
    ('simple_ratios', 'simple_ratios'),
    ('growth_dcf', 'growth_dcf'),
    ('multi_stage_dcf', 'multi_stage_dcf'),
]

def load_stock_data(ticker: str, reader: StockDataReader) -> Optional[dict]:
    cache_data = reader.get_stock_data(ticker)
    if not cache_data:
        return None

    stock_data = {
        'info': cache_data.get('info', {}),
        'market_data': reader.get_market_inputs(
            ticker=ticker,
            min_price_points=252,
            max_price_age_days=30,
            max_rate_age_days=30,
        ),
    }

    for stmt in ['cashflow', 'balance_sheet', 'income']:
        if stmt in cache_data and cache_data[stmt]:
            try:
                df = pd.DataFrame(cache_data[stmt])
                if 'index' in df.columns:
                    df = df.set_index('index')
                stock_data[stmt] = df
            except Exception as e:
                print(f'Warning: Could not convert {stmt} for {ticker}: {e}')

    return stock_data

def run_valuation(registry: ModelRegistry, registry_name: str, ticker: str, stock_data: dict) -> Optional[dict]:
    try:
        model = registry.get_model(registry_name)
        if not model.is_suitable(ticker, stock_data):
            reason = 'Data requirements not met'
            if hasattr(model, 'get_suitability_reason'):
                model_reason = model.get_suitability_reason()
                if model_reason:
                    reason = model_reason
            return {'suitable': False, 'reason': reason}

        model._validate_inputs(ticker, stock_data)
        result = model._calculate_valuation(ticker, stock_data)

        details = {}
        if hasattr(result, 'inputs'):
            details.update(result.inputs)
        if hasattr(result, 'outputs'):
            details.update(result.outputs)

        return {
            'fair_value': float(result.fair_value),
            'current_price': float(result.current_price),
            'margin_of_safety': float(result.margin_of_safety),
            'upside': float(((result.fair_value / result.current_price) - 1) * 100) if result.current_price > 0 else 0,
            'suitable': True,
            'confidence': result.confidence,
            'details': details
        }
    except Exception as e:
        return {'suitable': False, 'error': str(e), 'reason': f'Unexpected error: {type(e).__name__}'}

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/analyze_stock.py TICKER [TICKER...]")
        sys.exit(1)

    tickers = sys.argv[1:]
    reader = StockDataReader()
    registry = ModelRegistry()

    print(f"Analyzing tickers: {', '.join(tickers)}")
    print("-" * 60)

    for ticker in tickers:
        print(f"\nSTOCK: {ticker}")
        stock_data = load_stock_data(ticker, reader)
        if not stock_data:
            print(f"Error: No data found for {ticker}")
            continue

        current_price = stock_data['info'].get('currentPrice')
        if current_price:
            print(f"Current Price: ${current_price:.2f}")
        else:
            print("Current Price: Unknown")

        for reg_name, db_name in MODELS_TO_RUN:
            result = run_valuation(registry, reg_name, ticker, stock_data)
            if result.get('suitable'):
                upside = result['upside']
                fair_value = result['fair_value']
                confidence = result['confidence']
                print(f"  {db_name:20}: Fair Value: ${fair_value:8.2f} | Upside: {upside:6.1f}% | Confidence: {confidence}")
            else:
                print(f"  {db_name:20}: Not suitable - {result.get('reason', result.get('error', 'Unknown'))}")

if __name__ == "__main__":
    main()

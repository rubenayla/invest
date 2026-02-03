#!/usr/bin/env python3
"""
Currency conversion utilities for stock data.

Handles detection and conversion of foreign currency financials to USD.
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


# Hardcoded exchange rates for major currencies (updated periodically)
# These are approximate rates - in production would use a live forex API
EXCHANGE_RATES = {
    'USD': 1.0,
    'JPY': 0.0067,  # ~150 JPY = 1 USD
    'EUR': 1.08,
    'GBP': 1.27,
    'CAD': 0.73,
    'AUD': 0.66,
    'CHF': 1.15,
    'CNY': 0.14,
    'HKD': 0.13,
    'SGD': 0.75,
    'KRW': 0.00075,  # ~1330 KRW = 1 USD
    'TWD': 0.032,  # ~31 TWD = 1 USD
    'INR': 0.012,
    'BRL': 0.20,
    'MXN': 0.058,
    'DKK': 0.145,  # Danish Krone
    'NOK': 0.093,
    'SEK': 0.096,
    'NZD': 0.61,
    'ZAR': 0.054,
}


def convert_to_usd(value: float, from_currency: str) -> float:
    """
    Convert a value from another currency to USD.

    Parameters
    ----------
    value : float
        Value in the source currency
    from_currency : str
        ISO currency code (JPY, EUR, etc.)

    Returns
    -------
    float
        Value in USD
    """
    if not value or value == 0:
        return value

    rate = EXCHANGE_RATES.get(from_currency, 1.0)
    if rate == 1.0 and from_currency != 'USD':
        logger.warning(f'Unknown currency {from_currency}, assuming 1:1 with USD')

    return value * rate


def detect_currency_mismatch(info: Dict, financials: Dict) -> tuple[bool, Optional[str]]:
    """
    Detect if trading currency differs from financial currency.

    yfinance provides explicit 'financialCurrency' field that tells us
    what currency the company reports financials in.

    Parameters
    ----------
    info : Dict
        Stock info dict with currency and financialCurrency
    financials : Dict
        Financial metrics dict (unused but kept for compatibility)

    Returns
    -------
    tuple[bool, Optional[str]]
        (has_mismatch, financial_currency) where financial_currency is
        the currency of the financials (if different from USD)
    """
    # yfinance explicitly tells us the financial reporting currency
    financial_currency = info.get('financialCurrency', 'USD')

    # If financials are not in USD, they need conversion
    if financial_currency and financial_currency != 'USD':
        return True, financial_currency

    return False, None


def convert_financials_to_usd(info: Dict, financials: Dict) -> Dict:
    """
    Convert all financial metrics to USD if currency mismatch detected.

    Modifies the financials dict in place and returns it.

    Parameters
    ----------
    info : Dict
        Stock info dict (to detect currency)
    financials : Dict
        Financial metrics to convert

    Returns
    -------
    Dict
        Financials dict with all values converted to USD
    """
    has_mismatch, financial_currency = detect_currency_mismatch(info, financials)

    if not has_mismatch or not financial_currency:
        return financials

    # Fields to convert to USD
    fields_to_convert = [
        'totalRevenue',
        'totalCash',
        'totalDebt',
        'trailingEps',
        'bookValue',
        'revenuePerShare',
    ]

    ticker = info.get('symbol', 'UNKNOWN')
    logger.info(f'{ticker}: Converting financials from {financial_currency} to USD (rate: {EXCHANGE_RATES.get(financial_currency, 1.0):.4f})')

    # Convert each field
    converted_count = 0
    for field in fields_to_convert:
        value = financials.get(field)
        if value and value != 0:
            original = value
            financials[field] = convert_to_usd(value, financial_currency)
            converted_count += 1
            logger.debug(f'  {field}: {original:,.0f} {financial_currency} → ${financials[field]:,.2f} USD')

    # Add metadata about conversion
    financials['_currency_converted'] = True
    financials['_original_currency'] = financial_currency
    financials['_exchange_rate_used'] = EXCHANGE_RATES.get(financial_currency, 1.0)

    logger.info(f'{ticker}: Converted {converted_count} fields from {financial_currency} to USD')

    return financials


def convert_financial_statements_to_usd(
    data: Dict,
    financial_currency: str,
    exchange_rate: float
) -> Dict:
    """
    Convert financial statement values (cashflow, balance_sheet, income) to USD.

    Financial statements are stored as lists of dicts:
    [
        {'index': 'Free Cash Flow', '2023-12-31': 1000000000, '2022-12-31': 950000000},
        {'index': 'Operating Cash Flow', '2023-12-31': 1200000000, ...}
    ]

    Parameters
    ----------
    data : Dict
        Full stock data dict with 'cashflow', 'balance_sheet', 'income' keys
    financial_currency : str
        Currency code for the financial data (JPY, TWD, etc.)
    exchange_rate : float
        Exchange rate to USD

    Returns
    -------
    Dict
        Data dict with all financial statement values converted to USD
    """
    if not financial_currency or financial_currency == 'USD':
        return data

    ticker = data.get('ticker', 'UNKNOWN')
    converted_count = 0

    for statement_name in ['cashflow', 'balance_sheet', 'income']:
        statement = data.get(statement_name)
        if not statement or not isinstance(statement, list):
            continue

        for row in statement:
            if not isinstance(row, dict):
                continue

            # Convert all date columns (skip 'index' column)
            for key, value in row.items():
                if key == 'index':
                    continue

                # Convert numeric values (skip NaN, None, 0)
                if isinstance(value, (int, float)) and value and value == value:  # value == value checks for NaN
                    row[key] = value * exchange_rate
                    converted_count += 1

    if converted_count > 0:
        logger.info(f'{ticker}: Converted {converted_count} values in financial statements from {financial_currency} to USD')

    return data

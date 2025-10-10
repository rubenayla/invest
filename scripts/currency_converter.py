#!/usr/bin/env python3
"""
Currency conversion utilities for stock data.

Handles detection and conversion of foreign currency financials to USD.
"""

from typing import Dict, Optional
import logging

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

    For ADRs (American Depositary Receipts), the stock trades in USD but
    the company reports financials in their home currency (JPY, EUR, etc.).

    Parameters
    ----------
    info : Dict
        Stock info dict with currency and country
    financials : Dict
        Financial metrics dict with revenue, book value, etc.

    Returns
    -------
    tuple[bool, Optional[str]]
        (has_mismatch, financial_currency) where financial_currency is
        the detected currency of the financials (if different from trading currency)
    """
    trading_currency = info.get('currency', 'USD')
    country = info.get('country', '')

    # Quick check: if trading USD but company is not from US/Canada, likely an ADR
    if trading_currency == 'USD' and country not in ('United States', 'Canada', '', None):
        # Check for abnormally high values that suggest foreign currency
        revenue = financials.get('totalRevenue')
        book_value = financials.get('bookValue')

        # Map country to likely currency
        country_currency_map = {
            'Japan': 'JPY',
            'Taiwan': 'TWD',
            'South Korea': 'KRW',
            'China': 'CNY',
            'Hong Kong': 'HKD',
            'Singapore': 'SGD',
            'India': 'INR',
            'United Kingdom': 'GBP',
            'Germany': 'EUR',
            'France': 'EUR',
            'Spain': 'EUR',
            'Italy': 'EUR',
            'Netherlands': 'EUR',
            'Switzerland': 'CHF',
            'Denmark': 'DKK',
            'Norway': 'NOK',
            'Sweden': 'SEK',
            'Australia': 'AUD',
            'New Zealand': 'NZD',
            'Brazil': 'BRL',
            'Mexico': 'MXN',
            'South Africa': 'ZAR',
        }

        likely_currency = country_currency_map.get(country)

        if likely_currency:
            # Check if values are suspiciously high (suggesting foreign currency)
            if revenue and revenue > 200_000_000_000:  # > $200B
                return True, likely_currency
            if book_value and book_value > 100:  # > $100/share
                return True, likely_currency

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

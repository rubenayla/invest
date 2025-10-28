#!/usr/bin/env python3
"""
Screen stocks based on value investing criteria.

Criteria:
- Price-to-Book (P/B) < 1.5
- Return on Equity (ROE) > 8%
- Net-Debt / Equity < 1.0
- Dividend Yield > 3%
- Free Cash Flow (FCF) positive
- Evidence of shareholder returns (buybacks, dividends)
- P/E < 12-15x
- Business outlook indicators
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def get_db_path() -> Path:
    """Get the path to the stock database."""
    return Path(__file__).parent.parent / 'data' / 'stock_data.db'


def calculate_net_debt_to_equity(total_cash: float, total_debt: float,
                                  book_value: float, shares: float) -> Optional[float]:
    """Calculate Net Debt / Equity ratio."""
    if not all([book_value, shares]):
        return None

    equity = book_value * shares
    if equity <= 0:
        return None

    net_debt = (total_debt or 0) - (total_cash or 0)
    return net_debt / equity


def get_fcf_from_json(cashflow_json: str) -> Optional[float]:
    """Extract most recent FCF from cashflow JSON."""
    if not cashflow_json:
        return None

    try:
        cashflows = json.loads(cashflow_json)
        if not cashflows:
            return None

        # Get most recent year
        recent = cashflows[0]
        fcf = recent.get('Free Cash Flow')
        return float(fcf) if fcf and fcf != 'N/A' else None
    except (json.JSONDecodeError, ValueError, KeyError):
        return None


def has_shareholder_returns(dividend_yield: Optional[float], has_buybacks: bool) -> bool:
    """Check for evidence of shareholder returns (buybacks, consistent dividends)."""
    # Good dividend yield
    if dividend_yield and dividend_yield > 3.0:
        return True

    # Active buyback program
    if has_buybacks:
        return True

    return False


def get_dividend_info(cashflow_json: str, market_cap: float) -> Tuple[Optional[float], bool]:
    """
    Extract dividend info from cashflow JSON.

    Returns:
        (dividend_yield_pct, has_buybacks)
    """
    if not cashflow_json or not market_cap:
        return None, False

    try:
        cashflows = json.loads(cashflow_json)
        if not cashflows:
            return None, False

        # Find dividend and buyback rows
        dividend_yield = None
        has_buybacks = False

        for row in cashflows:
            index = row.get('index', '')

            # Look for dividends
            if 'dividend' in index.lower() or 'cash dividends paid' in index.lower():
                # Get most recent year value
                values = {k: v for k, v in row.items() if k != 'index'}
                if values:
                    most_recent = list(values.values())[0]
                    if most_recent and most_recent < 0:  # Dividends are negative cash flow
                        annual_dividend = abs(most_recent)
                        # Dividend yield = annual dividends / market cap
                        dividend_yield = (annual_dividend / market_cap) * 100

            # Look for buybacks
            if 'repurchase' in index.lower() or 'buyback' in index.lower():
                values = {k: v for k, v in row.items() if k != 'index'}
                if values:
                    most_recent = list(values.values())[0]
                    if most_recent and most_recent < 0:  # Buybacks are negative
                        has_buybacks = True

        return dividend_yield, has_buybacks

    except (json.JSONDecodeError, ValueError, KeyError):
        return None, False


def screen_stocks() -> List[Dict]:
    """Screen all stocks against value criteria."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all stocks
    cursor.execute('''
        SELECT
            ticker,
            short_name,
            long_name,
            sector,
            industry,
            current_price,
            trailing_pe,
            price_to_book,
            return_on_equity,
            total_cash,
            total_debt,
            book_value,
            shares_outstanding,
            market_cap,
            cashflow_json
        FROM current_stock_data
        WHERE current_price IS NOT NULL
    ''')

    results = []
    total_stocks = 0

    for row in cursor:
        total_stocks += 1
        ticker = row['ticker']

        # Extract values
        pb = row['price_to_book']
        roe = row['return_on_equity']
        pe = row['trailing_pe']
        current_price = row['current_price']
        market_cap = row['market_cap']

        # Get dividend and buyback info
        div_yield, has_buybacks = get_dividend_info(row['cashflow_json'], market_cap)

        # Skip if missing critical data
        if not all([pb, roe, pe]):
            continue

        # Apply filters
        if pb >= 1.5:
            continue

        if roe <= 8.0:
            continue

        if pe >= 15.0:  # Upper bound for value
            continue

        if not div_yield or div_yield <= 3.0:
            continue

        # Net Debt / Equity
        net_debt_equity = calculate_net_debt_to_equity(
            row['total_cash'],
            row['total_debt'],
            row['book_value'],
            row['shares_outstanding']
        )

        if net_debt_equity is None or net_debt_equity >= 1.0:
            continue

        # FCF check
        fcf = get_fcf_from_json(row['cashflow_json'])
        if not fcf or fcf <= 0:
            continue

        # Shareholder returns check
        if not has_shareholder_returns(div_yield, has_buybacks):
            continue

        # Passed all filters!
        results.append({
            'ticker': ticker,
            'name': row['short_name'] or row['long_name'] or ticker,
            'sector': row['sector'],
            'industry': row['industry'],
            'price': row['current_price'],
            'market_cap': row['market_cap'],
            'pe': pe,
            'pb': pb,
            'roe': roe,
            'net_debt_equity': net_debt_equity,
            'div_yield': div_yield,
            'fcf': fcf,
        })

    conn.close()

    print(f'\n📊 Screened {total_stocks} stocks')
    print(f'✅ Found {len(results)} stocks passing all criteria\n')

    return results


def print_results(stocks: List[Dict]):
    """Print screening results in a readable format."""
    if not stocks:
        print('❌ No stocks passed all filters.')
        return

    print(f'{"Ticker":<8} {"Name":<30} {"PE":<7} {"PB":<7} {"ROE":<7} {"ND/E":<7} {"Div%":<7} {"FCF":<12} {"Sector":<25}')
    print('=' * 140)

    # Sort by P/E (cheapest first)
    stocks.sort(key=lambda x: x['pe'])

    for stock in stocks:
        fcf_str = f"${stock['fcf']/1e9:.1f}B" if stock['fcf'] > 1e9 else f"${stock['fcf']/1e6:.0f}M"

        print(f"{stock['ticker']:<8} "
              f"{stock['name'][:29]:<30} "
              f"{stock['pe']:<7.1f} "
              f"{stock['pb']:<7.2f} "
              f"{stock['roe']:<7.1f} "
              f"{stock['net_debt_equity']:<7.2f} "
              f"{stock['div_yield']:<7.1f} "
              f"{fcf_str:<12} "
              f"{stock['sector'] or 'N/A':<25}")

    print(f'\n✨ Total qualifying stocks: {len(stocks)}')


if __name__ == '__main__':
    stocks = screen_stocks()
    print_results(stocks)

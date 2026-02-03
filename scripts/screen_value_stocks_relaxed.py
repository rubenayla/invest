#!/usr/bin/env python3
"""
Screen stocks based on relaxed value investing criteria.
Uses only data available in the database.

Relaxed Criteria:
- Price-to-Book (P/B) < 2.0 (was 1.5)
- Return on Equity (ROE) > 5% (was 8%) - OPTIONAL due to sparse data
- Net-Debt / Equity < 1.5 (was 1.0)
- P/E < 18x (was 12-15x)
- Positive operating margins (proxy for quality)
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional


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


def get_dividend_yield(cashflow_json: str, market_cap: float) -> Optional[float]:
    """Extract dividend yield from cashflow JSON."""
    if not cashflow_json or not market_cap:
        return None

    try:
        cashflows = json.loads(cashflow_json)
        if not cashflows:
            return None

        for row in cashflows:
            index = row.get('index', '')
            if 'dividend' in index.lower() or 'cash dividends paid' in index.lower():
                values = {k: v for k, v in row.items() if k != 'index'}
                if values:
                    most_recent = list(values.values())[0]
                    if most_recent and most_recent < 0:
                        annual_dividend = abs(most_recent)
                        return (annual_dividend / market_cap) * 100

        return None
    except (json.JSONDecodeError, ValueError, KeyError):
        return None


def screen_stocks() -> List[Dict]:
    """Screen all stocks against relaxed value criteria."""
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
            operating_margins,
            profit_margins,
            cashflow_json
        FROM current_stock_data
        WHERE current_price IS NOT NULL
    ''')

    results = []
    total_stocks = 0

    for row in cursor:
        total_stocks += 1
        ticker = row['ticker']

        try:
            # Extract values with type safety
            pb = float(row['price_to_book']) if row['price_to_book'] else None
            roe = float(row['return_on_equity']) if row['return_on_equity'] else None
            pe = float(row['trailing_pe']) if row['trailing_pe'] else None
            op_margin = float(row['operating_margins']) if row['operating_margins'] else None
            profit_margin = float(row['profit_margins']) if row['profit_margins'] else None

            # Skip if missing critical data (PE and PB are must-haves)
            if not all([pb, pe]):
                continue

            # Apply relaxed filters
            if pb >= 2.0:  # More lenient P/B
                continue

            if pe >= 18.0:  # More lenient P/E
                continue

            # Quality check: positive profitability
            if op_margin and op_margin <= 0:
                continue

            # Net Debt / Equity (relaxed to 1.5)
            net_debt_equity = calculate_net_debt_to_equity(
                row['total_cash'],
                row['total_debt'],
                row['book_value'],
                row['shares_outstanding']
            )

            if net_debt_equity is not None and net_debt_equity >= 1.5:
                continue

            # Get dividend yield (informational, not filtering)
            div_yield = get_dividend_yield(row['cashflow_json'], row['market_cap'])

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
                'op_margin': op_margin,
                'profit_margin': profit_margin,
                'div_yield': div_yield,
            })

        except (ValueError, TypeError):
            # Skip stocks with data type issues
            continue

    conn.close()

    print(f'\n📊 Screened {total_stocks} stocks')
    print(f'✅ Found {len(results)} stocks passing all criteria\n')

    return results


def print_results(stocks: List[Dict]):
    """Print screening results in a readable format."""
    if not stocks:
        print('❌ No stocks passed all filters.')
        return

    print(f'{"Ticker":<8} {"Name":<30} {"PE":<7} {"PB":<7} {"ROE":<8} {"ND/E":<8} {"OpMgn%":<8} {"Div%":<7} {"Sector":<25}')
    print('=' * 145)

    # Sort by P/E (cheapest first)
    stocks.sort(key=lambda x: x['pe'])

    for stock in stocks:
        roe_str = f"{stock['roe']:.1f}" if stock['roe'] else 'N/A'
        nde_str = f"{stock['net_debt_equity']:.2f}" if stock['net_debt_equity'] is not None else 'N/A'
        opm_str = f"{stock['op_margin']*100:.1f}" if stock['op_margin'] else 'N/A'
        div_str = f"{stock['div_yield']:.1f}" if stock['div_yield'] else 'N/A'

        print(f"{stock['ticker']:<8} "
              f"{stock['name'][:29]:<30} "
              f"{stock['pe']:<7.1f} "
              f"{stock['pb']:<7.2f} "
              f"{roe_str:<8} "
              f"{nde_str:<8} "
              f"{opm_str:<8} "
              f"{div_str:<7} "
              f"{(stock['sector'] or 'N/A'):<25}")

    print(f'\n✨ Total qualifying stocks: {len(stocks)}')
    print('\n📋 Criteria used:')
    print('  • P/B < 2.0')
    print('  • P/E < 18')
    print('  • Net Debt/Equity < 1.5')
    print('  • Positive operating margins')


if __name__ == '__main__':
    stocks = screen_stocks()
    print_results(stocks)

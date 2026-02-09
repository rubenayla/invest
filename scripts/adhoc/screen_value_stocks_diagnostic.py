#!/usr/bin/env python3
"""
Diagnostic version of value stock screener.
Shows how many stocks pass each filter.
"""

import json
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Optional, Tuple


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


def get_dividend_info(cashflow_json: str, market_cap: float) -> Tuple[Optional[float], bool]:
    """Extract dividend info from cashflow JSON."""
    if not cashflow_json or not market_cap:
        return None, False

    try:
        cashflows = json.loads(cashflow_json)
        if not cashflows:
            return None, False

        dividend_yield = None
        has_buybacks = False

        for row in cashflows:
            index = row.get('index', '')

            if 'dividend' in index.lower() or 'cash dividends paid' in index.lower():
                values = {k: v for k, v in row.items() if k != 'index'}
                if values:
                    most_recent = list(values.values())[0]
                    if most_recent and most_recent < 0:
                        annual_dividend = abs(most_recent)
                        dividend_yield = (annual_dividend / market_cap) * 100

            if 'repurchase' in index.lower() or 'buyback' in index.lower():
                values = {k: v for k, v in row.items() if k != 'index'}
                if values:
                    most_recent = list(values.values())[0]
                    if most_recent and most_recent < 0:
                        has_buybacks = True

        return dividend_yield, has_buybacks

    except (json.JSONDecodeError, ValueError, KeyError):
        return None, False


def diagnostic_screen():
    """Run diagnostic screening showing filter pass rates."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            ticker,
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

    total = 0
    filter_counts = defaultdict(int)
    examples = defaultdict(list)

    for row in cursor:
        total += 1
        ticker = row['ticker']

        pb = row['price_to_book']
        roe = row['return_on_equity']
        pe = row['trailing_pe']
        market_cap = row['market_cap']

        # Track each filter
        try:
            if pb and float(pb) < 1.5:
                filter_counts['P/B < 1.5'] += 1
                if len(examples['P/B < 1.5']) < 5:
                    examples['P/B < 1.5'].append(f'{ticker} (P/B={float(pb):.2f})')
        except (ValueError, TypeError):
            pass

        try:
            if roe and float(roe) > 8.0:
                filter_counts['ROE > 8%'] += 1
                if len(examples['ROE > 8%']) < 5:
                    examples['ROE > 8%'].append(f'{ticker} (ROE={float(roe):.1f}%)')
        except (ValueError, TypeError):
            pass

        try:
            if pe and float(pe) < 15.0:
                filter_counts['P/E < 15'] += 1
                if len(examples['P/E < 15']) < 5:
                    examples['P/E < 15'].append(f'{ticker} (P/E={float(pe):.1f})')
        except (ValueError, TypeError):
            pass

        net_debt_equity = calculate_net_debt_to_equity(
            row['total_cash'], row['total_debt'],
            row['book_value'], row['shares_outstanding']
        )
        if net_debt_equity is not None and net_debt_equity < 1.0:
            filter_counts['Net Debt/Equity < 1.0'] += 1
            if len(examples['Net Debt/Equity < 1.0']) < 5:
                examples['Net Debt/Equity < 1.0'].append(f'{ticker} (ND/E={net_debt_equity:.2f})')

        fcf = get_fcf_from_json(row['cashflow_json'])
        if fcf and fcf > 0:
            filter_counts['FCF > 0'] += 1
            if len(examples['FCF > 0']) < 5:
                fcf_str = f'${fcf/1e9:.1f}B' if fcf > 1e9 else f'${fcf/1e6:.0f}M'
                examples['FCF > 0'].append(f'{ticker} (FCF={fcf_str})')

        div_yield, has_buybacks = get_dividend_info(row['cashflow_json'], market_cap)
        if div_yield and div_yield > 3.0:
            filter_counts['Div Yield > 3%'] += 1
            if len(examples['Div Yield > 3%']) < 5:
                examples['Div Yield > 3%'].append(f'{ticker} (Div={div_yield:.1f}%)')

        if has_buybacks or (div_yield and div_yield > 3.0):
            filter_counts['Shareholder Returns'] += 1
            if len(examples['Shareholder Returns']) < 5:
                ret_type = 'buybacks' if has_buybacks else f'div={div_yield:.1f}%'
                examples['Shareholder Returns'].append(f'{ticker} ({ret_type})')

    print(f'\n📊 Total stocks analyzed: {total}\n')
    print(f'{"Filter":<30} {"Count":<10} {"Pass %":<10} {"Examples"}')
    print('=' * 100)

    filters = [
        'P/B < 1.5',
        'ROE > 8%',
        'P/E < 15',
        'Net Debt/Equity < 1.0',
        'FCF > 0',
        'Div Yield > 3%',
        'Shareholder Returns'
    ]

    for f in filters:
        count = filter_counts[f]
        pct = (count / total * 100) if total > 0 else 0
        ex = ', '.join(examples[f][:3]) if examples[f] else 'None'
        print(f'{f:<30} {count:<10} {pct:<10.1f} {ex}')

    conn.close()


if __name__ == '__main__':
    diagnostic_screen()

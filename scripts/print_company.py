"""
Print info about a specific company
"""

import sys

import yfinance as yf

ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
stock = yf.Ticker(ticker)
search = ['cap', 'gross', 'margin', 'shares', 'grow', 'ratio', 'revenue', 'expense']

print(f"--- Info for {ticker} ---")

for line in stock.info:
    response_line = f"{line:>36}: {stock.info[line]}"

    # PRINT EVERYTHING from Yahoo Finance
    # print(response_line)

    # PRINT FILTERED stuff
    for item in search:
        if item in response_line.lower():
            print(response_line)


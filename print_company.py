"""
Print info about a specific company
"""

import yfinance as yf
import pandas as pd
import re

stock = yf.Ticker("AAPL")
search = ['cap', 'gross', 'margin', 'shares', 'grow', 'ratio', 'revenue', 'expense']

for line in stock.info:
    response_line = f"{line:>36}: {stock.info[line]}"
    
    # PRINT EVERYTHING from Yahoo Finance
    # print(response_line)
    
    # PRINT FILTERED stuff
    for item in search:
        if item in response_line.lower():
            print(response_line)
    

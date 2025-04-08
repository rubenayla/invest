"""
Analyze the companies in the YAML file, and print the best ones
[Companies YAML](./companies.yaml)

# To add a new company:
- Add a new entry in the [companies.yaml](./companies.yaml) file, with the parameters:
    - _ticker
    ```yaml
    valoration:
      _value_to_gross: 8 # Typical value
    ```
NOTE THAT THE VALORATION IS VERY SENSITIVE TO THE PARAMETER "VALUE_TO_GROSS", WHICH IS SUBJECTIVE

TODO FIX FOR SONY, SOME VALUES COME IN YEN, OTHERS IN DOLLARS
"""

import yfinance as yf
import yaml
from datetime import datetime
import os
import re

# Set the current folder to the parent of this python file
os.chdir(os.path.dirname(os.path.realpath(__file__)))

def fill(company: dict, verbose = True) -> None:
    """
    Fills company with info from Yahoo Finance
    Prints the updated info
    
    c must have at least a ticker key, in lowercase
    
    """
    stock = yf.Ticker(company["_ticker"])
    
    # Attributes to extract and their new names in the dictionary
    atts = [
        ("cap", "marketCap"),
        ("gross", "grossProfits"),
        ("shares", "sharesOutstanding"),
        ("fcf", "freeCashflow"),
        ("margin_gross", "grossMargins"),
        ("margin_operating", "operatingMargins"),
        ("margin_earnings", "profitMargins"),
        ("revenue_growth", "revenueGrowth"),
        ("price_to_earnings_1yr", "trailingPE"),
        ("name", "longName"),
    ]
    # Other attributes: profitMargins, floatShares, , sharesShort, sharesShortPriorMonth, sharesShortPreviousMonthDate, sharesPercentSharesOut, impliedSharesOutstanding, , revenueGrowth
    
    # Extracting and assigning data
    company["did_not_update"] = None
    for new_name, att in atts:
        value = stock.info.get(att)
        if value is not None:
            # Assign to dict
            company[new_name] = value
        else:
            # Note the error, data not available
            company["did_not_update"] = att
            # If there is no data, assign a small value to avoid division by zero
            if company.get(new_name) is None:
                company[new_name] = 1e-15
            # else, keep the previous value
    
    # Custom fields
    company["stock_price"] = stock.info.get("previousClose") # $/share
    company["gross"] = float(company["gross"]) # $/year
    company["price_to_gross"] = company["cap"] / company["gross"]
    company["shares"] = company["cap"] / company["stock_price"]
    company["equity"] = stock.balance_sheet.loc["Common Stock Equity"].iloc[0]
    company["total_debt"] = stock.balance_sheet.loc['Total Debt'].iloc[0]
    company["revenue"] = stock.financials.loc["Total Revenue"].iloc[0]
    company["earnings"] = stock.financials.loc["Net Income"].iloc[0]
    
    # Update last_updated, formatted like 202311272013
    company["last_updated"] = datetime.now().strftime("%Y.%m.%d %H:%M")
    company["equity_per_share"] = company.get("equity", 0) / company["shares"]
    
    
    # Print all parameters of company
    if verbose:
        for i in company:
            print(f'{i:>36}: {company[i]}')

def update_data(file_path: str = "companies.yaml", verbose = False) -> None:
    """
    Updates the companies in the YAML file with data from Yahoo Finance. Keeps custom names, and ignores invalid results.
    
    Args:
        file_path (str): _description_
        verbose (bool, optional): _description_. Defaults to False.
    """
    print(f"Updating data... (in ./{file_path})")
    # Reading the YAML file
    with open(file_path, 'r') as file:
        companies = yaml.safe_load(file)

    # Modifying the values
    for company in companies.values():
        fill(company, verbose=False)

    # Saving the modified company back to the YAML file
    with open(file_path, 'w') as file:
        yaml.dump(companies, file)

def update_company(ticker: str, file_path: str = "companies.yaml", verbose = False) -> None:
    """
    Updates the company given the ticker, and optional file_path and verbose parameter
    """
    print(f"Updating data for {ticker}... (in ./{file_path})")
    ticker = ticker.lower()
    
    with open(file_path, 'r') as file:
        companies = yaml.safe_load(file)
    fill(companies[ticker], verbose=verbose)
    with open(file_path, 'w') as file:
        yaml.dump(companies, file)
    
def analyze_company(c: dict) -> None:
    """
    Calculates valorations from the c company dictionary
    Adds or modifies the values in c
    
    Args:
        c (dict): company dictionary
    
    """
    # TODO price_to_net
    # Valoration - value_to_gross is subjective, gives a valoration to the gross profit generated. Ignores the equity, unlike price_to_gross
    if 'valoration' not in c:
        c['valoration'] = {}
    c_val = c['valoration']
    c_val['value'] = c['equity'] + c_val.get('_value_to_gross', -1e15) * c['gross']
    c_val['target_stock_price'] = c_val['value'] / c['shares']
    
    c_val['gain_factor'] = c_val['target_stock_price'] / c['stock_price']
    
    # Add warnings
    c_val['warnings']: str = ""
    
    if (c['cap']/c['gross']) > 10.:
        c_val['warnings'] += f"cap/gross > 10, = {c['cap']/c['gross']:.2f}\n"
    if c['gross'] < .1:
        c_val['warnings'] += f"gross < .1, = {c['gross']:.2f}\n"
    if c['equity'] < 0:
        c_val['warnings'] += f"equity < 0, = {c['equity']/1e6:.2f} million\n"

def analyze_companies(file_path: str = "companies.yaml", verbose = False) -> None:
    print(f"Analyzing... (in ./{file_path})")
    # Reading the YAML file
    with open(file_path, 'r') as file:
        companies = yaml.safe_load(file)

    # Modifying the values
    for company in companies.values():
        analyze_company(company)

    # Saving the modified company back to the YAML file
    with open(file_path, 'w') as file:
        yaml.dump(companies, file)
    
def print_best(file_path = "companies.yaml"):
    """
    Prints the companies in the file_path from best to worst
    """
    # Reading the YAML file
    with open(file_path, 'r') as file:
        companies = yaml.safe_load(file)
    
    # Sort companies
    companies = list(companies.values())
    companies.sort(key=lambda c: c['valoration']['gain_factor'], reverse=True) # or pass a function, f ex sorter(c): return c['valoration']['gain_factor']...
    
    # Print best
    print(f"BEST COMPANIES:\n  {'TICKER':>8} | {'GAIN FACTOR':>11} | {'PRICE':>6} | TARGET | WARNINGS (More in {file_path})")
    for c in companies:
        msg = f"  {c['_ticker']:>8} | {c['valoration']['gain_factor']:^11.2f} | {c['stock_price']:6.2f} | {c['valoration']['target_stock_price']:6.2f} | {c['valoration']['warnings']}"
        msg = msg.replace('\n', ', ')
        print(msg)
    
    # --- Test other sortings
    # companies.sort(key=lambda c: c['equity_per_share']/c['stock_price'], reverse=True)
    # for c in companies:
    #     print(f"{c['_ticker']:>8} | {c['equity_per_share']/c['stock_price']:6.2f} | {c['equity_per_share']:6.2f} | {c['stock_price']:6.2f}")

if __name__ == "__main__":
    update_data()
    analyze_companies()
    print_best()
import yfinance as yf
import pandas as pd
from typing import List, Dict, Optional


def get_stock_data(ticker: str) -> Optional[Dict]:
    """Get basic stock data from Yahoo Finance."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Get key financial metrics
        return {
            'ticker': ticker,
            'market_cap': info.get('marketCap'),
            'enterprise_value': info.get('enterpriseValue'),
            'trailing_pe': info.get('trailingPE'),
            'forward_pe': info.get('forwardPE'),
            'price_to_book': info.get('priceToBook'),
            'ev_to_ebitda': info.get('enterpriseToEbitda'),
            'ev_to_revenue': info.get('enterpriseToRevenue'),
            'return_on_equity': info.get('returnOnEquity'),
            'return_on_assets': info.get('returnOnAssets'),
            'debt_to_equity': info.get('debtToEquity'),
            'current_ratio': info.get('currentRatio'),
            'revenue_growth': info.get('revenueGrowth'),
            'earnings_growth': info.get('earningsGrowth'),
            'sector': info.get('sector'),
            'industry': info.get('industry'),
            'current_price': info.get('currentPrice'),
            'target_high_price': info.get('targetHighPrice'),
            'target_low_price': info.get('targetLowPrice'),
            'target_mean_price': info.get('targetMeanPrice'),
        }
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None


def get_financials(ticker: str) -> Optional[Dict]:
    """Get detailed financial statements."""
    try:
        stock = yf.Ticker(ticker)
        
        # Get financial statements
        income_stmt = stock.financials
        balance_sheet = stock.balance_sheet
        cash_flow = stock.cashflow
        
        return {
            'ticker': ticker,
            'income_statement': income_stmt.to_dict() if not income_stmt.empty else {},
            'balance_sheet': balance_sheet.to_dict() if not balance_sheet.empty else {},
            'cash_flow': cash_flow.to_dict() if not cash_flow.empty else {}
        }
    except Exception as e:
        print(f"Error fetching financials for {ticker}: {e}")
        return None


def get_universe_data(tickers: List[str]) -> pd.DataFrame:
    """Get data for a list of tickers."""
    data = []
    
    for ticker in tickers:
        stock_data = get_stock_data(ticker)
        if stock_data:
            data.append(stock_data)
    
    return pd.DataFrame(data)


# Common stock universes
SP500_TICKERS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'BRK.B', 'UNH', 'JNJ',
    'V', 'WMT', 'JPM', 'PG', 'XOM', 'HD', 'CVX', 'MA', 'BAC', 'ABBV',
    'PFE', 'AVGO', 'KO', 'LLY', 'MRK', 'PEP', 'TMO', 'COST', 'WFC', 'DIS'
    # Add more as needed
]


def get_sp500_sample() -> List[str]:
    """Get a sample of S&P 500 tickers for testing."""
    return SP500_TICKERS
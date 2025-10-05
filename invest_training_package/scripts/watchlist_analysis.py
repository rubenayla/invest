#!/usr/bin/env python3
"""Analyze stocks from watchlist using yfinance."""

import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any

def analyze_stocks(tickers: List[str]) -> pd.DataFrame:
    """Fetch and analyze stock data for given tickers."""
    analysis_results = []
    
    for ticker in tickers:
        try:
            print(f"Fetching data for {ticker}...")
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Calculate tangible book value per share
            book_value = info.get('bookValue', 0)
            intangible_assets = info.get('intangibleAssets', 0) or 0
            goodwill = info.get('goodwill', 0) or 0
            shares_outstanding = info.get('sharesOutstanding', 0) or info.get('impliedSharesOutstanding', 0)
            
            # Calculate tangible book value per share
            if shares_outstanding and book_value:
                total_book_value = book_value * shares_outstanding
                tangible_book_value = total_book_value - intangible_assets - goodwill
                tangible_book_value_per_share = tangible_book_value / shares_outstanding
                
                # Calculate P/TBV ratio
                current_price = info.get('currentPrice', 0)
                p_tbv = round(current_price / tangible_book_value_per_share, 2) if tangible_book_value_per_share > 0 else 'N/A'
            else:
                tangible_book_value_per_share = 'N/A'
                p_tbv = 'N/A'

            # Extract key metrics
            result = {
                'Ticker': ticker,
                'Current Price': info.get('currentPrice', 'N/A'),
                'P/E Ratio': info.get('trailingPE', 'N/A'),
                'Forward P/E': info.get('forwardPE', 'N/A'),
                'P/B Ratio': info.get('priceToBook', 'N/A'),
                'P/TBV Ratio': p_tbv,
                'TBV/Share': round(tangible_book_value_per_share, 2) if tangible_book_value_per_share != 'N/A' else 'N/A',
                'Market Cap (B)': round(info.get('marketCap', 0) / 1e9, 2) if info.get('marketCap') else 'N/A',
                'Gross Margin': f"{info.get('grossMargins', 0) * 100:.1f}%" if info.get('grossMargins') else 'N/A',
                'ROE': f"{info.get('returnOnEquity', 0) * 100:.1f}%" if info.get('returnOnEquity') else 'N/A',
                'Debt/Equity': round(info.get('debtToEquity', 0) / 100, 2) if info.get('debtToEquity') else 'N/A',
                '52W High': info.get('fiftyTwoWeekHigh', 'N/A'),
                '52W Low': info.get('fiftyTwoWeekLow', 'N/A'),
                'Dividend Yield': f"{info.get('dividendYield', 0) * 100:.2f}%" if info.get('dividendYield') else 'N/A'
            }
            
            # Calculate discount from 52W high
            if result['Current Price'] != 'N/A' and result['52W High'] != 'N/A':
                discount = ((result['52W High'] - result['Current Price']) / result['52W High']) * 100
                result['Discount from High'] = f"{discount:.1f}%"
            else:
                result['Discount from High'] = 'N/A'
                
            analysis_results.append(result)
            
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            analysis_results.append({'Ticker': ticker, 'Error': str(e)})
    
    return pd.DataFrame(analysis_results)

def identify_value_stocks(df: pd.DataFrame) -> None:
    """Identify potentially undervalued stocks based on metrics."""
    print("\n=== VALUE OPPORTUNITIES ===\n")
    
    for _, row in df.iterrows():
        if 'Error' in row:
            continue
            
        value_signals = []
        
        # Check P/E ratio
        if row['P/E Ratio'] != 'N/A' and row['P/E Ratio'] < 15:
            value_signals.append(f"Low P/E: {row['P/E Ratio']:.1f}")
        
        # Check P/B ratio
        if row['P/B Ratio'] != 'N/A' and row['P/B Ratio'] < 1.5:
            value_signals.append(f"Low P/B: {row['P/B Ratio']:.1f}")
        
        # Check discount from high
        if row['Discount from High'] != 'N/A':
            discount_val = float(row['Discount from High'].strip('%'))
            if discount_val > 30:
                value_signals.append(f"Deep discount: {row['Discount from High']}")
        
        # Check ROE
        if row['ROE'] != 'N/A':
            roe_val = float(row['ROE'].strip('%'))
            if roe_val > 15:
                value_signals.append(f"High ROE: {row['ROE']}")
        
        if value_signals:
            print(f"{row['Ticker']}: {', '.join(value_signals)}")

def main():
    """Main analysis function."""
    # Tickers from watchlist
    wallet_tickers = ['MOH', 'TSLA', 'SQM', 'BRK-B', 'STLD', 'CVX']
    watchlist_tickers = ['ACGL', 'NEM', 'HIG', 'NE', 'ALLE', 'DHI', 'LAMR', 'NUE']
    tech_tickers = ['QCOM', 'ASML', 'META', 'ORCL', 'IBM', 'CSCO', 'PYPL']
    
    print("=== ANALYZING WALLET STOCKS ===")
    wallet_df = analyze_stocks(wallet_tickers)
    print("\n", wallet_df.to_string(index=False))
    
    print("\n=== ANALYZING WATCHLIST STOCKS ===")
    watchlist_df = analyze_stocks(watchlist_tickers)
    print("\n", watchlist_df.to_string(index=False))
    
    print("\n=== ANALYZING TECH STOCKS ===")
    tech_df = analyze_stocks(tech_tickers[:4])  # Limit to avoid rate limiting
    print("\n", tech_df.to_string(index=False))
    
    # Combine all for value analysis
    all_df = pd.concat([wallet_df, watchlist_df, tech_df], ignore_index=True)
    identify_value_stocks(all_df)
    
    # Export to CSV
    output_file = 'watchlist_analysis.csv'
    all_df.to_csv(output_file, index=False)
    print(f"\n✅ Analysis exported to {output_file}")

if __name__ == '__main__':
    main()
"""
TODO yf.Ticker("MSFT").earnings does not work. wrong package or python version. bug.

Filter stocks with python
- yfinance
    - This only works there: https://colab.research.google.com/drive/1wmJAzTsa1-wmQT2SMAHMl0dBovFNWpbv
    - pip install git+https://github.com/rodrigobercini/yfinance.git
    - (Alternative) python3 -m pip install yfinance
    - https://pypi.org/project/yfinance/
    - Recent url update problem: https://github.com/ranaroussi/yfinance/issues/254
- 20 calls/day free package
    - https://eodhistoricaldata.com/pricing?utm_source=medium&utm_medium=post&utm_campaign=extracting_financial_news_seamlessly_using_python
    - https://medium.com/codex/creating-a-simple-stock-screener-in-minutes-with-python-68c888d2fbf0
Alternative that costs money: https://www.alphavantage.co/
"""

import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Fetch stock data from yfinance
# data = yf.download('AAPL MSFT GOOGL AMZN META INTC NVDA GDOT ADBE CRM CSCO PYPL NFLX TSLA ORCL IBM SAP QCOM BIDU JD AMD SNAP PDD SHOP DOCU ZM BABA ATVI UBER LYFT SQ LRCX ZS NOW OKTA TEAM CRWD PINS ZI DOCN ESTC ROKU VMW SPLK AKAM TWLO HUBS RNG LSCC CRWD RGEN ETSY MPWR ARLO SFM HUBS APPS IPGP TEAM RPD VREX QDEL PLNT DORM QNST MRCY',
#                    period='1d', start='2022-01-01', end='2022-12-31')

data = yf.download('AAPL MSFT GOOGL AMZN META INTC NVDA GDOT ADBE CRM CSCO PYPL NFLX TSLA ORCL IBM SAP QCOM BIDU JD',
                   period='1d', start='2022-01-01', end='2022-12-31')

# data = yf.download('AAPL MSFT GOOGL AMZN', period='1d', start='2022-01-01', end=datetime.now().strftime('%Y-%m-%d'))

tickers = data['Close'].columns # Use the close data for each day
# Create an empty DataFrame to store the fundamental data
fundamental_data = pd.DataFrame() #columns=['Ticker', 'MarketCap', 'gross_profit', 'SharesOutstanding','revenue_growth','revenue']

# msft = yf.Ticker("MSFT")
# for i in msft.info:
#     print(f'{i:>36}: {msft.info[i]}')

for ticker in [ticker for ticker in tickers if ((yf.Ticker(ticker).info.get('revenueGrowth') is not None) and
                                                      (yf.Ticker(ticker).info.get('grossProfits') is not None) and
                                                      (yf.Ticker(ticker).info.get('marketCap') is not None))]:
    # Get stock data
    stock = data['Close'][ticker]
    
    # Get fundamental data
    stock_info = yf.Ticker(ticker).info
    
    # Append fundamental data to `fundamental_data`
    fundamental_data = fundamental_data.append({
        'Ticker': ticker,
        'MarketCap': stock_info.get('marketCap'),
        'gross_profit': stock_info.get('grossProfits'),
        'SharesOutstanding': stock_info.get('sharesOutstanding'),
        'revenue': stock_info.get('totalRevenue'),
        # 'cost_of_revenue': stock_info.get('costOfRevenue'),
        # 'equity': stock_info.get('totalStockholderEquity'),
        'freeCashflow': stock_info.get('freeCashflow'),
        'cap_over_gross': stock_info.get('marketCap')/stock_info.get('grossProfits'), #check1, P/E ratio
        # 'grossMargins': stock_info.get('grossMargins'),
        'operatingMargins': stock_info.get('operatingMargins'), #check2
        # 'profitMargins': stock_info.get('profitMargins'),
        'revenueGrowth': stock_info.get('revenueGrowth'), #check3 TODO Growth how many years in the past
        # 'earningsGrowth': stock_info.get('earningsGrowth'),
        'netIncomeToCommon': stock_info.get('netIncomeToCommon'),
    }, ignore_index=True)


# Print the fundamental data
# print(fundamental_data)

# FILTER
filtered = fundamental_data[(fundamental_data['operatingMargins'] > 0.1) & (fundamental_data['cap_over_gross'] < 10)]

print(f'FILTERED COMPANIES: \n{filtered}')


"""
0 language
1 region
2 quoteType
3 quoteSourceName
4 epsForward
5 currency
6 sharesOutstanding
7 bidSize
8 trailingPE
9 priceToBook
10 dividendDate
11 regularMarketChangePercent
12 market
13 fiftyDayAverageChange
14 forwardPE
15 regularMarketPrice
16 regularMarketTime
17 regularMarketChange
18 regularMarketOpen
19 regularMarketDayHigh
20 regularMarketDayLow
21 regularMarketVolume
22 bookValue
23 ask
24 regularMarketPreviousClose
25 preMarketChangePercent
26 regularMarketDayRange
27 twoHundredDayAverageChange
28 bid
29 fiftyTwoWeekLowChange
30 askSize
31 financialCurrency
32 twoHundredDayAverage
33 gmtOffSetMilliseconds
34 shortName
35 longName
36 preMarketChange
37 twoHundredDayAverageChangePercent
38 trailingAnnualDividendYield
39 exchangeDataDelayedBy
40 fiftyTwoWeekLow
41 fiftyTwoWeekHigh
42 averageDailyVolume3Month
43 fiftyDayAverage
44 exchangeTimezoneShortName
45 esgPopulated
46 marketState
47 marketCap
48 epsTrailingTwelveMonths
49 fullExchangeName
50 earningsTimestampStart
51 earningsTimestampEnd
52 trailingAnnualDividendRate
53 earningsTimestamp
54 fiftyTwoWeekLowChangePercent
55 fiftyTwoWeekHighChangePercent
56 averageDailyVolume10Day
57 exchange
58 priceHint
59 exchangeTimezoneName
60 preMarketTime
61 fiftyDayAverageChangePercent
62 fiftyTwoWeekRange
63 tradeable
64 fiftyTwoWeekHighChange
65 preMarketPrice
66 sourceInterval
67 messageBoardId
68 price
"""
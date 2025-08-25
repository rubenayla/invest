from typing import Dict, List, Optional

import pandas as pd
import requests
import yfinance as yf
from bs4 import BeautifulSoup

from ..config.logging_config import get_logger, log_data_fetch, log_error_with_context
from ..caching.cache_decorators import cached_api_call, cache_result_by_ticker

logger = get_logger(__name__)


@cached_api_call(data_type='sp500_tickers', ttl=24*3600, key_prefix='sp500')
def get_sp500_tickers() -> List[str]:
    """Get the list of S&P 500 tickers from Wikipedia."""
    logger.info("Fetching S&P 500 tickers from Wikipedia (not cached)")
    
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Get all wikitable tables and find the one with 'Symbol' header (constituents table)
    tables = soup.find_all("table", {"class": "wikitable"})
    constituents_table = None

    for table in tables:
        header_row = table.find("tr")
        if header_row:
            headers = [th.text.strip() for th in header_row.find_all(["th", "td"])]
            if headers and headers[0] == "Symbol":
                constituents_table = table
                break

    if not constituents_table:
        raise ValueError("Could not find S&P 500 constituents table")

    tickers = []
    for row in constituents_table.find_all("tr")[1:]:  # Skip header row
        cells = row.find_all("td")
        if len(cells) > 0:
            ticker = cells[0].text.strip()
            # Yahoo Finance uses dashes for some tickers, e.g. BRK-B
            ticker = ticker.replace(".", "-")
            tickers.append(ticker)

    logger.info(f"Successfully fetched {len(tickers)} S&P 500 tickers")
    return tickers


@cache_result_by_ticker('stock_info', ttl=24*3600)  # 24 hours
def get_stock_data(ticker: str) -> Optional[Dict]:
    """
    Get basic stock data from Yahoo Finance.
    
    This function is now cached to improve performance and reduce API calls.
    Returns normalized data with consistent field names.
    """
    try:
        log_data_fetch(logger, ticker, "stock_data", True)
        
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not info or 'regularMarketPrice' not in info:
            log_data_fetch(logger, ticker, "stock_data", False, error="No market data available")
            return None
            
        # Transform raw yfinance data to normalized format
        result = {
            "ticker": info.get("symbol", ticker),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "market_cap": info.get("marketCap"),
            "enterprise_value": info.get("enterpriseValue"),
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "trailing_pe": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "price_to_book": info.get("priceToBook"),
            "ev_to_ebitda": info.get("enterpriseToEbitda"),
            "ev_to_revenue": info.get("enterpriseToRevenue"),
            "return_on_equity": info.get("returnOnEquity"),
            "return_on_assets": info.get("returnOnAssets"),
            "debt_to_equity": info.get("debtToEquity"),
            "current_ratio": info.get("currentRatio"),
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
            "country": info.get("country"),
            "currency": info.get("currency"),
            "exchange": info.get("exchange"),
        }
        
        log_data_fetch(logger, ticker, "stock_data", True)
        return result
        
    except Exception as e:
        log_data_fetch(logger, ticker, "stock_data", False, error=str(e))
        return None


def get_financials(ticker: str) -> Optional[Dict]:
    """
    Get detailed financial statements.
    
    DEPRECATED: Use the new provider system instead:
    from src.invest.data.providers import get_provider_manager
    financial_statements = get_provider_manager().get_financial_statements(ticker)
    """
    try:
        # Use the new provider system internally for consistency
        from .providers import get_provider_manager
        manager = get_provider_manager()
        
        # Ensure we have providers setup
        if not manager.providers:
            from .providers import setup_default_providers
            setup_default_providers()
        
        financial_statements = manager.providers[manager.primary_provider].get_financial_statements(ticker)
        
        return {
            "ticker": ticker,
            "income_statement": financial_statements.financials,
            "balance_sheet": financial_statements.balance_sheet,
            "cash_flow": financial_statements.cash_flow,
        }
        
    except Exception as e:
        log_data_fetch(logger, ticker, "financials", False, error=str(e))
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
# Use a lazy-loading class to avoid network calls at import time
class _LazySP500Tickers:
    def __init__(self):
        self._tickers = None
    
    def __call__(self):
        if self._tickers is None:
            self._tickers = get_sp500_tickers()
        return self._tickers
    
    def __iter__(self):
        return iter(self())
    
    def __getitem__(self, key):
        return self()[key]
    
    def __len__(self):
        return len(self())

SP500_TICKERS = _LazySP500Tickers()


def get_sp500_sample() -> List[str]:
    """Get a sample of S&P 500 tickers for testing."""
    return SP500_TICKERS[:30]


def get_russell_2000_sample() -> List[str]:
    """Get a sample of smaller US companies similar to Russell 2000."""
    # Major small-cap and mid-cap US stocks
    russell_2000_sample = [
        # Technology
        'CYBR', 'FRPT', 'TENB', 'ESTC', 'NET', 'DDOG', 'SNOW', 'MDB', 'OKTA', 'ZS',
        'CRWD', 'S', 'FSLY', 'PLAN', 'TWLO', 'ZM', 'DOCN', 'PATH', 'GTLB', 'BILL',
        # Healthcare & Biotech
        'MRNA', 'NVAX', 'REGN', 'VRTX', 'ALNY', 'BMRN', 'TECB', 'ROIV', 'HALO', 'IONS',
        'SRPT', 'RARE', 'FOLD', 'ARWR', 'EDIT', 'NTLA', 'CRSP', 'BLUE', 'SAGE', 'PTCT',
        # Financial Services
        'SOFI', 'UPST', 'AFRM', 'PYPL', 'SQ', 'HOOD', 'COIN', 'OPEN', 'RKT', 'WISH',
        # Consumer & Retail
        'PTON', 'ROKU', 'NFLX', 'DIS', 'SPOT', 'UBER', 'LYFT', 'DASH', 'ABNB', 'ETSY',
        'W', 'CHWY', 'RVLV', 'STMP', 'FTCH', 'REAL', 'CVNA', 'CARG', 'VROOM', 'KMX',
        # Energy & Materials
        'FSLR', 'ENPH', 'SEDG', 'RUN', 'SPWR', 'PLUG', 'BE', 'BLDP', 'FCEL', 'CLNE',
        # Industrial & Transportation
        'SPCE', 'RKLB', 'JOBY', 'LILM', 'EVTL', 'ACHR', 'BLDE', 'EH', 'NKLA', 'RIDE',
        # Real Estate & REITs
        'RDFN', 'Z', 'OPEN', 'COMP', 'EXPI', 'HOUS', 'RMAX', 'PFGC', 'CIGI', 'NMRK',
    ]
    return russell_2000_sample


def get_sp600_smallcap() -> List[str]:
    """Get S&P SmallCap 600 representative stocks."""
    # Representative S&P 600 small-cap stocks
    sp600_sample = [
        # Technology
        'CACI', 'SAIC', 'MAXR', 'KTOS', 'AVAV', 'KRNT', 'PLTK', 'ADTN', 'CSGS', 'NTCT',
        # Healthcare
        'GKOS', 'OMCL', 'PCVX', 'PDCO', 'HSTM', 'TMDX', 'NEOG', 'ATRC', 'CRVL', 'IRTC',
        # Consumer Discretionary
        'BOOT', 'CREE', 'DORM', 'EXPR', 'FIZZ', 'GIII', 'HIBB', 'KIRK', 'LOVE', 'MCFT',
        # Industrials
        'AAON', 'AEIS', 'AGCO', 'AIT', 'ALGT', 'AMRC', 'ARCB', 'TILE', 'BLKB', 'BRC',
        # Financial Services
        'BANF', 'BHLB', 'BRKL', 'CATY', 'CBSH', 'CHCO', 'CIZN', 'CNB', 'COLB', 'CVBF',
        # Materials & Energy
        'BCPC', 'CBT', 'CENX', 'CRC', 'CPE', 'CRK', 'EQT', 'FANG', 'HCC', 'MGY',
    ]
    return sp600_sample


def get_nasdaq_smallcap() -> List[str]:
    """Get NASDAQ small-cap stocks for broader market exposure."""
    nasdaq_smallcap = [
        # Biotech & Life Sciences
        'ACAD', 'ADMA', 'AGTC', 'AIMT', 'AKBA', 'ALNA', 'AMRN', 'ANIK', 'ARDX', 'ARNA',
        'AXSM', 'BCRX', 'BDTX', 'BIIB', 'BPMC', 'BPTH', 'BTAI', 'CAPR', 'CARA', 'CBIO',
        # Technology & Software
        'ADBE', 'APPS', 'ATUS', 'AVID', 'BAND', 'BBOX', 'BLFS', 'CAMP', 'CIEN', 'CLDR',
        'CLSK', 'CMPR', 'COMM', 'COUP', 'CRNC', 'CRTO', 'DAKT', 'DCOM', 'DGII', 'DIOD',
        # Consumer & Services
        'CAKE', 'CBRL', 'CHUY', 'CMG', 'DENN', 'DIN', 'DNKN', 'EAT', 'FRGI', 'JACK',
        'KRUS', 'LOCO', 'NDLS', 'NOODLES', 'PBPB', 'PZZA', 'QSR', 'RRGB', 'RUTH', 'SHAK',
    ]
    return nasdaq_smallcap


def get_emerging_growth_stocks() -> List[str]:
    """Get emerging growth companies across different sectors."""
    emerging_growth = [
        # FinTech & Digital Payments
        'AFRM', 'SOFI', 'UPST', 'MELI', 'PAGS', 'STNE', 'NU', 'BKNG', 'PYPL', 'SQ',
        # Cloud & SaaS
        'SNOW', 'DDOG', 'CRWD', 'ZS', 'OKTA', 'NET', 'MDB', 'ESTC', 'TENB', 'FRPT',
        # E-commerce & Marketplaces
        'SHOP', 'ETSY', 'MELI', 'SE', 'BABA', 'JD', 'PDD', 'CPNG', 'GRAB', 'UBER',
        # Electric Vehicles & Clean Energy
        'TSLA', 'NIO', 'XPEV', 'LI', 'LCID', 'RIVN', 'ENPH', 'SEDG', 'FSLR', 'RUN',
        # Streaming & Digital Media
        'ROKU', 'FUBO', 'NFLX', 'DIS', 'SPOT', 'RBLX', 'U', 'TWTR', 'SNAP', 'PINS',
        # Healthcare Innovation
        'TDOC', 'VEEV', 'DXCM', 'ILMN', 'ISRG', 'NVTA', 'PACB', 'TMO', 'DHR', 'A',
    ]
    return emerging_growth


@cached_api_call(data_type='nyse_tickers', ttl=24*3600, key_prefix='nyse')
def get_nyse_tickers() -> List[str]:
    """Get all NYSE-listed tickers from NASDAQ's API."""
    logger.info("Fetching NYSE tickers from NASDAQ API (not cached)")
    
    try:
        # Use NASDAQ's API to get all NYSE listings
        url = "https://api.nasdaq.com/api/screener/stocks"
        params = {
            'tableonly': 'true',
            'limit': '25000',
            'exchange': 'NYSE'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        if 'data' not in data or 'table' not in data['data'] or 'rows' not in data['data']['table']:
            logger.warning("Unexpected NYSE API response format, falling back to hardcoded list")
            return _get_nyse_fallback_tickers()
        
        tickers = []
        for row in data['data']['table']['rows']:
            symbol = row.get('symbol', '').strip()
            if symbol and len(symbol) <= 5:  # Filter out weird symbols
                # Skip symbols with special characters that might cause issues
                if not any(char in symbol for char in ['.', '/', '+', '=']):
                    tickers.append(symbol)
        
        if len(tickers) < 1000:  # Sanity check - NYSE should have many tickers
            logger.warning(f"Got only {len(tickers)} NYSE tickers, falling back to hardcoded list")
            return _get_nyse_fallback_tickers()
        
        logger.info(f"Successfully fetched {len(tickers)} NYSE tickers")
        return sorted(tickers)
        
    except Exception as e:
        logger.error(f"Failed to fetch NYSE tickers from API: {e}")
        return _get_nyse_fallback_tickers()


def _get_nyse_fallback_tickers() -> List[str]:
    """Fallback list of major NYSE tickers including key companies like SQM."""
    logger.info("Using fallback NYSE ticker list")
    
    # Major NYSE companies across sectors, including SQM
    fallback_tickers = [
        # Large Cap Tech & Communication
        'T', 'VZ', 'IBM', 'CRM', 'ORCL', 'ACN', 'TXN', 'NOW', 'ADBE', 'INTU',
        # Financial Services
        'JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'AXP', 'V', 'MA', 'COF', 'USB', 'PNC',
        # Healthcare & Pharma
        'JNJ', 'PFE', 'ABT', 'MRK', 'BMY', 'LLY', 'UNH', 'CVS', 'ANTM', 'CI', 'HUM',
        # Consumer Goods
        'PG', 'KO', 'PEP', 'WMT', 'HD', 'NKE', 'MCD', 'SBUX', 'DIS', 'CMCSA',
        # Industrial & Manufacturing  
        'GE', 'CAT', 'BA', 'MMM', 'HON', 'LMT', 'RTX', 'UPS', 'FDX', 'DE', 'EMR',
        # Energy & Utilities
        'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'OXY', 'KMI', 'WMB', 'EPD', 'ET',
        # Materials & Mining (including SQM!)
        'SQM', 'FCX', 'NEM', 'GOLD', 'AA', 'X', 'CLF', 'NUE', 'STLD', 'DD',
        # Real Estate & REITs
        'AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'EXR', 'AVB', 'EQR', 'UDR', 'ESS',
        # Retail & E-commerce
        'COST', 'TGT', 'LOW', 'TJX', 'ROST', 'DG', 'DLTR', 'BBY', 'GPS', 'M',
        # Transportation & Logistics
        'UNP', 'CSX', 'NSC', 'CP', 'KSU', 'JBHT', 'CHRW', 'XPO', 'ODFL', 'SAIA',
        # Aerospace & Defense
        'LHX', 'NOC', 'GD', 'LMT', 'RTX', 'TDG', 'HII', 'TXT', 'CW', 'KTOS',
        # International Companies on NYSE
        'NVO', 'ASML', 'SAP', 'UL', 'SNY', 'DEO', 'BCS', 'ING', 'E', 'MT',
        # Energy Infrastructure
        'ENB', 'TRP', 'PPL', 'AEP', 'DTE', 'ED', 'EIX', 'PCG', 'PEG', 'SO',
        # Biotech & Life Sciences
        'GILD', 'AMGN', 'REGN', 'VRTX', 'BIIB', 'CELG', 'MYL', 'AGN', 'ZTS', 'TMO',
        # Chemicals & Specialty Materials
        'LIN', 'APD', 'ECL', 'PPG', 'SHW', 'NEM', 'VMC', 'MLM', 'ALB', 'CE',
    ]
    
    return sorted(fallback_tickers)

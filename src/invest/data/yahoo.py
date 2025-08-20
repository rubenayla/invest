from typing import Dict, List, Optional

import pandas as pd
import requests
import yfinance as yf
from bs4 import BeautifulSoup

from ..config.logging_config import get_logger, log_data_fetch, log_error_with_context

logger = get_logger(__name__)


def get_sp500_tickers() -> List[str]:
    """Get the list of S&P 500 tickers from Wikipedia."""
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

    return tickers


def get_stock_data(ticker: str) -> Optional[Dict]:
    """
    Get basic stock data from Yahoo Finance.
    
    DEPRECATED: Use the new provider system instead:
    from src.invest.data.providers import get_stock_info
    stock_info = get_stock_info(ticker)
    stock_data = stock_info.to_dict()
    """
    try:
        # Use the new provider system internally for consistency
        from .providers import get_provider_manager
        manager = get_provider_manager()
        
        # Ensure we have providers setup
        if not manager.providers:
            from .providers import setup_default_providers
            setup_default_providers()
        
        stock_info = manager.get_stock_info(ticker)
        return stock_info.to_dict()
        
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
SP500_TICKERS = get_sp500_tickers()


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

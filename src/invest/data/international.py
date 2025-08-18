from typing import Dict, List, Optional

import requests
import yfinance as yf
from bs4 import BeautifulSoup


def get_nikkei225_tickers() -> List[str]:
    """Get the list of Nikkei 225 tickers from Wikipedia."""
    url = "https://en.wikipedia.org/wiki/Nikkei_225"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Find the constituents table
    tables = soup.find_all("table", {"class": "wikitable"})
    constituents_table = None

    for table in tables:
        header_row = table.find("tr")
        if header_row:
            headers = [th.text.strip() for th in header_row.find_all(["th", "td"])]
            # Look for table with ticker/symbol column
            if any("Code" in header or "Symbol" in header for header in headers):
                constituents_table = table
                break

    if not constituents_table:
        # Fallback to manual list of major Japanese stocks
        return get_major_japanese_stocks()

    tickers = []
    for row in constituents_table.find_all("tr")[1:]:  # Skip header row
        cells = row.find_all("td")
        if len(cells) >= 2:
            # The code is usually in the first or second column
            code = cells[0].text.strip()
            if code.isdigit():
                # Add .T suffix for Tokyo Stock Exchange
                ticker = f"{code}.T"
                tickers.append(ticker)

    return tickers if tickers else get_major_japanese_stocks()


def get_major_japanese_stocks() -> List[str]:
    """Get a curated list of major Japanese stocks (Nikkei 225 components)."""
    # Major Japanese stocks with their Tokyo Stock Exchange codes
    major_japanese = [
        # Technology & Electronics
        "6758.T",  # Sony Group Corporation
        "7974.T",  # Nintendo Co., Ltd.
        "6861.T",  # Keyence Corporation
        "8035.T",  # Tokyo Electron Limited
        "4689.T",  # Yahoo Japan (Z Holdings)
        "9984.T",  # SoftBank Group Corp
        "6954.T",  # Fanuc Corporation
        # Automotive
        "7203.T",  # Toyota Motor Corporation
        "7267.T",  # Honda Motor Co., Ltd.
        "7201.T",  # Nissan Motor Co., Ltd.
        "7269.T",  # Suzuki Motor Corporation
        "7211.T",  # Mitsubishi Motors Corporation
        # Financial Services
        "8306.T",  # Mitsubishi UFJ Financial Group
        "8316.T",  # Sumitomo Mitsui Financial Group
        "8411.T",  # Mizuho Financial Group
        "8604.T",  # Nomura Holdings
        # Industrial & Manufacturing
        "9020.T",  # East Japan Railway Company
        "9021.T",  # West Japan Railway Company
        "6501.T",  # Hitachi, Ltd.
        "6502.T",  # Toshiba Corporation
        "7751.T",  # Canon Inc.
        "4901.T",  # Fujifilm Holdings Corporation
        # Retail & Consumer
        "4568.T",  # First Retailing Co., Ltd. (Uniqlo)
        "8267.T",  # AEON Co., Ltd.
        "2802.T",  # Ajinomoto Co., Inc.
        "2914.T",  # Japan Tobacco Inc.
        "4502.T",  # Takeda Pharmaceutical Company
        # Telecommunications
        "9432.T",  # Nippon Telegraph and Telephone Corporation (NTT)
        "9434.T",  # SoftBank Corp.
        "9433.T",  # KDDI Corporation
        # Energy & Materials
        "1605.T",  # INPEX Corporation
        "5020.T",  # ENEOS Holdings
        "5401.T",  # Nippon Steel Corporation
        "4063.T",  # Shin-Etsu Chemical Co., Ltd.
        # Real Estate & Construction
        "1928.T",  # Sekisui House, Ltd.
        "1801.T",  # Taisei Corporation
        "8802.T",  # Mitsubishi Estate Company
    ]

    return major_japanese


def get_ftse100_tickers() -> List[str]:
    """Get major UK stocks (FTSE 100 components)."""
    # Major UK stocks - using London Stock Exchange codes
    ftse_major = [
        # Financial Services
        "LLOY.L",  # Lloyds Banking Group
        "BARC.L",  # Barclays
        "RBS.L",  # NatWest Group
        "HSBA.L",  # HSBC Holdings
        "VOD.L",  # Vodafone Group
        # Oil & Gas
        "SHEL.L",  # Shell plc
        "BP.L",  # BP plc
        # Mining
        "RIO.L",  # Rio Tinto
        "AAL.L",  # Anglo American
        "GLEN.L",  # Glencore
        # Consumer Goods
        "ULVR.L",  # Unilever
        "DGE.L",  # Diageo
        "RKT.L",  # Reckitt Benckiser
        # Utilities
        "NG.L",  # National Grid
        "SSE.L",  # SSE
        # Technology
        "SAGE.L",  # Sage Group
    ]

    # Also include ADRs trading on US exchanges
    uk_adrs = [
        "SHEL",  # Shell ADR
        "BP",  # BP ADR
        "RIO",  # Rio Tinto ADR
        "UL",  # Unilever ADR
        "DEO",  # Diageo ADR
        "VOD",  # Vodafone ADR
    ]

    return ftse_major + uk_adrs


def get_dax_tickers() -> List[str]:
    """Get major German stocks (DAX components)."""
    # Major German stocks
    dax_major = [
        # Technology
        "SAP.DE",  # SAP SE
        # Automotive
        "VOW3.DE",  # Volkswagen
        "BMW.DE",  # BMW
        "MBG.DE",  # Mercedes-Benz Group
        # Financial Services
        "DBK.DE",  # Deutsche Bank
        "ALV.DE",  # Allianz
        # Industrial
        "SIE.DE",  # Siemens
        "BAS.DE",  # BASF
        "LIN.DE",  # Linde
        # Consumer
        "ADS.DE",  # Adidas
    ]

    # Also include ADRs
    german_adrs = [
        "SAP",  # SAP ADR
        "ADDYY",  # Adidas ADR
        "BAMXF",  # BMW ADR (OTC)
        "VLKAY",  # Volkswagen ADR
    ]

    return dax_major + german_adrs


def get_topix_core30_tickers() -> List[str]:
    """Get TOPIX Core 30 - the largest 30 Japanese stocks."""
    return [
        "7203.T",  # Toyota Motor
        "6758.T",  # Sony Group
        "8306.T",  # Mitsubishi UFJ Financial
        "9984.T",  # SoftBank Group
        "6861.T",  # Keyence
        "8316.T",  # Sumitomo Mitsui Financial
        "9432.T",  # NTT
        "4502.T",  # Takeda Pharmaceutical
        "6501.T",  # Hitachi
        "7974.T",  # Nintendo
        "8411.T",  # Mizuho Financial
        "9020.T",  # East Japan Railway
        "7267.T",  # Honda Motor
        "4568.T",  # Fast Retailing (Uniqlo)
        "6954.T",  # Fanuc
        "8035.T",  # Tokyo Electron
        "9433.T",  # KDDI
        "4063.T",  # Shin-Etsu Chemical
        "7751.T",  # Canon
        "6098.T",  # Recruit Holdings
        "2802.T",  # Ajinomoto
        "8802.T",  # Mitsubishi Estate
        "4901.T",  # Fujifilm Holdings
        "5020.T",  # ENEOS Holdings
        "7201.T",  # Nissan Motor
        "8604.T",  # Nomura Holdings
        "5401.T",  # Nippon Steel
        "9021.T",  # West Japan Railway
        "8267.T",  # AEON
        "1605.T",  # INPEX
    ]


def get_international_stock_data(ticker: str) -> Optional[Dict]:
    """Get stock data for international stocks with currency handling."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Get currency info for international stocks
        currency = info.get("currency", "USD")
        financial_currency = info.get("financialCurrency", currency)

        return {
            "ticker": ticker,
            "market_cap": info.get("marketCap"),
            "enterprise_value": info.get("enterpriseValue"),
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
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "current_price": info.get("currentPrice"),
            "target_high_price": info.get("targetHighPrice"),
            "target_low_price": info.get("targetLowPrice"),
            "target_mean_price": info.get("targetMeanPrice"),
            "currency": currency,
            "financial_currency": financial_currency,
            "country": info.get("country"),
            "exchange": info.get("exchange"),
            "market": info.get("market"),
        }
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None


# Market universe mappings
MARKET_UNIVERSES = {
    "japan_major": get_major_japanese_stocks(),
    "japan_topix30": get_topix_core30_tickers(),
    "uk_ftse": get_ftse100_tickers(),
    "germany_dax": get_dax_tickers(),
    "usa_sp500": None,  # Will use existing SP500 function
}


def get_market_tickers(market: str) -> List[str]:
    """Get tickers for a specific market."""
    if market == "usa_sp500":
        from .yahoo import get_sp500_tickers

        return get_sp500_tickers()
    elif market in MARKET_UNIVERSES:
        return MARKET_UNIVERSES[market]
    else:
        raise ValueError(f"Unknown market: {market}. Available: {list(MARKET_UNIVERSES.keys())}")


def get_buffett_favorites_japan() -> List[str]:
    """Get Japanese stocks that Warren Buffett has invested in or expressed interest in."""
    # Berkshire Hathaway's known Japanese holdings and interests
    return [
        # Berkshire's "Big 5" Japanese Trading Houses (Sogo Shosha)
        "8058.T",  # Mitsubishi Corporation
        "8031.T",  # Mitsui & Co.
        "8001.T",  # Itochu Corporation
        "2768.T",  # Sumitomo Corporation
        "8002.T",  # Marubeni Corporation
        # Other Japanese companies Buffett has mentioned positively
        "7203.T",  # Toyota Motor - Quality, moat, reasonable valuation
        "6758.T",  # Sony Group - Brand strength, diversified business
        "4502.T",  # Takeda Pharmaceutical - Healthcare, dividend
        "9984.T",  # SoftBank Group - Technology investments (though volatile)
        "8306.T",  # Mitsubishi UFJ Financial - Banking, undervalued
        "8316.T",  # Sumitomo Mitsui Financial - Banking, undervalued
        # Additional value plays that fit Buffett's criteria
        "6861.T",  # Keyence - High ROE, strong moat in automation
        "7974.T",  # Nintendo - Brand strength, recurring revenue
        "9020.T",  # East Japan Railway - Infrastructure, steady cash flows
        "4568.T",  # Fast Retailing (Uniqlo) - Consumer brand, expansion
    ]


def get_warren_buffett_international() -> List[str]:
    """Get international stocks that align with Warren Buffett's investment philosophy."""
    buffett_international = []

    # Japan - Berkshire's major positions and value plays
    buffett_international.extend(get_buffett_favorites_japan())

    # Europe - Companies that fit Buffett's criteria
    europe_buffett_style = [
        "NESN.SW",  # Nestlé - Consumer staples, brand moat
        "ASML.AS",  # ASML - Technology moat, essential equipment
        "UL",  # Unilever ADR - Consumer brands
        "DEO",  # Diageo ADR - Alcohol brands, pricing power
        "LIN",  # Linde - Industrial gases, essential service
        "SAP",  # SAP ADR - Enterprise software, switching costs
    ]
    buffett_international.extend(europe_buffett_style)

    # Other international value plays
    other_international = [
        "TSM",  # Taiwan Semiconductor - Technology infrastructure
        "0700.HK",  # Tencent (Hong Kong) - Network effects, gaming
        "BABA",  # Alibaba ADR - E-commerce platform
        "PDD",  # PDD Holdings ADR - Chinese e-commerce
    ]
    buffett_international.extend(other_international)

    return buffett_international

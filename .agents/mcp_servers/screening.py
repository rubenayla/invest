#!/usr/bin/env python3
"""
MCP Server for Stock Screening Tools

This MCP server provides Claude with stock screening capabilities:
- Custom screening with various criteria
- Sector screening
- Value/growth/quality screens
- International screening

Usage:
    python screening.py
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server
from mcp.server.models import InitializationOptions

from invest.data.universal_fetcher import UniversalStockFetcher

# Initialize the MCP server
server = Server("stock-screening")

# Predefined stock universes for screening
STOCK_UNIVERSES = {
    "us_large_cap": [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "BRK-B",
        "UNH", "XOM", "JNJ", "JPM", "PG", "V", "HD", "MA", "PFE", "AVGO",
        "CVX", "ABBV", "KO", "LLY", "BAC", "COST", "PEP", "TMO", "WMT",
        "DIS", "ABT", "ACN", "VZ", "MRK", "CSCO", "ADBE", "CRM", "NKE"
    ],
    "japanese_blue_chip": [
        "7203.T", "6758.T", "8058.T", "9984.T", "6861.T", "8002.T",
        "4063.T", "9432.T", "6752.T", "7267.T", "6954.T", "4502.T"
    ],
    "european_leaders": [
        "ASML.AS", "SAP.DE", "MC.PA", "NESN.SW", "NOVO-B.CO", "RMS.PA",
        "AZN.L", "SHEL.AS", "OR.PA", "INGA.AS"
    ],
    "mixed_international": [
        "AAPL", "MSFT", "7203.T", "ASML.AS", "NESN.SW", "8002.T",
        "BABA", "TSM", "BIDU", "0700.HK", "MC.PA", "SAP.DE"
    ]
}


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available stock screening tools."""
    return [
        types.Tool(
            name="screen_stocks",
            description="Screen stocks based on financial criteria",
            inputSchema={
                "type": "object",
                "properties": {
                    "universe": {
                        "type": "string",
                        "enum": list(STOCK_UNIVERSES.keys()),
                        "description": "Stock universe to screen",
                        "default": "us_large_cap"
                    },
                    "criteria": {
                        "type": "object",
                        "properties": {
                            "max_pe": {"type": "number", "description": "Maximum P/E ratio"},
                            "min_pe": {"type": "number", "description": "Minimum P/E ratio"},
                            "max_pb": {"type": "number", "description": "Maximum P/B ratio"},
                            "min_roe": {"type": "number", "description": "Minimum ROE (decimal)"},
                            "min_dividend_yield": {"type": "number", "description": "Minimum dividend yield (decimal)"},
                            "max_debt_equity": {"type": "number", "description": "Maximum debt/equity ratio"},
                            "min_market_cap": {"type": "number", "description": "Minimum market cap (billions)"},
                            "sectors": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Include only these sectors"
                            }
                        }
                    },
                    "custom_tickers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Custom list of tickers to screen instead of universe"
                    }
                },
                "required": ["criteria"]
            }
        ),
        types.Tool(
            name="value_screen",
            description="Pre-configured value stock screen",
            inputSchema={
                "type": "object",
                "properties": {
                    "universe": {
                        "type": "string",
                        "enum": list(STOCK_UNIVERSES.keys()),
                        "default": "us_large_cap"
                    },
                    "aggressive": {
                        "type": "boolean",
                        "description": "Use aggressive value criteria",
                        "default": False
                    }
                }
            }
        ),
        types.Tool(
            name="quality_screen",
            description="Pre-configured quality/dividend screen",
            inputSchema={
                "type": "object",
                "properties": {
                    "universe": {
                        "type": "string",
                        "enum": list(STOCK_UNIVERSES.keys()),
                        "default": "us_large_cap"
                    }
                }
            }
        ),
        types.Tool(
            name="growth_screen",
            description="Pre-configured growth stock screen",
            inputSchema={
                "type": "object",
                "properties": {
                    "universe": {
                        "type": "string",
                        "enum": list(STOCK_UNIVERSES.keys()),
                        "default": "us_large_cap"
                    }
                }
            }
        ),
        types.Tool(
            name="sector_screen",
            description="Screen stocks by sector",
            inputSchema={
                "type": "object",
                "properties": {
                    "sector": {
                        "type": "string",
                        "description": "Sector to screen (e.g., 'Technology', 'Healthcare')"
                    },
                    "universe": {
                        "type": "string",
                        "enum": list(STOCK_UNIVERSES.keys()),
                        "default": "mixed_international"
                    }
                },
                "required": ["sector"]
            }
        )
    ]


def apply_screen_criteria(stock_data: Dict, criteria: Dict) -> tuple[bool, List[str]]:
    """Apply screening criteria to stock data."""
    passes = True
    reasons = []

    # P/E ratio checks
    pe = stock_data.get('trailing_pe')
    if pe:
        if criteria.get('max_pe') and pe > criteria['max_pe']:
            passes = False
            reasons.append(f"P/E {pe:.1f} > {criteria['max_pe']}")
        if criteria.get('min_pe') and pe < criteria['min_pe']:
            passes = False
            reasons.append(f"P/E {pe:.1f} < {criteria['min_pe']}")

    # P/B ratio check
    pb = stock_data.get('price_to_book')
    if pb and criteria.get('max_pb') and pb > criteria['max_pb']:
        passes = False
        reasons.append(f"P/B {pb:.1f} > {criteria['max_pb']}")

    # ROE check
    roe = stock_data.get('return_on_equity')
    if roe and criteria.get('min_roe') and roe < criteria['min_roe']:
        passes = False
        reasons.append(f"ROE {roe*100:.1f}% < {criteria['min_roe']*100:.1f}%")

    # Dividend yield check
    div_yield = stock_data.get('dividend_yield')
    if criteria.get('min_dividend_yield'):
        if not div_yield or div_yield < criteria['min_dividend_yield']:
            passes = False
            reasons.append(f"Dividend yield {(div_yield or 0)*100:.2f}% < {criteria['min_dividend_yield']*100:.2f}%")

    # Debt/Equity check
    debt_equity = stock_data.get('debt_to_equity')
    if debt_equity and criteria.get('max_debt_equity') and debt_equity > criteria['max_debt_equity']:
        passes = False
        reasons.append(f"D/E {debt_equity:.1f} > {criteria['max_debt_equity']}")

    # Market cap check (in billions)
    market_cap = stock_data.get('market_cap_usd', stock_data.get('market_cap', 0))
    if market_cap and criteria.get('min_market_cap'):
        market_cap_b = market_cap / 1e9
        if market_cap_b < criteria['min_market_cap']:
            passes = False
            reasons.append(f"Market cap ${market_cap_b:.1f}B < ${criteria['min_market_cap']}B")

    # Sector check
    if criteria.get('sectors'):
        sector = stock_data.get('sector', '')
        if sector not in criteria['sectors']:
            passes = False
            reasons.append(f"Sector '{sector}' not in allowed list")

    return passes, reasons


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool calls for stock screening."""

    if name == "screen_stocks":
        universe_name = arguments.get("universe", "us_large_cap")
        criteria = arguments.get("criteria", {})
        custom_tickers = arguments.get("custom_tickers")

        # Get tickers to screen
        if custom_tickers:
            tickers = custom_tickers
            universe_name = "custom"
        else:
            tickers = STOCK_UNIVERSES.get(universe_name, STOCK_UNIVERSES["us_large_cap"])

        # Fetch data
        fetcher = UniversalStockFetcher(convert_currency=True)
        stock_data = fetcher.fetch_multiple(tickers)

        # Apply screening
        passed_stocks = []
        failed_stocks = []

        for ticker in tickers:
            data = stock_data.get(ticker)
            if not data:
                failed_stocks.append((ticker, ["No data available"]))
                continue

            passes, reasons = apply_screen_criteria(data, criteria)

            if passes:
                passed_stocks.append((ticker, data))
            else:
                failed_stocks.append((ticker, reasons))

        # Format results
        result = f"🔍 **Stock Screening Results** ({universe_name})\n\n"
        result += f"**📊 Summary:** {len(passed_stocks)} passed, {len(failed_stocks)} failed\n\n"

        if passed_stocks:
            result += "**✅ Stocks That Passed:**\n"
            for ticker, data in passed_stocks:
                name = data.get('longName', ticker)[:25]
                price = data.get('current_price_usd', data.get('current_price', 0))
                pe = data.get('trailing_pe', 0)
                pb = data.get('price_to_book', 0)
                roe = data.get('return_on_equity', 0) * 100
                sector = data.get('sector', 'N/A')[:15]

                result += f"• **{ticker}** ({name}) - ${price:.2f}\n"
                result += f"  P/E: {pe:.1f} | P/B: {pb:.1f} | ROE: {roe:.1f}% | {sector}\n"

        if failed_stocks and len(failed_stocks) <= 10:  # Only show failures for small lists
            result += "\n**❌ Stocks That Failed:**\n"
            for ticker, reasons in failed_stocks[:5]:  # Limit to first 5
                result += f"• {ticker}: {', '.join(reasons[:2])}\n"  # First 2 reasons

        return [types.TextContent(type="text", text=result)]

    elif name == "value_screen":
        universe_name = arguments.get("universe", "us_large_cap")
        aggressive = arguments.get("aggressive", False)

        if aggressive:
            criteria = {
                "max_pe": 12,
                "max_pb": 1.5,
                "min_roe": 0.15,
                "min_dividend_yield": 0.02
            }
        else:
            criteria = {
                "max_pe": 20,
                "max_pb": 2.5,
                "min_roe": 0.10,
                "max_debt_equity": 1.0
            }

        # Reuse the screen_stocks logic
        return await handle_call_tool("screen_stocks", {
            "universe": universe_name,
            "criteria": criteria
        })

    elif name == "quality_screen":
        universe_name = arguments.get("universe", "us_large_cap")

        criteria = {
            "min_roe": 0.15,
            "max_debt_equity": 0.5,
            "min_dividend_yield": 0.015,  # 1.5%+
            "min_market_cap": 1.0  # $1B+
        }

        return await handle_call_tool("screen_stocks", {
            "universe": universe_name,
            "criteria": criteria
        })

    elif name == "growth_screen":
        universe_name = arguments.get("universe", "us_large_cap")

        criteria = {
            "min_roe": 0.15,
            "max_debt_equity": 1.5,
            "min_market_cap": 0.5  # Allow smaller growth companies
        }

        return await handle_call_tool("screen_stocks", {
            "universe": universe_name,
            "criteria": criteria
        })

    elif name == "sector_screen":
        sector = arguments["sector"]
        universe_name = arguments.get("universe", "mixed_international")

        criteria = {"sectors": [sector]}

        return await handle_call_tool("screen_stocks", {
            "universe": universe_name,
            "criteria": criteria
        })

    else:
        return [types.TextContent(
            type="text",
            text=f"❌ Unknown tool: {name}"
        )]


async def main():
    """Run the MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="stock-screening",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                )
            )
        )


if __name__ == "__main__":
    asyncio.run(main())

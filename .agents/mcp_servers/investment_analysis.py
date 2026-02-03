#!/usr/bin/env python3
"""
MCP Server for Investment Analysis Tools

This MCP server provides Claude with direct access to investment analysis capabilities:
- Stock data retrieval and analysis
- DCF valuations (all models)
- Financial metrics calculation
- International stock support

Usage:
    python investment_analysis.py

Then configure in Claude Desktop with:
    "investment-analysis": {
        "command": "python",
        "args": ["/path/to/investment_analysis.py"],
        "env": {}
    }
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server
from mcp.server.models import InitializationOptions

from invest.data.universal_fetcher import UniversalStockFetcher, compare_international_stocks
from invest.dividend_aware_dcf import calculate_enhanced_dcf
from invest.growth_phase_dcf import calculate_multi_stage_dcf
from invest.probabilistic_dcf import calculate_monte_carlo_dcf
from invest.simple_ratios import calculate_simple_ratios_valuation
from invest.standard_dcf import calculate_dcf

# Initialize the MCP server
server = Server("investment-analysis")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available investment analysis tools."""
    return [
        types.Tool(
            name="get_stock_data",
            description="Get comprehensive stock data for any ticker (US, international)",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker (e.g., 'AAPL', '7203.T', 'ASML.AS')"
                    },
                    "convert_currency": {
                        "type": "boolean",
                        "description": "Convert prices to USD for comparison",
                        "default": False
                    }
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="compare_stocks",
            description="Compare multiple stocks across different exchanges",
            inputSchema={
                "type": "object",
                "properties": {
                    "tickers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of tickers to compare"
                    },
                    "metrics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific metrics to compare",
                        "default": ["current_price", "trailing_pe", "return_on_equity", "market_cap"]
                    }
                },
                "required": ["tickers"]
            }
        ),
        types.Tool(
            name="dcf_valuation",
            description="Run DCF valuation using specified model",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker to value"
                    },
                    "model": {
                        "type": "string",
                        "enum": ["standard", "dividend_aware", "probabilistic", "growth_phase"],
                        "description": "DCF model to use",
                        "default": "standard"
                    },
                    "discount_rate": {
                        "type": "number",
                        "description": "Discount rate (WACC)",
                        "default": 0.12
                    },
                    "terminal_growth": {
                        "type": "number",
                        "description": "Terminal growth rate",
                        "default": 0.025
                    }
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="ratio_analysis",
            description="Calculate key financial ratios and valuations",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker to analyze"
                    }
                },
                "required": ["ticker"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool calls for investment analysis."""

    if name == "get_stock_data":
        ticker = arguments["ticker"]
        convert_currency = arguments.get("convert_currency", False)

        fetcher = UniversalStockFetcher(convert_currency=convert_currency, target_currency='USD')
        data = fetcher.fetch_stock(ticker)

        if not data:
            return [types.TextContent(
                type="text",
                text=f"❌ Could not fetch data for {ticker}. Please check the ticker symbol."
            )]

        # Format key information
        result = f"""📊 **{data.get('longName', ticker)}** ({ticker})

**📍 Company Info:**
• Exchange: {data.get('exchange', 'N/A')}
• Country: {data.get('country', 'N/A')} 
• Sector: {data.get('sector', 'N/A')}
• Industry: {data.get('industry', 'N/A')}

**💰 Valuation Metrics:**
• Current Price: {data.get('currency', 'USD')} {data.get('current_price', 'N/A'):.2f}
• Market Cap: {data.get('market_cap', 0)/1e9:.1f}B {data.get('currency', 'USD')}
• P/E Ratio: {data.get('trailing_pe', 'N/A')}
• P/B Ratio: {data.get('price_to_book', 'N/A')}
• EV/EBITDA: {data.get('ev_to_ebitda', 'N/A')}

**🏢 Quality Metrics:**
• ROE: {data.get('return_on_equity', 0)*100:.1f}%
• Current Ratio: {data.get('current_ratio', 'N/A')}
• Debt/Equity: {data.get('debt_to_equity', 'N/A')}
• Dividend Yield: {data.get('dividend_yield', 0)*100:.2f}%

**📈 Growth:**
• Revenue Growth: {data.get('revenue_growth', 0)*100:.1f}%
• Earnings Growth: {data.get('earnings_growth', 0)*100:.1f}%
• Beta: {data.get('beta', 'N/A')}
"""

        if convert_currency and data.get('converted_to') == 'USD':
            result += f"\n**💱 USD Converted:**\n• Price: ${data.get('current_price_usd', 'N/A'):.2f}\n• Market Cap: ${data.get('market_cap_usd', 0)/1e9:.1f}B"

        return [types.TextContent(type="text", text=result)]

    elif name == "compare_stocks":
        tickers = arguments["tickers"]
        metrics = arguments.get("metrics", ["current_price", "trailing_pe", "return_on_equity", "market_cap"])

        comparison = compare_international_stocks(tickers, metrics)

        if not comparison:
            return [types.TextContent(
                type="text",
                text="❌ Could not fetch comparison data for the provided tickers."
            )]

        result = "📊 **Stock Comparison**\n\n"

        for ticker, info in comparison.items():
            result += f"**{ticker}** - {info['name']}\n"
            result += f"• Exchange: {info['exchange']} | Country: {info['country']}\n"
            result += f"• Sector: {info['sector']}\n"

            for metric in metrics:
                value = info['metrics'].get(metric)
                if value is not None:
                    if metric in ['current_price', 'market_cap']:
                        result += f"• {metric.replace('_', ' ').title()}: {value:.2f}\n"
                    elif metric in ['trailing_pe', 'return_on_equity']:
                        result += f"• {metric.replace('_', ' ').title()}: {value:.2f}\n"
                    else:
                        result += f"• {metric.replace('_', ' ').title()}: {value}\n"
            result += "\n"

        return [types.TextContent(type="text", text=result)]

    elif name == "dcf_valuation":
        ticker = arguments["ticker"]
        model = arguments.get("model", "standard")
        discount_rate = arguments.get("discount_rate", 0.12)
        terminal_growth = arguments.get("terminal_growth", 0.025)

        try:
            if model == "standard":
                result = calculate_dcf(ticker, discount_rate=discount_rate, terminal_growth=terminal_growth)
            elif model == "dividend_aware":
                result = calculate_enhanced_dcf(ticker, discount_rate=discount_rate, terminal_growth=terminal_growth)
            elif model == "probabilistic":
                result = calculate_monte_carlo_dcf(ticker, base_discount_rate=discount_rate, base_terminal_growth=terminal_growth)
            elif model == "growth_phase":
                result = calculate_multi_stage_dcf(ticker, discount_rate=discount_rate, terminal_growth=terminal_growth)
            else:
                return [types.TextContent(
                    type="text",
                    text=f"❌ Unknown DCF model: {model}"
                )]

            if result.get('error'):
                return [types.TextContent(
                    type="text",
                    text=f"❌ DCF Error for {ticker}: {result['error']}"
                )]

            # Format DCF results
            fair_value = result.get('fair_value_per_share', 0)
            current_price = result.get('current_price', 0)
            upside = ((fair_value - current_price) / current_price * 100) if current_price else 0

            dcf_text = f"""🧮 **{model.replace('_', ' ').title()} DCF Analysis: {ticker}**

**💰 Valuation Results:**
• Fair Value: ${fair_value:.2f}
• Current Price: ${current_price:.2f}
• Implied Upside: {upside:+.1f}%
• Discount Rate: {discount_rate*100:.1f}%
• Terminal Growth: {terminal_growth*100:.1f}%

**📊 Key Metrics:**
• Enterprise Value: ${result.get('enterprise_value', 0)/1e6:.0f}M
• Terminal Value: ${result.get('terminal_value', 0)/1e6:.0f}M
"""

            if model == "probabilistic":
                # Add confidence intervals for Monte Carlo
                conf_68 = result.get('confidence_intervals', {}).get(0.68, [0, 0])
                conf_95 = result.get('confidence_intervals', {}).get(0.95, [0, 0])
                dcf_text += f"""
**🎯 Confidence Intervals:**
• 68% range: ${conf_68[0]:.2f} - ${conf_68[1]:.2f}
• 95% range: ${conf_95[0]:.2f} - ${conf_95[1]:.2f}
• Probability of 50%+ upside: {result.get('upside_probability', 0)*100:.1f}%
"""

            return [types.TextContent(type="text", text=dcf_text)]

        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ DCF calculation failed for {ticker}: {str(e)}"
            )]

    elif name == "ratio_analysis":
        ticker = arguments["ticker"]

        try:
            result = calculate_simple_ratios_valuation(ticker)

            if result.get('error'):
                return [types.TextContent(
                    type="text",
                    text=f"❌ Ratio analysis error for {ticker}: {result['error']}"
                )]

            ratios_text = f"""📊 **Financial Ratio Analysis: {ticker}**

**🎯 Valuation Ratios:**
• P/E Target Fair Value: ${result.get('pe_fair_value', 0):.2f}
• P/B Target Fair Value: ${result.get('pb_fair_value', 0):.2f} 
• P/S Target Fair Value: ${result.get('ps_fair_value', 0):.2f}
• EV/EBITDA Fair Value: ${result.get('ev_ebitda_fair_value', 0):.2f}

**📈 Current Ratios:**
• P/E: {result.get('current_pe', 'N/A')}
• P/B: {result.get('current_pb', 'N/A')}
• P/S: {result.get('current_ps', 'N/A')}
• EV/EBITDA: {result.get('current_ev_ebitda', 'N/A')}

**💡 Analysis:**
• Average Fair Value: ${result.get('average_fair_value', 0):.2f}
• Current Price: ${result.get('current_price', 0):.2f}
• Implied Upside: {result.get('upside_percentage', 0):+.1f}%
"""

            return [types.TextContent(type="text", text=ratios_text)]

        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Ratio analysis failed for {ticker}: {str(e)}"
            )]

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
                server_name="investment-analysis",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                )
            )
        )


if __name__ == "__main__":
    asyncio.run(main())

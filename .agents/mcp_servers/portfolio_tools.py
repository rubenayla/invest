#!/usr/bin/env python3
"""
MCP Server for Portfolio Management Tools

This MCP server provides Claude with portfolio management capabilities:
- Portfolio analysis and optimization
- Risk assessment
- Asset allocation recommendations
- Performance tracking

Usage:
    python portfolio_tools.py
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

from invest.data.universal_fetcher import UniversalStockFetcher
import numpy as np


# Initialize the MCP server
server = Server("portfolio-tools")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available portfolio management tools."""
    return [
        types.Tool(
            name="analyze_portfolio",
            description="Analyze a portfolio of stocks with weights",
            inputSchema={
                "type": "object",
                "properties": {
                    "holdings": {
                        "type": "array",
                        "items": {
                            "type": "object", 
                            "properties": {
                                "ticker": {"type": "string"},
                                "weight": {"type": "number", "minimum": 0, "maximum": 1}
                            },
                            "required": ["ticker", "weight"]
                        },
                        "description": "Portfolio holdings with tickers and weights"
                    }
                },
                "required": ["holdings"]
            }
        ),
        types.Tool(
            name="risk_assessment",
            description="Assess portfolio risk metrics",
            inputSchema={
                "type": "object",
                "properties": {
                    "tickers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of tickers to analyze for risk"
                    }
                },
                "required": ["tickers"]
            }
        ),
        types.Tool(
            name="diversification_check",
            description="Check portfolio diversification across sectors/countries",
            inputSchema={
                "type": "object",
                "properties": {
                    "tickers": {
                        "type": "array", 
                        "items": {"type": "string"},
                        "description": "List of tickers to check diversification"
                    }
                },
                "required": ["tickers"]
            }
        ),
        types.Tool(
            name="rebalancing_suggestions", 
            description="Suggest portfolio rebalancing based on target allocation",
            inputSchema={
                "type": "object",
                "properties": {
                    "current_holdings": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ticker": {"type": "string"},
                                "current_value": {"type": "number"}
                            }
                        }
                    },
                    "target_allocation": {
                        "type": "object",
                        "description": "Target sector/geographic allocation",
                        "properties": {
                            "us_stocks": {"type": "number", "default": 0.6},
                            "international_stocks": {"type": "number", "default": 0.3}, 
                            "bonds": {"type": "number", "default": 0.1}
                        }
                    }
                },
                "required": ["current_holdings"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool calls for portfolio management."""
    
    if name == "analyze_portfolio":
        holdings = arguments["holdings"]
        
        # Validate weights sum to ~1
        total_weight = sum(h["weight"] for h in holdings)
        if abs(total_weight - 1.0) > 0.01:
            return [types.TextContent(
                type="text",
                text=f"⚠️ Warning: Portfolio weights sum to {total_weight:.2f}, not 1.00"
            )]
        
        # Fetch data for all holdings
        fetcher = UniversalStockFetcher(convert_currency=True)
        tickers = [h["ticker"] for h in holdings]
        stock_data = fetcher.fetch_multiple(tickers)
        
        # Calculate portfolio metrics
        portfolio_value = 0
        portfolio_pe = 0
        portfolio_dividend_yield = 0
        portfolio_beta = 0
        sector_allocation = {}
        country_allocation = {}
        
        result = "📊 **Portfolio Analysis**\n\n"
        result += "**🏢 Holdings:**\n"
        
        for holding in holdings:
            ticker = holding["ticker"]
            weight = holding["weight"]
            data = stock_data.get(ticker)
            
            if not data:
                result += f"• {ticker}: {weight*100:.1f}% - ❌ Data not available\n"
                continue
            
            # Add to result
            name = data.get('longName', ticker)[:30]
            price = data.get('current_price_usd', data.get('current_price', 0))
            result += f"• **{ticker}** ({name}): {weight*100:.1f}% - ${price:.2f}\n"
            
            # Aggregate metrics (weighted)
            if data.get('trailing_pe'):
                portfolio_pe += data['trailing_pe'] * weight
            if data.get('dividend_yield'):
                portfolio_dividend_yield += data['dividend_yield'] * weight  
            if data.get('beta'):
                portfolio_beta += data['beta'] * weight
            
            # Sector allocation
            sector = data.get('sector', 'Unknown')
            sector_allocation[sector] = sector_allocation.get(sector, 0) + weight
            
            # Country allocation  
            country = data.get('country', 'Unknown')
            country_allocation[country] = country_allocation.get(country, 0) + weight
        
        # Portfolio summary
        result += f"\n**📈 Portfolio Metrics:**\n"
        result += f"• Weighted P/E: {portfolio_pe:.1f}\n"
        result += f"• Weighted Dividend Yield: {portfolio_dividend_yield*100:.2f}%\n"
        result += f"• Weighted Beta: {portfolio_beta:.2f}\n"
        
        # Diversification analysis
        result += f"\n**🌍 Geographic Allocation:**\n"
        for country, allocation in sorted(country_allocation.items(), key=lambda x: x[1], reverse=True):
            result += f"• {country}: {allocation*100:.1f}%\n"
        
        result += f"\n**🏭 Sector Allocation:**\n"
        for sector, allocation in sorted(sector_allocation.items(), key=lambda x: x[1], reverse=True):
            result += f"• {sector}: {allocation*100:.1f}%\n"
        
        # Concentration risk
        max_weight = max(h["weight"] for h in holdings)
        if max_weight > 0.25:
            result += f"\n⚠️ **High Concentration Risk**: Largest position is {max_weight*100:.1f}%"
        
        return [types.TextContent(type="text", text=result)]
    
    elif name == "risk_assessment":
        tickers = arguments["tickers"]
        
        fetcher = UniversalStockFetcher(convert_currency=True)
        stock_data = fetcher.fetch_multiple(tickers)
        
        result = "⚠️ **Portfolio Risk Assessment**\n\n"
        
        high_risk_stocks = []
        low_risk_stocks = []
        high_pe_stocks = []
        high_debt_stocks = []
        
        for ticker in tickers:
            data = stock_data.get(ticker)
            if not data:
                continue
            
            name = data.get('longName', ticker)[:25]
            beta = data.get('beta', 1.0)
            pe = data.get('trailing_pe', 0)
            debt_equity = data.get('debt_to_equity', 0)
            
            # Risk categorization
            if beta > 1.5:
                high_risk_stocks.append(f"{ticker} (β={beta:.1f})")
            elif beta < 0.8:
                low_risk_stocks.append(f"{ticker} (β={beta:.1f})")
            
            if pe > 30:
                high_pe_stocks.append(f"{ticker} (P/E={pe:.1f})")
            
            if debt_equity > 1.0:
                high_debt_stocks.append(f"{ticker} (D/E={debt_equity:.1f})")
        
        if high_risk_stocks:
            result += f"🔴 **High Beta (>1.5):** {', '.join(high_risk_stocks)}\n\n"
        
        if high_pe_stocks:
            result += f"📈 **High Valuation (P/E >30):** {', '.join(high_pe_stocks)}\n\n"
        
        if high_debt_stocks:
            result += f"💳 **High Debt (D/E >1.0):** {', '.join(high_debt_stocks)}\n\n"
        
        if low_risk_stocks:
            result += f"🟢 **Low Beta (<0.8):** {', '.join(low_risk_stocks)}\n\n"
        
        if not (high_risk_stocks or high_pe_stocks or high_debt_stocks):
            result += "✅ **Low Risk Portfolio**: No major risk factors detected\n"
        
        return [types.TextContent(type="text", text=result)]
    
    elif name == "diversification_check":
        tickers = arguments["tickers"]
        
        fetcher = UniversalStockFetcher(convert_currency=True)
        stock_data = fetcher.fetch_multiple(tickers)
        
        sectors = {}
        countries = {}
        
        for ticker in tickers:
            data = stock_data.get(ticker)
            if not data:
                continue
            
            sector = data.get('sector', 'Unknown')
            country = data.get('country', 'Unknown')
            
            sectors[sector] = sectors.get(sector, 0) + 1
            countries[country] = countries.get(country, 0) + 1
        
        total_stocks = len([t for t in tickers if stock_data.get(t)])
        
        result = "🌐 **Diversification Analysis**\n\n"
        
        # Sector diversification
        result += "**📊 Sector Distribution:**\n"
        for sector, count in sorted(sectors.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_stocks) * 100
            result += f"• {sector}: {count} stocks ({percentage:.1f}%)\n"
        
        # Geographic diversification
        result += f"\n**🌍 Geographic Distribution:**\n"
        for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_stocks) * 100
            result += f"• {country}: {count} stocks ({percentage:.1f}%)\n"
        
        # Diversification score
        sector_concentration = max(sectors.values()) / total_stocks if sectors else 1
        country_concentration = max(countries.values()) / total_stocks if countries else 1
        
        result += f"\n**🎯 Diversification Score:**\n"
        if sector_concentration > 0.6:
            result += f"• ⚠️ High sector concentration ({sector_concentration*100:.1f}%)\n"
        else:
            result += f"• ✅ Good sector diversification\n"
        
        if country_concentration > 0.8:
            result += f"• ⚠️ High country concentration ({country_concentration*100:.1f}%)\n"
        else:
            result += f"• ✅ Good geographic diversification\n"
        
        return [types.TextContent(type="text", text=result)]
    
    elif name == "rebalancing_suggestions":
        current_holdings = arguments["current_holdings"]
        target_allocation = arguments.get("target_allocation", {
            "us_stocks": 0.6,
            "international_stocks": 0.3,
            "bonds": 0.1
        })
        
        # This is a simplified example - in practice you'd need more sophisticated logic
        total_value = sum(h["current_value"] for h in current_holdings)
        
        result = "⚖️ **Rebalancing Suggestions**\n\n"
        result += f"**Total Portfolio Value: ${total_value:,.2f}**\n\n"
        
        result += "**🎯 Target vs Current Allocation:**\n"
        for category, target_pct in target_allocation.items():
            target_value = total_value * target_pct
            result += f"• {category.replace('_', ' ').title()}: {target_pct*100:.1f}% (${target_value:,.0f})\n"
        
        result += "\n**💡 Rebalancing Actions:**\n"
        result += "• Review individual holdings against targets\n"
        result += "• Consider tax implications before selling\n"
        result += "• Use new contributions for rebalancing first\n"
        result += "• Rebalance quarterly or when >5% off target\n"
        
        return [types.TextContent(type="text", text=result)]
    
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
                server_name="portfolio-tools", 
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                )
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
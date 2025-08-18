"""
Shared core portfolio construction logic for multi-provider AI tools.

This module contains the business logic for portfolio construction and analysis
that can be used by any AI provider (Claude, Gemini, etc.).
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from invest.data.yahoo import get_stock_data  # noqa: E402


def build_optimized_portfolio(
    stock_list: List[str],
    objective: str = "balanced",
    constraints: Optional[Dict[str, Any]] = None,
    target_amount: float = 100000,
) -> Dict[str, Any]:
    """
    Build an optimized portfolio from a list of stocks.

    Args:
        stock_list: List of ticker symbols
        objective: Portfolio objective ('growth', 'value', 'income', 'balanced')
        constraints: Portfolio constraints (max_position_size, sector_limits, etc.)
        target_amount: Target portfolio value in USD

    Returns:
        Dict containing optimized portfolio allocation and metrics
    """
    if constraints is None:
        constraints = {
            "max_position_size": 0.15,  # Max 15% per stock
            "min_position_size": 0.02,  # Min 2% per stock
            "max_sector_weight": 0.30,  # Max 30% per sector
        }

    try:
        # Get stock data
        portfolio_data = []
        for ticker in stock_list:
            stock_data = get_stock_data(ticker)
            if stock_data:
                portfolio_data.append(
                    {
                        "ticker": ticker.upper(),
                        "name": stock_data.get("longName", "N/A"),
                        "sector": stock_data.get("sector", "N/A"),
                        "price": stock_data.get("current_price", 0),
                        "market_cap": stock_data.get("market_cap", 0),
                        "pe_ratio": stock_data.get("trailing_pe", 0),
                        "dividend_yield": stock_data.get("dividend_yield", 0),
                        "beta": stock_data.get("beta", 1.0),
                        "roe": stock_data.get("return_on_equity", 0),
                        "revenue_growth": stock_data.get("revenue_growth", 0),
                    }
                )

        if not portfolio_data:
            return {"error": "No valid stock data found"}

        # Calculate optimal allocation based on objective
        allocations = _calculate_allocations(portfolio_data, objective, constraints)

        # Build portfolio summary
        portfolio_summary = _build_portfolio_summary(portfolio_data, allocations, target_amount)

        return portfolio_summary

    except Exception as e:
        return {"error": str(e), "message": "Failed to build optimized portfolio"}


def analyze_portfolio_risk(
    portfolio_allocation: Dict[str, float], time_horizon: str = "1_year"
) -> Dict[str, Any]:
    """
    Analyze portfolio risk characteristics.

    Args:
        portfolio_allocation: Dict of ticker -> weight
        time_horizon: Analysis time horizon

    Returns:
        Dict containing risk analysis results
    """
    try:
        # Get portfolio data
        portfolio_data = []
        for ticker, weight in portfolio_allocation.items():
            stock_data = get_stock_data(ticker)
            if stock_data:
                portfolio_data.append(
                    {
                        "ticker": ticker,
                        "weight": weight,
                        "beta": stock_data.get("beta", 1.0),
                        "sector": stock_data.get("sector", "N/A"),
                        "market_cap": stock_data.get("market_cap", 0),
                        "debt_equity": stock_data.get("debt_to_equity", 0),
                    }
                )

        # Calculate risk metrics
        risk_analysis = _calculate_risk_metrics(portfolio_data)

        return {
            "time_horizon": time_horizon,
            "risk_metrics": risk_analysis,
            "risk_level": _determine_risk_level(risk_analysis),
            "recommendations": _generate_risk_recommendations(risk_analysis),
        }

    except Exception as e:
        return {"error": str(e), "message": "Failed to analyze portfolio risk"}


def rebalance_portfolio(
    current_allocation: Dict[str, float],
    target_allocation: Dict[str, float],
    current_values: Dict[str, float],
    min_trade_size: float = 100,
) -> Dict[str, Any]:
    """
    Generate rebalancing recommendations.

    Args:
        current_allocation: Current portfolio weights
        target_allocation: Target portfolio weights
        current_values: Current position values
        min_trade_size: Minimum trade size to consider

    Returns:
        Dict containing rebalancing trades and analysis
    """
    try:
        trades = []
        total_value = sum(current_values.values())

        for ticker in set(list(current_allocation.keys()) + list(target_allocation.keys())):
            current_weight = current_allocation.get(ticker, 0)
            target_weight = target_allocation.get(ticker, 0)
            current_value = current_values.get(ticker, 0)

            target_value = total_value * target_weight
            trade_amount = target_value - current_value

            if abs(trade_amount) >= min_trade_size:
                trades.append(
                    {
                        "ticker": ticker,
                        "current_weight": f"{current_weight:.1%}",
                        "target_weight": f"{target_weight:.1%}",
                        "current_value": f"${current_value:,.2f}",
                        "target_value": f"${target_value:,.2f}",
                        "trade_amount": f"${trade_amount:,.2f}",
                        "action": "BUY" if trade_amount > 0 else "SELL",
                    }
                )

        return {
            "total_portfolio_value": f"${total_value:,.2f}",
            "trades_required": len(trades),
            "trades": trades,
            "total_turnover": sum(
                abs(float(t["trade_amount"].replace("$", "").replace(",", ""))) for t in trades
            ),
            "rebalancing_summary": _generate_rebalancing_summary(trades),
        }

    except Exception as e:
        return {"error": str(e), "message": "Failed to generate rebalancing recommendations"}


def screen_etfs(
    category: str = "broad_market", criteria: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Screen ETFs based on criteria.

    Args:
        category: ETF category to screen
        criteria: Screening criteria

    Returns:
        Dict containing ETF screening results
    """
    if criteria is None:
        criteria = {
            "max_expense_ratio": 0.20,
            "min_aum": 1e9,  # $1B minimum assets
            "min_volume": 1e6,  # $1M daily volume
        }

    # Common ETF universes by category
    etf_lists = {
        "broad_market": ["SPY", "VTI", "ITOT", "SPTM"],
        "international": ["VEA", "VXUS", "IXUS", "FTIHX"],
        "emerging_markets": ["VWO", "IEMG", "EEM", "SCHE"],
        "bonds": ["BND", "AGG", "VTEB", "VGIT"],
        "sectors": ["XLK", "XLV", "XLF", "XLE", "XLI"],
        "growth": ["VUG", "IVW", "MGK", "VBK"],
        "value": ["VTV", "IVE", "MGV", "VBR"],
    }

    try:
        etf_tickers = etf_lists.get(category, etf_lists["broad_market"])

        etf_results = []
        for ticker in etf_tickers:
            etf_data = get_stock_data(ticker)
            if etf_data:
                etf_results.append(
                    {
                        "ticker": ticker,
                        "name": etf_data.get("longName", "N/A"),
                        "expense_ratio": etf_data.get("annual_holdings_turnover", 0) / 100,
                        "aum": etf_data.get("total_assets", 0),
                        "yield": etf_data.get("dividend_yield", 0),
                        "pe_ratio": etf_data.get("trailing_pe", 0),
                        "category": category,
                    }
                )

        return {
            "category": category,
            "criteria_used": criteria,
            "etfs_screened": len(etf_results),
            "etf_results": etf_results,
            "recommendations": _generate_etf_recommendations(etf_results, criteria),
        }

    except Exception as e:
        return {"error": str(e), "message": f"Failed to screen {category} ETFs"}


def _calculate_allocations(
    portfolio_data: List[Dict], objective: str, constraints: Dict[str, Any]
) -> Dict[str, float]:
    """Calculate optimal portfolio allocations based on objective."""
    n_stocks = len(portfolio_data)

    if objective == "equal_weight":
        # Equal weight allocation
        weight = 1.0 / n_stocks
        return {stock["ticker"]: weight for stock in portfolio_data}

    elif objective == "market_cap":
        # Market cap weighted
        total_mcap = sum(stock["market_cap"] for stock in portfolio_data)
        return {stock["ticker"]: stock["market_cap"] / total_mcap for stock in portfolio_data}

    elif objective == "income":
        # Dividend yield weighted
        total_yield = sum(stock.get("dividend_yield", 0) for stock in portfolio_data)
        if total_yield > 0:
            return {
                stock["ticker"]: stock.get("dividend_yield", 0) / total_yield
                for stock in portfolio_data
            }
        else:
            # Fallback to equal weight if no dividends
            weight = 1.0 / n_stocks
            return {stock["ticker"]: weight for stock in portfolio_data}

    else:  # balanced, growth, value
        # Score-based allocation
        scores = _calculate_stock_scores(portfolio_data, objective)
        total_score = sum(scores.values())

        return {
            ticker: max(
                constraints["min_position_size"],
                min(constraints["max_position_size"], score / total_score),
            )
            for ticker, score in scores.items()
        }


def _calculate_stock_scores(portfolio_data: List[Dict], objective: str) -> Dict[str, float]:
    """Calculate stock scores based on objective."""
    scores = {}

    for stock in portfolio_data:
        score = 1.0  # Base score

        if objective == "growth":
            # Growth scoring
            if stock.get("revenue_growth", 0) > 0:
                score *= 1 + stock["revenue_growth"]
            if stock.get("pe_ratio", 0) > 0:
                score *= min(2.0, 50 / stock["pe_ratio"])  # Prefer reasonable P/E
            if stock.get("roe", 0) > 0:
                score *= 1 + stock["roe"]

        elif objective == "value":
            # Value scoring
            if stock.get("pe_ratio", 0) > 0:
                score *= max(0.5, 25 / stock["pe_ratio"])  # Lower P/E is better
            if stock.get("dividend_yield", 0) > 0:
                score *= 1 + stock["dividend_yield"] * 10  # Reward dividends
            if stock.get("roe", 0) > 0:
                score *= 1 + stock["roe"]

        else:  # balanced
            # Balanced scoring
            if stock.get("roe", 0) > 0:
                score *= 1 + stock["roe"]
            if stock.get("pe_ratio", 0) > 0 and stock["pe_ratio"] < 30:
                score *= 1.2  # Modest P/E bonus
            if stock.get("dividend_yield", 0) > 0:
                score *= 1 + stock["dividend_yield"] * 5

        scores[stock["ticker"]] = max(0.1, score)  # Minimum score

    return scores


def _build_portfolio_summary(
    portfolio_data: List[Dict], allocations: Dict[str, float], target_amount: float
) -> Dict[str, Any]:
    """Build comprehensive portfolio summary."""
    positions = []
    sector_weights = {}
    total_dividend_yield = 0

    for stock in portfolio_data:
        ticker = stock["ticker"]
        weight = allocations.get(ticker, 0)
        position_value = target_amount * weight
        shares = int(position_value / stock["price"]) if stock["price"] > 0 else 0

        position = {
            "ticker": ticker,
            "company_name": stock["name"],
            "sector": stock["sector"],
            "weight": f"{weight:.1%}",
            "position_value": f"${position_value:,.2f}",
            "shares": shares,
            "price_per_share": f"${stock['price']:.2f}",
            "dividend_yield": f"{stock.get('dividend_yield', 0):.2%}",
            "pe_ratio": f"{stock.get('pe_ratio', 0):.1f}" if stock.get("pe_ratio") else "N/A",
        }
        positions.append(position)

        # Sector allocation
        sector = stock["sector"]
        sector_weights[sector] = sector_weights.get(sector, 0) + weight

        # Portfolio dividend yield
        total_dividend_yield += weight * stock.get("dividend_yield", 0)

    # Calculate portfolio metrics
    portfolio_beta = sum(
        allocations.get(stock["ticker"], 0) * stock.get("beta", 1.0) for stock in portfolio_data
    )

    avg_pe = np.average(
        [stock.get("pe_ratio", 20) for stock in portfolio_data],
        weights=[allocations.get(stock["ticker"], 0) for stock in portfolio_data],
    )

    return {
        "target_amount": f"${target_amount:,.2f}",
        "positions": positions,
        "sector_allocation": {k: f"{v:.1%}" for k, v in sector_weights.items()},
        "portfolio_metrics": {
            "total_positions": len(positions),
            "portfolio_beta": f"{portfolio_beta:.2f}",
            "weighted_avg_pe": f"{avg_pe:.1f}",
            "portfolio_dividend_yield": f"{total_dividend_yield:.2%}",
            "largest_position": f"{max(allocations.values()):.1%}",
            "smallest_position": f"{min(allocations.values()):.1%}",
        },
    }


def _calculate_risk_metrics(portfolio_data: List[Dict]) -> Dict[str, Any]:
    """Calculate portfolio risk metrics."""
    # Portfolio beta
    portfolio_beta = sum(stock["weight"] * stock["beta"] for stock in portfolio_data)

    # Sector concentration
    sector_weights = {}
    for stock in portfolio_data:
        sector = stock["sector"]
        sector_weights[sector] = sector_weights.get(sector, 0) + stock["weight"]

    max_sector_weight = max(sector_weights.values()) if sector_weights else 0

    # Market cap distribution
    large_cap_weight = sum(
        stock["weight"]
        for stock in portfolio_data
        if stock["market_cap"] > 10e9  # > $10B
    )

    # Debt levels
    avg_debt_equity = np.average(
        [stock.get("debt_equity", 0) for stock in portfolio_data],
        weights=[stock["weight"] for stock in portfolio_data],
    )

    return {
        "portfolio_beta": portfolio_beta,
        "max_sector_weight": max_sector_weight,
        "sector_diversification": len(sector_weights),
        "large_cap_weight": large_cap_weight,
        "avg_debt_equity": avg_debt_equity,
        "position_concentration": max(stock["weight"] for stock in portfolio_data),
    }


def _determine_risk_level(risk_metrics: Dict[str, Any]) -> str:
    """Determine overall portfolio risk level."""
    risk_score = 0

    # Beta risk
    if risk_metrics["portfolio_beta"] > 1.3:
        risk_score += 2
    elif risk_metrics["portfolio_beta"] > 1.1:
        risk_score += 1

    # Concentration risk
    if risk_metrics["max_sector_weight"] > 0.4:
        risk_score += 2
    elif risk_metrics["max_sector_weight"] > 0.3:
        risk_score += 1

    if risk_metrics["position_concentration"] > 0.2:
        risk_score += 1

    # Diversification
    if risk_metrics["sector_diversification"] < 4:
        risk_score += 1

    if risk_score >= 4:
        return "HIGH"
    elif risk_score >= 2:
        return "MEDIUM"
    else:
        return "LOW"


def _generate_risk_recommendations(risk_metrics: Dict[str, Any]) -> List[str]:
    """Generate risk management recommendations."""
    recommendations = []

    if risk_metrics["portfolio_beta"] > 1.3:
        recommendations.append(
            "Consider adding defensive stocks to reduce portfolio beta below 1.3"
        )

    if risk_metrics["max_sector_weight"] > 0.35:
        recommendations.append(
            f"Sector concentration risk: {risk_metrics['max_sector_weight']:.1%} in single sector. "
            "Consider diversifying across more sectors."
        )

    if risk_metrics["position_concentration"] > 0.15:
        recommendations.append(
            f"Position concentration: {risk_metrics['position_concentration']:.1%} in single stock. "
            "Consider reducing individual position sizes."
        )

    if risk_metrics["sector_diversification"] < 5:
        recommendations.append(
            f"Limited sector diversification ({risk_metrics['sector_diversification']} sectors). "
            "Consider adding exposure to more sectors."
        )

    if not recommendations:
        recommendations.append("Portfolio shows good risk characteristics across key metrics.")

    return recommendations


def _generate_rebalancing_summary(trades: List[Dict]) -> str:
    """Generate rebalancing summary."""
    if not trades:
        return "Portfolio is already well-balanced. No trades required."

    buy_trades = [t for t in trades if t["action"] == "BUY"]
    sell_trades = [t for t in trades if t["action"] == "SELL"]

    summary = f"Rebalancing requires {len(trades)} trades: "
    summary += f"{len(buy_trades)} purchases, {len(sell_trades)} sales. "

    total_turnover = sum(
        abs(float(t["trade_amount"].replace("$", "").replace(",", ""))) for t in trades
    )
    summary += f"Total turnover: ${total_turnover:,.2f}"

    return summary


def _generate_etf_recommendations(etf_results: List[Dict], criteria: Dict[str, Any]) -> List[str]:
    """Generate ETF recommendations based on screening results."""
    recommendations = []

    # Filter ETFs that meet criteria
    qualifying_etfs = [
        etf
        for etf in etf_results
        if (
            etf.get("expense_ratio", 1.0) <= criteria.get("max_expense_ratio", 0.20)
            and etf.get("aum", 0) >= criteria.get("min_aum", 1e9)
        )
    ]

    if qualifying_etfs:
        # Sort by expense ratio (lower is better)
        qualifying_etfs.sort(key=lambda x: x.get("expense_ratio", 1.0))

        top_etf = qualifying_etfs[0]
        recommendations.append(
            f"Top recommendation: {top_etf['ticker']} - {top_etf['name']} "
            f"(Expense Ratio: {top_etf.get('expense_ratio', 0):.2%})"
        )

        if len(qualifying_etfs) > 1:
            recommendations.append(
                f"Alternative options: {', '.join([etf['ticker'] for etf in qualifying_etfs[1:3]])}"
            )
    else:
        recommendations.append("No ETFs meet the specified criteria.")

    return recommendations

"""
Gemini tools for portfolio construction and analysis.

These tools help Gemini build and analyze investment portfolios based on
systematic screening results and additional constraints.
"""

from typing import Any, Dict, List, Optional

from ..core.portfolio import (
    analyze_portfolio_risk,
    build_optimized_portfolio,
    rebalance_portfolio,
    screen_etfs,
)


def build_portfolio(
    candidate_stocks: List[str],
    portfolio_constraints: Optional[Dict] = None,
    optimization_objective: str = "balanced",
    max_positions: int = 10,
) -> Dict[str, Any]:
    """
    Build an optimized portfolio from candidate stocks.

    Args:
        candidate_stocks: List of ticker symbols to consider
        portfolio_constraints: Dict with constraints like max_single_position,
                              sector_limits, min_yield, etc.
        optimization_objective: 'balanced', 'growth', 'value', 'income', 'low_risk'
        max_positions: Maximum number of positions in portfolio

    Returns:
        Dict containing optimized portfolio allocation and analysis
    """
    return build_optimized_portfolio(
        candidate_stocks, optimization_objective, portfolio_constraints, 100000
    )


def analyze_portfolio_by_tickers(
    portfolio_tickers: List[str],
    portfolio_weights: Optional[List[float]] = None,
    risk_factors: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Analyze risk characteristics of a portfolio from ticker list.

    Args:
        portfolio_tickers: List of tickers in the portfolio
        portfolio_weights: List of weights (if None, assumes equal weighting)
        risk_factors: Risk factors to analyze ['sector', 'size', 'geography', 'style']

    Returns:
        Dict containing comprehensive risk analysis
    """
    if portfolio_weights is None:
        portfolio_weights = [1.0 / len(portfolio_tickers)] * len(portfolio_tickers)

    # Convert to allocation dict format
    portfolio_allocation = {
        ticker: weight for ticker, weight in zip(portfolio_tickers, portfolio_weights)
    }

    return analyze_portfolio_risk(portfolio_allocation)


def optimize_allocation(
    current_portfolio: Dict[str, float],
    target_allocation: Dict[str, float],
    optimization_constraints: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Optimize portfolio allocation to move from current to target weights.

    Args:
        current_portfolio: Dict of {ticker: current_weight}
        target_allocation: Dict of {ticker: target_weight}
        optimization_constraints: Trading constraints (min_trade_size, max_turnover, etc.)

    Returns:
        Dict containing rebalancing recommendations
    """
    if optimization_constraints is None:
        optimization_constraints = {
            "min_trade_size": 0.01,  # 1% minimum trade
            "max_turnover": 0.50,  # 50% max turnover
            "transaction_cost": 0.001,  # 0.1% transaction cost estimate
        }

    # Convert to current values format (assuming 100k portfolio)
    portfolio_value = 100000
    current_values = {
        ticker: weight * portfolio_value for ticker, weight in current_portfolio.items()
    }

    return rebalance_portfolio(current_portfolio, target_allocation, current_values)


def screen_etfs_by_category(
    category: str = "broad_market", criteria: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Screen ETFs based on category and criteria.

    Args:
        category: ETF category to screen
        criteria: Screening criteria

    Returns:
        Dict containing ETF screening results
    """
    return screen_etfs(category, criteria)


def generate_portfolio_report(
    portfolio_data: Dict[str, Any], include_sections: Optional[List[str]] = None
) -> str:
    """
    Generate a comprehensive portfolio report.

    Args:
        portfolio_data: Portfolio data from build_portfolio() or similar
        include_sections: Sections to include ['summary', 'allocation', 'risk', 'recommendations']

    Returns:
        Formatted string report
    """
    if include_sections is None:
        include_sections = ["summary", "allocation", "risk", "recommendations"]

    try:
        from datetime import datetime

        report = f"""
PORTFOLIO ANALYSIS REPORT
{'='*50}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Target Amount: {portfolio_data.get('target_amount', '$100,000')}

"""

        if "summary" in include_sections and "portfolio_metrics" in portfolio_data:
            metrics = portfolio_data["portfolio_metrics"]
            report += f"""
PORTFOLIO SUMMARY
-----------------
Total Positions: {metrics.get('total_positions', 0)}
Portfolio Beta: {metrics.get('portfolio_beta', 0)}
Weighted Avg P/E: {metrics.get('weighted_avg_pe', 0)}
Portfolio Dividend Yield: {metrics.get('portfolio_dividend_yield', '0.0%')}
Largest Position: {metrics.get('largest_position', '0.0%')}
Smallest Position: {metrics.get('smallest_position', '0.0%')}

"""

        if "allocation" in include_sections and "positions" in portfolio_data:
            report += """
PORTFOLIO ALLOCATION
--------------------
"""
            for position in portfolio_data["positions"]:
                report += (
                    f"{position['ticker']:6} {position['weight']:>6} - {position['company_name']}\n"
                )
            report += "\n"

        if "risk" in include_sections and "sector_allocation" in portfolio_data:
            report += """
SECTOR ALLOCATION
-----------------
"""
            for sector, weight in portfolio_data["sector_allocation"].items():
                report += f"{sector:20} {weight:>6}\n"
            report += "\n"

        if "recommendations" in include_sections:
            report += """
RECOMMENDATIONS
---------------
• Review portfolio regularly for rebalancing opportunities
• Monitor sector concentration limits
• Consider tax implications of any changes
• Evaluate individual position performance quarterly

"""

        report += f"{'='*50}\nGenerated by AI Investment Analysis Tools\n"

        return report

    except Exception as e:
        return f"Error generating portfolio report: {str(e)}"

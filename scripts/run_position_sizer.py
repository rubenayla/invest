#!/usr/bin/env python3
"""CLI for Kelly Criterion position sizing.

Usage:
    uv run python scripts/run_position_sizer.py AAPL MSFT GOOG
    uv run python scripts/run_position_sizer.py --portfolio-value 50000 AAPL
    uv run python scripts/run_position_sizer.py --fraction 0.25 AAPL  # quarter-Kelly
    uv run python scripts/run_position_sizer.py --verbose AAPL        # show model breakdown
    uv run python scripts/run_position_sizer.py --portfolio --budget 30000  # auto-build portfolio
"""

from __future__ import annotations

import argparse
import sys

from invest.sizing.kelly import HEADER, SEPARATOR, KellyPositionSizer, KellyResult


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Kelly Criterion position sizer")
    parser.add_argument("tickers", nargs="*", help="Stock tickers to size")
    parser.add_argument(
        "--portfolio-value",
        type=float,
        default=50000,
        help="Total portfolio value in USD (default: 50000)",
    )
    parser.add_argument(
        "--fraction",
        type=float,
        default=0.5,
        help="Kelly fraction (default: 0.5 = half-Kelly)",
    )
    parser.add_argument(
        "--max-position",
        type=float,
        default=0.15,
        help="Max single position as fraction of portfolio (default: 0.15)",
    )
    parser.add_argument(
        "--max-sector",
        type=float,
        default=0.35,
        help="Max sector exposure as fraction of portfolio (default: 0.35)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show model-by-model breakdown",
    )
    parser.add_argument(
        "--portfolio",
        "-p",
        action="store_true",
        help="Build an optimal portfolio from all stocks with edge",
    )
    parser.add_argument(
        "--budget",
        type=float,
        default=None,
        help="Budget for portfolio mode (defaults to --portfolio-value)",
    )
    parser.add_argument(
        "--max-positions",
        type=int,
        default=15,
        help="Max number of positions in portfolio mode (default: 15)",
    )
    return parser.parse_args()


def print_model_breakdown(result: KellyResult) -> None:
    """Print per-model bull/bear breakdown."""
    if not result.model_agreement:
        return
    print(f"\n  Model breakdown for {result.ticker}:")
    bulls = [m for m, v in result.model_agreement.items() if v == "bull"]
    bears = [m for m, v in result.model_agreement.items() if v == "bear"]
    print(f"    Bullish ({len(bulls)}): {', '.join(bulls) or 'none'}")
    print(f"    Bearish ({len(bears)}): {', '.join(bears) or 'none'}")
    if result.risk:
        r = result.risk
        print(f"    Volatility: {r.volatility_annual:.1%} | VaR(95%): {r.var_95_annual:.1%} | Max DD: {r.max_drawdown_1y:.1%} | Sector: {r.sector}")


def run_portfolio_mode(args: argparse.Namespace) -> None:
    """Build and display an optimal portfolio."""
    budget = args.budget or args.portfolio_value
    tickers = [t.upper() for t in args.tickers] if args.tickers else None

    sizer = KellyPositionSizer(
        portfolio_value=budget,
        fraction=args.fraction,
        max_position_pct=args.max_position,
        max_sector_pct=args.max_sector,
    )

    scope = f"from {len(tickers)} tickers" if tickers else "from all stocks in DB"
    print(f"\nBuilding portfolio: ${budget:,.0f} budget | {scope} | max {args.max_positions} positions")
    print("Scanning stocks for edge...\n")

    results = sizer.build_portfolio(
        budget=budget,
        tickers=tickers,
        max_positions=args.max_positions,
    )

    if not results:
        print("No stocks with positive edge found.")
        return

    # Print results
    print(HEADER)
    print(SEPARATOR)

    total = 0.0
    sectors: dict[str, float] = {}
    for r in results:
        print(r.summary_line())
        total += r.dollar_amount
        if r.risk:
            sec = r.risk.sector
            sectors[sec] = sectors.get(sec, 0) + r.dollar_amount
        if args.verbose:
            print_model_breakdown(r)

    print(SEPARATOR)
    print(f"\n  Positions: {len(results)} | Invested: ${total:,.0f} ({total / budget:.1%}) | Cash: ${budget - total:,.0f} ({(budget - total) / budget:.1%})")

    # Sector breakdown
    if sectors:
        print(f"\n  Sector allocation:")
        for sec, amt in sorted(sectors.items(), key=lambda x: -x[1]):
            print(f"    {sec:<30} ${amt:>8,.0f}  ({amt / budget:>5.1%})")


def run_ticker_mode(args: argparse.Namespace) -> None:
    """Size specific tickers."""
    if not args.tickers:
        print("Error: provide tickers or use --portfolio mode")
        sys.exit(1)

    tickers = [t.upper() for t in args.tickers]

    sizer = KellyPositionSizer(
        portfolio_value=args.portfolio_value,
        fraction=args.fraction,
        max_position_pct=args.max_position,
        max_sector_pct=args.max_sector,
    )

    print(f"\nPortfolio: ${args.portfolio_value:,.0f} | Kelly fraction: {args.fraction} | Max position: {args.max_position:.0%} | Max sector: {args.max_sector:.0%}\n")
    print(HEADER)
    print(SEPARATOR)

    results = sizer.size_multiple(tickers)

    total_allocated = 0.0
    for r in results:
        print(r.summary_line())
        total_allocated += r.dollar_amount
        if args.verbose:
            print_model_breakdown(r)

    print(SEPARATOR)
    print(f"Total allocation: ${total_allocated:,.0f} ({total_allocated / args.portfolio_value:.1%} of portfolio)")

    no_edge = [r.ticker for r in results if "no_edge" in r.flags]
    if no_edge:
        print(f"\nNo edge (Kelly says don't trade): {', '.join(no_edge)}")


def main() -> None:
    args = parse_args()
    if args.portfolio:
        run_portfolio_mode(args)
    else:
        run_ticker_mode(args)


if __name__ == "__main__":
    main()

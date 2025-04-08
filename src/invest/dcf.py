import yfinance as yf

PROJECTION_YEARS = 10  # default projection horizon


def project_fcfs(initial_fcf: float, growth_rates: list[float]) -> list[float]:
    """Projects free cash flows for N years given an initial FCF and list of yearly growth rates."""
    fcfs = []
    fcf = initial_fcf
    for g in growth_rates:
        fcf *= (1 + g)
        fcfs.append(fcf)
    return fcfs


def discounted_sum(values: list[float], rate: float) -> float:
    """Discounts a list of values at a given rate to present value."""
    return sum(v / (1 + rate) ** (i + 1) for i, v in enumerate(values))


def calculate_dcf(
    ticker: str,
    fcf: float = None,
    shares: float = None,
    cash: float = None,
    debt: float = None,
    current_price: float = None,
    growth_rates: list[float] = None,
    discount_rate: float = 0.12,
    terminal_growth: float = 0.02,
    projection_years: int = PROJECTION_YEARS,
    verbose: bool = True,
) -> dict:
    """
    Runs a full DCF valuation on a given ticker using Yahoo Finance data (unless manually overridden).
    Returns a dictionary with the valuation breakdown.
    """
    stock = yf.Ticker(ticker)
    info = stock.info

    # Autofill if missing
    if fcf is None:
        fcf = info.get("freeCashflow")
    if shares is None:
        shares = info.get("sharesOutstanding")
    if cash is None:
        cash = info.get("totalCash", 0)
    if debt is None:
        debt = info.get("totalDebt", 0)
    if current_price is None:
        current_price = info.get("currentPrice")

    if any(x is None for x in [fcf, shares, current_price]):
        raise RuntimeError(f"Missing essential data for {ticker}: FCF, shares, or price.")

    # Default growth inference
    if growth_rates is None:
        inferred = info.get("revenueGrowth", 0.05)
        growth_rates = [
            inferred * (1 - 0.1 * i) for i in range(projection_years)
        ]  # decay 10% per year

    fcfs = project_fcfs(fcf, growth_rates)
    terminal_value = fcfs[-1] * (1 + terminal_growth) / (discount_rate - terminal_growth)

    npv_fcfs = discounted_sum(fcfs, discount_rate)
    npv_terminal = terminal_value / (1 + discount_rate) ** projection_years

    enterprise_value = npv_fcfs + npv_terminal
    equity_value = enterprise_value - debt + cash
    fair_value = equity_value / shares
    margin = (fair_value - current_price) / current_price

    if verbose:
        print(f"\nDCF Valuation for {ticker}")
        print(f"{'-'*40}")
        print(f"Current Price:        ${current_price:,.2f}")
        print(f"Fair Value Estimate:  ${fair_value:,.2f}")
        print(f"Margin of Safety:      {margin * 100:.1f}%")
        print(f"Free Cash Flow (ttm): ${fcf:,.0f}")
        print(f"Growth Rates:         {['{:.1%}'.format(g) for g in growth_rates]}")

    return {
        "ticker": ticker,
        "fair_value": fair_value,
        "current_price": current_price,
        "margin_of_safety": margin,
        "fcf_projection": fcfs,
        "terminal_value": terminal_value,
        "equity_value": equity_value,
        "discount_rate": discount_rate,
        "growth_rates": growth_rates,
        "inputs": {
            "fcf": fcf,
            "shares": shares,
            "cash": cash,
            "debt": debt,
        },
    }

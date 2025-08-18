"""
dcf.py - Discounted Cash Flow valuation module

This module provides a function to estimate the fair value per share using a DCF model.
It improves auto mode by computing a normalized free cash flow (FCF) from historical
data to smooth out one-off events that might distort the TTM FCF. It also gracefully
handles cases where market data is not available (e.g., dummy tickers) and uses manual
override values in those cases.

Key Variables:
    enterprise_value       : npv_fcf + tv_pv, the DCF-estimated total value of operating assets.
    estimated_market_cap   : enterprise_value - debt + cash; our estimated market cap.
    fair_value_per_share   : estimated_market_cap divided by shares outstanding.

The discount rate used is assumed to be the WACC.

Author: Your Name
Date: YYYY-MM-DD
"""

import yfinance as yf

PROJECTION_YEARS = 10  # Number of years for FCF projection

def project_fcfs(initial_fcf: float, growth_rates: list[float]) -> list[float]:
    """
    Projects free cash flows over the projection horizon.

    Parameters:
        initial_fcf (float): The base free cash flow.
        growth_rates (list[float]): Annual growth rates for each projection year.

    Returns:
        list[float]: Projected FCF values for each year.
    """
    fcfs = []
    fcf = initial_fcf
    for g in growth_rates:
        fcf *= (1 + g)
        fcfs.append(fcf)
    return fcfs

def discounted_sum(values: list[float], rate: float) -> float:
    """
    Computes the present value (NPV) of a series of future values.

    Parameters:
        values (list[float]): Future cash flows.
        rate (float): Annual discount rate.

    Returns:
        float: Sum of discounted cash flows.
    """
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
    use_normalized_fcf: bool = True,
    verbose: bool = True,
) -> dict:
    """
    Calculate the DCF-based valuation for a given ticker.

    Data is fetched from yfinance. In auto mode, the function computes a normalized free
    cash flow (FCF) from historical cash flow data to avoid distortions from one-off events.
    If market data is not available (e.g., a dummy ticker), a warning is issued and provided
    manual inputs are used.

    Parameters:
        ticker (str): Stock ticker.
        fcf (float, optional): TTM free cash flow. If None, it is taken from market data.
        shares (float, optional): Shares outstanding.
        cash (float, optional): Total cash & equivalents.
        debt (float, optional): Total debt.
        current_price (float, optional): Current market price.
        growth_rates (list[float], optional): Annual projection growth rates. If None, defaults are inferred.
        discount_rate (float, optional): The discount rate (WACC). Defaults to 0.12.
        terminal_growth (float, optional): Terminal (perpetual) growth rate. Defaults to 0.02.
        projection_years (int, optional): Number of years to project FCF. Defaults to 10.
        use_normalized_fcf (bool, optional): Whether to compute normalized FCF from historical data.
        verbose (bool, optional): Whether to print valuation details.

    Returns:
        dict: A dictionary with valuation details including:
              - fair_value_per_share: The estimated fair share price.
              - enterprise_value: The DCF-estimated total enterprise value.
              - estimated_market_cap: enterprise_value - debt + cash.
              - Other inputs and intermediate values.
    """
    stock = yf.Ticker(ticker)
    
    try:
        info = stock.info
    except Exception as e:
        info = {}
        if verbose:
            print(f"Warning: Unable to retrieve market data for ticker '{ticker}'. Using manual inputs. Error: {e}")

    # Autofill inputs from stock.info if missing:
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
    
    # When market data is not available, you must supply fcf, shares, and current_price manually.
    if (not info) and any(x is None for x in [fcf, shares, current_price]):
        raise RuntimeError(f"Missing essential manual inputs for {ticker}: fcf, shares, or current_price.")

    # Use normalized FCF if enabled.
    if use_normalized_fcf:
        try:
            cf_df = stock.cashflow
            if not cf_df.empty:
                if "Free Cash Flow" in cf_df.index:
                    norm_fcf = cf_df.loc["Free Cash Flow"].mean()
                else:
                    norm_fcf = (cf_df.loc["Total Cash From Operating Activities"] -
                                cf_df.loc["Capital Expenditures"]).mean()
            else:
                # If cashflow data is unavailable, fallback to provided fcf.
                norm_fcf = fcf
        except Exception as e:
            norm_fcf = fcf
            if verbose:
                print("Warning: Could not compute normalized FCF; falling back to TTM FCF. Error:", e)
    else:
        norm_fcf = fcf

    base_fcf = norm_fcf

    if any(x is None for x in [base_fcf, shares, current_price]):
        raise RuntimeError(f"Missing essential data for {ticker}: fcf, shares, or current_price.")

    # If growth rates are not provided, infer from revenueGrowth or default to 5%.
    if growth_rates is None:
        inferred_growth = info.get("revenueGrowth", 0.05)
        if inferred_growth < 0:
            inferred_growth = 0.00
        growth_rates = [inferred_growth * (1 - 0.1 * i) for i in range(projection_years)]

    # Project FCFs over the projection period.
    fcfs = project_fcfs(base_fcf, growth_rates)
    
    # Terminal Value: Using the Gordon Growth Model.
    TV = fcfs[-1] * (1 + terminal_growth) / (discount_rate - terminal_growth)
    tv_pv = TV / ((1 + discount_rate) ** projection_years)

    # NPV of projected FCFs (years 1 to projection_years).
    npv_fcf = discounted_sum(fcfs, discount_rate)

    # Enterprise value from DCF.
    enterprise_value = npv_fcf + tv_pv

    # Estimated market cap from our valuation.
    estimated_market_cap = enterprise_value - debt + cash

    # Fair value per share.
    fair_value_per_share = estimated_market_cap / shares
    
    # Calculate margin of safety (always, not just when verbose)
    margin = (fair_value_per_share - current_price) / current_price if current_price > 0 else 0

    if verbose:
        print(f"\nDCF Valuation for {ticker}")
        print("-" * 40)
        print(f"Current Price:        ${current_price:,.2f}")
        print(f"Estimated Market Cap: ${estimated_market_cap:,.2f}")
        print(f"Fair Value per Share: ${fair_value_per_share:,.2f}")
        print(f"Margin of Safety:      {margin * 100:.1f}%")
        print(f"Normalized FCF:       ${base_fcf:,.0f}")
        print("Growth Rates:         " + ", ".join(f"{g:.1%}" for g in growth_rates))
    
    return {
        "ticker": ticker,
        "fair_value_per_share": fair_value_per_share,
        "current_price": current_price,
        "margin_of_safety": margin,
        "fcf_projection": fcfs,
        "TV": TV,
        "tv_pv": tv_pv,
        "npv_fcf": npv_fcf,
        "enterprise_value": enterprise_value,
        "estimated_market_cap": estimated_market_cap,
        "discount_rate": discount_rate,
        "growth_rates": growth_rates,
        "inputs": {
            "normalized_fcf": base_fcf,
            "shares": shares,
            "cash": cash,
            "debt": debt,
        },
    }

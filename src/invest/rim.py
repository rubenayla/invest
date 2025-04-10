def rim_valuation(
    book_equity: float,
    net_income: float,
    cost_of_equity: float,
    n_years: int = 10,
    growth_rate: float = 0.0
) -> float:
    """
    Residual Income Model (RIM) valuation using net income directly.

    Parameters
    ----------
    book_equity : float
        Current book equity ($).
    net_income : float
        Current net income ($), assumed constant or growing.
    cost_of_equity : float
        Required return on equity (as decimal).
    n_years : int
        Forecast horizon.
    growth_rate : float
        Perpetual residual income growth after forecast.

    Returns
    -------
    float
        Estimated intrinsic value of the company.
    """
    assert cost_of_equity > growth_rate, "Growth rate must be < cost of equity"

    equity = book_equity
    residual_income = 0.0

    for t in range(1, n_years + 1):
        equity_charge = equity * cost_of_equity
        ri = net_income - equity_charge
        residual_income += ri / (1 + cost_of_equity) ** t
        equity += net_income  # assume all earnings are reinvested

    terminal_ri = (net_income - equity * cost_of_equity) / (cost_of_equity - growth_rate)
    residual_income += terminal_ri / (1 + cost_of_equity) ** (n_years + 1)

    return book_equity + residual_income

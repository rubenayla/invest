## My previous super simple model
Value = Book Equity + operating profits * multiple compared to other companies
Put estimated future values in there and you get your value

## DCF -- Discounted Free Cash Flow
> An asset is worth the present value of all future cash flows to its shareholders, discounted at the required rate of return.
> = sum for all years: FCF / (1 + r)^n, where r is the discount rate, n is the year

- FairValuePerShare = fair_value / shares
- fair_value = (enterprise_value - debt + cash) / shares
- enterprise_value = npv_fcf + pv_tv
    - Enterprise Value
- npv_fcf = sum of FCF for the next 10 years, discounted to the present with the WACC (weighted average cost of capital)
    - `npv_fcf = Σ [FCFₜ / (1 + r)^t]  for t = 1 to N`
    - ```python
      npv = sum(fcf[t] * 1 / (1 + r) ** (t + 1) for t in range(N))
      ```
- pv_tv = tv / (1 + r)^n
    > The terminal value is the present value of all FCF after year 10. We discount it back to the present value with the WACC, to get PV_TV.
    > Since we can't predict that far into the future, we assume a constant growth rate with the Gordon growth model. The growth rate `g` is usually lower than the discount rate `r`, making the sum converge.
    - `TV = FCF_11 × (1 + g) / (r - g)` 
        > From this: `TV = FCF₁₁ + FCF₁₂ / (1 + r) + FCF₁₃ / (1 + r)^2 + ...`
- r = WACC = cap/enterprise_value * Re + D/enterprise_value * Rd * (1 - Tc)
    - Rd = cost of debt = Rf + default spread
    - enterprise_value = cap + D
    - Weighted average cost of capital = Financing cost
    - Tc = Corporate tax rate
        > Interest on debt is tax-deductible, so the effective cost is reduced by Tc
- Re = cost of equity = Rf + β × (Rm - Rf)
    - Rf = risk-free rate = yield on 10-year government bonds
    - beta = measure of risk (volatility) of the stock
- Rd = cost of debt = Rf + default spread
    - default spread = risk premium for the company


> For startups, how to adjust it? If they reinvest everything, the value of the company can't be accurately determined from then net income, but the operating income and growth expectations.

## Comparables -- Relative Valuation


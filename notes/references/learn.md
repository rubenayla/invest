# Definitions

## Income Statement --- Revenue, Income, Profit, Expenses, Net Income, EBIT, EBITDA, Free Cash Flow, Equity, Enterprise Value
> - **Revenue** (all money in) = Turnover
> - `- Expenses` = COGS = Cost Of Goods Sold. Linked to production
> - = **Gross Profit** Profit ignoring investment and R&D expenses -- Related to Gross Margin = Gross profit / Revenue
> - `- Operating expenses` = OpEx -- marketing, R&D expenses, depreciation/amortization of assets, land rent --- Whole business expenses, unlinked to production
> - = Operating **Income** = EBIT -- Related to Operating Margin = Operating Income / Revenue
> - `- Other non-operating expenses` Interests, Investments, Taxes
> - = Net **Earnings**, Net Income, Net Profit - Related to Profit Margin = Net Earnings / Revenue
>     - Beware, net income may be low or negative and the company go well, if they're investing for growth!

- If you exclude Depreciation and Amortization from Operating Expenses, the new Operating Income obtained is EBITDA. It basically pretends that capital doesn’t wear out. Charlie Munger hates it for this reason.

- CapEx: Long-term investments, like a factory
    - Buyin an asset spends cash. Right after the purchase, the net earnings **are unchanged**. The depreciation of the assets will slowly cause OpEx in the following years.
    - The sudden impact is visible in the cash flow statement
- Depreciation/Amortization: The decrease in value of an asset over time. Depreciation is for physical assets (machinery, buildings), amortization for intangible assets (patents, trademarks). Doesn't affect the cash flow.
- Equity (Book Equity) = Assets - Liabilities
    > In accounting terms
- Market Equity = Market Cap. DO NOT USE THE TERM Equity in Market terms. Just use Market cap in that case!
- EV = Enterprise Value = EqV + Total Debt - Cash (and equivalents)
    - EqV = Equity Value
    > This is the money that you have to pay to get the company by itself, with no money accounts or debt, no storage or money. You have to pay for the debt, but you get the cash of the company to pay
    - A low EV for a valuable company means it's cheap to buy. It's good.
- ROI = Return On Invested capital = (Gross Profit / Cost of the investment) ~= 10%
- P/E ratio = Price / Earnings ~= 12
- P/TBV = Price / Tangible Book Value
    - Excludes Goodwill from the book value to actually reflect the tangible assets of the company. If 1 it means you liquidate the company and get about the same amount of money as the market cap.
- P/G ratio = Price / Gross Profit ~= 91
- EPS = Earnings Per Share = Earnings / Shares
- FCF = Free Cash Flow = net income adding depreciation, amortization, capex, working capital, interests etc = net income * (1 - reinvestment rate)
    - How much did the cash balance vary from year to year. Money left for investors and creditors (after investments).
- CARG = Compound Annual Growth Rate, Rate of Return ROR required to grow from beginning balance to ending balance
- FCF = Free Cash Flow
    - = Profit from operations - Capital expenditures
    - = EBI - Investments (capital expenditures, capex)
- OFCF = Operating Free Cash Flow
    - = EBITDA - Taxes - Capital expenditures
    - Cash Flow of core business, ignoring financing and investing.
- IFCF = Investing Free Cash Flow
    - = Capital expenditures - Depreciation
    - Cash flow from investments, capex, purchase/sale. Shows growth strategy. <0 -> investing in growth.
- FFCF = Financing Free Cash Flow
    - = Dividends + Buybacks - Issuance
    - Capital structure, how the company is financed. Shareholder return.
- EBIT: Earnings before interest and taxes. But includes depreciation and amortization.
- EBITDA: Earnings before interest, taxes, depreciation, and amortization = E + I(Interest) + T(Taxes) + D(Depreciation) + A(Amortization)
    - "How much pure cash a business generates from its core operations, before any financing or accounting tricks."

Debt to Equity
Current ratio = Assets / Liabilities

Macro economic parameter: STOCK / Gross Domestic Product (.75 historical average)

Price / Sales (1 historical average)

Shares outstanding: Amount of shares in existence (which are not owned by the company itself)

Gross profit margin = Gross Profit / Revenue = (Revenue - COGS expenses) / Revenue

- WACC = Weighted Average Cost of Capital, the average rate that a company is expected to pay to finance its assets, including the opportunity cost for equity investors and the cost of debt. It's the average rate of return that a company expects to compensate all its different investors (including itself).
- TV = Terminal Value = The value of the company at the end of the projection period.
    - This is done with the Gordon Growth Model, which solves the integral for a constant growth rate g in perpetuity, assuming g < r, where r is the discount rate, usually the WACC. So the company is assumed to grow slower than the market. Otherwise, TV would be infinite.
    - $TV = \frac{FCF_{n+1}}{r-g}$
- PV = Present Value = The present value of a company, including its future predicted cash flows (TV)
    - It's the value of all future cash flows beyond the projection period.
        - To understand this, think that the value of a company is the sum of all its future cash flows, discounted to the present. By discounted we mean that we value more the cash flows that we get sooner, because they can further generate more cash flows. It can't be infinity, since the value of the company should be infinity too. When we have a money-generating machine that can work forever, we don't give it an infinite value, because we value future money less, in such a way that the integral of all future cash flows converges to a finite value, which is the terminal value, TV.
- NPV: Net Present Value, Present value of next 10 years of cash flows
- 
- Terminal value in year n = free cash flow in year (n+1) / (discount rate - perpetual growth rate)
- FX control means: you manually convert your EUR to JPY before buying the stock.
- RTH: Regular Trading Hours
- TSE: Tokyo Stock Exchange
- ADR: American Depositary Receipt, a negotiable certificate issued by a bank representing a specified number of shares (or one share) in a foreign stock traded on a U.S. exchange. It allows U.S. investors to buy shares in foreign companies without dealing with the complexities of foreign stock ownership.

## Ratios
- P/E ratio = Price / Earnings ~= 12
- P/G ratio = Price / Gross Profit
- P/B ratio = Price / Book value (?)
- 10 YR PE ratio = Price / Net Income average over 10 year period (16 historical average) ~= about 15 average

# Valuation models

## Discounted Cash Flow (DCF)
- **Discounted Cash Flow** (DCF) is a valuation method used to estimate the value of an investment based on its expected future cash flows.

## Graham's Formula
Estimates the intrinsic value of a stock based on its earnings per share (EPS) and the price-to-earnings (P/E) ratio.

# Options
## The ABC June 20 call has a premium of 3.5 at a time when ABC stock is trading at $22 per share.
This means, for $3.5, I can buy the right (but not obligation) to buy shares of ABC at $20, no matter the stock price, until June (not 20th of June, that's the strike price).
Since I can buy the shares at $20, $2 below the current market price, the **intrinsic value** of the option is $2.5. 
But I have to pay $3.5 for it, so the total money I'd be losing compared to buying the shares directly = the actual premium i'm paying over the market = the time value of the option = premium - intrinsic value = premium + strike price - stock price = $1.5

## 
OTC Option: Over-the-counter, traded directly between two parties, not in a public exchange.

## Options that may be exercised at any time up to the day on which they expire are:
- American style exercise options
- European style exercise options
- Plain vanilla style exercise options

Answer: American style exercise options.
European style can only be exercised at the expiration date, and plain vanilla a basic type of option, not the way too exercise the option.

## Consider a call option selling for $3 in which the exercise price is $50 and the current price of the underlying is $48. The value at expiration and the profit for a call seller if the price of the underlying at expiration is $41 are:
- **The call option value at expiration is $0 and the call seller's profit is $300.**
- The call option value at expiration is $600 and the call seller's profit is $300.
- The call option value at expiration is $0 and the call seller's profit is $1,200.

Since the exercise price is higher than the price in both cases, the option is worth $0 in both cases.
The seller then gets the $3 premium, and since standard options are for 100 shares, the profit of the seller is $300.

## The following risks are associated with trading options, except for:
- Counterparty credit risk
    - May happen, for OTC options the counterparty may not be able to pay (default). In exchanges this is not a problem
- Liquidity risk
    - Yeah this is always there. Options need liquidity too.
- **Destabilization and systemic risk**
    - Doesn't make sense for options. They're not like banks lending money.

## If an investor buys a call, what position is taken on the underlying interest of the option?
- **Bullish**
    - Has to buy so bullish
- Bearish
- Short
- Hedged
    - Not offsetting anything

## If an investor writes an ABC stock put and the option is exercised, the investor must:
- Receive cash
- Deliver cash
- Buy stock
- Deliver stock

write = sell
stock put = option to sell stock
If the investor writes an ABC stock put, he is selling the option to sell stock. So his buyer will have the RIGHT to sell stock, to him, at the option price. This means the investor will be OBLIGATED to buy stock.

## With no other positions, an investor sells short 100 XYZ at $40 and sells 1 XYZ Oct 40 put at $5. If the put is exercised when the market price of the stock is $35 and the stock is used to cover the short position, what would the investor's profit or loss be?
- $500 loss
- **$500 profit**
- $0 profit
- $1,000 profit
- I don't know.

So he sells short (he will have to buy later) 100 shares, at $40, gaining $4000 + obligation to buy later.
He sells a put option, so he gives another person the right to sell him 100 (standard amount) shares at $5 premium.
When exercised, he gets $500 of premiums. But has to buy the put option shares at $40, paying $4000.
He is basically lending stock from the put option buyer + selling it in one operation, the selling operation provides the cash for the put option buyer, so he needs no cash reserves. He is buying and selling at $40, so he is not affected by the stock price (if the put option is exercised, which it is). Therefore his profit comes from the $500 premium.

## A decline in the volatility of the underlying price:
- **Decreases the value of both a call option and a put option.**
- Decreases the value of a call option.
- Decreases the value of a put option.
- I don't know.

The lower the movement in stock price, the lower the need to pay a premium for the option. The option is less likely to be exercised, so it's worth less.

## A put option is considered at-the-money at expiration if:
- The stock's market price is above the strike price of the option
- The stock's market price is below the strike price of the option
- **Intrinsic value is 0**
- Intrinsic value is negative
- I don't know.

If, ignoring the premium, the option is not better or worse than the market price. That's intrinsic value = strike price - stock price = 0.

## Which of the following option positions has the potential for an unlimited loss (mentioned short positions are uncovered)?
- Long put.
    - Long means you own the put, so you can sell stock at the strike price whenever you want. Your losses are limited to the premium you paid, and gains are limited to the strike price. I would get max gains if the stock goes to 0, I buy from the market and sell at the strike price, exercising the put option.
    - Objective: Sell fixed something worthless. WILL GO DOWN.
- Long call.
    - Long means you own the call, so you can buy stock at the strike price whenever you want. Your losses are limited to the premium you paid, and gains are unlimited, since the market price can go to infinity.
    - Objective: Buy cheap something valuable. WILL GO UP.
- Short put.
    - You sell a put option, so the buyer has the right to sell you stock at the strike price. If the stock goes to 0, i will have to pay the strike price and get no value in return. My losses are limited to the strike price.
    - Objective: Buy not expensive, WILL NOT GO DOWN.
- **Short call.**
    - You sell a call option without owning the stock. So the buyer has the right to buy stock from you at the strike price, and you're forced to buy it paying the stock price, which could go to infinity, to then deliver it and sell it at the strike price. This is the only case where you are forced to own something of unlimited value.
    - Objective: Buy not expensive, WILL NOT GO UP.
- I don't know.

# Bonds
## A bond bought at 98.8 has a par value of $1000 and a coupon rate of 6%. Coupon payments are made semi-annually. The periodic interest payment is:
- $30.00, paid twice a year
- $60.00, paid once a year
- $29.64, paid twice a year
- I don't know

## What is the clean price of a bond?
- The price net of tax
- The price excluding accrued interest
- The price excluding the broker's commission
- I don't know

## The bond coupon payment is most likely to be taxed at a rate applicable to:
- ordinary income
- short-term capital gain
- ordinary dividend income
- I don't know

## A 'buy-and-hold until maturity' investor purchases a fixed-rate bond. Which of the following sources of return is most likely exposed to interest rate risk?
- Capital gain or loss
- Redemption of principal
- Reinvestment of coupon payments
- I don't know

## Relative to an otherwise similar option-free bond, a:
- putable bond will trade at a higher price
- callable bond will trade at a higher price
- convertible bond will trade at a lower price
- I don't know

## Which of the following is NOT correct regarding callable bonds?
- Prepayment risk involves the scenario where an issuer calls the bond prior to maturity
- Prepayment risk is taken into account in the pricing of the bond
- Issuers usually call their bonds when interest rates raise above current bond rates
- I don't know

## An investor paid $900 for a bond with a par value of $1000 and a coupon rate of 5%. Coupon payments are made semi-annually. Bond's current yield is:
- 0.05
- 0.055
- 0.025
- I don't know

## If a bond is traded at a discount, then:
- The current yield is higher than the nominal yield
- the yield-to-maturity is lower than the current yield
- the yield-to-maturity is lower than the nominal yield
- I don't know

## The term most likely used to refer to the legal contract that describes the form of the bond, the issuer's obligations, and the investor's rights is:
- indenture
- debenture
- letter of credit
- I don't know

## Which of the following is correct regarding inflation risk?
- Inflation risk is the risk that the bondholder realises a positive real yield-to-maturity
- Inflation risk is the risk that the rate of the yield to call or maturity of the bond will not provide a positive return over the rate of inflation for the period of the investment
- As the inflation rate rises, the market price of existing bonds tends to increase
- I don't know

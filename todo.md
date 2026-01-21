# Todo List

- [ ] Configure Grafana (Fix permissions and setup dashboards)

_(Note: Restored from previous content on 2026-01-21)_

- marubeni not in dashboard? add them if missing
- whats up with the rim model with some stocks? it provides crazy high values

- META?
- check energy companies

- I want to run some simulations of investments using each model, investing on
  old data, so we can check how much money would they have made if used in the
  past. I'm not sure if this would fail due to analyzing on already seen data
  though. Maybe skip some stocks and periods randomly from training and use them
  for testing? Or create a separate test model, just for this task?


- I basically want to take the max price of the period from next year to next 2
  years, and train with that, instead of the price just after one year. Maybe this
  should be the opportunistic model. To this model, somehow make it conservative so
  we actually check that it is super super unlikely to get stocks in the lower % of
  returns, even if some % of super high gains. (Think about probability
  distribution and how to rate it?)

- i want gbm for 1y 3y both in normal and lite version
- show them all in the dashboard


- Does the neural network predictor look good? I just cloned the repo, so we may
  need to retrain it. I'd like to understand the cases where it's very different
  from other predictions and undertsand why. We need a reliable way to determine
  how good it is at predictions. Use a suite of data from various decades and
  sectors, and use separate test and training sets to analyze it well. Determine
  some factor of confidence in the prediction. Oh and make it visible in the
  dashboard.

- Is the industry of the company included as input parameter for the neural
  network? that data is available from yfinance
---


- to invest in warren style, human like instructions or can be programmed?


- nem P/tangible book value?

- now compare your previous analysis to the one of the repo, and try to
  understand why your recommendations differ. What is different?



- - Create parameter that includes the 5 year past earning growth as in the
  video, and use it in filter. It certainly matches with high PE companies, might
  wanna do it for small caps that combine that with low PE. Might want to do the
  analysis of the video taking the second derivative of the earnings too, see if
  there's correlation too
    - https://youtu.be/-xq7a-tptno?si=kl6EQT-Jfxu1xmyG
    - https://www.hellostocks.ai/superinvestor/strategies


- check wallet design in stuff.md

- why most models say this is overpriced: 8031.T

- how much upside has bitcoin left? Should i sell bitcoin to invest in cheap
  stocks? let's look at the total money invested in bitcoin vs gold, stocks, and
  bonds.

- What symbol to put when a model failed to evaluate the stock (nonsense values,
  can't apply it), an x instead of -

# Analyze stocks like Berkshire correctly
  Given the current system's capabilities, here are more feasible ways to
  improve the analysis for such businesses:

   * Focus on Book Value Growth: For companies like Berkshire Hathaway, growth
     in book value per share is often a more meaningful metric
     than traditional revenue or earnings growth. It directly reflects the
     compounding of their underlying assets. We could incorporate
     this as a key growth metric in the screening process.
   * Adjusting Thresholds/Weights: For identified holding companies, we could
     apply different, more lenient growth thresholds, or give
     less weight to traditional growth metrics and more weight to balance sheet
     strength (e.g., high current ratio, low debt-to-equity)
     and overall return on assets/equity, which reflect efficient capital
     deployment.
   * Custom Configuration: We could create a specific configuration file
     tailored for holding companies, with adjusted metrics and
     thresholds.

  In summary, while a full automated Sum-of-the-Parts valuation is complex, we
  can make significant improvements by:
   1. Developing methods to identify these "special kinds" of businesses.
   2. Incorporating more relevant metrics like book value growth.
   3. Adjusting the weighting or thresholds of existing metrics to better
     reflect their unique financial characteristics.



# Check
PBR


- IBKR Market screener 2.0
- Expand investable-universe coverage for Revolut/IBKR markets (tickers +
  exchange mapping)
- Update checklists to use check operating margin instead of gross?

- Study LOGI in more depth. Great fundamentals. I would pay twice its stock
  value
- Study skyworks in more depth
- Study steel dynamics. What's going to happen with steel demand? If it falls
  back down after all these investments, the stock will collapse.

- [ ] Create spreadsheet to calculate price according to assumptions in bad -
  medium - good scenarios.(https://youtu.be/H1gfAXvRoSM)
- [ ] gdi? P/E = 12 cuando es predecible y crece

- Valuation models
    - Graham
        - ![](readme/20230523133421.png)
    - Discounted Cash Flow (DCF)
    - Multiples
    - Dividend discount

---



## Copypaste to do one
Price:
Shares:

Checklist:
- Price/Gross Profit =  < 10
- Gross profit margin =  > .1
- Revenue grows
- Gross profit grows
- Shares outstanding
- Equity
- Equity per share = $/share
- Time to pay debt: Long term liabilities / free cash flow =  /  =  < 5

### Estimate stock price
- Value = Equity + PE_estimated * Gross Profit =
- Price per stock = Value / Shares = $/stock
- Current price: $/stock

---
EDGAR parsing? implement it?

---
# INVESTMENTS
This is my current wallet, what would you do with it? What modifications? Which
is the first stock you would sell, and what would you buy with it?



---

- Consider gold, bitcoin, etc. as alternatives to stocks, instructions for AI
  to consider waiting, like berkshire has sometimes done, to wait for better
  opportunities with treasuries, short-term bonds, etc.
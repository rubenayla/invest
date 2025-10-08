I just noticed we have two dashboards. The html
  file:///Users/rubenayla/repos/invest/dashboard/valuation_dashboard.html and the one that runs a
  server http://localhost:3446/. Which one should we use and why? We can't have this duplicated.

About your suggestion to re-fetch the failed stocks: this is going to drive me crazy. I've told you like 4 times to make sure that the code retries by itself. It should wait a variable amount, and end up downloading everything by itself. The only failed stocks at the end can be ones that have been retried 6 times and still failed.

show in dashboard predictions of neural net for all stocks < clean db with required raw data and ratios for the training of neural nets, and working code so the nets can run predictions and save them in the db too


Update the documentation with the new multi output neuron models and the cache.


Does the neural network predictor look good? I just cloned the repo, so we may need to retrain it. I'd like to understand the cases where it's very different from other predictions and undertsand why. We need a reliable way to determine how good it is at predictions. Use a suite of data from various decades and sectors, and use separate test and training sets to analyze it well. Determine some factor of confidence in the prediction.

Let's commit our changes cleanly please.

- Neural network that takes the stock price, fundamental ratios, growths, etc and returns a score. Run that over all known data for past companies, and train, maybe genetic algorithm, so it learns the best possible valuation technique.
  - The problem is not knowing the time interval to consider. Maybe it's bad for next month, but great for next 5 years. 

Is the industry of the company included as input parameter for the neural network? that data is available from yfinance




to invest in warren style, human like instructions or can be programmed?


nem P/tangible book value?

now compare your previous analysis to the one of the repo, and try to understand why your recommendations differ. What is different?

- take a look: https://www.ark-funds.com/funds/arkvx

- Create parameter that includes the 5 year past earning growth as in the video, and use it in filter. It certainly matches with high PE companies, might wanna do it for small caps that combine that with low PE. Might want to do the analysis of the video taking the second derivative of the earnings too, see if there's correlation too
    - https://youtu.be/-xq7a-tptno?si=kl6EQT-Jfxu1xmyG
    - https://www.hellostocks.ai/superinvestor/strategies


check wallet design in stuff.md

why most models say this is overpriced: 8031.T

how much upside has bitcoin left? Should i sell bitcoin to invest in cheap stocks? let's look at the total money invested in bitcoin vs gold, stocks, and bonds.

What symbol to put when a model failed to evaluate the stock (nonsense values, can't apply it), an x instead of -

# Analyze stocks like Berkshire correctly
  Given the current system's capabilities, here are more feasible ways to improve the analysis for such businesses:

   * Focus on Book Value Growth: For companies like Berkshire Hathaway, growth in book value per share is often a more meaningful metric
     than traditional revenue or earnings growth. It directly reflects the compounding of their underlying assets. We could incorporate
     this as a key growth metric in the screening process.
   * Adjusting Thresholds/Weights: For identified holding companies, we could apply different, more lenient growth thresholds, or give
     less weight to traditional growth metrics and more weight to balance sheet strength (e.g., high current ratio, low debt-to-equity)
     and overall return on assets/equity, which reflect efficient capital deployment.
   * Custom Configuration: We could create a specific configuration file tailored for holding companies, with adjusted metrics and
     thresholds.

  In summary, while a full automated Sum-of-the-Parts valuation is complex, we can make significant improvements by:
   1. Developing methods to identify these "special kinds" of businesses.
   2. Incorporating more relevant metrics like book value growth.
   3. Adjusting the weighting or thresholds of existing metrics to better reflect their unique financial characteristics.



# Check
- IBKR Market screener 2.0
- Update checklists to use check operating margin instead of gross?

- Study LOGI in more depth. Great fundamentals. I would pay twice its stock value
- Study skyworks in more depth
- Study steel dynamics. What's going to happen with steel demand? If it falls back down after all these investments, the stock will collapse.

- [ ] Create spreadsheet to calculate price according to assumptions in bad - medium - good scenarios.(https://youtu.be/H1gfAXvRoSM)
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
This is my current wallet, what would you do with it? What modifications? Which is the first stock you would sell, and what would you buy with it?



---

- Consider gold, bitcoin, etc. as alternatives to stocks, instructions for AI to consider waiting, like berkshire has sometimes done, to wait for better opportunities with treasuries, short-term bonds, etc.
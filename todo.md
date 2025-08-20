Can you check for bad habits or things we could improve in this project, so it grows with no problems and keeps being organized? Good practice and so on.

Analyze APA and the other top stocks

- investigate levels.vc

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

## Advanced Valuation Models to Implement
- [x] **Residual Income Model (RIM)** ⭐⭐⭐ - Perfect for financial companies
    - RIM = Book Value + PV(Abnormal Earnings)
    - Abnormal Earnings = (ROE - Cost of Equity) × Book Value
    - Great for banks, insurance companies where DCF struggles
- [x] **Monte Carlo DCF** ⭐⭐ - Add confidence intervals
    - Use probability distributions for growth rates, discount rates
    - Output: "Fair Value: $45.67 (Range: $38.12 - $52.34, 68% confidence)"
- [x] **Multi-Stage DCF** ⭐⭐⭐ - More realistic growth phases
    - Phase 1: High growth (Years 1-5)
    - Phase 2: Transition (Years 6-10)
    - Phase 3: Terminal stable growth
- [ ] **Sector-Specific Models** ⭐⭐
    - REITs: FFO (Funds From Operations) based
    - Banks: ROE/Book value, regulatory capital ratios
    - Tech: Revenue multiples, user-based metrics  
    - Utilities: Dividend discount, regulatory frameworks
- [ ] **Ensemble/Blended Model** ⭐⭐⭐
    - Weighted average of all models: 0.3×DCF + 0.3×Enhanced DCF + 0.2×RIM + 0.2×Ratios
    - Automatically adjust weights based on sector and data quality
- [ ] **Real Options Valuation** ⭐ - For high-growth tech companies
    - Value growth opportunities as call options
    - Especially good for companies with significant R&D or expansion potential

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

- MOH (Molina Healthcare)
  - Giant crash like CNC, but they have a better balance sheet and are more efficient.
  - Their Medical Cost Ratio went from 88% to 90%, but it was already expected. The sudden fall seems quite irrational, since it affected CNC not MOH. "wait, if Centene got hit, maybe all Medicaid/ACA insurers are riskier than we thought".
- CNC (Centene)
  - Giant crash due to unexpected ACA risk adjustment payment (they have healthier patients for the same costs)
- Cognizant (CTSH)
  - 
- HIG (Hartford)
- NEM (Newmont)?
- IBM
- Argetina
- MITSY
- acgl
- BIDU
- CSCO
- META
- ORCL
- PYPL
- QCOM
- SAP


---

- Consider gold, bitcoin, etc. as alternatives to stocks, instructions for AI to consider waiting, like berkshire has sometimes done, to wait for better opportunities with treasuries, short-term bonds, etc.
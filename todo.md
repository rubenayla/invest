Hey let's move all these extra files to their own folder. Clean up a bit the main folder
rubenayla@y540:~/repos/invest$ ls
asset_valuation.md                                    htmlcov                                          sp500_test25_screen_20250813_000353_results.csv
backtesting                                           INSTALL.md                                       sp500_test50_screen_20250813_000635_report.txt
CLAUDE_DESKTOP_GUIDE.md                               learn.md                                         sp500_test50_screen_20250813_000635_results.csv
CLAUDE.md                                             mkdocs.yml                                       sp500_top100_screen_20250812_234131_report.txt
configs                                               poetry.lock                                      sp500_top100_screen_20250812_234131_results.csv
conservative_value_screen_20250812_223153_report.txt  pyproject.toml                                   sp500_top100_screen_20250813_002407_report.txt
coverage.xml                                          README.md                                        sp500_top100_screen_20250813_002407_results.csv
dashboard                                             scripts                                          src
default_analysis_20250818_132054_report.txt           setup.py                                         stuff
default_analysis_20250818_132054_results.csv          site                                             stuff.md
default_analysis_20250818_132206_report.txt           sp500_full_screen_20250813_003356_report.txt     tests
default_analysis_20250818_132206_results.csv          sp500_full_screen_20250813_003356_results.csv    todo.md
default_analysis_20250818_132302_report.txt           sp500_subset_screen_20250818_123218_report.txt   watchlist.md
default_analysis_20250818_132302_results.csv          sp500_subset_screen_20250818_123218_results.csv
docs                                                  sp500_test25_screen_20250813_000353_report.txt




For testing, add an agent (how are they called? the ones that choose what to invest in. It's not the same as the valuation model, since it must choose one or several stocks to invest in, not just value them independently) that simply buys the biggest stocks of the sp500. If forced to diversity, the top x stocks, otherwise the top stock. Just that. I'd like it for comparison purposes and to see how it performs. Some curiosity.

Make sure the actions either work or are deleted

- modelos de inversion: gestion de riesgo, diversificación?

- Let's update the code to be able to value ETFs, and do the backtest with those. Should we make the code able to handle anything, or separate ETFs and stocks, so each one is separate and easier to understand/manage?
- Consider gold, bitcoin, etc. as alternatives to stocks, instructions for AI to consider waiting, like berkshire has sometimes done, to wait for better opportunities with treasuries, short-term bonds, etc.

- dashboard with the top companies and critical data
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

- Cognizant (CTSH)
- HIG (Hartford)
- NEM (Newmont)?
- Argetina
- MITSY
- acgl
- BIDU
- CSCO
- IBM
- META
- ORCL
- PYPL
- QCOM
- SAP
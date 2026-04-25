<!-- read in full — kept under 150 lines -->
# Data Conventions

**Ratios stored as ratios, not percentages:**
- Store: `0.93` (not `93`)
- Multiply directly: `debt * 0.93`

**yfinance returns `debtToEquity` as percentage, so calculate manually:**
```python
debt_to_equity = total_debt / (book_value * shares_outstanding)
```
Location: `scripts/data_fetcher.py:289-299`

# Solutions — Recurring Fixes

## uv run fails in sandbox
Use `sqlite3` + `jq` for quick data extraction instead of `uv run python`.

## Pre-push hook blocks push with uncommitted changes
`git stash push && git push && git stash pop`

## yfinance debtToEquity is a percentage, not a ratio
Calculate manually: `total_debt / (book_value * shares_outstanding)`.
See `scripts/data_fetcher.py:289-299`.

## Edit tool "string not found"
Re-read the file first — trailing whitespace or line endings may differ from what you expect.

## EDGAR rate limiting (429 errors)
Reuse `TokenBucketRateLimiter` from `insider_fetcher.py` (10 req/s). Set `User-Agent` header with contact email.

## 13F values are in thousands
Multiply by 1000. Exception: schema X0202 may report actual USD — check the filing header.

## CUSIP-to-ticker resolution missing
Run `scripts/fetch_holdings_data.py --build-cusip-map` or let it build lazily on first fetch.

## Database schema mismatch with script queries
Database is source of truth. Run `PRAGMA table_info(table_name)` to check, then fix the script.

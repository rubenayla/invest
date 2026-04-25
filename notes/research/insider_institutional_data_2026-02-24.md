# Insider/Institutional Data Expansion — Research Notes (2026-02-24)

## What we CAN do (free, programmatic)

1. **SEC 13D/13G** (activist stakes, 5%+ holders) — Same EDGAR submissions API we already use. Filter `"13D" in form or "13G" in form` in company's submissions JSON. XML has: holder name, shares, % of class, purpose/intent (activist vs passive). Filed within 10 days of crossing 5%.

2. **SEC 13F** (institutional holdings, quarterly) — EDGAR, but requires the **fund's CIK** (not the company's). Need a curated list of "smart money" fund CIKs. Holdings in `informationTable` XML: issuer name, CUSIP, shares, value (USD, not thousands in schema X0202). Quarter-over-quarter change requires diffing two filings by CUSIP.

3. **Japan large shareholding reports (大量保有報告書)** — EDINET API v2 (free, REST JSON, requires free API key registration at `api.edinet-fsa.go.jp`). docTypeCode 350 (initial 5%+ report) and 360 (change report for 1%+ changes). XBRL/CSV output. Python library: `edinet-tools`.

4. **France PDMR director trades** — Free CSV from data.gouv.fr + API at lestransactions.fr/api. 12 fields: ISIN, declarant, date, price, volume, % of market cap. Data from 2017+.

## What's NOT feasible (free) — parked for now

- **Japan director-level trades (Form 4 equivalent):** No free structured API. Filed with local Finance Bureaus, not EDINET. Would need LSEG/Refinitiv (enterprise pricing) or Bloomberg Terminal.
- **Germany PDMR (BaFin):** Web-only portal, no API, data lags weeks. Would require web scraping.
- **UK PDMR (FCA/RNS):** No centralized download API. Disclosures go through RNS on LSE website.
- **EU-wide unified feed:** Does not exist. Each country has its own OAM (Officially Appointed Mechanism).
- **13F "who holds this stock" reverse lookup:** EDGAR has no query-by-CUSIP endpoint. Would need to scrape thousands of fund filings. Third-party (WhaleWisdom) exists commercially.
- **InsiderScreener (16 markets):** €14-49/mo, API by contact only. Covers EU+US+AU+IN but not Japan.

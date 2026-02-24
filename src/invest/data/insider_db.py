"""
Insider Transaction Database — schema, storage, and signal computation.

Stores Form 4 insider transactions and computes aggregate insider signals
(net buy %, cluster score, recency, dollar conviction).
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "stock_data.db"


def ensure_schema(conn: sqlite3.Connection) -> None:
    """Create insider tables if they don't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS insider_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            cik TEXT NOT NULL,
            accession_number TEXT NOT NULL,
            filing_date TEXT NOT NULL,
            transaction_date TEXT NOT NULL,
            reporter_name TEXT NOT NULL,
            reporter_title TEXT,
            transaction_type TEXT NOT NULL,
            shares REAL NOT NULL,
            price_per_share REAL,
            shares_owned_after REAL,
            is_open_market INTEGER DEFAULT 0,
            UNIQUE(accession_number, reporter_name, transaction_date, shares)
        );

        CREATE INDEX IF NOT EXISTS idx_insider_ticker
            ON insider_transactions(ticker);
        CREATE INDEX IF NOT EXISTS idx_insider_ticker_date
            ON insider_transactions(ticker, transaction_date);

        CREATE TABLE IF NOT EXISTS insider_fetch_log (
            ticker TEXT PRIMARY KEY,
            cik TEXT NOT NULL,
            fetched_at TEXT NOT NULL,
            form4_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'ok'
        );
    """)


def insert_transactions(conn: sqlite3.Connection,
                        transactions: List[Dict[str, Any]]) -> int:
    """Insert transactions, ignoring duplicates. Returns count inserted."""
    inserted = 0
    for txn in transactions:
        try:
            conn.execute("""
                INSERT OR IGNORE INTO insider_transactions
                (ticker, cik, accession_number, filing_date, transaction_date,
                 reporter_name, reporter_title, transaction_type, shares,
                 price_per_share, shares_owned_after, is_open_market)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                txn["ticker"], txn["cik"], txn["accession_number"],
                txn["filing_date"], txn["transaction_date"],
                txn["reporter_name"], txn.get("reporter_title", ""),
                txn["transaction_type"], txn["shares"],
                txn.get("price_per_share"), txn.get("shares_owned_after"),
                txn.get("is_open_market", 0),
            ))
            inserted += conn.total_changes  # approximate
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    return inserted


def log_fetch(conn: sqlite3.Connection, ticker: str, cik: str,
              form4_count: int, status: str = "ok") -> None:
    """Record that we fetched insider data for a ticker."""
    conn.execute("""
        INSERT OR REPLACE INTO insider_fetch_log (ticker, cik, fetched_at, form4_count, status)
        VALUES (?, ?, ?, ?, ?)
    """, (ticker, cik, datetime.utcnow().isoformat(), form4_count, status))
    conn.commit()


def get_known_accessions(conn: sqlite3.Connection, ticker: str) -> Set[str]:
    """Get set of accession numbers already stored for a ticker."""
    try:
        rows = conn.execute(
            "SELECT DISTINCT accession_number FROM insider_transactions WHERE ticker = ?",
            (ticker,)
        ).fetchall()
        return {r[0] for r in rows}
    except sqlite3.OperationalError:
        return set()


def compute_insider_signal(conn: sqlite3.Connection, ticker: str,
                           lookback_days: int = 180) -> Dict[str, Any]:
    """
    Compute aggregate insider activity signal for a ticker.

    Returns dict with: net_buy_pct, cluster_score, recency_days,
    dollar_conviction, buy_count, sell_count, has_data.
    """
    no_data = {
        "has_data": False,
        "net_buy_pct": 0.0,
        "cluster_score": 0,
        "recency_days": None,
        "dollar_conviction": 0.0,
        "buy_count": 0,
        "sell_count": 0,
    }

    # Check table exists
    try:
        conn.execute("SELECT 1 FROM insider_transactions LIMIT 1")
    except sqlite3.OperationalError:
        return no_data

    cutoff = (datetime.utcnow() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    rows = conn.execute("""
        SELECT transaction_type, shares, price_per_share, transaction_date,
               reporter_name, is_open_market
        FROM insider_transactions
        WHERE ticker = ? AND transaction_date >= ? AND is_open_market = 1
        ORDER BY transaction_date DESC
    """, (ticker, cutoff)).fetchall()

    if not rows:
        return no_data

    buy_shares = 0.0
    sell_shares = 0.0
    buy_dollars = 0.0
    buy_count = 0
    sell_count = 0
    last_buy_date = None
    buy_events: List[Dict[str, Any]] = []  # for cluster calculation

    for tx_type, shares, price, tx_date, reporter, is_om in rows:
        if tx_type == "P":
            buy_shares += shares
            buy_count += 1
            if price:
                buy_dollars += shares * price
            if last_buy_date is None:
                last_buy_date = tx_date
            buy_events.append({"date": tx_date, "reporter": reporter})
        elif tx_type == "S":
            sell_shares += shares
            sell_count += 1

    # Net buy % (relative to total traded volume as proxy)
    total_shares = buy_shares + sell_shares
    net_buy_pct = ((buy_shares - sell_shares) / total_shares * 100) if total_shares > 0 else 0.0

    # Cluster score: max distinct insiders buying in any 30-day window
    cluster_score = _compute_cluster_score(buy_events)

    # Recency: days since last open-market purchase
    recency_days = None
    if last_buy_date:
        try:
            last_dt = datetime.strptime(last_buy_date, "%Y-%m-%d")
            recency_days = (datetime.utcnow() - last_dt).days
        except ValueError:
            pass

    return {
        "has_data": True,
        "net_buy_pct": round(net_buy_pct, 2),
        "cluster_score": cluster_score,
        "recency_days": recency_days,
        "dollar_conviction": round(buy_dollars, 2),
        "buy_count": buy_count,
        "sell_count": sell_count,
    }


def _compute_cluster_score(buy_events: List[Dict[str, Any]]) -> int:
    """Max distinct insiders buying in any 30-day rolling window."""
    if not buy_events:
        return 0

    dated_events = []
    for ev in buy_events:
        try:
            dt = datetime.strptime(ev["date"], "%Y-%m-%d")
            dated_events.append((dt, ev["reporter"]))
        except ValueError:
            continue

    if not dated_events:
        return 0

    dated_events.sort(key=lambda x: x[0])
    max_distinct = 0

    for i, (dt_i, _) in enumerate(dated_events):
        window_end = dt_i + timedelta(days=30)
        reporters_in_window = set()
        for dt_j, reporter in dated_events[i:]:
            if dt_j <= window_end:
                reporters_in_window.add(reporter)
            else:
                break
        max_distinct = max(max_distinct, len(reporters_in_window))

    return max_distinct

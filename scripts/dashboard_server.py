#!/usr/bin/env python3
"""
Live dashboard server.

Serves the valuation dashboard with real-time health monitoring
and the ability to trigger data updates from the browser.

Usage:
    uv run python scripts/dashboard_server.py
    uv run python scripts/dashboard_server.py --port 8050
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import sqlite3
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse
from starlette.routing import Route

REPO_ROOT = Path(__file__).parent.parent
DB_PATH = REPO_ROOT / "data" / "stock_data.db"
LOG_PATH = REPO_ROOT / "logs" / "update_server.log"

sys.path.insert(0, str(REPO_ROOT / "src"))

logger = logging.getLogger("dashboard_server")

# Auto-shutdown after 2 hours of no page loads
AUTO_SHUTDOWN_SECONDS = 2 * 3600
_last_activity = time.monotonic()
_server_ref: uvicorn.Server | None = None


def _touch_activity():
    global _last_activity
    _last_activity = time.monotonic()


def _auto_shutdown_watchdog():
    """Background thread: exits the process after idle timeout."""
    while True:
        time.sleep(60)
        idle = time.monotonic() - _last_activity
        if idle >= AUTO_SHUTDOWN_SECONDS:
            logger.info("Auto-shutdown: idle for %.0f minutes", idle / 60)
            if _server_ref:
                _server_ref.should_exit = True
            else:
                os._exit(0)
            return

# ── Update process singleton ─────────────────────────────────────────────

class UpdateManager:
    """Manages a single update subprocess. Prevents concurrent runs."""

    def __init__(self):
        self._lock = threading.Lock()
        self._process: subprocess.Popen | None = None
        self._status = "idle"          # idle | running | completed | failed
        self._started_at: str | None = None
        self._finished_at: str | None = None
        self._error: str | None = None
        self._output_lines: list[str] = []
        self._exit_code: int | None = None
        self._phase: str = ""
        self._thread: threading.Thread | None = None

    @property
    def status_dict(self) -> dict:
        return {
            "status": self._status,
            "started_at": self._started_at,
            "finished_at": self._finished_at,
            "error": self._error,
            "exit_code": self._exit_code,
            "phase": self._phase,
            "tail": self._output_lines[-30:],
        }

    def start(self, universe: str = "sp500", extra_args: list[str] | None = None) -> dict:
        with self._lock:
            if self._status == "running" and self._process and self._process.poll() is None:
                return {"ok": False, "reason": "already_running", **self.status_dict}

            self._status = "running"
            self._started_at = _now_iso()
            self._finished_at = None
            self._error = None
            self._exit_code = None
            self._output_lines = []
            self._phase = "starting"

            cmd = [
                "uv", "run", "python", "scripts/update_all.py",
                "--universe", universe,
                "--skip-dashboard",   # we regenerate via the server
            ]
            if extra_args:
                cmd.extend(extra_args)

            self._thread = threading.Thread(target=self._run, args=(cmd,), daemon=True)
            self._thread.start()

            return {"ok": True, **self.status_dict}

    def _run(self, cmd: list[str]):
        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(REPO_ROOT),
            )
            for line in self._process.stdout:
                line = line.rstrip("\n")
                self._output_lines.append(line)
                # Parse phase from "==> Phase name" lines
                if line.startswith("==>"):
                    self._phase = line[4:].strip()

            self._process.wait()
            self._exit_code = self._process.returncode

            if self._exit_code == 0:
                self._status = "completed"
                self._phase = "done"
            else:
                self._status = "failed"
                self._error = f"Process exited with code {self._exit_code}"
        except Exception as exc:
            self._status = "failed"
            self._error = str(exc)
            self._exit_code = -1
        finally:
            self._finished_at = _now_iso()

    def cancel(self) -> dict:
        with self._lock:
            if self._process and self._process.poll() is None:
                self._process.terminate()
                try:
                    self._process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                self._status = "failed"
                self._error = "Cancelled by user"
                self._finished_at = _now_iso()
                self._exit_code = -2
                return {"ok": True, "reason": "cancelled"}
            return {"ok": False, "reason": "not_running"}


update_manager = UpdateManager()


# ── Alarm checker ────────────────────────────────────────────────────────

def _ensure_alarm_table():
    """Create the price_alarms table if it doesn't exist."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS price_alarms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            condition TEXT NOT NULL CHECK(condition IN ('above', 'below')),
            target_price REAL NOT NULL,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
            triggered_at TEXT,
            active INTEGER NOT NULL DEFAULT 1
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_price_alarms_active ON price_alarms(active, ticker)")
    conn.commit()
    conn.close()


class AlarmChecker:
    """Periodically checks active alarms against current prices."""

    def __init__(self):
        self._thread: threading.Thread | None = None

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while True:
            try:
                self._check_alarms()
            except Exception as e:
                logger.error("Alarm check failed: %s", e)
            time.sleep(60)

    def _check_alarms(self):
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row

        alarms = conn.execute(
            "SELECT id, ticker, condition, target_price FROM price_alarms WHERE active = 1"
        ).fetchall()

        if not alarms:
            conn.close()
            return

        tickers = list({r["ticker"] for r in alarms})
        placeholders = ",".join("?" * len(tickers))
        prices = conn.execute(
            f"SELECT ticker, current_price FROM current_stock_data WHERE ticker IN ({placeholders})",
            tickers,
        ).fetchall()
        price_map = {r["ticker"]: r["current_price"] for r in prices if r["current_price"]}

        now = _now_iso()
        triggered_ids = []
        for alarm in alarms:
            price = price_map.get(alarm["ticker"])
            if price is None:
                continue
            if alarm["condition"] == "above" and price >= alarm["target_price"]:
                triggered_ids.append(alarm["id"])
            elif alarm["condition"] == "below" and price <= alarm["target_price"]:
                triggered_ids.append(alarm["id"])

        if triggered_ids:
            ph = ",".join("?" * len(triggered_ids))
            conn.execute(
                f"UPDATE price_alarms SET triggered_at = ?, active = 0 WHERE id IN ({ph})",
                [now, *triggered_ids],
            )
            conn.commit()
        conn.close()


alarm_checker = AlarmChecker()


# ── Database health queries ──────────────────────────────────────────────

def get_db_health() -> dict:
    """Query database for freshness and health metrics."""
    if not DB_PATH.exists():
        return {"ok": False, "error": "Database file not found"}

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    now = datetime.now(timezone.utc)

    health: dict = {"ok": True, "generated_at": _now_iso()}

    # ── Stock data freshness (use fetch_timestamp, count stale) ──
    try:
        row = conn.execute(
            "SELECT COUNT(*) as cnt, MIN(fetch_timestamp) as oldest, MAX(fetch_timestamp) as newest "
            "FROM current_stock_data WHERE current_price IS NOT NULL"
        ).fetchone()
        stale_row = conn.execute(
            "SELECT COUNT(*) as cnt FROM current_stock_data "
            "WHERE current_price IS NOT NULL AND fetch_timestamp < datetime('now', '-7 days')"
        ).fetchone()
        # p80 age: 80th percentile fetch_timestamp (ignores the ~20% oldest outliers)
        p80_row = conn.execute(
            "SELECT fetch_timestamp FROM current_stock_data "
            "WHERE current_price IS NOT NULL AND fetch_timestamp IS NOT NULL "
            "ORDER BY fetch_timestamp ASC "
            "LIMIT 1 OFFSET (SELECT CAST(COUNT(*) * 0.2 AS INTEGER) "
            "FROM current_stock_data WHERE current_price IS NOT NULL AND fetch_timestamp IS NOT NULL)"
        ).fetchone()
        health["stock_data"] = {
            "count": row["cnt"],
            "oldest": row["oldest"],
            "newest": row["newest"],
            "age_hours": _hours_ago(row["oldest"], now),
            "newest_age_hours": _hours_ago(row["newest"], now),
            "p80_age_hours": _hours_ago(p80_row["fetch_timestamp"], now) if p80_row else None,
            "stale_count": stale_row["cnt"],
        }
    except Exception as exc:
        health["stock_data"] = {"error": str(exc)}

    # ── Per-model valuation freshness ──
    try:
        rows = conn.execute(
            "SELECT model_name, COUNT(*) as cnt, "
            "SUM(CASE WHEN suitable = 1 THEN 1 ELSE 0 END) as ok_cnt, "
            "SUM(CASE WHEN suitable = 0 THEN 1 ELSE 0 END) as fail_cnt, "
            "MIN(timestamp) as oldest, MAX(timestamp) as newest "
            "FROM valuation_results GROUP BY model_name"
        ).fetchall()
        models = {}
        for r in rows:
            models[r["model_name"]] = {
                "total": r["cnt"],
                "successful": r["ok_cnt"],
                "failed": r["fail_cnt"],
                "oldest": r["oldest"],
                "newest": r["newest"],
                "age_hours": _hours_ago(r["oldest"], now),
                "newest_age_hours": _hours_ago(r["newest"], now),
            }
        health["models"] = models
    except Exception as exc:
        health["models"] = {"error": str(exc)}

    # ── SEC data freshness ──
    sec_dbs = {
        "insider": REPO_ROOT / "data" / "sec_edgar" / "insider_transactions.db",
        "activist": REPO_ROOT / "data" / "sec_edgar" / "activist_stakes.db",
        "holdings": REPO_ROOT / "data" / "sec_edgar" / "fund_holdings.db",
    }
    sec_health = {}
    for name, path in sec_dbs.items():
        if path.exists():
            try:
                sec_conn = sqlite3.connect(str(path))
                # Get file mod time as proxy for freshness
                mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
                age_h = (now - mtime).total_seconds() / 3600
                # Try to get row count from main table
                tables = [r[0] for r in sec_conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()]
                count = 0
                if tables:
                    count = sec_conn.execute(f"SELECT COUNT(*) FROM [{tables[0]}]").fetchone()[0]
                sec_conn.close()
                sec_health[name] = {
                    "exists": True,
                    "rows": count,
                    "last_modified": mtime.isoformat(),
                    "age_hours": round(age_h, 1),
                }
            except Exception as exc:
                sec_health[name] = {"exists": True, "error": str(exc)}
        else:
            sec_health[name] = {"exists": False}
    health["sec_data"] = sec_health

    # ── Database file size ──
    health["db_size_mb"] = round(DB_PATH.stat().st_size / (1024 * 1024), 1)

    # ── Recent errors (last 20 failed valuations) ──
    try:
        rows = conn.execute(
            "SELECT ticker, model_name, error_message, failure_reason, timestamp "
            "FROM valuation_results WHERE suitable = 0 AND error_message IS NOT NULL "
            "ORDER BY timestamp DESC LIMIT 20"
        ).fetchall()
        health["recent_errors"] = [dict(r) for r in rows]
    except Exception as exc:
        health["recent_errors"] = {"error": str(exc)}

    conn.close()
    return health


# ── Route handlers ───────────────────────────────────────────────────────

async def index(request: Request) -> HTMLResponse:
    """Serve the dashboard HTML, regenerated from DB on each request."""
    _touch_activity()
    from invest.dashboard_components.html_generator import HTMLGenerator

    # Import the loading function from the existing dashboard script
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from dashboard import load_stocks_from_database

    stocks_data = load_stocks_from_database()

    generator = HTMLGenerator()
    progress_data = {
        "total_analyzed": len(stocks_data),
        "successful": len(stocks_data),
        "failed": 0,
    }
    health = get_db_health()
    metadata = {
        "last_updated": _now_iso(),
        "server_mode": True,
        "health": health,
        "update_status": update_manager.status_dict,
    }
    html = generator.generate_dashboard_html(stocks_data, progress_data, metadata)
    return HTMLResponse(html, headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"})


async def api_health(request: Request) -> JSONResponse:
    """Return database health/freshness data."""
    return JSONResponse(get_db_health())


async def api_update_start(request: Request) -> JSONResponse:
    """Start an update process."""
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    universe = body.get("universe", "sp500")
    extra_args = body.get("extra_args", [])
    result = update_manager.start(universe=universe, extra_args=extra_args)
    return JSONResponse(result)


async def api_update_status(request: Request) -> JSONResponse:
    """Return current update status."""
    return JSONResponse(update_manager.status_dict)


async def api_update_cancel(request: Request) -> JSONResponse:
    """Cancel a running update."""
    return JSONResponse(update_manager.cancel())


async def api_shutdown(request: Request) -> JSONResponse:
    """Gracefully shut down the server."""
    logger.info("Shutdown requested via API")
    if _server_ref:
        _server_ref.should_exit = True
    else:
        threading.Timer(0.5, lambda: os._exit(0)).start()
    return JSONResponse({"ok": True})


# ── Alarm API ────────────────────────────────────────────────────────────

async def api_alarm_create(request: Request) -> JSONResponse:
    """Create a new price alarm."""
    body = await request.json()
    ticker = body.get("ticker", "").upper().strip()
    condition = body.get("condition")
    target_price = body.get("target_price")

    if not ticker or condition not in ("above", "below") or not isinstance(target_price, (int, float)):
        return JSONResponse({"ok": False, "error": "Invalid parameters"}, status_code=400)

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        "INSERT INTO price_alarms (ticker, condition, target_price) VALUES (?, ?, ?)",
        (ticker, condition, target_price),
    )
    conn.commit()
    alarm_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return JSONResponse({"ok": True, "id": alarm_id})


async def api_alarm_list(request: Request) -> JSONResponse:
    """List alarms, optionally filtered by ticker."""
    ticker = request.query_params.get("ticker")
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    if ticker:
        rows = conn.execute(
            "SELECT * FROM price_alarms WHERE ticker = ? ORDER BY active DESC, created_at DESC",
            (ticker.upper(),),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM price_alarms ORDER BY active DESC, created_at DESC"
        ).fetchall()
    conn.close()
    return JSONResponse({"ok": True, "alarms": [dict(r) for r in rows]})


async def api_alarm_delete(request: Request) -> JSONResponse:
    """Delete an alarm by id."""
    alarm_id = request.path_params["alarm_id"]
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("DELETE FROM price_alarms WHERE id = ?", (alarm_id,))
    conn.commit()
    conn.close()
    return JSONResponse({"ok": True})


async def api_alarm_triggered(request: Request) -> JSONResponse:
    """Return alarms triggered since a given timestamp."""
    since = request.query_params.get("since")
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    if since:
        rows = conn.execute(
            "SELECT * FROM price_alarms WHERE triggered_at IS NOT NULL AND triggered_at > ? "
            "ORDER BY triggered_at DESC",
            (since,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM price_alarms WHERE triggered_at IS NOT NULL AND active = 0 "
            "ORDER BY triggered_at DESC LIMIT 20"
        ).fetchall()
    conn.close()
    return JSONResponse({"ok": True, "triggered": [dict(r) for r in rows]})


# ── Insider history API ──────────────────────────────────────────────────


async def api_insider_history(request: Request) -> JSONResponse:
    """Return monthly insider buy/sell counts for a ticker (SVG chart data)."""
    ticker = request.path_params["ticker"].upper()
    conn = sqlite3.connect(str(DB_PATH))
    try:
        rows = conn.execute("""
            SELECT strftime('%Y-%m', transaction_date) AS month,
                   transaction_type,
                   COUNT(*) AS cnt
            FROM insider_transactions
            WHERE ticker = ? AND is_open_market = 1
            GROUP BY month, transaction_type
            ORDER BY month
        """, (ticker,)).fetchall()
    except sqlite3.OperationalError:
        return JSONResponse({"ok": True, "ticker": ticker, "months": []})
    finally:
        conn.close()

    # Build month → {buys, sells} map
    month_map: dict[str, dict] = {}
    for month, tx_type, cnt in rows:
        if month not in month_map:
            month_map[month] = {"month": month, "buys": 0, "sells": 0}
        if tx_type == "P":
            month_map[month]["buys"] = cnt
        elif tx_type == "S":
            month_map[month]["sells"] = cnt

    return JSONResponse({
        "ok": True,
        "ticker": ticker,
        "months": list(month_map.values()),
    })


# ── Notes (company .md files) ────────────────────────────────────────────

NOTES_DIR = REPO_ROOT / "notes" / "companies"


async def api_notes(request: Request):
    """Serve a company analysis .md file as rendered HTML."""
    import re

    ticker = request.path_params["ticker"].upper()
    # Sanitize: only allow alphanumeric, dots, hyphens (for tickers like BTC-USD, 4578.T)
    if not re.match(r"^[A-Z0-9._-]+$", ticker):
        return PlainTextResponse("Invalid ticker", status_code=400)

    md_path = NOTES_DIR / f"{ticker}.md"
    if not md_path.is_file():
        return HTMLResponse(
            f"<html><body style='background:#0d1117;color:#e0e6ed;font-family:system-ui;padding:40px;'>"
            f"<h2>No analysis notes for {ticker}</h2>"
            f"<p style='color:#738091;'>Create <code>notes/companies/{ticker}.md</code> to add notes.</p>"
            f"</body></html>",
            status_code=404,
        )

    content = md_path.read_text(encoding="utf-8")
    # Simple markdown-to-HTML: use Python markdown if available, else serve raw
    try:
        import markdown

        body = markdown.markdown(content, extensions=["tables", "fenced_code"])
    except ImportError:
        body = f"<pre style='white-space:pre-wrap;'>{content}</pre>"

    html = (
        f"<html><head><title>{ticker} - Analysis</title>"
        f"<style>"
        f"body {{ background:#0d1117; color:#e0e6ed; font-family:system-ui,-apple-system,sans-serif; "
        f"padding:40px 60px; max-width:900px; margin:0 auto; line-height:1.6; }}"
        f"h1,h2,h3 {{ color:#58a6ff; }} a {{ color:#58a6ff; }}"
        f"code {{ background:#161b22; padding:2px 6px; border-radius:3px; font-size:14px; }}"
        f"pre {{ background:#161b22; padding:16px; border-radius:6px; overflow-x:auto; }}"
        f"table {{ border-collapse:collapse; width:100%; }} "
        f"th,td {{ border:1px solid #30363d; padding:8px 12px; text-align:left; }}"
        f"th {{ background:#161b22; }}"
        f"</style></head><body>{body}</body></html>"
    )
    return HTMLResponse(html)


# ── Helpers ──────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _hours_ago(timestamp_str: str | None, now: datetime) -> float | None:
    if not timestamp_str:
        return None
    try:
        ts = datetime.fromisoformat(timestamp_str)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return round((now - ts).total_seconds() / 3600, 1)
    except (ValueError, TypeError):
        return None


# ── App ──────────────────────────────────────────────────────────────────

app = Starlette(
    routes=[
        Route("/", index),
        Route("/api/health", api_health),
        Route("/api/update", api_update_start, methods=["POST"]),
        Route("/api/update/status", api_update_status),
        Route("/api/update/cancel", api_update_cancel, methods=["POST"]),
        Route("/api/shutdown", api_shutdown, methods=["POST"]),
        Route("/api/alarms", api_alarm_create, methods=["POST"]),
        Route("/api/alarms", api_alarm_list),
        Route("/api/alarms/triggered", api_alarm_triggered),
        Route("/api/alarms/{alarm_id:int}", api_alarm_delete, methods=["DELETE"]),
        Route("/api/insider/{ticker}", api_insider_history),
        Route("/api/notes/{ticker}", api_notes),
    ],
)


def main():
    parser = argparse.ArgumentParser(description="Live investment dashboard server")
    parser.add_argument("--port", type=int, default=8050, help="Port (default: 8050)")
    parser.add_argument("--host", default="::", help="Host (default: :: — listens on both IPv4 and IPv6)")
    args = parser.parse_args()

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n  Dashboard server starting at http://{args.host}:{args.port}")
    print(f"  Database: {DB_PATH}")
    print(f"  DB size: {DB_PATH.stat().st_size / (1024*1024):.1f} MB")
    print(f"  Auto-shutdown after {AUTO_SHUTDOWN_SECONDS // 3600}h idle\n")

    # Ensure alarm table exists
    _ensure_alarm_table()

    # Start idle watchdog
    watchdog = threading.Thread(target=_auto_shutdown_watchdog, daemon=True)
    watchdog.start()

    # Start alarm checker (polls every 60s)
    alarm_checker.start()

    global _server_ref
    config = uvicorn.Config(app, host=args.host, port=args.port, log_level="info")
    server = uvicorn.Server(config)
    _server_ref = server
    server.run()


if __name__ == "__main__":
    main()

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
LOG_PATH = REPO_ROOT / "logs" / "update_server.log"

sys.path.insert(0, str(REPO_ROOT / "src"))

from invest.data.db import get_connection

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
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_alarms (
            id SERIAL PRIMARY KEY,
            ticker TEXT NOT NULL,
            condition TEXT NOT NULL CHECK(condition IN ('above', 'below')),
            target_price REAL NOT NULL,
            created_at TEXT NOT NULL DEFAULT (TO_CHAR(NOW() AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"')),
            triggered_at TEXT,
            active INTEGER NOT NULL DEFAULT 1
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_alarms_active ON price_alarms(active, ticker)")
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
        conn = get_connection(dict_cursor=True)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, ticker, condition, target_price FROM price_alarms WHERE active = 1"
        )
        alarms = cursor.fetchall()

        if not alarms:
            conn.close()
            return

        tickers = list({r["ticker"] for r in alarms})
        placeholders = ",".join("%s" for _ in tickers)
        cursor.execute(
            f"SELECT ticker, current_price FROM current_stock_data WHERE ticker IN ({placeholders})",
            tickers,
        )
        prices = cursor.fetchall()
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
            ph = ",".join("%s" for _ in triggered_ids)
            cursor.execute(
                f"UPDATE price_alarms SET triggered_at = %s, active = 0 WHERE id IN ({ph})",
                [now, *triggered_ids],
            )
            conn.commit()
        conn.close()


alarm_checker = AlarmChecker()


# ── Database health queries ──────────────────────────────────────────────

def get_db_health() -> dict:
    """Query database for freshness and health metrics."""
    conn = get_connection(dict_cursor=True)
    cursor = conn.cursor()
    now = datetime.now(timezone.utc)

    health: dict = {"ok": True, "generated_at": _now_iso()}

    # ── Stock data freshness (use fetch_timestamp, count stale) ──
    try:
        cursor.execute(
            "SELECT COUNT(*) as cnt, MIN(fetch_timestamp) as oldest, MAX(fetch_timestamp) as newest "
            "FROM current_stock_data WHERE current_price IS NOT NULL"
        )
        row = cursor.fetchone()
        cursor.execute(
            "SELECT COUNT(*) as cnt FROM current_stock_data "
            "WHERE current_price IS NOT NULL AND fetch_timestamp < NOW() - INTERVAL '7 days'"
        )
        stale_row = cursor.fetchone()
        # p80 age: 80th percentile fetch_timestamp (ignores the ~20% oldest outliers)
        cursor.execute(
            "SELECT fetch_timestamp FROM current_stock_data "
            "WHERE current_price IS NOT NULL AND fetch_timestamp IS NOT NULL "
            "ORDER BY fetch_timestamp ASC "
            "LIMIT 1 OFFSET (SELECT CAST(COUNT(*) * 0.2 AS INTEGER) "
            "FROM current_stock_data WHERE current_price IS NOT NULL AND fetch_timestamp IS NOT NULL)"
        )
        p80_row = cursor.fetchone()
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
        conn.rollback()

    # ── Per-model valuation freshness ──
    try:
        cursor.execute(
            "SELECT model_name, COUNT(*) as cnt, "
            "SUM(CASE WHEN suitable THEN 1 ELSE 0 END) as ok_cnt, "
            "SUM(CASE WHEN NOT suitable THEN 1 ELSE 0 END) as fail_cnt, "
            "MIN(timestamp) as oldest, MAX(timestamp) as newest "
            "FROM valuation_results GROUP BY model_name"
        )
        rows = cursor.fetchall()
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
        conn.rollback()

    # ── SEC data freshness (now in main Postgres DB) ──
    sec_tables = {
        "insider": "insider_transactions",
        "activist": "activist_stakes",
        "holdings": "fund_holdings",
    }
    sec_health = {}
    for name, table in sec_tables.items():
        try:
            cursor.execute(f"SELECT COUNT(*) as cnt FROM {table}")
            count = cursor.fetchone()["cnt"]
            sec_health[name] = {"exists": True, "rows": count}
        except Exception as exc:
            sec_health[name] = {"exists": False, "error": str(exc)}
            conn.rollback()
    health["sec_data"] = sec_health

    # ── Database size (PostgreSQL) ──
    try:
        cursor.execute("SELECT pg_database_size('invest')")
        size_bytes = cursor.fetchone()["pg_database_size"]
        health["db_size_mb"] = round(size_bytes / (1024 * 1024), 1)
    except Exception as exc:
        health["db_size_mb"] = None
        conn.rollback()

    # ── Recent errors (last 20 failed valuations) ──
    try:
        cursor.execute(
            "SELECT ticker, model_name, error_message, failure_reason, timestamp "
            "FROM valuation_results WHERE NOT suitable AND error_message IS NOT NULL "
            "ORDER BY timestamp DESC LIMIT 20"
        )
        rows = cursor.fetchall()
        health["recent_errors"] = [dict(r) for r in rows]
    except Exception as exc:
        health["recent_errors"] = {"error": str(exc)}
        conn.rollback()

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
    return JSONResponse(_json_safe(get_db_health()))


async def api_update_start(request: Request) -> JSONResponse:
    """Start an update process."""
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    universe = body.get("universe", "all")
    extra_args = body.get("extra_args", [])
    if body.get("lite", False) and "--lite-fetch" not in extra_args:
        extra_args.append("--lite-fetch")
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

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO price_alarms (ticker, condition, target_price) VALUES (%s, %s, %s) RETURNING id",
        (ticker, condition, target_price),
    )
    alarm_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return JSONResponse({"ok": True, "id": alarm_id})


async def api_alarm_list(request: Request) -> JSONResponse:
    """List alarms, optionally filtered by ticker."""
    ticker = request.query_params.get("ticker")
    conn = get_connection(dict_cursor=True)
    cursor = conn.cursor()
    if ticker:
        cursor.execute(
            "SELECT * FROM price_alarms WHERE ticker = %s ORDER BY active DESC, created_at DESC",
            (ticker.upper(),),
        )
    else:
        cursor.execute(
            "SELECT * FROM price_alarms ORDER BY active DESC, created_at DESC"
        )
    rows = cursor.fetchall()
    conn.close()
    return JSONResponse(_json_safe({"ok": True, "alarms": [dict(r) for r in rows]}))


async def api_alarm_delete(request: Request) -> JSONResponse:
    """Delete an alarm by id."""
    alarm_id = request.path_params["alarm_id"]
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM price_alarms WHERE id = %s", (alarm_id,))
    conn.commit()
    conn.close()
    return JSONResponse({"ok": True})


async def api_alarm_triggered(request: Request) -> JSONResponse:
    """Return alarms triggered since a given timestamp."""
    since = request.query_params.get("since")
    conn = get_connection(dict_cursor=True)
    cursor = conn.cursor()
    if since:
        cursor.execute(
            "SELECT * FROM price_alarms WHERE triggered_at IS NOT NULL AND triggered_at > %s "
            "ORDER BY triggered_at DESC",
            (since,),
        )
    else:
        cursor.execute(
            "SELECT * FROM price_alarms WHERE triggered_at IS NOT NULL AND active = 0 "
            "ORDER BY triggered_at DESC LIMIT 20"
        )
    rows = cursor.fetchall()
    conn.close()
    return JSONResponse(_json_safe({"ok": True, "triggered": [dict(r) for r in rows]}))


# ── Insider history API ──────────────────────────────────────────────────


async def api_insider_history(request: Request) -> JSONResponse:
    """Return monthly insider buy/sell counts for a ticker (SVG chart data)."""
    ticker = request.path_params["ticker"].upper()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT TO_CHAR(transaction_date, 'YYYY-MM') AS month,
                   transaction_type,
                   COUNT(*) AS cnt
            FROM insider_transactions
            WHERE ticker = %s AND is_open_market = 1
            GROUP BY month, transaction_type
            ORDER BY month
        """, (ticker,))
        rows = cursor.fetchall()
    except Exception:
        conn.rollback()
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
        f"font-size:18px; padding:48px 72px; max-width:960px; margin:0 auto; line-height:1.7; }}"
        f"h1 {{ color:#58a6ff; font-size:2em; }} h2 {{ color:#58a6ff; font-size:1.5em; }} h3 {{ color:#58a6ff; font-size:1.25em; }}"
        f"a {{ color:#58a6ff; }}"
        f"code {{ background:#161b22; padding:2px 6px; border-radius:3px; font-size:0.9em; }}"
        f"pre {{ background:#161b22; padding:16px; border-radius:6px; overflow-x:auto; font-size:0.85em; }}"
        f"table {{ border-collapse:collapse; width:100%; font-size:0.95em; }} "
        f"th,td {{ border:1px solid #30363d; padding:10px 14px; text-align:left; }}"
        f"th {{ background:#161b22; }}"
        f"</style></head><body>{body}</body></html>"
    )
    return HTMLResponse(html)


# ── Helpers ──────────────────────────────────────────────────────────────

def _json_safe(obj):
    """Recursively convert datetime/date objects to ISO strings for JSON serialization."""
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, datetime):
        return obj.isoformat(timespec="seconds")
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    return obj


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _hours_ago(timestamp_str: str | None, now: datetime) -> float | None:
    if not timestamp_str:
        return None
    try:
        if isinstance(timestamp_str, datetime):
            ts = timestamp_str
        else:
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
    parser.add_argument("--host", default="::", help="Host (default: :: — IPv6, also accepts IPv4 on most systems)")
    parser.add_argument("--no-auto-shutdown", action="store_true", help="Disable idle auto-shutdown (for systemd service)")
    args = parser.parse_args()

    if args.no_auto_shutdown:
        global AUTO_SHUTDOWN_SECONDS
        AUTO_SHUTDOWN_SECONDS = 0

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    display_host = "[::1]" if args.host == "::" else ("127.0.0.1" if args.host == "0.0.0.0" else args.host)
    print(f"\n  Dashboard server starting at http://{display_host}:{args.port}")
    print(f"  Database: PostgreSQL (invest)")
    if AUTO_SHUTDOWN_SECONDS > 0:
        print(f"  Auto-shutdown after {AUTO_SHUTDOWN_SECONDS // 3600}h idle\n")
    else:
        print(f"  Auto-shutdown disabled\n")

    # Ensure alarm table exists
    _ensure_alarm_table()

    # Start idle watchdog (unless disabled)
    if AUTO_SHUTDOWN_SECONDS > 0:
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

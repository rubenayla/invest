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
from starlette.responses import HTMLResponse, JSONResponse
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


# ── Database health queries ──────────────────────────────────────────────

def get_db_health() -> dict:
    """Query database for freshness and health metrics."""
    if not DB_PATH.exists():
        return {"ok": False, "error": "Database file not found"}

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    now = datetime.now(timezone.utc)

    health: dict = {"ok": True, "generated_at": _now_iso()}

    # ── Stock data freshness ──
    try:
        row = conn.execute(
            "SELECT COUNT(*) as cnt, MIN(last_updated) as oldest, MAX(last_updated) as newest "
            "FROM current_stock_data WHERE current_price IS NOT NULL"
        ).fetchone()
        health["stock_data"] = {
            "count": row["cnt"],
            "oldest": row["oldest"],
            "newest": row["newest"],
            "age_hours": _hours_ago(row["oldest"], now),
            "newest_age_hours": _hours_ago(row["newest"], now),
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
    return HTMLResponse(html)


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
    ],
)


def main():
    parser = argparse.ArgumentParser(description="Live investment dashboard server")
    parser.add_argument("--port", type=int, default=8050, help="Port (default: 8050)")
    parser.add_argument("--host", default="127.0.0.1", help="Host (default: 127.0.0.1)")
    args = parser.parse_args()

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n  Dashboard server starting at http://{args.host}:{args.port}")
    print(f"  Database: {DB_PATH}")
    print(f"  DB size: {DB_PATH.stat().st_size / (1024*1024):.1f} MB")
    print(f"  Auto-shutdown after {AUTO_SHUTDOWN_SECONDS // 3600}h idle\n")

    # Start idle watchdog
    watchdog = threading.Thread(target=_auto_shutdown_watchdog, daemon=True)
    watchdog.start()

    global _server_ref
    config = uvicorn.Config(app, host=args.host, port=args.port, log_level="info")
    server = uvicorn.Server(config)
    _server_ref = server
    server.run()


if __name__ == "__main__":
    main()

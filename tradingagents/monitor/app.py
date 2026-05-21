"""FastAPI app for the live bot monitoring UI.

Read-only. Serves an HTML shell at ``/`` and JSON at ``/api/*``. Every
route requires HTTP basic auth. All endpoints tolerate an empty or missing
journal: empty DBs yield empty payloads, an unreadable DB yields HTTP 503.
"""
from __future__ import annotations

import os
import secrets
import sqlite3
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from tradingagents.monitor import db, health, metrics

_DIR = Path(__file__).parent
_AUTH_USER = "admin"


def create_app(
    journal_path: str,
    log_dir: str,
    start_capital: float = 10000.0,
) -> FastAPI:
    """Build the monitor app. Raises RuntimeError if TA_MONITOR_PASSWORD
    is unset — the UI must never run without a password."""
    password = os.environ.get("TA_MONITOR_PASSWORD", "")
    if not password:
        raise RuntimeError("TA_MONITOR_PASSWORD environment variable is not set")

    app = FastAPI(title="V5 MIX Live Monitor", docs_url=None, redoc_url=None)
    templates = Jinja2Templates(directory=str(_DIR / "templates"))
    app.mount("/static", StaticFiles(directory=str(_DIR / "static")), name="static")
    security = HTTPBasic()

    def require_auth(creds: HTTPBasicCredentials = Depends(security)) -> str:
        user_ok = secrets.compare_digest(creds.username, _AUTH_USER)
        pass_ok = secrets.compare_digest(creds.password, password)
        if not (user_ok and pass_ok):
            raise HTTPException(
                status_code=401, detail="Unauthorized",
                headers={"WWW-Authenticate": "Basic"})
        return creds.username

    def _journal() -> sqlite3.Connection:
        """Open the journal read-only, or raise HTTP 503 with {error: ...}."""
        try:
            return db.open_journal(journal_path)
        except sqlite3.OperationalError as exc:
            # Raise OperationalError directly so the exception handler below
            # returns {"error": ...} (not {"detail": ...}).
            raise exc

    @app.get("/")
    def index(request: Request, _: str = Depends(require_auth)):
        return templates.TemplateResponse(request, "base.html")

    @app.get("/api/performance")
    def api_performance(_: str = Depends(require_auth)):
        conn = _journal()
        try:
            snaps = db.portfolio_snapshots(conn)
            trades = db.all_trades(conn)
        finally:
            conn.close()
        equity = metrics.equity_series(snaps, trades, start_capital)
        values = [pt["value"] for pt in equity]
        open_trades = [t for t in trades if t.get("status") == "open"]

        per_coin: dict[str, dict] = {}
        for t in trades:
            c = per_coin.setdefault(
                t["coin"], {"coin": t["coin"], "realized_pnl": 0.0,
                            "open": False})
            if t.get("pnl") is not None:
                c["realized_pnl"] += t["pnl"]
            if t.get("status") == "open":
                c["open"] = True

        return {
            "cards": {
                "equity": values[-1] if values else start_capital,
                "sharpe": round(metrics.sharpe(values), 2),
                "max_drawdown": round(metrics.max_drawdown(values), 4),
                "open_positions": len(open_trades),
            },
            "equity": equity,
            "backtest_anchor_sharpe": 3.18,
            "per_coin": list(per_coin.values()),
        }

    @app.get("/api/trades")
    def api_trades(_: str = Depends(require_auth)):
        conn = _journal()
        try:
            trades = db.all_trades(conn)
        finally:
            conn.close()
        return {
            "trades": trades,
            "open_positions": [t for t in trades if t.get("status") == "open"],
        }

    @app.get("/api/cycles")
    def api_cycles(_: str = Depends(require_auth)):
        conn = _journal()
        try:
            return {"cycles": db.list_cycles(conn)}
        finally:
            conn.close()

    @app.get("/api/cycle/{cycle_id}")
    def api_cycle(cycle_id: str, _: str = Depends(require_auth)):
        conn = _journal()
        try:
            return db.cycle_detail(conn, cycle_id)
        finally:
            conn.close()

    @app.get("/api/health")
    def api_health(_: str = Depends(require_auth)):
        conn = _journal()
        try:
            timeline = db.list_cycles(conn)
            retrains = db.retrains(conn)
        finally:
            conn.close()
        steps = health.read_structured_log(log_dir)
        return {
            "timeline": timeline,
            "steps": steps,
            "errors": health.recent_errors(steps),
            "retrains": retrains,
        }

    @app.exception_handler(sqlite3.OperationalError)
    def _db_error(request: Request, exc: sqlite3.OperationalError):
        return JSONResponse(status_code=503, content={"error": str(exc)})

    return app

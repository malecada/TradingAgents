"""FastAPI app for the live bot monitoring UI.

Read-only. Serves an HTML shell at ``/`` and JSON at ``/api/*``. Every
route requires HTTP basic auth. All endpoints tolerate an empty or missing
journal: empty DBs yield empty payloads, an unreadable DB yields HTTP 503.
"""
from __future__ import annotations

import json
import os
import secrets
import sqlite3
import time
from pathlib import Path
from typing import Callable

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from tradingagents.execution.live.config import from_binance_symbol
from tradingagents.monitor import db, health, metrics
from tradingagents.execution.live.rebacktest import compare_quant_hybrid

_DIR = Path(__file__).parent
_AUTH_USER = "admin"


def create_app(
    journal_path: str,
    log_dir: str,
    start_capital: float = 10000.0,
    position_provider: Callable[[], list[dict]] | None = None,
    position_cache_ttl: float = 30.0,
    clock: Callable[[], float] = time.monotonic,
) -> FastAPI:
    """Build the monitor app. Raises RuntimeError if TA_MONITOR_PASSWORD
    is unset — the UI must never run without a password.

    ``position_provider`` returns the live exchange positions as
    ``[{symbol, qty, usd}, ...]``; the default queries Binance via
    ``ExchangeClient.get_open_positions``. Results (and failures) are cached
    for ``position_cache_ttl`` seconds so 30-second UI polling — and retries
    during an IP ban — never hammer the exchange.
    """
    password = os.environ.get("TA_MONITOR_PASSWORD", "")
    if not password:
        raise RuntimeError("TA_MONITOR_PASSWORD environment variable is not set")

    # Default provider: lazy ExchangeClient, reused across calls. Raises (so
    # the endpoint falls back to the journal snapshot) when no creds are set.
    _exchange: dict = {"client": None}

    def _default_position_provider() -> list[dict]:
        if not os.environ.get("BINANCE_API_KEY"):
            raise RuntimeError(
                "BINANCE_API_KEY not set — live positions unavailable")
        if _exchange["client"] is None:
            from tradingagents.execution.exchange import ExchangeClient
            _exchange["client"] = ExchangeClient()
        return _exchange["client"].get_open_positions()

    provider = position_provider or _default_position_provider
    _pos_cache: dict = {"exp": 0.0, "data": None, "error": None}

    def live_positions() -> list[dict]:
        """Cached live positions. Re-raises a cached failure within the TTL
        rather than re-querying — repeated calls during a ban extend it."""
        now = clock()
        if now < _pos_cache["exp"]:
            if _pos_cache["error"] is not None:
                raise _pos_cache["error"]
            return _pos_cache["data"]
        try:
            data = provider()
            _pos_cache.update(exp=now + position_cache_ttl, data=data, error=None)
            return data
        except Exception as exc:
            _pos_cache.update(exp=now + position_cache_ttl, data=None, error=exc)
            raise

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
            # Latest cycle's predictions carry a ref_price per coin — the
            # journal-native price used to value current holdings in USD.
            latest = db.latest_cycle(conn)
            ref_prices: dict[str, float] = {}
            if latest:
                for p in db.cycle_detail(conn, latest["cycle_id"])["predictions"]:
                    if p.get("ref_price") is not None:
                        ref_prices[p["coin"]] = p["ref_price"]
        finally:
            conn.close()
        equity = metrics.equity_series(snaps, trades, start_capital)
        values = [pt["value"] for pt in equity]

        # Current holdings: live exchange positions valued at live mark price.
        # On any live failure (IP ban, missing creds, timeout) fall back to the
        # latest journal snapshot's position_qty_per_coin map valued at the
        # last-cycle ref price, flagged stale so the UI never presents frozen
        # positions as live. The V5 bot is a rebalancing strategy — it never
        # journals round-trip trades, so the equity curve is the PnL story.
        holdings: list[dict] = []
        holdings_stale = False
        holdings_as_of = None
        holdings_live_error = None
        try:
            for p in sorted(live_positions(), key=lambda x: x["symbol"]):
                if not p["qty"]:
                    continue
                holdings.append({
                    "coin": from_binance_symbol(p["symbol"]),
                    "qty": p["qty"],
                    "usd": p["usd"],
                })
        except Exception as exc:  # live unavailable — fall back to snapshot
            holdings_stale = True
            holdings_live_error = str(exc)
            if snaps:
                holdings_as_of = snaps[-1].get("ts")
                raw = snaps[-1].get("position_qty_per_coin")
                try:
                    qty_map = json.loads(raw) if raw else {}
                except (json.JSONDecodeError, TypeError):
                    qty_map = {}
                for coin, qty in sorted(qty_map.items()):
                    if not qty:
                        continue
                    price = ref_prices.get(coin)
                    holdings.append({
                        "coin": coin,
                        "qty": qty,
                        "usd": qty * price if price is not None else None,
                    })
        holdings_usd_total = sum(
            h["usd"] for h in holdings if h["usd"] is not None
        )

        return {
            "cards": {
                "equity": values[-1] if values else start_capital,
                "sharpe": round(metrics.sharpe(values), 2),
                "max_drawdown": round(metrics.max_drawdown(values), 4),
                "open_positions": len(holdings),
            },
            "equity": equity,
            "backtest_anchor_sharpe": 3.18,
            "holdings": holdings,
            "holdings_usd_total": holdings_usd_total,
            "holdings_stale": holdings_stale,
            "holdings_as_of": holdings_as_of,
            "holdings_live_error": holdings_live_error,
        }

    @app.get("/api/trades")
    def api_trades(_: str = Depends(require_auth)):
        """Execution log. The journal records one row per executed order;
        exit_price/pnl/fees are never back-filled (rebalancing strategy)."""
        conn = _journal()
        try:
            executions = db.all_trades(conn)
        finally:
            conn.close()
        return {"executions": executions}

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

    @app.get("/api/compare")
    def api_compare(_: str = Depends(require_auth)):
        """Quant vs hybrid live equity-curve comparison.

        Resolves journal paths from QUANT_DATA_DIR and HYBRID_DATA_DIR env vars
        (both default to DATA_DIR so the route degrades gracefully when only one
        bot is running).  Returns the compare_quant_hybrid dict: quant/hybrid/
        delta metrics (sharpe, ret, maxdd) + the overlapping date window.
        """
        quant_dir = Path(os.environ.get(
            "QUANT_DATA_DIR", os.environ.get("DATA_DIR", "data")))
        hybrid_dir = Path(os.environ.get(
            "HYBRID_DATA_DIR", os.environ.get("DATA_DIR", "data")))
        quant_db = quant_dir / "trade_journal.db"
        hybrid_db = hybrid_dir / "trade_journal.db"
        if quant_db == hybrid_db:
            return {"error": (
                "hybrid not configured — "
                "HYBRID_DATA_DIR not set or equals QUANT_DATA_DIR"
            )}
        coins_env = os.environ.get("COMPARE_COINS", "")
        coins = [c.strip() for c in coins_env.split(",") if c.strip()]
        return compare_quant_hybrid(quant_db, hybrid_db, coins=coins)

    @app.exception_handler(sqlite3.OperationalError)
    def _db_error(request: Request, exc: sqlite3.OperationalError):
        return JSONResponse(status_code=503, content={"error": str(exc)})

    return app

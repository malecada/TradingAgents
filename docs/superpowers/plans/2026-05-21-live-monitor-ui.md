# Live Bot Monitoring UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a read-only FastAPI web dashboard that runs on the Hetzner VPS and lets the operator monitor the V5 MIX live bot — performance, trades, per-cycle predictions/decisions, and system health — by reading the bot's `trade_journal.db` and structured logs.

**Architecture:** A new `tradingagents/monitor/` package. Pure-read layer (`db.py`, `metrics.py`, `health.py`) produces plain dicts; a FastAPI app (`app.py`) composes them into JSON endpoints and serves a Jinja HTML shell with four tabs. The journal SQLite file is opened read-only (`mode=ro` URI) so the UI never writes to or locks the bot's database. Runs as a persistent `systemd` service behind a TLS reverse proxy.

**Tech Stack:** Python, FastAPI, Uvicorn, Jinja2, vendored Chart.js, SQLite (read-only), pytest + Starlette `TestClient`.

**Spec:** `docs/superpowers/specs/2026-05-21-live-monitor-ui-design.md`

---

## File Structure

| File | Responsibility |
|------|----------------|
| `tradingagents/monitor/__init__.py` | Package marker |
| `tradingagents/monitor/db.py` | Read-only journal connection + one query function per data need |
| `tradingagents/monitor/metrics.py` | Derived stats: equity series, Sharpe, max drawdown, cumulative PnL |
| `tradingagents/monitor/health.py` | Parse newest `cycle_*.jsonl` into timeline + error records |
| `tradingagents/monitor/app.py` | FastAPI app factory, basic-auth dependency, HTML + JSON routes |
| `tradingagents/monitor/__main__.py` | `python -m tradingagents.monitor` uvicorn entrypoint |
| `tradingagents/monitor/templates/base.html` | Page shell: header + tab nav |
| `tradingagents/monitor/static/app.js` | Tab switching + 30 s poll loop, renders each tab from JSON |
| `tradingagents/monitor/static/app.css` | Dark theme matching the approved mockup |
| `tradingagents/monitor/static/chart.umd.min.js` | Vendored Chart.js (no CDN) |
| `deploy/systemd/ta-monitor.service` | Persistent systemd unit |
| `deploy/Caddyfile` | Reverse-proxy + automatic HTTPS config |
| `tests/monitor/conftest.py` | Fixture: temp journal DB + sample structured log |
| `tests/monitor/test_db.py` | Tests for `db.py` |
| `tests/monitor/test_metrics.py` | Tests for `metrics.py` |
| `tests/monitor/test_health.py` | Tests for `health.py` |
| `tests/monitor/test_app.py` | Tests for routes + auth |

The frontend renders entirely from JSON in `app.js`; `base.html` is the only template, so no per-tab partial files are needed (simpler than the spec's sketch — same result).

---

## Task 1: Dependencies and package skeleton

**Files:**
- Modify: `pyproject.toml`
- Create: `tradingagents/monitor/__init__.py`
- Create: `tests/monitor/__init__.py`

- [ ] **Step 1: Add web dependencies to `pyproject.toml`**

In the `dependencies = [` list, after the `"python-binance>=1.0.19",` line, add:

```python
    # Live monitoring UI
    "fastapi>=0.115.0",
    "uvicorn>=0.32.0",
    "jinja2>=3.1.0",
    "httpx>=0.27.0",
```

(`httpx` is needed by Starlette's `TestClient`.)

- [ ] **Step 2: Install the new dependencies**

Run: `pip install -e .`
Expected: installs fastapi, uvicorn, jinja2, httpx with no errors.

- [ ] **Step 3: Verify imports**

Run: `python -c "import fastapi, uvicorn, jinja2, httpx; print('ok')"`
Expected: prints `ok`

- [ ] **Step 4: Create package markers**

Create `tradingagents/monitor/__init__.py` with content:

```python
"""Read-only web UI for monitoring the live trading bot."""
```

Create `tests/monitor/__init__.py` as an empty file.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml tradingagents/monitor/__init__.py tests/monitor/__init__.py
git commit -m "chore: add monitor UI dependencies and package skeleton"
```

---

## Task 2: Test fixtures — temp journal DB + sample log

**Files:**
- Create: `tests/monitor/conftest.py`

- [ ] **Step 1: Write the fixture file**

Create `tests/monitor/conftest.py`:

```python
"""Shared fixtures for monitor UI tests.

Builds a temporary SQLite journal from the live schema and inserts
representative rows, plus a sample structured-log file.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

_SCHEMA = Path(__file__).resolve().parents[2] / "tradingagents/execution/live/schema.sql"


@pytest.fixture
def journal_path(tmp_path) -> str:
    """A populated journal DB. Returns the file path as a string."""
    db = tmp_path / "trade_journal.db"
    conn = sqlite3.connect(str(db))
    with open(_SCHEMA) as f:
        conn.executescript(f.read())

    conn.executemany(
        "INSERT INTO cycles (cycle_id, start_ts, end_ts, status, n_trades, "
        "critical_data_fail_sources, supplementary_stale_sources) VALUES (?,?,?,?,?,?,?)",
        [
            ("c1", "2026-05-19T07:00:00+00:00", "2026-05-19T07:05:00+00:00", "ok", 2, "", ""),
            ("c2", "2026-05-20T07:00:00+00:00", "2026-05-20T07:05:00+00:00", "ok", 1, "", "gdelt"),
        ],
    )
    conn.executemany(
        "INSERT INTO predictions (cycle_id, coin, horizon, pred_value, "
        "pred_quantile_low, pred_quantile_high, ref_price, signal_h7, signal_h14, "
        "consensus_signal, bundle_route) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        [
            ("c2", "bitcoin", 7, 0.021, 0.005, 0.040, 68000.0, 1, 1, 1, "78f"),
            ("c2", "ethereum", 7, -0.010, -0.030, 0.008, 3800.0, -1, 0, 0, "193f"),
        ],
    )
    conn.executemany(
        "INSERT INTO sizing (cycle_id, coin, realized_vol, target_vol, kelly, "
        "confidence, base_size, leverage, sma30_multiplier, final_size_notional) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)",
        [
            ("c2", "bitcoin", 0.45, 0.30, 0.25, 0.62, 1000.0, 1.5, 1.0, 1500.0),
            ("c2", "ethereum", 0.55, 0.30, 0.25, 0.40, 0.0, 0.0, 1.0, 0.0),
        ],
    )
    conn.executemany(
        "INSERT INTO risk_checks (cycle_id, coin, check_name, passed, value, "
        "threshold, reason) VALUES (?,?,?,?,?,?,?)",
        [
            ("c2", "bitcoin", "max_leverage", 1, 1.5, 3.0, "ok"),
            ("c2", "ethereum", "min_confidence", 0, 0.40, 0.50, "below threshold"),
        ],
    )
    conn.executemany(
        "INSERT INTO trades (cycle_id, coin, side, qty, entry_price, exit_price, "
        "pnl, fees, slippage, order_id, status) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        [
            ("c1", "bitcoin", "BUY", 0.05, 65000.0, 67000.0, 100.0, 3.2, 1.1, "o1", "closed"),
            ("c1", "ethereum", "BUY", 1.0, 3600.0, 3650.0, 50.0, 1.8, 0.6, "o2", "closed"),
            ("c2", "bitcoin", "BUY", 0.06, 68000.0, None, 0.0, 4.0, 1.4, "o3", "open"),
        ],
    )
    conn.executemany(
        "INSERT INTO portfolio_snapshots (cycle_id, ts, total_value, usdt_balance, "
        "position_qty_per_coin, unrealized_pnl) VALUES (?,?,?,?,?,?)",
        [
            ("c1", "2026-05-19T07:05:00+00:00", 10150.0, 6000.0, '{"bitcoin": 0.05}', 0.0),
            ("c2", "2026-05-20T07:05:00+00:00", 10280.0, 4000.0, '{"bitcoin": 0.06}', 80.0),
        ],
    )
    conn.executemany(
        "INSERT INTO retrains (retrain_id, cycle_id, n_train_rows, "
        "train_window_start, train_dir_acc, status, routes) VALUES (?,?,?,?,?,?,?)",
        [
            ("r1", "c2", 2500, "2019-05-01", 0.58, "ok", "78f,193f"),
        ],
    )
    conn.executemany(
        "INSERT INTO shadow_decisions (cycle_id, coin, live_signal, "
        "backtest_signal, agree, live_size, backtest_size, size_delta_pct) "
        "VALUES (?,?,?,?,?,?,?,?)",
        [
            ("c2", "bitcoin", 1, 1, 1, 1500.0, 1520.0, -1.3),
            ("c2", "ethereum", 0, -1, 0, 0.0, 200.0, -100.0),
        ],
    )
    conn.commit()
    conn.close()
    return str(db)


@pytest.fixture
def empty_journal_path(tmp_path) -> str:
    """An empty but schema-valid journal DB."""
    db = tmp_path / "empty_journal.db"
    conn = sqlite3.connect(str(db))
    with open(_SCHEMA) as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    return str(db)


@pytest.fixture
def log_dir(tmp_path) -> str:
    """A log directory with one sample cycle structured-log file."""
    d = tmp_path / "logs"
    d.mkdir()
    records = [
        {"ts": "2026-05-20T07:00:00+00:00", "cycle_id": "c2", "step": "data_refresh",
         "status": "ok", "duration_ms": 120, "payload": {}},
        {"ts": "2026-05-20T07:01:00+00:00", "cycle_id": "c2", "step": "predict",
         "status": "ok", "duration_ms": 30, "payload": {}},
        {"ts": "2026-05-20T07:02:00+00:00", "cycle_id": "c2", "step": "execute",
         "status": "error", "duration_ms": 90, "payload": {"error": "binance timeout"}},
    ]
    with open(d / "cycle_c2.jsonl", "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    return str(d)
```

- [ ] **Step 2: Verify the fixture file collects**

Run: `pytest tests/monitor/conftest.py --collect-only -q`
Expected: no collection errors (fixtures are not tests, so `no tests ran` is fine).

- [ ] **Step 3: Commit**

```bash
git add tests/monitor/conftest.py
git commit -m "test: add monitor UI test fixtures"
```

---

## Task 3: `db.py` — read-only journal queries

**Files:**
- Create: `tradingagents/monitor/db.py`
- Test: `tests/monitor/test_db.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/monitor/test_db.py`:

```python
import sqlite3

import pytest

from tradingagents.monitor import db


def test_open_journal_is_read_only(journal_path):
    conn = db.open_journal(journal_path)
    with pytest.raises(sqlite3.OperationalError):
        conn.execute("INSERT INTO cycles (cycle_id, start_ts) VALUES ('x', 'y')")
    conn.close()


def test_open_journal_missing_file_raises():
    with pytest.raises(sqlite3.OperationalError):
        db.open_journal("/nonexistent/path/trade_journal.db")


def test_list_cycles_newest_first(journal_path):
    conn = db.open_journal(journal_path)
    cycles = db.list_cycles(conn)
    assert [c["cycle_id"] for c in cycles] == ["c2", "c1"]
    assert cycles[0]["status"] == "ok"
    conn.close()


def test_latest_cycle(journal_path):
    conn = db.open_journal(journal_path)
    assert db.latest_cycle(conn)["cycle_id"] == "c2"
    conn.close()


def test_latest_cycle_empty(empty_journal_path):
    conn = db.open_journal(empty_journal_path)
    assert db.latest_cycle(conn) is None
    conn.close()


def test_cycle_detail(journal_path):
    conn = db.open_journal(journal_path)
    detail = db.cycle_detail(conn, "c2")
    assert len(detail["predictions"]) == 2
    assert len(detail["sizing"]) == 2
    assert len(detail["risk_checks"]) == 2
    assert len(detail["shadow_decisions"]) == 2
    assert detail["predictions"][0]["coin"] == "bitcoin"
    conn.close()


def test_all_trades(journal_path):
    conn = db.open_journal(journal_path)
    trades = db.all_trades(conn)
    assert len(trades) == 3
    assert trades[0]["status"] == "open"  # newest first
    conn.close()


def test_portfolio_snapshots(journal_path):
    conn = db.open_journal(journal_path)
    snaps = db.portfolio_snapshots(conn)
    assert [s["total_value"] for s in snaps] == [10150.0, 10280.0]  # oldest first
    conn.close()


def test_retrains(journal_path):
    conn = db.open_journal(journal_path)
    rows = db.retrains(conn)
    assert rows[0]["retrain_id"] == "r1"
    conn.close()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/monitor/test_db.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tradingagents.monitor.db'`

- [ ] **Step 3: Implement `db.py`**

Create `tradingagents/monitor/db.py`:

```python
"""Read-only access to the live bot's SQLite forensic journal.

Every connection is opened with the SQLite ``mode=ro`` URI so the UI can
never write to or lock the bot's database.
"""
from __future__ import annotations

import sqlite3


def open_journal(db_path: str) -> sqlite3.Connection:
    """Open the journal DB read-only. Raises sqlite3.OperationalError if the
    file is missing or unreadable."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _rows(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> list[dict]:
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def list_cycles(conn: sqlite3.Connection, limit: int = 200) -> list[dict]:
    """Cycles, newest first."""
    return _rows(
        conn,
        "SELECT cycle_id, start_ts, end_ts, status, error_msg, n_trades, "
        "critical_data_fail_sources, supplementary_stale_sources "
        "FROM cycles ORDER BY start_ts DESC LIMIT ?",
        (limit,),
    )


def latest_cycle(conn: sqlite3.Connection) -> dict | None:
    rows = list_cycles(conn, limit=1)
    return rows[0] if rows else None


def cycle_detail(conn: sqlite3.Connection, cycle_id: str) -> dict:
    """Predictions, sizing, risk checks and shadow decisions for one cycle."""
    return {
        "predictions": _rows(
            conn, "SELECT * FROM predictions WHERE cycle_id = ? ORDER BY coin",
            (cycle_id,)),
        "sizing": _rows(
            conn, "SELECT * FROM sizing WHERE cycle_id = ? ORDER BY coin",
            (cycle_id,)),
        "risk_checks": _rows(
            conn, "SELECT * FROM risk_checks WHERE cycle_id = ? ORDER BY coin",
            (cycle_id,)),
        "shadow_decisions": _rows(
            conn, "SELECT * FROM shadow_decisions WHERE cycle_id = ? ORDER BY coin",
            (cycle_id,)),
    }


def all_trades(conn: sqlite3.Connection) -> list[dict]:
    """All trades, newest first (by row id)."""
    return _rows(conn, "SELECT * FROM trades ORDER BY id DESC")


def portfolio_snapshots(conn: sqlite3.Connection) -> list[dict]:
    """Portfolio snapshots, oldest first (chronological for charting)."""
    return _rows(conn, "SELECT * FROM portfolio_snapshots ORDER BY ts ASC")


def retrains(conn: sqlite3.Connection) -> list[dict]:
    """Retrain history, newest first."""
    return _rows(conn, "SELECT * FROM retrains ORDER BY rowid DESC")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/monitor/test_db.py -v`
Expected: PASS — all 9 tests.

- [ ] **Step 5: Commit**

```bash
git add tradingagents/monitor/db.py tests/monitor/test_db.py
git commit -m "feat: read-only journal query layer for monitor UI"
```

---

## Task 4: `metrics.py` — derived performance stats

**Files:**
- Create: `tradingagents/monitor/metrics.py`
- Test: `tests/monitor/test_metrics.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/monitor/test_metrics.py`:

```python
import math

from tradingagents.monitor import metrics


def test_max_drawdown():
    # peak 120, trough 90 -> (90-120)/120 = -0.25
    series = [100.0, 120.0, 110.0, 90.0, 130.0]
    assert math.isclose(metrics.max_drawdown(series), -0.25)


def test_max_drawdown_monotonic_increasing():
    assert metrics.max_drawdown([100.0, 110.0, 120.0]) == 0.0


def test_max_drawdown_too_short():
    assert metrics.max_drawdown([100.0]) == 0.0


def test_sharpe_zero_variance():
    # constant equity -> no returns variance -> Sharpe 0.0
    assert metrics.sharpe([100.0, 100.0, 100.0]) == 0.0


def test_sharpe_positive_trend():
    series = [100.0, 101.0, 102.0, 103.5, 104.0, 106.0]
    assert metrics.sharpe(series) > 0.0


def test_sharpe_too_short():
    assert metrics.sharpe([100.0]) == 0.0


def test_cumulative_pnl():
    trades = [{"pnl": 100.0}, {"pnl": -30.0}, {"pnl": None}, {"pnl": 50.0}]
    assert metrics.cumulative_pnl(trades) == 120.0


def test_equity_series_from_snapshots():
    snaps = [
        {"ts": "2026-05-19T07:05:00+00:00", "total_value": 10150.0},
        {"ts": "2026-05-20T07:05:00+00:00", "total_value": 10280.0},
    ]
    series = metrics.equity_series(snaps, trades=[], start_capital=10000.0)
    assert series == [
        {"ts": "2026-05-19T07:05:00+00:00", "value": 10150.0},
        {"ts": "2026-05-20T07:05:00+00:00", "value": 10280.0},
    ]


def test_equity_series_fallback_to_trades():
    # no snapshots -> reconstruct from cumulative realized PnL
    trades = [
        {"cycle_id": "c1", "pnl": 100.0},
        {"cycle_id": "c1", "pnl": 50.0},
        {"cycle_id": "c2", "pnl": -30.0},
    ]
    series = metrics.equity_series([], trades=trades, start_capital=10000.0)
    assert series[-1]["value"] == 10120.0
    assert series[0]["value"] == 10000.0  # start point prepended


def test_equity_series_empty():
    assert metrics.equity_series([], trades=[], start_capital=10000.0) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/monitor/test_metrics.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tradingagents.monitor.metrics'`

- [ ] **Step 3: Implement `metrics.py`**

Create `tradingagents/monitor/metrics.py`:

```python
"""Derived performance statistics for the monitor UI.

All functions are pure: they take plain rows (dicts/floats) and return
numbers or plain lists. No DB access here.
"""
from __future__ import annotations

import math

# Crypto trades every day -> annualize daily returns with sqrt(365).
_ANNUALIZATION = math.sqrt(365.0)


def max_drawdown(values: list[float]) -> float:
    """Largest peak-to-trough decline as a negative fraction (e.g. -0.25).
    Returns 0.0 for a series that never declines or is too short."""
    if len(values) < 2:
        return 0.0
    peak = values[0]
    worst = 0.0
    for v in values:
        peak = max(peak, v)
        if peak > 0:
            worst = min(worst, (v - peak) / peak)
    return worst


def sharpe(values: list[float]) -> float:
    """Annualized Sharpe ratio of an equity series (risk-free rate 0).
    Returns 0.0 if the series is too short or has zero variance."""
    if len(values) < 2:
        return 0.0
    returns = [
        (values[i] - values[i - 1]) / values[i - 1]
        for i in range(1, len(values))
        if values[i - 1] != 0
    ]
    if len(returns) < 2:
        return 0.0
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    std = math.sqrt(var)
    if std == 0:
        return 0.0
    return (mean / std) * _ANNUALIZATION


def cumulative_pnl(trades: list[dict]) -> float:
    """Sum of realized trade PnL, ignoring None values."""
    return sum(t["pnl"] for t in trades if t.get("pnl") is not None)


def equity_series(
    snapshots: list[dict], trades: list[dict], start_capital: float
) -> list[dict]:
    """Equity curve as a list of {ts, value} dicts, chronological.

    Primary source is ``portfolio_snapshots.total_value``. When no snapshots
    exist, the curve is reconstructed from cumulative realized trade PnL,
    prepended with the starting-capital point.
    """
    if snapshots:
        return [
            {"ts": s["ts"], "value": s["total_value"]}
            for s in snapshots
            if s.get("total_value") is not None
        ]
    if not trades:
        return []
    # Trades arrive newest-first from db.all_trades; reverse to chronological.
    chrono = list(reversed(trades))
    series = [{"ts": "start", "value": start_capital}]
    running = start_capital
    for t in chrono:
        running += t["pnl"] if t.get("pnl") is not None else 0.0
        series.append({"ts": t.get("cycle_id", ""), "value": running})
    return series
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/monitor/test_metrics.py -v`
Expected: PASS — all 10 tests.

- [ ] **Step 5: Commit**

```bash
git add tradingagents/monitor/metrics.py tests/monitor/test_metrics.py
git commit -m "feat: performance metrics for monitor UI"
```

---

## Task 5: `health.py` — structured log parsing

**Files:**
- Create: `tradingagents/monitor/health.py`
- Test: `tests/monitor/test_health.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/monitor/test_health.py`:

```python
from tradingagents.monitor import health


def test_read_structured_log(log_dir):
    records = health.read_structured_log(log_dir)
    assert len(records) == 3
    assert records[0]["step"] == "data_refresh"
    assert records[-1]["status"] == "error"


def test_read_structured_log_missing_dir():
    assert health.read_structured_log("/nonexistent/logs") == []


def test_read_structured_log_empty_dir(tmp_path):
    assert health.read_structured_log(str(tmp_path)) == []


def test_recent_errors(log_dir):
    records = health.read_structured_log(log_dir)
    errors = health.recent_errors(records)
    assert len(errors) == 1
    assert errors[0]["step"] == "execute"
    assert errors[0]["payload"]["error"] == "binance timeout"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/monitor/test_health.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tradingagents.monitor.health'`

- [ ] **Step 3: Implement `health.py`**

Create `tradingagents/monitor/health.py`:

```python
"""Parse the live bot's structured JSONL logs for the System Health view.

The journal stores *what* happened (trades, sizing); these per-cycle JSONL
files capture *when* and *how long* each pipeline step ran.
"""
from __future__ import annotations

import json
from pathlib import Path


def read_structured_log(log_dir: str) -> list[dict]:
    """Parse the newest ``cycle_*.jsonl`` file in ``log_dir``.

    Returns one dict per step record, in file order. Returns an empty list
    if the directory or any matching file is missing. Malformed lines are
    skipped rather than raising.
    """
    d = Path(log_dir)
    if not d.is_dir():
        return []
    files = sorted(d.glob("cycle_*.jsonl"), key=lambda p: p.stat().st_mtime)
    if not files:
        return []
    records: list[dict] = []
    with open(files[-1]) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def recent_errors(records: list[dict]) -> list[dict]:
    """Step records whose status is not ``ok``."""
    return [r for r in records if r.get("status") != "ok"]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/monitor/test_health.py -v`
Expected: PASS — all 4 tests.

- [ ] **Step 5: Commit**

```bash
git add tradingagents/monitor/health.py tests/monitor/test_health.py
git commit -m "feat: structured-log parsing for monitor UI health view"
```

---

## Task 6: FastAPI app — auth + JSON endpoints

**Files:**
- Create: `tradingagents/monitor/app.py`
- Test: `tests/monitor/test_app.py`

This task builds the whole API in one app factory. The factory takes explicit
`journal_path` and `log_dir` so tests can point it at fixtures.

- [ ] **Step 1: Write the failing tests**

Create `tests/monitor/test_app.py`:

```python
import base64

import pytest
from starlette.testclient import TestClient

from tradingagents.monitor.app import create_app

_PW = "testpw"


def _auth_header(user="admin", pw=_PW):
    raw = f"{user}:{pw}".encode()
    return {"Authorization": "Basic " + base64.b64encode(raw).decode()}


@pytest.fixture
def client(journal_path, log_dir, monkeypatch):
    monkeypatch.setenv("TA_MONITOR_PASSWORD", _PW)
    app = create_app(journal_path=journal_path, log_dir=log_dir,
                      start_capital=10000.0)
    return TestClient(app)


@pytest.fixture
def empty_client(empty_journal_path, tmp_path, monkeypatch):
    monkeypatch.setenv("TA_MONITOR_PASSWORD", _PW)
    app = create_app(journal_path=empty_journal_path, log_dir=str(tmp_path),
                      start_capital=10000.0)
    return TestClient(app)


def test_create_app_requires_password(journal_path, log_dir, monkeypatch):
    monkeypatch.delenv("TA_MONITOR_PASSWORD", raising=False)
    with pytest.raises(RuntimeError):
        create_app(journal_path=journal_path, log_dir=log_dir)


def test_root_requires_auth(client):
    assert client.get("/").status_code == 401


def test_root_rejects_bad_password(client):
    r = client.get("/", headers=_auth_header(pw="wrong"))
    assert r.status_code == 401


def test_root_ok_with_auth(client):
    r = client.get("/", headers=_auth_header())
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_api_performance(client):
    r = client.get("/api/performance", headers=_auth_header())
    assert r.status_code == 200
    body = r.json()
    assert body["cards"]["open_positions"] == 1
    assert len(body["equity"]) == 2
    assert len(body["per_coin"]) >= 1


def test_api_trades(client):
    r = client.get("/api/trades", headers=_auth_header())
    assert r.status_code == 200
    body = r.json()
    assert len(body["trades"]) == 3
    assert len(body["open_positions"]) == 1


def test_api_cycles(client):
    r = client.get("/api/cycles", headers=_auth_header())
    assert r.status_code == 200
    assert [c["cycle_id"] for c in r.json()["cycles"]] == ["c2", "c1"]


def test_api_cycle_detail(client):
    r = client.get("/api/cycle/c2", headers=_auth_header())
    assert r.status_code == 200
    body = r.json()
    assert len(body["predictions"]) == 2
    assert len(body["risk_checks"]) == 2


def test_api_health(client):
    r = client.get("/api/health", headers=_auth_header())
    assert r.status_code == 200
    body = r.json()
    assert len(body["timeline"]) == 2
    assert len(body["steps"]) == 3
    assert len(body["errors"]) == 1
    assert len(body["retrains"]) == 1


def test_api_empty_db_returns_empty_states(empty_client):
    r = empty_client.get("/api/performance", headers=_auth_header())
    assert r.status_code == 200
    body = r.json()
    assert body["equity"] == []
    assert body["cards"]["open_positions"] == 0

    r = empty_client.get("/api/trades", headers=_auth_header())
    assert r.json()["trades"] == []


def test_api_missing_db_returns_503(log_dir, monkeypatch):
    monkeypatch.setenv("TA_MONITOR_PASSWORD", _PW)
    app = create_app(journal_path="/nonexistent/trade_journal.db",
                      log_dir=log_dir, start_capital=10000.0)
    client = TestClient(app)
    r = client.get("/api/performance", headers=_auth_header())
    assert r.status_code == 503
    assert "error" in r.json()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/monitor/test_app.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tradingagents.monitor.app'`

- [ ] **Step 3: Implement `app.py`**

Create `tradingagents/monitor/app.py`:

```python
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
        """Open the journal read-only, or raise HTTP 503."""
        try:
            return db.open_journal(journal_path)
        except sqlite3.OperationalError as exc:
            raise HTTPException(status_code=503, detail=f"journal unavailable: {exc}")

    @app.get("/")
    def index(request: Request, _: str = Depends(require_auth)):
        return templates.TemplateResponse("base.html", {"request": request})

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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/monitor/test_app.py -v`
Expected: FAIL on `test_root_ok_with_auth` only — `templates/base.html` does not exist yet. All API and auth tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tradingagents/monitor/app.py tests/monitor/test_app.py
git commit -m "feat: monitor UI FastAPI app with auth and JSON endpoints"
```

---

## Task 7: HTML shell + static assets

**Files:**
- Create: `tradingagents/monitor/templates/base.html`
- Create: `tradingagents/monitor/static/app.css`
- Create: `tradingagents/monitor/static/app.js`
- Create: `tradingagents/monitor/static/chart.umd.min.js`

- [ ] **Step 1: Vendor Chart.js**

Run:
```bash
curl -fsSL https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js \
  -o tradingagents/monitor/static/chart.umd.min.js
```
Expected: file ~200 KB. Verify: `head -c 40 tradingagents/monitor/static/chart.umd.min.js` shows a JS license/banner comment.

- [ ] **Step 2: Create `templates/base.html`**

Create `tradingagents/monitor/templates/base.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>V5 MIX Live Monitor</title>
  <link rel="stylesheet" href="/static/app.css">
  <script src="/static/chart.umd.min.js"></script>
</head>
<body>
  <header id="topbar">
    <strong>V5 MIX Live</strong>
    <span id="status-dot" class="dot">&#9679;</span>
    <span id="status-text">loading…</span>
    <span id="equity-summary"></span>
  </header>
  <nav id="tabs">
    <button class="tab active" data-tab="performance">Performance</button>
    <button class="tab" data-tab="trades">Trades</button>
    <button class="tab" data-tab="decisions">Predictions &amp; decisions</button>
    <button class="tab" data-tab="health">System health</button>
  </nav>
  <main id="content"><p class="muted">Loading…</p></main>
  <div id="banner" class="banner hidden"></div>
  <script src="/static/app.js"></script>
</body>
</html>
```

- [ ] **Step 3: Create `static/app.css`**

Create `tradingagents/monitor/static/app.css`:

```css
:root { --bg:#0e1117; --panel:#161b22; --border:#2a2f3a; --fg:#d6dae0;
        --muted:#8b949e; --green:#3fb950; --red:#f85149; --blue:#58a6ff;
        --amber:#d29922; }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--fg);
       font:13px/1.5 -apple-system,Segoe UI,Roboto,sans-serif; }
#topbar { display:flex; align-items:center; gap:14px; padding:12px 16px;
          background:var(--panel); border-bottom:1px solid var(--border); }
#topbar strong { font-size:15px; }
#equity-summary { margin-left:auto; text-align:right; }
.dot { font-size:11px; }
.dot.ok { color:var(--green); } .dot.stale { color:var(--amber); }
.dot.fail { color:var(--red); }
#tabs { display:flex; gap:4px; padding:8px 16px 0; background:var(--panel);
        border-bottom:1px solid var(--border); }
.tab { padding:6px 14px; background:none; border:1px solid transparent;
       color:var(--muted); cursor:pointer; border-radius:6px 6px 0 0;
       font-size:13px; }
.tab.active { background:var(--bg); border-color:var(--border);
              border-bottom-color:var(--bg); color:var(--fg); }
main { padding:16px; }
.cards { display:flex; gap:10px; margin-bottom:14px; flex-wrap:wrap; }
.card { flex:1; min-width:140px; background:var(--panel);
        border:1px solid var(--border); border-radius:8px; padding:10px; }
.card .label { color:var(--muted); font-size:11px; text-transform:uppercase; }
.card .value { font-size:17px; font-weight:700; }
.panel { background:var(--panel); border:1px solid var(--border);
         border-radius:8px; padding:12px; margin-bottom:14px; }
.panel h3 { margin:0 0 8px; font-size:11px; text-transform:uppercase;
            color:var(--muted); font-weight:600; }
table { width:100%; border-collapse:collapse; font-size:12px; }
th { text-align:left; color:var(--muted); padding:4px 6px; }
td { padding:5px 6px; border-top:1px solid var(--border); }
.pos { color:var(--green); } .neg { color:var(--red); }
.muted { color:var(--muted); }
.pass { color:var(--green); } .failv { color:var(--red); }
select { background:var(--panel); color:var(--fg);
         border:1px solid var(--border); border-radius:6px; padding:4px 8px; }
.banner { position:fixed; bottom:0; left:0; right:0; padding:8px 16px;
          background:var(--red); color:#fff; text-align:center; }
.hidden { display:none; }
</style>
```

Note: remove the stray trailing `</style>` — CSS files have no tags. The
final file must end after `.hidden { display:none; }`.

- [ ] **Step 4: Create `static/app.js`**

Create `tradingagents/monitor/static/app.js`:

```javascript
"use strict";
const POLL_MS = 30000;
let activeTab = "performance";
let equityChart = null;

function fmtMoney(v) {
  if (v === null || v === undefined) return "—";
  return "$" + Number(v).toLocaleString(undefined, {minimumFractionDigits: 2,
    maximumFractionDigits: 2});
}
function pnlClass(v) { return Number(v) >= 0 ? "pos" : "neg"; }

async function getJSON(path) {
  const r = await fetch(path);
  if (!r.ok) throw new Error("HTTP " + r.status);
  return r.json();
}

function showBanner(msg) {
  const b = document.getElementById("banner");
  b.textContent = msg; b.classList.remove("hidden");
}
function hideBanner() { document.getElementById("banner").classList.add("hidden"); }

function renderTopbar(perf, health) {
  document.getElementById("equity-summary").innerHTML =
    "<div style='font-size:18px;font-weight:700'>" +
    fmtMoney(perf.cards.equity) + "</div>";
  const dot = document.getElementById("status-dot");
  const txt = document.getElementById("status-text");
  const latest = health.timeline[0];
  if (!latest) { dot.className = "dot stale"; txt.textContent = "no cycles yet"; return; }
  const ageH = (Date.now() - Date.parse(latest.start_ts)) / 3.6e6;
  if (latest.status && latest.status !== "ok") {
    dot.className = "dot fail"; txt.textContent = "last cycle FAILED";
  } else if (ageH > 2) {
    dot.className = "dot stale";
    txt.textContent = "stale — last cycle " + ageH.toFixed(1) + "h ago";
  } else {
    dot.className = "dot ok"; txt.textContent = "running";
  }
}

function renderPerformance(d) {
  const c = d.cards;
  let html = "<div class='cards'>" +
    card("Equity", fmtMoney(c.equity)) +
    card("Live Sharpe (ann.)", c.sharpe) +
    card("Max drawdown", (c.max_drawdown * 100).toFixed(1) + "%") +
    card("Open positions", c.open_positions) + "</div>";
  html += "<div class='panel'><h3>Equity curve · backtest anchor SR " +
    d.backtest_anchor_sharpe + "</h3>";
  html += d.equity.length
    ? "<canvas id='equity-canvas' height='90'></canvas>"
    : "<p class='muted'>No equity data yet.</p>";
  html += "</div>";
  html += "<div class='panel'><h3>Per-coin PnL</h3>";
  if (d.per_coin.length) {
    html += "<table><tr><th>Coin</th><th>Position</th><th>Realized PnL</th></tr>";
    for (const p of d.per_coin) {
      html += "<tr><td>" + p.coin + "</td><td>" +
        (p.open ? "open" : "flat") + "</td><td class='" +
        pnlClass(p.realized_pnl) + "'>" + fmtMoney(p.realized_pnl) +
        "</td></tr>";
    }
    html += "</table>";
  } else { html += "<p class='muted'>No trades yet.</p>"; }
  html += "</div>";
  document.getElementById("content").innerHTML = html;
  if (d.equity.length) drawEquity(d.equity);
}

function drawEquity(equity) {
  const ctx = document.getElementById("equity-canvas").getContext("2d");
  if (equityChart) equityChart.destroy();
  equityChart = new Chart(ctx, {
    type: "line",
    data: { labels: equity.map(p => p.ts),
            datasets: [{ label: "Live equity", data: equity.map(p => p.value),
              borderColor: "#3fb950", tension: 0.2, pointRadius: 0 }] },
    options: { plugins: { legend: { display: false } },
      scales: { x: { ticks: { color: "#8b949e" } },
                y: { ticks: { color: "#8b949e" } } } }
  });
}

function renderTrades(d) {
  let html = "<div class='panel'><h3>Open positions</h3>";
  html += d.open_positions.length ? tradeTable(d.open_positions)
    : "<p class='muted'>No open positions.</p>";
  html += "</div><div class='panel'><h3>Trade log</h3>";
  html += d.trades.length ? tradeTable(d.trades)
    : "<p class='muted'>No trades yet.</p>";
  html += "</div>";
  document.getElementById("content").innerHTML = html;
}

function tradeTable(rows) {
  let h = "<table><tr><th>Cycle</th><th>Coin</th><th>Side</th><th>Qty</th>" +
    "<th>Entry</th><th>Exit</th><th>PnL</th><th>Fees</th><th>Slippage</th>" +
    "<th>Status</th></tr>";
  for (const t of rows) {
    h += "<tr><td>" + t.cycle_id + "</td><td>" + t.coin + "</td><td>" +
      (t.side || "—") + "</td><td>" + (t.qty ?? "—") + "</td><td>" +
      (t.entry_price ?? "—") + "</td><td>" + (t.exit_price ?? "—") +
      "</td><td class='" + pnlClass(t.pnl ?? 0) + "'>" +
      (t.pnl == null ? "—" : fmtMoney(t.pnl)) + "</td><td>" +
      (t.fees ?? "—") + "</td><td>" + (t.slippage ?? "—") + "</td><td>" +
      (t.status || "—") + "</td></tr>";
  }
  return h + "</table>";
}

async function renderDecisions() {
  const { cycles } = await getJSON("/api/cycles");
  if (!cycles.length) {
    document.getElementById("content").innerHTML =
      "<div class='panel'><p class='muted'>No cycles logged yet.</p></div>";
    return;
  }
  let html = "<div class='panel'><h3>Cycle</h3><select id='cycle-pick'>";
  for (const c of cycles) {
    html += "<option value='" + c.cycle_id + "'>" + c.cycle_id +
      " — " + c.start_ts + "</option>";
  }
  html += "</select></div><div id='cycle-detail'></div>";
  document.getElementById("content").innerHTML = html;
  const pick = document.getElementById("cycle-pick");
  pick.addEventListener("change", () => loadCycleDetail(pick.value));
  loadCycleDetail(cycles[0].cycle_id);
}

async function loadCycleDetail(cycleId) {
  const d = await getJSON("/api/cycle/" + encodeURIComponent(cycleId));
  let html = "<div class='panel'><h3>Predictions</h3>";
  html += d.predictions.length
    ? table(d.predictions, ["coin", "horizon", "pred_value",
        "pred_quantile_low", "pred_quantile_high", "ref_price",
        "consensus_signal", "bundle_route"])
    : "<p class='muted'>No predictions.</p>";
  html += "</div><div class='panel'><h3>Sizing</h3>";
  html += d.sizing.length
    ? table(d.sizing, ["coin", "realized_vol", "target_vol", "kelly",
        "confidence", "leverage", "sma30_multiplier", "final_size_notional"])
    : "<p class='muted'>No sizing.</p>";
  html += "</div><div class='panel'><h3>Risk checks</h3>";
  if (d.risk_checks.length) {
    html += "<table><tr><th>Coin</th><th>Check</th><th>Result</th>" +
      "<th>Value</th><th>Threshold</th><th>Reason</th></tr>";
    for (const r of d.risk_checks) {
      html += "<tr><td>" + (r.coin || "—") + "</td><td>" + r.check_name +
        "</td><td class='" + (r.passed ? "pass'>PASS" : "failv'>FAIL") +
        "</td><td>" + (r.value ?? "—") + "</td><td>" +
        (r.threshold ?? "—") + "</td><td>" + (r.reason || "") +
        "</td></tr>";
    }
    html += "</table>";
  } else { html += "<p class='muted'>No risk checks.</p>"; }
  html += "</div><div class='panel'><h3>Shadow decisions</h3>";
  html += d.shadow_decisions.length
    ? table(d.shadow_decisions, ["coin", "live_signal", "backtest_signal",
        "agree", "live_size", "backtest_size", "size_delta_pct"])
    : "<p class='muted'>No shadow decisions.</p>";
  html += "</div>";
  document.getElementById("cycle-detail").innerHTML = html;
}

function renderHealth(d) {
  let html = "<div class='panel'><h3>Cycle timeline</h3>";
  if (d.timeline.length) {
    html += "<table><tr><th>Cycle</th><th>Start</th><th>End</th>" +
      "<th>Status</th><th>Trades</th><th>Stale sources</th></tr>";
    for (const c of d.timeline) {
      html += "<tr><td>" + c.cycle_id + "</td><td>" + c.start_ts +
        "</td><td>" + (c.end_ts || "—") + "</td><td class='" +
        (c.status === "ok" ? "pass'>" : "failv'>") + (c.status || "—") +
        "</td><td>" + (c.n_trades ?? "—") + "</td><td>" +
        (c.supplementary_stale_sources || "—") + "</td></tr>";
    }
    html += "</table>";
  } else { html += "<p class='muted'>No cycles logged yet.</p>"; }
  html += "</div><div class='panel'><h3>Recent errors</h3>";
  html += d.errors.length
    ? table(d.errors, ["ts", "cycle_id", "step", "status"])
    : "<p class='muted'>No errors in latest cycle log.</p>";
  html += "</div><div class='panel'><h3>Retrain history</h3>";
  html += d.retrains.length
    ? table(d.retrains, ["retrain_id", "cycle_id", "n_train_rows",
        "train_window_start", "train_dir_acc", "status", "routes"])
    : "<p class='muted'>No retrains yet.</p>";
  html += "</div>";
  document.getElementById("content").innerHTML = html;
}

function table(rows, cols) {
  let h = "<table><tr>";
  for (const c of cols) h += "<th>" + c + "</th>";
  h += "</tr>";
  for (const r of rows) {
    h += "<tr>";
    for (const c of cols) h += "<td>" + (r[c] ?? "—") + "</td>";
    h += "</tr>";
  }
  return h + "</table>";
}

function card(label, value) {
  return "<div class='card'><div class='label'>" + label +
    "</div><div class='value'>" + value + "</div></div>";
}

async function refresh() {
  try {
    const [perf, health] = await Promise.all([
      getJSON("/api/performance"), getJSON("/api/health")]);
    hideBanner();
    renderTopbar(perf, health);
    if (activeTab === "performance") renderPerformance(perf);
    else if (activeTab === "trades") renderTrades(await getJSON("/api/trades"));
    else if (activeTab === "decisions") await renderDecisions();
    else if (activeTab === "health") renderHealth(health);
  } catch (e) {
    showBanner("Data unavailable: " + e.message + " — retrying…");
  }
}

document.querySelectorAll(".tab").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    activeTab = btn.dataset.tab;
    refresh();
  });
});

refresh();
setInterval(refresh, POLL_MS);
```

- [ ] **Step 5: Run the app test to confirm the HTML route now passes**

Run: `pytest tests/monitor/test_app.py::test_root_ok_with_auth -v`
Expected: PASS

- [ ] **Step 6: Run the full monitor test suite**

Run: `pytest tests/monitor/ -v`
Expected: PASS — all tests across test_db, test_metrics, test_health, test_app.

- [ ] **Step 7: Commit**

```bash
git add tradingagents/monitor/templates tradingagents/monitor/static
git commit -m "feat: monitor UI HTML shell, styles, client rendering"
```

---

## Task 8: `__main__.py` entrypoint + manual smoke test

**Files:**
- Create: `tradingagents/monitor/__main__.py`

- [ ] **Step 1: Create `__main__.py`**

Create `tradingagents/monitor/__main__.py`:

```python
"""Entrypoint: ``python -m tradingagents.monitor``.

Reads DATA_DIR / LOG_DIR / TA_MONITOR_PASSWORD / TA_MONITOR_START_CAPITAL
from the environment (same env contract as the live runner). Binds
127.0.0.1 only — a reverse proxy terminates TLS in production.
"""
from __future__ import annotations

import os
from pathlib import Path

import uvicorn

from tradingagents.monitor.app import create_app


def main() -> None:
    data_dir = Path(os.environ.get("DATA_DIR", "data"))
    log_dir = os.environ.get("LOG_DIR", "logs")
    start_capital = float(os.environ.get("TA_MONITOR_START_CAPITAL", "10000"))
    host = os.environ.get("TA_MONITOR_HOST", "127.0.0.1")
    port = int(os.environ.get("TA_MONITOR_PORT", "8800"))

    app = create_app(
        journal_path=str(data_dir / "trade_journal.db"),
        log_dir=log_dir,
        start_capital=start_capital,
    )
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke-test against the real journal (if present) or skip**

Run:
```bash
TA_MONITOR_PASSWORD=devpw TA_MONITOR_PORT=8801 \
  timeout 4 python -m tradingagents.monitor || true
```
Expected: Uvicorn logs `Uvicorn running on http://127.0.0.1:8801` then exits at the timeout with no traceback. (A missing real journal is fine — the app starts; API calls would 503.)

- [ ] **Step 3: Verify the auth wall over HTTP**

Run (in two steps — start server, then curl):
```bash
TA_MONITOR_PASSWORD=devpw TA_MONITOR_PORT=8802 python -m tradingagents.monitor &
SRV=$!; sleep 2
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8802/
curl -s -o /dev/null -w "%{http_code}\n" -u admin:devpw http://127.0.0.1:8802/
kill $SRV
```
Expected: first curl prints `401`, second prints `200`.

- [ ] **Step 4: Commit**

```bash
git add tradingagents/monitor/__main__.py
git commit -m "feat: monitor UI uvicorn entrypoint"
```

---

## Task 9: Deployment — systemd unit + reverse proxy

**Files:**
- Create: `deploy/systemd/ta-monitor.service`
- Create: `deploy/Caddyfile`
- Modify: `deploy/deploy.sh`

- [ ] **Step 1: Create the systemd unit**

Create `deploy/systemd/ta-monitor.service`:

```ini
[Unit]
Description=TradingAgents live monitoring UI
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=tabot
WorkingDirectory=/opt/tradingagents/repo
EnvironmentFile=/opt/tradingagents/secrets/.env.trading
EnvironmentFile=/opt/tradingagents/secrets/.env.monitor
Environment=DATA_DIR=/opt/tradingagents/data
Environment=LOG_DIR=/opt/tradingagents/logs
Environment=TA_MONITOR_HOST=127.0.0.1
Environment=TA_MONITOR_PORT=8800
ExecStart=/opt/tradingagents/venv/bin/python -m tradingagents.monitor
Restart=always
RestartSec=5
Nice=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

`.env.monitor` holds `TA_MONITOR_PASSWORD=...` (and optionally
`TA_MONITOR_START_CAPITAL=...`). It is created by hand on the VPS, never
committed.

- [ ] **Step 2: Create the Caddy reverse-proxy config**

Create `deploy/Caddyfile`:

```
# TradingAgents live monitor — automatic HTTPS via Let's Encrypt.
# Replace monitor.example.com with the real VPS hostname before deploy.
monitor.example.com {
    encode gzip
    reverse_proxy 127.0.0.1:8800
}
```

- [ ] **Step 3: Add a deploy section to `deploy/deploy.sh`**

Read `deploy/deploy.sh` first. At the end of the script (after the existing
systemd handling for `ta-cycle`), append:

```bash
# --- Monitoring UI -----------------------------------------------------------
echo "==> Installing monitor UI service"
sudo cp deploy/systemd/ta-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ta-monitor.service
echo "    monitor UI running on 127.0.0.1:8800 (reverse-proxy terminates TLS)"
echo "    NOTE: create /opt/tradingagents/secrets/.env.monitor with"
echo "          TA_MONITOR_PASSWORD before first start, and install Caddy"
echo "          with deploy/Caddyfile for public HTTPS access."
```

If `deploy/deploy.sh` has a different structure (e.g. functions), place the
equivalent block alongside the existing `ta-cycle` install logic, matching
the file's style.

- [ ] **Step 4: Verify the systemd unit syntax**

Run: `systemd-analyze verify deploy/systemd/ta-monitor.service 2>&1 || true`
Expected: no `Failed` lines about syntax (a warning that the unit is not
installed in the system path is acceptable).

- [ ] **Step 5: Commit**

```bash
git add deploy/systemd/ta-monitor.service deploy/Caddyfile deploy/deploy.sh
git commit -m "feat: deploy monitor UI as systemd service behind Caddy"
```

---

## Task 10: Documentation + final verification

**Files:**
- Modify: `tradingagents/monitor/__init__.py` (expand docstring into usage notes)
- Create: `tradingagents/monitor/README.md`

- [ ] **Step 1: Write `tradingagents/monitor/README.md`**

Create `tradingagents/monitor/README.md`:

```markdown
# Live Bot Monitoring UI

Read-only FastAPI dashboard for the V5 MIX live bot. Reads the bot's
`trade_journal.db` (SQLite, `mode=ro`) and structured cycle logs. Never
writes to the bot's data.

## Run locally

```bash
TA_MONITOR_PASSWORD=somepw python -m tradingagents.monitor
# open http://127.0.0.1:8800  (user: admin)
```

## Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `TA_MONITOR_PASSWORD` | — (required) | Basic-auth password; app refuses to start if unset |
| `DATA_DIR` | `data` | Directory holding `trade_journal.db` |
| `LOG_DIR` | `logs` | Directory holding `cycle_*.jsonl` |
| `TA_MONITOR_HOST` | `127.0.0.1` | Bind host (keep loopback; proxy terminates TLS) |
| `TA_MONITOR_PORT` | `8800` | Bind port |
| `TA_MONITOR_START_CAPITAL` | `10000` | Starting capital for equity reconstruction when no snapshots exist |

## Deployment

`deploy/systemd/ta-monitor.service` runs it as a persistent service;
`deploy/Caddyfile` provides public HTTPS. See `deploy/deploy.sh`.

## Tabs

- **Performance** — equity curve vs backtest anchor (SR 3.18), Sharpe, drawdown, per-coin PnL
- **Trades** — full trade log + open positions
- **Predictions & decisions** — per-cycle LGB predictions, sizing, risk checks, shadow decisions
- **System health** — cycle timeline, recent errors, retrain history
```

- [ ] **Step 2: Run the full monitor test suite**

Run: `pytest tests/monitor/ -v`
Expected: PASS — every test.

- [ ] **Step 3: Confirm no write path to the journal**

Run: `grep -rnE "mode=rw|INSERT|UPDATE|DELETE|executescript" tradingagents/monitor/`
Expected: no matches (the UI is strictly read-only).

- [ ] **Step 4: Commit**

```bash
git add tradingagents/monitor/README.md
git commit -m "docs: monitor UI usage and deployment notes"
```

- [ ] **Step 5: Final review against the spec**

Confirm each spec section maps to delivered code: data access (Task 3),
metrics (Task 4), health (Task 5), endpoints + auth (Task 6), four views
(Task 7), entrypoint (Task 8), deploy + auth env (Task 9), docs (Task 10).

---

## Self-Review Notes

- **Spec coverage:** data sources → Task 3; stack/architecture → Tasks 1,6,7,8; endpoints → Task 6; four views → Tasks 6+7; auth/deploy → Tasks 6,9; error handling/empty states → Tasks 4,6,7 (tested in `test_app.py`); testing → every task is TDD. All covered.
- **Deviation from spec:** spec sketched per-tab Jinja partials; this plan renders tabs client-side from JSON in `app.js` with a single `base.html`. Same result, fewer files, simpler. Noted in File Structure.
- **New env var:** `TA_MONITOR_START_CAPITAL` (equity reconstruction when snapshots absent) — not in spec; documented in Task 10 README. Minor, default-safe.
- **Type consistency:** `db.py` returns `list[dict]`; `metrics.equity_series` consumes `snapshots`/`trades` dicts and emits `{ts, value}`; `app.py` consumes all of these; `app.js` reads the documented JSON keys. Consistent end to end.

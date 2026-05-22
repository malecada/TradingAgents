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
        # The live runner logs one row per executed order; exit_price/pnl/fees
        # are never back-filled (V5 is a rebalancing strategy). Real status
        # values are EXECUTED / FAILED / UNPROTECTED.
        [
            ("c1", "bitcoin", "BUY", 0.05, 65000.0, None, None, None, 1.1, "o1", "EXECUTED"),
            ("c1", "ethereum", "SELL", 1.0, 3600.0, None, None, None, 0.6, "o2", "EXECUTED"),
            ("c2", "bitcoin", "BUY", 0.06, 68000.0, None, None, None, 1.4, "o3", "FAILED"),
        ],
    )
    conn.executemany(
        "INSERT INTO portfolio_snapshots (cycle_id, ts, total_value, usdt_balance, "
        "position_qty_per_coin, unrealized_pnl) VALUES (?,?,?,?,?,?)",
        [
            ("c1", "2026-05-19T07:05:00+00:00", 10150.0, 6000.0, '{"bitcoin": 0.05}', 0.0),
            ("c2", "2026-05-20T07:05:00+00:00", 10280.0, 4000.0, '{"bitcoin": 0.06, "ethereum": 1.4}', 80.0),
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

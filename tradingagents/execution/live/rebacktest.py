"""Weekly re-backtest: re-run V2 from live_start through prior day, diff to live."""
from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


def compute_live_metrics(live_start_date, live_end_date) -> dict:
    """Compute Sharpe / Return / MaxDD / win-rate from `portfolio_snapshots`.

    Reads `$DATA_DIR/trade_journal.db` (default ``data/``) and computes
    metrics over the inclusive date range [live_start_date, live_end_date].
    Returns NaN/zero defaults if the DB is missing or has fewer than two
    snapshots in the window — callers must tolerate that.
    """
    import sqlite3
    import numpy as np

    db = Path(os.environ.get("DATA_DIR", "data")) / "trade_journal.db"
    if not db.exists():
        return {
            "sharpe": float("nan"),
            "return_pct": 0.0,
            "max_dd": 0.0,
            "n_trades": 0,
            "win_rate": 0.0,
        }
    conn = sqlite3.connect(db)
    rows = conn.execute(
        "SELECT ts, total_value FROM portfolio_snapshots "
        "WHERE date(ts) >= ? AND date(ts) <= ? ORDER BY ts",
        (live_start_date, live_end_date),
    ).fetchall()
    conn.close()
    if len(rows) < 2:
        return {
            "sharpe": float("nan"),
            "return_pct": 0.0,
            "max_dd": 0.0,
            "n_trades": len(rows),
            "win_rate": 0.0,
        }
    values = np.array([r[1] for r in rows], dtype=float)
    rets = np.diff(values) / values[:-1]
    if len(rets) > 1 and np.std(rets, ddof=1) > 0:
        sharpe = float(np.mean(rets) / np.std(rets, ddof=1) * np.sqrt(252))
    else:
        sharpe = 0.0
    cum = np.cumprod(1 + rets)
    peak = np.maximum.accumulate(cum)
    dd = float(np.max((peak - cum) / peak)) if len(cum) else 0.0
    return {
        "sharpe": sharpe,
        "return_pct": float((values[-1] - values[0]) / values[0]),
        "max_dd": dd,
        "n_trades": len(rows),
        "win_rate": float(np.mean(rets > 0)) if len(rets) else 0.0,
    }


def compute_backtest_metrics(start_date, end_date) -> dict:
    """Re-run `scripts/baseline_strategy_v2.py` and parse its stdout.

    The strategy script prints a per-coin table plus an Equal-Weight
    Portfolio summary. We parse the portfolio summary for sharpe / return /
    max_dd, and aggregate per-coin lines for n_trades / win_rate. Output
    format is fixed by `scripts/baseline_strategy_v2.py`; if that changes,
    the regex parsing below must change with it.

    Args:
        start_date / end_date: Currently unused — `baseline_strategy_v2`
            runs over the full prediction CSV range. Kept in the signature
            for forward-compat with a date-bounded runner.
    """
    del start_date, end_date  # baseline_strategy_v2 spans full pred dir

    out_dir = Path(tempfile.mkdtemp())
    pred_dir = os.environ.get("BACKTEST_PRED_DIR", "data/multi_3coins_bnb")
    # sys.executable, not bare "python" — under systemd the service user has no
    # venv on PATH, so "python" raises FileNotFoundError.
    cmd = [
        sys.executable, "scripts/baseline_strategy_v2.py",
        "--pred-dir", pred_dir,
        "--symmetric",
        "--output-plot", str(out_dir / "equity.png"),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    text = result.stdout

    # Equal-Weight Portfolio block (preferred). Falls back to NaN if missing.
    sharpe_m = re.search(r"Sharpe\s*:\s*([+-]?[0-9.]+)", text)
    ret_m = re.search(r"Return\s*:\s*([+-]?[0-9.]+)%", text)
    dd_m = re.search(r"Max DD\s*:\s*([+-]?[0-9.]+)%", text)

    sharpe = float(sharpe_m.group(1)) if sharpe_m else float("nan")
    return_pct = float(ret_m.group(1)) / 100 if ret_m else float("nan")
    max_dd = float(dd_m.group(1)) / 100 if dd_m else float("nan")

    # Per-coin rows like:
    #   bitcoin        +111.65%    +68.53%     2.16   12.06%    53.1%       61    +124.39%
    coin_row_re = re.compile(
        r"^\s+(\S+)\s+([+-][\d.]+)%\s+([+-][\d.]+)%\s+([+-]?[\d.]+)\s+"
        r"([\d.]+)%\s+([\d.]+)%\s+(\d+)\s+([+-][\d.]+)%\s*$",
        re.MULTILINE,
    )
    rows = coin_row_re.findall(text)
    if rows:
        # Aggregate trade count + size-weighted (equal here) win rate across coins.
        n_trades = sum(int(r[6]) for r in rows)
        win_rates = [float(r[5]) for r in rows]
        win_rate = sum(win_rates) / (len(win_rates) * 100.0)
    else:
        n_trades = 0
        win_rate = 0.0

    return {
        "sharpe": sharpe,
        "return_pct": return_pct,
        "max_dd": max_dd,
        "n_trades": n_trades,
        "win_rate": win_rate,
    }


def classify_verdict(delta: dict) -> str:
    sharpe_delta = delta.get("sharpe", 0)
    if abs(sharpe_delta) <= 0.3:
        return "CONVERGING"
    if abs(sharpe_delta) > 1.0:
        return "BROKEN"
    return "DIVERGING"


def run_weekly_report(*, week_end, live_start_date, live_end_date, output_dir: Path) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    live = compute_live_metrics(live_start_date, live_end_date)
    bt = compute_backtest_metrics(live_start_date, live_end_date)
    delta = {k: live[k] - bt[k] for k in live if k in bt}
    report = {
        "week_end": week_end,
        "live_start_date": live_start_date,
        "live_end_date": live_end_date,
        "live": live,
        "backtest": bt,
        "delta": delta,
        "verdict": classify_verdict(delta),
    }
    out_path = output_dir / f"rebacktest_{week_end}.json"
    out_path.write_text(json.dumps(report, indent=2))
    return out_path

"""Weekly V5 drift check — live journal metrics + parity refetch-and-replay.

`compute_live_metrics` summarises the live `portfolio_snapshots` table.
`run_weekly_parity` shells `scripts/parity_refetch_and_replay.py`, which
refetches every data source fresh into a sandbox, replays V5 MIX over the
live cycle window, and diffs against the live journal — the V5-correct
successor to the retired V1 `baseline_strategy_v2` re-backtest.
"""
from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# repo root: tradingagents/execution/live/rebacktest.py → parents[3]
_REPO_ROOT = Path(__file__).resolve().parents[3]


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


def run_weekly_parity(*, week_end, live_start_date, live_end_date,
                       output_dir, journal_db=None, sandbox=None,
                       kelly: float = 0.25, lookback_days: int = 1500) -> Path:
    """Run the V5 parity refetch-and-replay check and capture its verdict.

    Shells `scripts/parity_refetch_and_replay.py`, which prints a
    ``VERDICT: PASS|INVESTIGATE|FAIL`` line and the path to a markdown
    parity report. We persist a JSON summary alongside the live metrics.

    Args:
        week_end: ISO week label, e.g. "2026-W21".
        live_start_date / live_end_date: ISO dates ("YYYY-MM-DD"); converted
            to the parity script's YYYYMMDD cycle-id arguments.
        output_dir: where the `parity_<week_end>.json` summary is written.
        journal_db: live trade journal; defaults to `$DATA_DIR/trade_journal.db`.
        sandbox: scratch dir the parity script wipes + refetches into;
            defaults to `$DATA_DIR/parity_sandbox`.
        kelly: Kelly fraction for the replay (0.25 = V5 live).
        lookback_days: feature-history depth for the refetch.

    Returns:
        Path to the JSON summary.

    Note:
        The parity replay runs `baseline_v5_mix.py`, which consumes the four
        pre-generated walk-forward prediction CSV dirs (see that script's
        DEFAULT_ROUTING). Those must exist under the repo `data/` dir or the
        replay subprocess fails with `Missing prediction file`.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    data_root = Path(os.environ.get("DATA_DIR", "data"))
    journal_db = Path(journal_db) if journal_db else data_root / "trade_journal.db"
    sandbox = Path(sandbox) if sandbox else data_root / "parity_sandbox"

    start_cycle = live_start_date.replace("-", "")
    end_cycle = live_end_date.replace("-", "")

    live = compute_live_metrics(live_start_date, live_end_date)

    script = _REPO_ROOT / "scripts" / "parity_refetch_and_replay.py"
    # sys.executable, not bare "python" — the service user has no venv on PATH.
    cmd = [
        sys.executable, str(script),
        "--journal", str(journal_db),
        "--start-cycle", start_cycle,
        "--end-cycle", end_cycle,
        "--sandbox", str(sandbox),
        "--kelly", str(kelly),
        "--lookback-days", str(lookback_days),
    ]
    verdict = "ERROR"
    parity_report = ""
    stdout_tail = ""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        stdout_tail = result.stdout[-2000:]
        verdict_m = re.search(r"VERDICT:\s*(\w+)", result.stdout)
        report_m = re.search(r"REPORT:\s*(\S+)", result.stdout)
        verdict = verdict_m.group(1) if verdict_m else "UNKNOWN"
        parity_report = report_m.group(1) if report_m else ""
    except subprocess.CalledProcessError as e:
        # Never raise: a failed parity run must still write a summary so the
        # operator sees ERROR rather than a silent missing report.
        stdout_tail = ((e.stdout or "") + "\n--- stderr ---\n" + (e.stderr or ""))[-2000:]
        logger.error("Parity script failed (exit %s)", e.returncode)

    report = {
        "week_end": week_end,
        "live_start_date": live_start_date,
        "live_end_date": live_end_date,
        "live": live,
        "verdict": verdict,
        "parity_report": parity_report,
        "stdout_tail": stdout_tail,
    }
    out_path = output_dir / f"parity_{week_end}.json"
    out_path.write_text(json.dumps(report, indent=2))
    logger.info("Weekly parity %s → verdict %s", week_end, verdict)
    return out_path

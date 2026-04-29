"""Weekly re-backtest: re-run V2 from live_start through prior day, diff to live."""
from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def compute_live_metrics(live_start_date, live_end_date) -> dict:
    """Compute Sharpe/Return/MaxDD/etc. from portfolio_snapshots in trade_journal.db.

    Stub. Real implementation arrives in Task 12.2.
    """
    raise NotImplementedError("wire up to journal in Phase 12.2")


def compute_backtest_metrics(start_date, end_date) -> dict:
    """Re-run baseline_strategy_v2 from start_date to end_date and return metrics.

    Stub. Real implementation arrives in Task 12.2.
    """
    raise NotImplementedError("wire up to baseline_strategy_v2 in Phase 12.2")


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

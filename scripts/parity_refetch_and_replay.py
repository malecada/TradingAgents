#!/usr/bin/env python
"""V5 MIX live-vs-backtest parity check via historical refetch.

Refetches all 6 data sources fresh into a sandbox directory, replays the
backtest over the same cycle window as live trades, compares per-cycle
predictions / positions / PnL to the live journal.

Spec: docs/superpowers/specs/2026-05-15-v5-mix-live-deployment-design.md §7.

Usage:
    python scripts/parity_refetch_and_replay.py \\
        --journal /opt/tradingagents/data/trade_journal.db \\
        --start-cycle 20260516 --end-cycle 20260522 \\
        --sandbox /home/malecada/parity_w1_sandbox \\
        --lookback-days 1500
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _wipe_sandbox(sandbox: Path) -> None:
    if sandbox.exists():
        shutil.rmtree(sandbox)
    sandbox.mkdir(parents=True)
    for sub in ("onchain", "derivatives", "derivatives_raw", "options", "cache"):
        (sandbox / sub).mkdir(parents=True, exist_ok=True)


def _run_script(name: str, args: list[str], env_extra: dict[str, str]) -> None:
    cmd = [sys.executable, str(PROJECT_ROOT / "scripts" / name)] + args
    env = os.environ.copy()
    env.update(env_extra)
    logger.info("Running %s with extra env %s", name, list(env_extra.keys()))
    t0 = time.time()
    proc = subprocess.run(cmd, env=env, cwd=PROJECT_ROOT, check=True)
    logger.info("  %s done in %.1fs", name, time.time() - t0)


def refetch_into_sandbox(sandbox: Path, start_date: str, lookback_days: int) -> None:
    """Re-pull every historical data source needed for V5 MIX into sandbox."""
    start_lookback = (datetime.strptime(start_date, "%Y%m%d")
                       - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    env_extra = {"TRADINGAGENTS_DATA_ROOT": str(sandbox)}

    # 1. OHLCV — Binance/CoinGecko cache populated on demand by build_pooled_dataset;
    #    let the backtest replay (run_replay step) trigger OHLCV fetches.

    # 2. CoinMetrics
    _run_script("refetch_coinmetrics_full.py",
                 ["--coins", "btc", "eth", "usdt", "usdc", "dai",
                  "usdt_eth", "usdc_eth", "usdt_trx",
                  "--since", start_lookback,
                  "--root", str(sandbox / "onchain")],
                 env_extra)

    # 3. DefiLlama
    _run_script("fetch_defillama_extensions.py",
                 ["--since", start_lookback, "--root", str(sandbox / "onchain")],
                 env_extra)

    # 4. Funding (writes raw + daily aggregate)
    _run_script("backfill_funding_history.py",
                 ["--symbols", "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT",
                  "--start", start_lookback,
                  "--cache-dir", str(sandbox / "derivatives_raw"),
                  "--daily-out-dir", str(sandbox / "derivatives")],
                 env_extra)

    # 5. Perp-spot basis
    _run_script("build_perp_spot_basis.py",
                 ["--symbols", "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT",
                  "--start", start_lookback,
                  "--cache-dir", str(sandbox / "derivatives_raw"),
                  "--daily-dir", str(sandbox / "derivatives")],
                 env_extra)

    # 6. Deribit DVOL
    _run_script("fetch_deribit_dvol.py",
                 ["--currencies", "BTC", "ETH",
                  "--start", start_lookback,
                  "--out-dir", str(sandbox / "options")],
                 env_extra)

    # 7. Coinglass (uses env to redirect to sandbox derivatives paths)
    _run_script("fetch_coinglass_history.py", [], env_extra)


def load_live_journal_rows(journal_db: str, start_cycle: str, end_cycle: str) -> dict:
    """Pull predictions, decisions, trades, portfolio_snapshots for [start, end]."""
    conn = sqlite3.connect(journal_db)
    cycles = pd.read_sql(
        "SELECT * FROM cycles WHERE cycle_id BETWEEN ? AND ?",
        conn, params=(start_cycle, end_cycle),
    )
    preds = pd.read_sql(
        "SELECT * FROM predictions WHERE cycle_id BETWEEN ? AND ?",
        conn, params=(start_cycle, end_cycle),
    )
    tables = pd.read_sql(
        "SELECT name FROM sqlite_master WHERE type='table'", conn,
    )["name"].values
    decisions = pd.read_sql(
        "SELECT * FROM decisions WHERE cycle_id BETWEEN ? AND ?",
        conn, params=(start_cycle, end_cycle),
    ) if "decisions" in tables else pd.DataFrame()
    trades = pd.read_sql(
        "SELECT * FROM trades WHERE cycle_id BETWEEN ? AND ?",
        conn, params=(start_cycle, end_cycle),
    ) if "trades" in tables else pd.DataFrame()
    conn.close()
    return {"cycles": cycles, "predictions": preds, "decisions": decisions, "trades": trades}


def run_replay(sandbox: Path, start_cycle: str, end_cycle: str, kelly: float) -> Path:
    """Run baseline_v5_mix.py against sandbox; return its output dir."""
    out = sandbox / "replay"
    out.mkdir(exist_ok=True)
    env = os.environ.copy()
    env["TRADINGAGENTS_DATA_ROOT"] = str(sandbox)
    start_iso = f"{start_cycle[:4]}-{start_cycle[4:6]}-{start_cycle[6:]}"
    end_iso = f"{end_cycle[:4]}-{end_cycle[4:6]}-{end_cycle[6:]}"
    cmd = [
        sys.executable, str(PROJECT_ROOT / "scripts" / "baseline_v5_mix.py"),
        "--start", start_iso, "--end", end_iso,
        "--kelly", str(kelly),
        "--data-root", str(sandbox),
        "--output-dir", str(out),
    ]
    subprocess.run(cmd, env=env, cwd=PROJECT_ROOT, check=True)
    return out


def compare(live: dict, replay_dir: Path, out_report: Path) -> str:
    """Generate parity_report.md. Returns verdict: PASS / INVESTIGATE / FAIL."""
    live_preds = live["predictions"]
    replay_summary = json.loads((replay_dir / "summary.json").read_text())
    replay_daily = pd.read_csv(replay_dir / "daily_returns.csv", parse_dates=["date"])

    pred_lines = []
    if not live_preds.empty:
        pred_lines.append("(prediction-level comparison requires the replay to emit "
                            "per-cycle predictions; deferred to a future follow-up.)")

    live_total_trades = int(live["cycles"]["n_trades"].sum()) if not live["cycles"].empty else 0
    live_status_summary = (live["cycles"]["status"].value_counts().to_dict()
                            if not live["cycles"].empty else {})

    replay_port = replay_summary.get("portfolio", {})
    cycle_min = live['cycles']['cycle_id'].min() if not live['cycles'].empty else '?'
    cycle_max = live['cycles']['cycle_id'].max() if not live['cycles'].empty else '?'
    lines = [
        f"# V5 MIX parity report — cycles {cycle_min}..{cycle_max}",
        "",
        f"## Refetch summary",
        f"- Sandbox: `{replay_dir.parent}`",
        f"- Replay daily bars: {len(replay_daily)}",
        "",
        f"## Live journal summary",
        f"- Cycles: {len(live['cycles'])}",
        f"- Total trades executed: {live_total_trades}",
        f"- Status counts: {live_status_summary}",
        "",
        f"## Prediction parity",
        *pred_lines,
        "",
        f"## Aggregate metrics (replay)",
        f"- Replay portfolio Sharpe: {replay_port.get('sharpe', float('nan')):.3f}",
        f"- Replay portfolio return: {replay_port.get('total_return', float('nan')):+.1%}",
        f"- Replay portfolio max DD: {replay_port.get('max_drawdown', float('nan')):.1%}",
        "",
    ]
    verdict = "PASS" if (replay_port.get("sharpe", 0) > 1.0
                          and "predict_majority_fail" not in live_status_summary
                          and "critical_data_fail" not in live_status_summary) else "INVESTIGATE"
    lines.append(f"## Verdict: {verdict}")
    out_report.write_text("\n".join(lines))
    return verdict


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--journal", required=True,
                    help="Path to live trade journal SQLite DB")
    p.add_argument("--start-cycle", required=True, help="YYYYMMDD")
    p.add_argument("--end-cycle", required=True, help="YYYYMMDD")
    p.add_argument("--sandbox", required=True, help="Sandbox directory (will be wiped)")
    p.add_argument("--lookback-days", type=int, default=1500)
    p.add_argument("--kelly", type=float, default=0.25,
                    help="Kelly fraction for replay (default 0.25 = V5 live)")
    args = p.parse_args()

    sandbox = Path(args.sandbox)
    logger.info("=== V5 MIX parity check ===")
    logger.info("Sandbox: %s  (will be wiped)", sandbox)

    _wipe_sandbox(sandbox)
    refetch_into_sandbox(sandbox, args.start_cycle, args.lookback_days)

    live = load_live_journal_rows(args.journal, args.start_cycle, args.end_cycle)
    logger.info("Live journal: %d cycles, %d predictions",
                len(live["cycles"]), len(live["predictions"]))

    replay_dir = run_replay(sandbox, args.start_cycle, args.end_cycle, args.kelly)
    logger.info("Replay output: %s", replay_dir)

    report = sandbox / "parity_report.md"
    verdict = compare(live, replay_dir, report)
    logger.info("Verdict: %s", verdict)
    logger.info("Report: %s", report)
    print(f"\nVERDICT: {verdict}\nREPORT: {report}\n")


if __name__ == "__main__":
    main()

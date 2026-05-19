#!/usr/bin/env python
"""V5 MIX TP/SL walk-forward parameter split orchestrator.

Runs the §29 (close-only) and §30 (intrabar) 378-cell sweeps on a TRAIN
window and a TEST window, joins cells across IS/OOS, computes per-engine
verdict, and writes WF artifacts.

Outputs to data/v5_sltp_wf/:
  co_train/, co_test/, ib_train/, ib_test/ — per-sweep outputs
  wf_results.csv  — joined per-cell IS-SR + OOS-SR per engine
  wf_summary.json — train-best per engine + OOS scores + verdicts
  wf_report.md    — human-readable summary
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.baseline_v5_mix import COSTS, EARLY_EXIT_DEFAULT  # noqa: E402
from scripts.v5_mix_sltp_sweep import run_sweep as run_sweep_co  # noqa: E402
from scripts.v5_mix_sltp_sweep import (  # noqa: E402
    SL_GRID, EE_GRID, TP_GRID, SMOKE_SL, SMOKE_EE, SMOKE_TP,
)
from scripts.v5_mix_sltp_sweep_intrabar import run_sweep as run_sweep_ib  # noqa: E402

_BASELINE_SL = COSTS["stop_loss"]      # 0.03
_BASELINE_EE = EARLY_EXIT_DEFAULT      # 0.015
_BASELINE_TP = COSTS["take_profit"]    # 0.0


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT
        ).decode().strip()
    except Exception:
        return "unknown"


def _join_is_oos(train_csv: Path, test_csv: Path, engine: str) -> pd.DataFrame:
    """Join train (IS) and test (OOS) per-cell portfolio metrics."""
    tr = pd.read_csv(train_csv)
    te = pd.read_csv(test_csv)
    tr = tr[tr["scope"] == "portfolio"].copy()
    te = te[te["scope"] == "portfolio"].copy()
    keys = ["sl", "ee", "tp"]
    cols = ["sharpe", "max_drawdown", "calmar", "total_return"]
    joined = tr[keys + cols].merge(
        te[keys + cols], on=keys, suffixes=("_is", "_oos"),
    )
    joined["engine"] = engine
    joined = joined.rename(columns={
        "sharpe_is": "is_sr", "sharpe_oos": "oos_sr",
        "max_drawdown_is": "is_dd", "max_drawdown_oos": "oos_dd",
        "calmar_is": "is_calmar", "calmar_oos": "oos_calmar",
        "total_return_is": "is_ret", "total_return_oos": "oos_ret",
    })
    return joined[
        ["engine"] + keys
        + ["is_sr", "oos_sr", "is_dd", "oos_dd", "is_calmar", "oos_calmar",
           "is_ret", "oos_ret"]
    ]


def _per_engine_verdict(joined: pd.DataFrame, engine: str) -> dict:
    """Compute train-best, OOS of train-best, baseline OOS, verdict."""
    sub = joined[joined["engine"] == engine].copy()
    train_best = sub.sort_values("is_sr", ascending=False).iloc[0]
    baseline_rows = sub[
        (sub["sl"] == _BASELINE_SL)
        & (sub["ee"] == _BASELINE_EE)
        & (sub["tp"] == _BASELINE_TP)
    ]
    baseline_oos_sr = (
        float(baseline_rows["oos_sr"].iloc[0]) if len(baseline_rows) else None
    )
    train_best_oos_sr = float(train_best["oos_sr"])
    verdict = (
        "pass" if baseline_oos_sr is not None
        and train_best_oos_sr > baseline_oos_sr
        else "fail"
    )
    return dict(
        engine=engine,
        train_best=dict(
            sl=float(train_best["sl"]), ee=float(train_best["ee"]),
            tp=float(train_best["tp"]),
            is_sr=float(train_best["is_sr"]),
            oos_sr=train_best_oos_sr,
            is_dd=float(train_best["is_dd"]),
            oos_dd=float(train_best["oos_dd"]),
            oos_calmar=float(train_best["oos_calmar"]),
        ),
        baseline_oos_sr=baseline_oos_sr,
        verdict=verdict,
    )


def _write_report(summary: dict, out_path: Path) -> None:
    co = summary["close_only"]
    ib = summary["intrabar"]
    lines = [
        "# V5 MIX TP/SL Walk-Forward Parameter Split Report",
        "",
        f"Train window: {summary['windows']['train']['start']} → {summary['windows']['train']['end']}",
        f"Test window:  {summary['windows']['test']['start']} → {summary['windows']['test']['end']}",
        "",
        f"Baseline cell: SL={_BASELINE_SL}, EE={_BASELINE_EE}, TP={_BASELINE_TP}",
        "",
        "## Close-only engine",
        "",
        f"- Train-best: SL={co['train_best']['sl']:g}, "
        f"EE={co['train_best']['ee']:g}, TP={co['train_best']['tp']:g}",
        f"  - IS SR  = {co['train_best']['is_sr']:+.3f}",
        f"  - OOS SR = {co['train_best']['oos_sr']:+.3f}",
        f"  - OOS DD = {co['train_best']['oos_dd']:.1%}",
        f"  - OOS Calmar = {co['train_best']['oos_calmar']:+.2f}",
        f"- Baseline OOS SR = "
        f"{co['baseline_oos_sr']:+.3f}" if co['baseline_oos_sr'] is not None else "n/a",
        f"- **Verdict: {co['verdict'].upper()}** "
        f"(train-best OOS > baseline OOS? "
        f"{co['train_best']['oos_sr']:+.3f} vs {co['baseline_oos_sr']:+.3f})",
        "",
        "## Intrabar engine",
        "",
        f"- Train-best: SL={ib['train_best']['sl']:g}, "
        f"EE={ib['train_best']['ee']:g}, TP={ib['train_best']['tp']:g}",
        f"  - IS SR  = {ib['train_best']['is_sr']:+.3f}",
        f"  - OOS SR = {ib['train_best']['oos_sr']:+.3f}",
        f"  - OOS DD = {ib['train_best']['oos_dd']:.1%}",
        f"  - OOS Calmar = {ib['train_best']['oos_calmar']:+.2f}",
        f"- Baseline OOS SR = "
        f"{ib['baseline_oos_sr']:+.3f}" if ib['baseline_oos_sr'] is not None else "n/a",
        f"- **Verdict: {ib['verdict'].upper()}** "
        f"(train-best OOS > baseline OOS? "
        f"{ib['train_best']['oos_sr']:+.3f} vs {ib['baseline_oos_sr']:+.3f})",
        "",
        "## Joint outcome",
        "",
        f"- Close-only: {co['verdict']}",
        f"- Intrabar:   {ib['verdict']}",
        "",
        f"git SHA: {summary['git_sha']}",
        f"wall clock: {summary['wall_clock_sec']:.1f} s",
        "",
    ]
    out_path.write_text("\n".join(lines) + "\n")


def run_wf(
    sl_grid: list[float], ee_grid: list[float], tp_grid: list[float],
    train_start: str, train_end: str,
    test_start: str, test_end: str,
    kelly_fraction: float, out_dir: Path,
) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    sweeps = [
        ("co_train", run_sweep_co, train_start, train_end),
        ("co_test",  run_sweep_co, test_start,  test_end),
        ("ib_train", run_sweep_ib, train_start, train_end),
        ("ib_test",  run_sweep_ib, test_start,  test_end),
    ]
    for name, runner, start, end in sweeps:
        print(f"\n  === {name}: {start} → {end} ===")
        sub_dir = out_dir / name
        runner(sl_grid, ee_grid, tp_grid, start, end, kelly_fraction, sub_dir)

    joined_co = _join_is_oos(
        out_dir / "co_train" / "results.csv",
        out_dir / "co_test" / "results.csv",
        engine="close_only",
    )
    joined_ib = _join_is_oos(
        out_dir / "ib_train" / "results.csv",
        out_dir / "ib_test" / "results.csv",
        engine="intrabar",
    )
    joined = pd.concat([joined_co, joined_ib], ignore_index=True)
    joined.to_csv(out_dir / "wf_results.csv", index=False)

    co_verdict = _per_engine_verdict(joined, "close_only")
    ib_verdict = _per_engine_verdict(joined, "intrabar")

    summary = dict(
        grid=dict(sl=sl_grid, ee=ee_grid, tp=tp_grid),
        windows=dict(
            train=dict(start=train_start, end=train_end),
            test=dict(start=test_start, end=test_end),
        ),
        kelly_fraction=kelly_fraction,
        baseline_cell=dict(sl=_BASELINE_SL, ee=_BASELINE_EE, tp=_BASELINE_TP),
        close_only=co_verdict,
        intrabar=ib_verdict,
        wall_clock_sec=time.time() - t0,
        git_sha=_git_sha(),
    )
    with open(out_dir / "wf_summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)
    _write_report(summary, out_dir / "wf_report.md")

    print(f"\n  Wrote: {out_dir / 'wf_results.csv'}  ({len(joined)} rows)")
    print(f"  Wrote: {out_dir / 'wf_summary.json'}")
    print(f"  Wrote: {out_dir / 'wf_report.md'}")
    print(f"\n  CO verdict: {co_verdict['verdict'].upper()}  "
          f"(train-best OOS SR={co_verdict['train_best']['oos_sr']:+.3f} vs "
          f"baseline OOS SR={co_verdict['baseline_oos_sr']:+.3f})")
    print(f"  IB verdict: {ib_verdict['verdict'].upper()}  "
          f"(train-best OOS SR={ib_verdict['train_best']['oos_sr']:+.3f} vs "
          f"baseline OOS SR={ib_verdict['baseline_oos_sr']:+.3f})")

    return summary


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--train-start", default="2021-11-07")
    p.add_argument("--train-end",   default="2024-12-31")
    p.add_argument("--test-start",  default="2025-01-01")
    p.add_argument("--test-end",    default="2026-04-15")
    p.add_argument("--output-dir",  default="data/v5_sltp_wf")
    p.add_argument("--kelly",       type=float, default=0.5)
    p.add_argument("--smoke", action="store_true",
                   help="Smoke run on tiny grid (2x1x2=4 cells)")
    p.add_argument("--data-root", default=None)
    args = p.parse_args()

    if args.data_root:
        os.environ["TRADINGAGENTS_DATA_ROOT"] = args.data_root

    if args.smoke:
        sl, ee, tp = SMOKE_SL, SMOKE_EE, SMOKE_TP
        print("  SMOKE MODE — small grid")
    else:
        sl, ee, tp = SL_GRID, EE_GRID, TP_GRID

    out_dir = PROJECT_ROOT / args.output_dir
    print(f"\n  V5 MIX TP/SL walk-forward")
    print(f"  train  : {args.train_start} → {args.train_end}")
    print(f"  test   : {args.test_start} → {args.test_end}")
    print(f"  grid   : SL={len(sl)} EE={len(ee)} TP={len(tp)} = "
          f"{len(sl) * len(ee) * len(tp)} cells × 4 sweeps")
    print(f"  output : {out_dir}\n")

    run_wf(sl, ee, tp,
           args.train_start, args.train_end,
           args.test_start, args.test_end,
           args.kelly, out_dir)


if __name__ == "__main__":
    main()

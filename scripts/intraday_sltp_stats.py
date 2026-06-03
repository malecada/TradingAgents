#!/usr/bin/env python
"""Statistical adjudication of the intraday SL/TP/trailing sweep.

Reads the sweep's best cell, re-derives the best-cell and 3%-baseline daily
portfolio return series on the intrabar engine, then:
  1. DSR (deflated Sharpe) on the best cell with n_trials = #grid cells.
  2. Block-bootstrap 95% CI for the best cell's Sharpe.
  3. Paired block-bootstrap best-vs-3% (delta_sr_ci, p_delta_le_0).

Verdict: the best cell is a defensible improvement over the a-priori 3% only if
DSR >= 0.95 AND the paired delta_sr_ci excludes 0 (P(best>3%) high). Otherwise
3% is statistically indistinguishable and stays.

Usage:
    python scripts/intraday_sltp_stats.py --sweep-dir data/intraday_sltp_sweep
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.baseline_v5_mix import COSTS, CORE_COINS, DEFAULT_ROUTING, _v2_positions  # noqa: E402
from scripts.bootstrap_hybrid import diff_sharpe_ci  # noqa: E402
from scripts.bootstrap_sharpe import bootstrap_sharpe_ci  # noqa: E402
from scripts.intraday_fills import group_intraday_by_day, run_coin_backtest_intrabar  # noqa: E402
from scripts.intraday_sltp_sweep import _load_coin_data, EE_OFF, INTRADAY_DIR  # noqa: E402
from tradingagents.strategies.v3.backtest.dsr import (  # noqa: E402
    deflated_sharpe_ratio, expected_max_sharpe, variance_of_sr,
)


def _portfolio_returns(sl, tp, trail, start, end, kelly=0.5) -> np.ndarray:
    coin_rets = {}
    for c in CORE_COINS:
        merged = _load_coin_data(c, PROJECT_ROOT / DEFAULT_ROUTING[c], start, end)
        imap = group_intraday_by_day(pd.read_parquet(INTRADAY_DIR / f"{c}.parquet"), merged["date"].values)
        pos = _v2_positions(merged, kelly_fraction=kelly, early_exit_loss=EE_OFF)
        costs = dict(COSTS); costs["stop_loss"] = sl; costs["take_profit"] = tp
        eq, _ = run_coin_backtest_intrabar(
            dates=merged["date"].values, prices=merged["Close"].values, positions=pos,
            intraday=imap, initial_capital=10_000.0, trailing_stop=trail, **costs)
        eq = np.asarray(eq, dtype=float)
        coin_rets[c] = pd.Series(eq[1:] / eq[:-1] - 1.0, index=pd.to_datetime(merged["date"].values[1:]))
    return pd.DataFrame(coin_rets).dropna().mean(axis=1).values


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--sweep-dir", default="data/intraday_sltp_sweep")
    p.add_argument("--start", default="2021-11-07")
    p.add_argument("--end", default="2026-04-15")
    p.add_argument("--n-iter", type=int, default=5000)
    p.add_argument("--block-size", type=int, default=21)
    args = p.parse_args()

    sdir = PROJECT_ROOT / args.sweep_dir
    summary = json.loads((sdir / "summary.json").read_text())
    best = summary["best_cell"]
    n_cells = summary["n_cells"]

    best_ret = _portfolio_returns(best["sl"], best["tp"], best["trail"], args.start, args.end)
    base_ret = _portfolio_returns(COSTS["stop_loss"], 0.0, 0.0, args.start, args.end)

    # 1. DSR on the best cell (non-annualized SR units, matching dsr.py).
    var_sr = variance_of_sr(best_ret)
    se_sr = float(np.sqrt(var_sr))
    sr_obs_raw = float(np.mean(best_ret) / np.std(best_ret, ddof=1))
    sr_exp = expected_max_sharpe(n_trials=n_cells, var_sr=var_sr)
    dsr = deflated_sharpe_ratio(sr_obs_raw, sr_exp, se_sr)

    # 2. Bootstrap CI on best cell (annualized SR units).
    pt, lo, hi, _ = bootstrap_sharpe_ci(best_ret, n_iter=args.n_iter, block_size=args.block_size)

    # 3. Paired bootstrap best vs 3%.
    pair = diff_sharpe_ci(best_ret, base_ret, n_iter=args.n_iter, block_size=args.block_size)

    beats_3pct = (dsr >= 0.95) and (pair["delta_sr_ci"][0] > 0)
    out = dict(
        best_cell=best, n_trials=n_cells,
        dsr=dict(value=float(dsr), sr_obs_raw=sr_obs_raw,
                 expected_max_sr_null=float(sr_exp), se_sr=se_sr,
                 significant_at_95=bool(dsr >= 0.95)),
        best_bootstrap=dict(sharpe=pt, ci95=[lo, hi]),
        best_vs_3pct=pair,
        verdict=("Best cell is a statistically defensible improvement over 3%"
                 if beats_3pct else
                 "No cell beats the a-priori 3% after multiple-testing correction — keep 3%"),
    )
    (sdir / "stats.json").write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()

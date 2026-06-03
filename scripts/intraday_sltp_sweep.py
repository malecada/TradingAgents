#!/usr/bin/env python
"""Intraday triple-barrier SL/TP+trailing sweep for the 4-coin V5 MIX.

Refined SL × TP × trailing grid (EE fixed off — §29 settled that early-exit
deteriorates), evaluated on the intraday-fill engine (scripts/intraday_fills).
Also emits bias.json: the canonical 3% cell on the daily engine vs the intrabar
engine, quantifying §29's close-to-close look-ahead bias.

Outputs to data/intraday_sltp_sweep/:
  results.csv  — one row per (sl, tp, trail) × scope (portfolio + 4 coins)
  summary.json — grid + baseline cell + best cell + git SHA
  bias.json    — daily-vs-intrabar deltas for the 3% baseline cell

Usage:
    python scripts/intraday_sltp_sweep.py --start 2021-11-07 --end 2026-04-15
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.baseline_strategy_v2 import run_coin_backtest  # noqa: E402
from scripts.baseline_v5_mix import (  # noqa: E402
    COSTS, CORE_COINS, DEFAULT_ROUTING, _load_preds, _v2_positions,
)
from scripts.intraday_fills import (  # noqa: E402
    group_intraday_by_day, run_coin_backtest_intrabar,
)
from scripts.v5_mix_sltp_sweep import _metrics  # noqa: E402
from tradingagents.dataflows.coingecko_binance import _load_crypto_ohlcv  # noqa: E402

EE_OFF = 1.0
SL_GRID = [0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.07, 0.10]
TP_GRID = [0.0, 0.02, 0.03, 0.05, 0.08, 0.12]
TRAIL_GRID = [0.0, 0.03, 0.05, 0.08]
INTRADAY_DIR = PROJECT_ROOT / "data" / "intraday_1h"

SMOKE_SL = [0.0, 0.03]
SMOKE_TP = [0.0, 0.05]
SMOKE_TRAIL = [0.0]


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT).decode().strip()
    except Exception:
        return "unknown"


def _load_coin_data(coin: str, pred_dir: Path, start: str, end: str) -> pd.DataFrame:
    preds = _load_preds(pred_dir, coin)
    preds = preds[(preds["date"] >= start) & (preds["date"] <= end)]
    if preds.empty:
        raise ValueError(f"{coin}: no predictions in [{start}, {end}] under {pred_dir}")
    ohlcv = _load_crypto_ohlcv(coin, end)
    ohlcv["Date"] = pd.to_datetime(ohlcv["Date"]).dt.tz_localize(None).dt.normalize()
    merged = preds.merge(ohlcv[["Date", "Close"]], left_on="date", right_on="Date")
    merged = merged.dropna(subset=["Close"]).reset_index(drop=True)
    merged["ref_price"] = merged["Close"]
    return merged


def _load_intraday_map(coin: str, daily_dates: np.ndarray) -> dict:
    path = INTRADAY_DIR / f"{coin}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"{path} missing — run scripts/fetch_intraday_1h.py first")
    return group_intraday_by_day(pd.read_parquet(path), daily_dates)


def _intra_returns(merged, intraday_map, positions, sl, tp, trail) -> pd.Series:
    costs = dict(COSTS); costs["stop_loss"] = sl; costs["take_profit"] = tp
    equity, _m = run_coin_backtest_intrabar(
        dates=merged["date"].values, prices=merged["Close"].values,
        positions=positions, intraday=intraday_map, initial_capital=10_000.0,
        trailing_stop=trail, **costs)
    eq = np.asarray(equity, dtype=float)
    return pd.Series(eq[1:] / eq[:-1] - 1.0, index=pd.to_datetime(merged["date"].values[1:]))


def _daily_returns(merged, positions, sl, tp) -> pd.Series:
    costs = dict(COSTS); costs["stop_loss"] = sl; costs["take_profit"] = tp
    equity, _m = run_coin_backtest(
        dates=merged["date"].values, prices=merged["Close"].values,
        positions=positions, initial_capital=10_000.0, **costs)
    eq = np.asarray(equity, dtype=float)
    return pd.Series(eq[1:] / eq[:-1] - 1.0, index=pd.to_datetime(merged["date"].values[1:]))


def run_sweep(sl_grid, tp_grid, trail_grid, start, end, kelly_fraction, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    coin_data, intraday_maps, positions = {}, {}, {}
    for coin in CORE_COINS:
        merged = _load_coin_data(coin, PROJECT_ROOT / DEFAULT_ROUTING[coin], start, end)
        coin_data[coin] = merged
        intraday_maps[coin] = _load_intraday_map(coin, merged["date"].values)
        positions[coin] = _v2_positions(merged, kelly_fraction=kelly_fraction, early_exit_loss=EE_OFF)
    print(f"  Loaded {len(coin_data)} coins + intraday in {time.time()-t0:.1f}s")

    rows = []
    n_cells = len(sl_grid) * len(tp_grid) * len(trail_grid)
    cell_i = 0
    baseline_sr = None
    for sl in sl_grid:
        for tp in tp_grid:
            for trail in trail_grid:
                cell_i += 1
                coin_rets = {c: _intra_returns(coin_data[c], intraday_maps[c], positions[c], sl, tp, trail)
                             for c in CORE_COINS}
                df = pd.DataFrame(coin_rets).dropna()
                pm = _metrics(df.mean(axis=1).values)
                rows.append(dict(sl=sl, tp=tp, trail=trail, scope="portfolio", **pm))
                for c, r in coin_rets.items():
                    rows.append(dict(sl=sl, tp=tp, trail=trail, scope=c, **_metrics(r.values)))
                if sl == COSTS["stop_loss"] and tp == 0.0 and trail == 0.0:
                    baseline_sr = pm["sharpe"]
                if cell_i % 10 == 0 or cell_i == n_cells:
                    el = time.time() - t0
                    print(f"  cell {cell_i}/{n_cells} SL={sl} TP={tp} TR={trail} "
                          f"SR={pm['sharpe']:+.2f} elapsed={el:.0f}s eta={el/cell_i*(n_cells-cell_i):.0f}s")

    df_out = pd.DataFrame(rows)
    df_out.to_csv(out_dir / "results.csv", index=False)
    port = df_out[df_out["scope"] == "portfolio"].sort_values("sharpe", ascending=False)
    best = port.iloc[0]

    summary = dict(
        engine="intrabar_1h", coins=list(CORE_COINS),
        grid=dict(sl=sl_grid, tp=tp_grid, trail=trail_grid, ee="off"),
        window=dict(start=start, end=end), kelly_fraction=kelly_fraction,
        baseline_cell=dict(sl=COSTS["stop_loss"], tp=0.0, trail=0.0, portfolio_sharpe=baseline_sr),
        best_cell=dict(sl=float(best["sl"]), tp=float(best["tp"]), trail=float(best["trail"]),
                       portfolio_sharpe=float(best["sharpe"]),
                       total_return=float(best["total_return"]),
                       max_drawdown=float(best["max_drawdown"]), calmar=float(best["calmar"])),
        n_cells=n_cells, wall_clock_sec=time.time() - t0, git_sha=_git_sha(),
    )
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))

    bias_coin = {}
    for c in CORE_COINS:
        d = _daily_returns(coin_data[c], positions[c], COSTS["stop_loss"], 0.0)
        ii = _intra_returns(coin_data[c], intraday_maps[c], positions[c], COSTS["stop_loss"], 0.0, 0.0)
        bias_coin[c] = dict(daily=_metrics(d.values), intrabar=_metrics(ii.values))
    d_port = pd.DataFrame({c: _daily_returns(coin_data[c], positions[c], COSTS["stop_loss"], 0.0) for c in CORE_COINS}).dropna().mean(axis=1)
    i_port = pd.DataFrame({c: _intra_returns(coin_data[c], intraday_maps[c], positions[c], COSTS["stop_loss"], 0.0, 0.0) for c in CORE_COINS}).dropna().mean(axis=1)
    bias = dict(
        cell=dict(sl=COSTS["stop_loss"], tp=0.0, trail=0.0),
        portfolio=dict(daily=_metrics(d_port.values), intrabar=_metrics(i_port.values)),
        per_coin=bias_coin,
    )
    bias["portfolio"]["sharpe_delta_intrabar_minus_daily"] = (
        bias["portfolio"]["intrabar"]["sharpe"] - bias["portfolio"]["daily"]["sharpe"])
    (out_dir / "bias.json").write_text(json.dumps(bias, indent=2, default=str))

    print(f"\n  Wrote {out_dir/'results.csv'} ({len(df_out)} rows), summary.json, bias.json")
    print(f"  Baseline 3% cell intrabar SR = {baseline_sr:+.3f}")
    print(f"  Best cell: SL={best['sl']} TP={best['tp']} TR={best['trail']} "
          f"SR={best['sharpe']:+.3f} DD={best['max_drawdown']:.1%}")
    print(f"  BIAS (intrabar - daily) portfolio SR delta = "
          f"{bias['portfolio']['sharpe_delta_intrabar_minus_daily']:+.3f}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--start", default="2021-11-07")
    p.add_argument("--end", default="2026-04-15")
    p.add_argument("--output-dir", default="data/intraday_sltp_sweep")
    p.add_argument("--kelly", type=float, default=0.5)
    p.add_argument("--smoke", action="store_true")
    args = p.parse_args()
    sl, tp, tr = (SMOKE_SL, SMOKE_TP, SMOKE_TRAIL) if args.smoke else (SL_GRID, TP_GRID, TRAIL_GRID)
    out_dir = PROJECT_ROOT / args.output_dir
    print(f"\n  Intraday SL/TP/trailing sweep — {args.start} → {args.end}")
    print(f"  grid: SL={len(sl)} TP={len(tp)} TRAIL={len(tr)} = {len(sl)*len(tp)*len(tr)} cells (EE off)\n")
    run_sweep(sl, tp, tr, args.start, args.end, args.kelly, out_dir)


if __name__ == "__main__":
    main()

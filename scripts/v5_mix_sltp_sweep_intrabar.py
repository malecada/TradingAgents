#!/usr/bin/env python
"""V5 MIX TP/SL intrabar OHLC sensitivity sweep (Approach B).

Same 378-cell grid as scripts/v5_mix_sltp_sweep.py, but with intrabar SL/TP
fills (low <= SL_price, high >= TP_price; SL-first on same-bar collision).
Records n_intrabar_sl / n_intrabar_tp diagnostic counts per cell.

Outputs to data/v5_sltp_sweep_intrabar/:
  results.csv  — one row per (sl, ee, tp) × scope; includes intrabar diagnostics
  summary.json — grid + close-only-§29 baseline + intrabar baseline + best + git SHA
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

from scripts.baseline_strategy_v2 import run_coin_backtest  # noqa: E402
from scripts.baseline_v5_mix import (  # noqa: E402
    COSTS, DEFAULT_ROUTING, EARLY_EXIT_DEFAULT, _load_preds, _v2_positions,
)
from scripts.v5_mix_sltp_sweep import (  # noqa: E402
    SL_GRID, EE_GRID, TP_GRID, SMOKE_SL, SMOKE_EE, SMOKE_TP, _metrics,
)
from tradingagents.dataflows.coingecko_binance import _load_crypto_ohlcv  # noqa: E402

ANN = float(np.sqrt(252))

_BASELINE_SL = COSTS["stop_loss"]       # 0.03
_BASELINE_EE = EARLY_EXIT_DEFAULT       # 0.015
_BASELINE_TP = COSTS["take_profit"]     # 0.0


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT
        ).decode().strip()
    except Exception:
        return "unknown"


def _load_coin_data(coin: str, pred_dir: Path, start: str, end: str) -> pd.DataFrame:
    """Load + merge preds with full OHLCV (Close + High + Low)."""
    preds = _load_preds(pred_dir, coin)
    preds = preds[(preds["date"] >= start) & (preds["date"] <= end)]
    if preds.empty:
        raise ValueError(f"{coin}: no predictions in [{start}, {end}] under {pred_dir}")
    ohlcv = _load_crypto_ohlcv(coin, end)
    ohlcv["Date"] = pd.to_datetime(ohlcv["Date"]).dt.tz_localize(None).dt.normalize()
    merged = preds.merge(
        ohlcv[["Date", "Open", "High", "Low", "Close"]],
        left_on="date", right_on="Date",
    )
    merged = merged.dropna(subset=["Close", "High", "Low"]).reset_index(drop=True)
    merged["ref_price"] = merged["Close"]
    return merged


def _engine_returns_intrabar(merged: pd.DataFrame, positions: np.ndarray,
                              sl: float, tp: float) -> tuple[pd.Series, int, int]:
    """Run intrabar engine. Returns (returns, n_intrabar_sl, n_intrabar_tp).

    The n_* counts are reconstructed by comparing the intrabar equity to a
    parallel close-only run on the same positions/SL/TP — every bar where the
    paths diverge had an intrabar fill. SL vs TP is inferred from the sign of
    divergence (negative on the diverging bar → SL; positive → TP).
    """
    costs = dict(COSTS)
    costs["stop_loss"] = sl
    costs["take_profit"] = tp

    eq_ib, _ = run_coin_backtest(
        dates=merged["date"].values, prices=merged["Close"].values,
        positions=positions, initial_capital=10_000.0,
        intrabar=True,
        highs=merged["High"].values, lows=merged["Low"].values,
        **costs,
    )
    eq_co, _ = run_coin_backtest(
        dates=merged["date"].values, prices=merged["Close"].values,
        positions=positions, initial_capital=10_000.0,
        intrabar=False,
        **costs,
    )
    eq_ib = np.asarray(eq_ib, dtype=float)
    eq_co = np.asarray(eq_co, dtype=float)

    # Bar-level divergence: where intrabar return differs from close-only.
    rets_ib = eq_ib[1:] / eq_ib[:-1] - 1.0
    rets_co = eq_co[1:] / eq_co[:-1] - 1.0
    diff = rets_ib - rets_co
    n_sl = int((diff < -1e-9).sum())   # intrabar lost more this bar → SL
    n_tp = int((diff > 1e-9).sum())    # intrabar gained more this bar → TP

    return (
        pd.Series(rets_ib, index=pd.to_datetime(merged["date"].values[1:])),
        n_sl, n_tp,
    )


def run_sweep(
    sl_grid: list[float], ee_grid: list[float], tp_grid: list[float],
    start: str, end: str, kelly_fraction: float, out_dir: Path,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    coin_data: dict[str, pd.DataFrame] = {}
    for coin, pdir in DEFAULT_ROUTING.items():
        coin_data[coin] = _load_coin_data(coin, PROJECT_ROOT / pdir, start, end)
    print(f"  Loaded {len(coin_data)} coins (with OHLC) in {time.time() - t0:.1f}s")

    rows: list[dict] = []
    n_cells = len(sl_grid) * len(ee_grid) * len(tp_grid)
    cell_i = 0
    intrabar_baseline_sr = None

    # EE outer: positions are EE-dependent only.
    for ee in ee_grid:
        position_cache: dict[str, np.ndarray] = {}
        for coin, merged in coin_data.items():
            position_cache[coin] = _v2_positions(
                merged, kelly_fraction=kelly_fraction, early_exit_loss=ee,
            )
        for sl in sl_grid:
            for tp in tp_grid:
                cell_i += 1
                coin_rets: dict[str, pd.Series] = {}
                n_sl_total = 0
                n_tp_total = 0
                for coin, merged in coin_data.items():
                    r, n_sl, n_tp = _engine_returns_intrabar(
                        merged, position_cache[coin], sl=sl, tp=tp,
                    )
                    coin_rets[coin] = r
                    n_sl_total += n_sl
                    n_tp_total += n_tp

                df = pd.DataFrame(coin_rets).dropna()
                port = df.mean(axis=1)
                pm = _metrics(port.values)

                rows.append(dict(
                    sl=sl, ee=ee, tp=tp, scope="portfolio",
                    n_intrabar_sl=n_sl_total, n_intrabar_tp=n_tp_total, **pm,
                ))
                for coin, r in coin_rets.items():
                    cm = _metrics(r.values)
                    # Per-coin counts not split here — coarse aggregate only.
                    rows.append(dict(
                        sl=sl, ee=ee, tp=tp, scope=coin,
                        n_intrabar_sl=-1, n_intrabar_tp=-1, **cm,
                    ))

                if sl == _BASELINE_SL and ee == _BASELINE_EE and tp == _BASELINE_TP:
                    intrabar_baseline_sr = pm["sharpe"]

                if cell_i % 20 == 0 or cell_i == n_cells:
                    elapsed = time.time() - t0
                    eta = elapsed / cell_i * (n_cells - cell_i)
                    print(f"  cell {cell_i}/{n_cells}  "
                          f"SL={sl:.3f} EE={ee:.3f} TP={tp:.3f}  "
                          f"port SR={pm['sharpe']:+.2f}  "
                          f"n_sl={n_sl_total} n_tp={n_tp_total}  "
                          f"elapsed={elapsed:.0f}s  eta={eta:.0f}s")

    df_out = pd.DataFrame(rows)
    df_out.to_csv(out_dir / "results.csv", index=False)

    port_only = df_out[df_out["scope"] == "portfolio"].copy()
    best = port_only.sort_values("sharpe", ascending=False).iloc[0]

    if intrabar_baseline_sr is None:
        print(
            f"  WARNING: baseline cell (SL={_BASELINE_SL}, EE={_BASELINE_EE}, "
            f"TP={_BASELINE_TP}) was NOT in the sweep grid — "
            f"summary.json intrabar_baseline_cell.portfolio_sharpe will be null.",
            file=sys.stderr,
        )

    delta_sr = (
        float(best["sharpe"]) - intrabar_baseline_sr
        if intrabar_baseline_sr is not None else None
    )

    summary = dict(
        grid=dict(sl=sl_grid, ee=ee_grid, tp=tp_grid),
        window=dict(start=start, end=end),
        kelly_fraction=kelly_fraction,
        intrabar_baseline_cell=dict(
            sl=_BASELINE_SL, ee=_BASELINE_EE, tp=_BASELINE_TP,
            portfolio_sharpe=intrabar_baseline_sr,
        ),
        close_only_published_baseline_sharpe=3.178,  # §29 reference for context
        best_cell=dict(
            sl=float(best["sl"]), ee=float(best["ee"]), tp=float(best["tp"]),
            portfolio_sharpe=float(best["sharpe"]),
            total_return=float(best["total_return"]),
            max_drawdown=float(best["max_drawdown"]),
            calmar=float(best["calmar"]),
            n_intrabar_sl=int(best["n_intrabar_sl"]),
            n_intrabar_tp=int(best["n_intrabar_tp"]),
        ),
        delta_sr_best_vs_intrabar_baseline=delta_sr,
        acceptance_threshold=0.15,
        verdict=(
            None if intrabar_baseline_sr is None
            else ("confirm" if delta_sr is not None and delta_sr >= 0.15 else "reject")
        ),
        n_cells=n_cells,
        wall_clock_sec=time.time() - t0,
        git_sha=_git_sha(),
    )
    with open(out_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"\n  Wrote: {out_dir / 'results.csv'}  ({len(df_out)} rows)")
    print(f"  Wrote: {out_dir / 'summary.json'}")
    if intrabar_baseline_sr is not None:
        print(f"  Intrabar baseline SR = {intrabar_baseline_sr:+.3f} "
              f"(close-only §29 = +3.178)")
        print(f"  Best cell: SL={best['sl']} EE={best['ee']} TP={best['tp']}  "
              f"SR={best['sharpe']:+.3f}  DD={best['max_drawdown']:.1%}  "
              f"ΔSR={delta_sr:+.3f}  verdict={summary['verdict'].upper()}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--start", default="2021-11-07")
    p.add_argument("--end", default="2026-04-15")
    p.add_argument("--output-dir", default="data/v5_sltp_sweep_intrabar")
    p.add_argument("--kelly", type=float, default=0.5)
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
    print(f"\n  V5 MIX TP/SL intrabar sweep (approach B)")
    print(f"  window : {args.start} → {args.end}")
    print(f"  grid   : SL={len(sl)} EE={len(ee)} TP={len(tp)} = {len(sl) * len(ee) * len(tp)} cells")
    print(f"  output : {out_dir}\n")

    run_sweep(sl, ee, tp, args.start, args.end, args.kelly, out_dir)


if __name__ == "__main__":
    main()

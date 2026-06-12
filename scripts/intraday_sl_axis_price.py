#!/usr/bin/env python
"""PRICE-stop SL-axis — deployable live STOP_LOSS_PCT (§31.4c).

Live places STOP_MARKET at entry_price*(1-stop_loss_pct) (a PRICE stop), not the
equity stop §31.4b optimized. This re-runs the SL axis in PRICE-stop terms via
intraday_fills stop_mode='price', so the result maps directly to the live
STOP_LOSS_PCT knob. Outputs the price-stop SR landscape (portfolio), best-vs-3%
paired bootstrap (full window + 4 OOS splits), and per-coin attribution.

The stop optimum is invariant to the Kelly fraction (stop hits are
price-determined; only absolute SR scales), so kelly=0.5 here ports to the live
kelly=0.25 bot.

Usage:  python scripts/intraday_sl_axis_price.py
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

from scripts.baseline_v5_mix import COSTS, CORE_COINS  # noqa: E402
from scripts.bootstrap_hybrid import diff_sharpe_ci  # noqa: E402
from scripts.intraday_fills import run_coin_backtest_intrabar  # noqa: E402
from scripts.intraday_sltp_stats import _preload  # noqa: E402

SL_PRICE_GRID = [0.0, 0.015, 0.02, 0.03, 0.04, 0.05, 0.07, 0.10]
SPLITS = ["2024-07-15", "2024-10-15", "2025-01-15", "2025-04-15"]
LIVE_SL = 0.03  # current production price stop


def _ann_sr(r) -> float:
    r = np.asarray(r, dtype=float)
    sd = np.std(r, ddof=1) if len(r) > 1 else 0.0
    return float(np.mean(r) / sd * np.sqrt(252)) if sd > 0 else 0.0


def _coin_series_price(merged, imap, pos, sl) -> pd.Series:
    costs = dict(COSTS); costs["stop_loss"] = sl; costs["take_profit"] = 0.0
    eq, _ = run_coin_backtest_intrabar(
        dates=merged["date"].values, prices=merged["Close"].values, positions=pos,
        intraday=imap, initial_capital=10_000.0, trailing_stop=0.0,
        stop_mode="price", **costs)
    eq = np.asarray(eq, dtype=float)
    return pd.Series(eq[1:] / eq[:-1] - 1.0, index=pd.to_datetime(merged["date"].values[1:]))


def _portfolio_series_price(data, sl) -> pd.Series:
    rets = {c: _coin_series_price(m, im, p, sl) for c, (m, im, p) in data.items()}
    return pd.DataFrame(rets).dropna().mean(axis=1)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start", default="2021-11-07")
    ap.add_argument("--end", default="2026-04-15")
    ap.add_argument("--n-iter", type=int, default=5000)
    ap.add_argument("--block-size", type=int, default=21)
    ap.add_argument("--output", default="data/intraday_sltp_sweep/sl_axis_price.json")
    args = ap.parse_args()

    data = _preload(args.start, args.end)

    # Landscape + cache series.
    series = {}
    landscape = []
    for sl in SL_PRICE_GRID:
        s = _portfolio_series_price(data, sl); series[sl] = s
        landscape.append(dict(sl=sl, sharpe=_ann_sr(s.values)))

    # Best price-stop EXCLUDING the degenerate always-firing stop (0.0: any adverse
    # excursion triggers — NOT "no stop") which circuit-breaks.
    cand = max((c for c in landscape if c["sl"] > 0), key=lambda c: c["sharpe"])
    best_sl = cand["sl"]
    s_best, s_live = series[best_sl], series[LIVE_SL]

    def _pair(a, b):
        r = diff_sharpe_ci(np.asarray(a), np.asarray(b), n_iter=args.n_iter, block_size=args.block_size)
        return dict(sr_cand=_ann_sr(a), sr_base=_ann_sr(b), delta_sr=r["delta_sr_point"],
                    delta_sr_ci=r["delta_sr_ci"], p_cand_gt_base=1.0 - r["p_delta_le_0"])

    windows = {"full": _pair(s_best.values, s_live.values)}
    for sp in SPLITS:
        spt = pd.Timestamp(sp)
        windows[f"oos>={sp}"] = _pair(s_best[s_best.index >= spt].values, s_live[s_live.index >= spt].values)

    per_coin = {}
    for c, (m, im, p) in data.items():
        a = _coin_series_price(m, im, p, best_sl); b = _coin_series_price(m, im, p, LIVE_SL)
        r = diff_sharpe_ci(a.values, b.values, n_iter=args.n_iter, block_size=args.block_size)
        per_coin[c] = dict(sr_cand=_ann_sr(a), sr_base=_ann_sr(b), delta_sr=r["delta_sr_point"],
                           p_cand_gt_base=1.0 - r["p_delta_le_0"])

    n_split_ship = sum(1 for k, v in windows.items() if k != "full" and v["delta_sr_ci"][0] > 0)
    out = dict(
        stop_mode="price", window=[args.start, args.end], live_sl=LIVE_SL, best_sl=best_sl,
        sl_marginal_portfolio=landscape, best_vs_live_by_window=windows, per_coin=per_coin,
        n_oos_splits_ship=n_split_ship, n_oos_splits=len(SPLITS),
        recommendation=(
            f"Widen live STOP_LOSS_PCT 3% -> {best_sl:.0%} (price): full dSR "
            f"{windows['full']['delta_sr']:+.3f}, ships {n_split_ship}/{len(SPLITS)} OOS splits"
            if windows['full']['delta_sr_ci'][0] > 0 and n_split_ship >= 3 else
            f"Keep live STOP_LOSS_PCT at 3% (price): best price-stop {best_sl:.0%} not robustly "
            f"better (full dSR {windows['full']['delta_sr']:+.3f}, ships {n_split_ship}/{len(SPLITS)})"),
    )
    Path(PROJECT_ROOT / args.output).write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()

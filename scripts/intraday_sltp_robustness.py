#!/usr/bin/env python
"""Robustness probe for the intraday SL/TP sweep finding (SL=4%/TP=8% best cell).

Three complementary checks:
  1. Split-date sensitivity — IS-select best cell on 4 different IS/OOS boundaries,
     check OOS performance each time. Also checks seed stability on the 2025-04-15 split.
  2. Per-coin attribution — decompose the SL=4%/TP=8% benefit by coin.
  3. Neighborhood robustness — rank all 192 cells by full-window SR; check whether
     the top-10 form a ridge (TP benefit is broad) or a lone spike.

Usage:
    python scripts/intraday_sltp_robustness.py \\
        --start 2021-11-07 --end 2026-04-15 --n-iter 5000 --block-size 21
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

from scripts.intraday_sltp_stats import _preload, _portfolio_return_series  # noqa: E402
from scripts.intraday_sltp_sweep import SL_GRID, TP_GRID, TRAIL_GRID  # noqa: E402
from scripts.baseline_v5_mix import COSTS, CORE_COINS  # noqa: E402
from scripts.bootstrap_hybrid import diff_sharpe_ci  # noqa: E402


# ── helpers ──────────────────────────────────────────────────────────────────


def ann_sr(r) -> float:
    r = np.asarray(r, float)
    sd = np.std(r, ddof=1) if len(r) > 1 else 0
    return float(np.mean(r) / sd * np.sqrt(252)) if sd > 0 else 0.0


# ── checks ───────────────────────────────────────────────────────────────────


def check1_split_sensitivity(
    full_cache: dict[tuple, pd.Series],
    data: dict,
    base_series: pd.Series,
    splits: list[str],
    n_iter: int,
    block_size: int,
) -> list[dict]:
    """IS-select on each split, OOS-validate with block bootstrap."""
    results = []

    for split_str in splits:
        split = pd.Timestamp(split_str)

        # IS selection: best cell by in-sample SR
        best_is_cell = None
        best_is_sr = -1e9
        for (sl, tp, trail), series in full_cache.items():
            is_r = series[series.index < split].values
            sr = ann_sr(is_r)
            if sr > best_is_sr:
                best_is_sr = sr
                best_is_cell = (sl, tp, trail)

        sl_b, tp_b, trail_b = best_is_cell
        best_series = full_cache[best_is_cell]
        best_oos = best_series[best_series.index >= split].values
        base_oos = base_series[base_series.index >= split].values
        n_oos = int(len(best_oos))

        # Bootstrap with default seed=7
        ci7 = diff_sharpe_ci(best_oos, base_oos, n_iter=n_iter,
                             block_size=block_size, seed=7)
        ship = ci7["delta_sr_ci"][0] > 0

        rec: dict = {
            "split": split_str,
            "selected_cell": {"sl": sl_b, "tp": tp_b, "trail": trail_b},
            "is_sharpe": float(best_is_sr),
            "oos_best_sharpe": ann_sr(best_oos),
            "oos_3pct_sharpe": ann_sr(base_oos),
            "n_oos_bars": n_oos,
            "delta_sr_point": ci7["delta_sr_point"],
            "delta_sr_ci": ci7["delta_sr_ci"],
            "p_delta_le_0": ci7["p_delta_le_0"],
            "ship": bool(ship),
        }

        # Dual-seed stability check for the 2025-04-15 split only
        if split_str == "2025-04-15":
            ci123 = diff_sharpe_ci(best_oos, base_oos, n_iter=n_iter,
                                   block_size=block_size, seed=123)
            rec["seed7"] = {
                "delta_sr_point": ci7["delta_sr_point"],
                "delta_sr_ci": ci7["delta_sr_ci"],
                "p_delta_le_0": ci7["p_delta_le_0"],
            }
            rec["seed123"] = {
                "delta_sr_point": ci123["delta_sr_point"],
                "delta_sr_ci": ci123["delta_sr_ci"],
                "p_delta_le_0": ci123["p_delta_le_0"],
            }

        results.append(rec)
        print(
            f"  split={split_str}  cell=({sl_b:.2f},{tp_b:.2f},{trail_b:.2f})"
            f"  IS-SR={best_is_sr:+.3f}  OOS-best={ann_sr(best_oos):+.3f}"
            f"  OOS-3pct={ann_sr(base_oos):+.3f}  ΔSR={ci7['delta_sr_point']:+.3f}"
            f"  CI=[{ci7['delta_sr_ci'][0]:+.3f},{ci7['delta_sr_ci'][1]:+.3f}]"
            f"  p={ci7['p_delta_le_0']:.3f}  SHIP={ship}"
        )

    return results


def check2_per_coin(
    data: dict,
    sl_best: float, tp_best: float, trail_best: float,
    sl_base: float, tp_base: float, trail_base: float,
) -> dict:
    """Per-coin attribution: best cell vs baseline cell, full window."""
    results = {}
    for coin in CORE_COINS:
        coin_data = {coin: data[coin]}
        best_s = _portfolio_return_series(coin_data, sl_best, tp_best, trail_best)
        base_s = _portfolio_return_series(coin_data, sl_base, tp_base, trail_base)
        sr_best = ann_sr(best_s.values)
        sr_base = ann_sr(base_s.values)
        results[coin] = {
            "sr_best_cell": sr_best,
            "sr_base_cell": sr_base,
            "delta_sr": sr_best - sr_base,
        }
        print(
            f"  {coin:12s}  best={sr_best:+.3f}  base={sr_base:+.3f}"
            f"  delta={sr_best - sr_base:+.3f}"
        )
    return results


def check3_neighborhood(
    full_cache: dict[tuple, pd.Series],
    base_series: pd.Series,
    oos_start: str,
    top_n: int = 10,
) -> dict:
    """Rank all 192 cells by full-window SR; examine the top-10 neighborhood."""
    oos_split = pd.Timestamp(oos_start)

    # Full-window SR for every cell
    ranked = []
    for (sl, tp, trail), series in full_cache.items():
        fw_sr = ann_sr(series.values)
        oos_r = series[series.index >= oos_split].values
        oos_sr = ann_sr(oos_r)
        ranked.append({
            "sl": sl, "tp": tp, "trail": trail,
            "full_window_sharpe": fw_sr,
            "oos_sharpe": oos_sr,
        })

    ranked.sort(key=lambda x: x["full_window_sharpe"], reverse=True)
    top10 = ranked[:top_n]

    base_oos_sr = ann_sr(base_series[base_series.index >= oos_split].values)
    n_tp_positive = int(sum(1 for c in top10 if c["tp"] > 0))
    n_beat_base = int(sum(1 for c in top10 if c["oos_sharpe"] > base_oos_sr))

    print(f"  3%cell OOS SR = {base_oos_sr:+.3f}")
    print(f"  rank  (sl, tp, trail)         FW-SR   OOS-SR  beat3pct")
    for i, c in enumerate(top10):
        beat = "YES" if c["oos_sharpe"] > base_oos_sr else "no"
        print(
            f"  #{i+1:2d}   ({c['sl']:.2f},{c['tp']:.2f},{c['trail']:.2f})"
            f"  {c['full_window_sharpe']:+.3f}  {c['oos_sharpe']:+.3f}  {beat}"
        )
    print(f"  tp>0 in top-10: {n_tp_positive}/10   beat 3% OOS: {n_beat_base}/10")

    return {
        "oos_start": oos_start,
        "base_oos_sharpe": base_oos_sr,
        "top10": top10,
        "n_tp_positive_in_top10": n_tp_positive,
        "n_beat_3pct_oos": n_beat_base,
    }


# ── main ─────────────────────────────────────────────────────────────────────


def main():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--start", default="2021-11-07")
    p.add_argument("--end", default="2026-04-15")
    p.add_argument("--n-iter", type=int, default=5000)
    p.add_argument("--block-size", type=int, default=21)
    args = p.parse_args()

    out_dir = PROJECT_ROOT / "data" / "intraday_sltp_sweep"
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── 1. Preload ONCE ──────────────────────────────────────────────────────
    print("\n[preload] loading per-coin data (merged, intraday_map, positions)...")
    data = _preload(args.start, args.end, kelly=0.5)
    print(f"  Loaded {len(data)} coins.")

    # ── 2. Compute all 192 return series ONCE ────────────────────────────────
    print(f"\n[cache] computing {len(SL_GRID)*len(TP_GRID)*len(TRAIL_GRID)} return series...")
    full_cache: dict[tuple, pd.Series] = {}
    total = len(SL_GRID) * len(TP_GRID) * len(TRAIL_GRID)
    i = 0
    for sl in SL_GRID:
        for tp in TP_GRID:
            for trail in TRAIL_GRID:
                i += 1
                full_cache[(sl, tp, trail)] = _portfolio_return_series(data, sl, tp, trail)
                if i % 20 == 0 or i == total:
                    print(f"  {i}/{total} cells done...")

    # Baseline (3% cell)
    base_series = full_cache[(COSTS["stop_loss"], 0.0, 0.0)]
    best_cell = (0.04, 0.08, 0.0)  # SL=4%/TP=8%/trail=0 — the finding under test

    # ── Check 1: Split-date sensitivity ─────────────────────────────────────
    print("\n[Check 1] split-date sensitivity")
    splits = ["2024-07-15", "2024-10-15", "2025-01-15", "2025-04-15"]
    c1 = check1_split_sensitivity(
        full_cache, data, base_series, splits, args.n_iter, args.block_size
    )

    # ── Check 2: Per-coin attribution ────────────────────────────────────────
    print("\n[Check 2] per-coin attribution (SL=4%/TP=8%/trail=0 vs SL=3%/TP=0/trail=0)")
    c2 = check2_per_coin(
        data,
        sl_best=0.04, tp_best=0.08, trail_best=0.0,
        sl_base=COSTS["stop_loss"], tp_base=0.0, trail_base=0.0,
    )

    # ── Check 3: Neighborhood robustness ────────────────────────────────────
    print("\n[Check 3] neighborhood — top-10 cells (full-window IS rank) + OOS 2025-04-15")
    c3 = check3_neighborhood(full_cache, base_series, oos_start="2025-04-15", top_n=10)

    # ── Write output ─────────────────────────────────────────────────────────
    out = {
        "config": {
            "start": args.start,
            "end": args.end,
            "n_iter": args.n_iter,
            "block_size": args.block_size,
            "baseline_cell": {"sl": COSTS["stop_loss"], "tp": 0.0, "trail": 0.0},
            "finding_cell": {"sl": 0.04, "tp": 0.08, "trail": 0.0},
        },
        "check1_split_sensitivity": c1,
        "check2_per_coin": c2,
        "check3_neighborhood": c3,
    }
    out_path = out_dir / "robustness.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))

    # ── Human summary ────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("ROBUSTNESS PROBE SUMMARY")
    print("=" * 70)

    # Check 1 summary
    n_ship = sum(1 for r in c1 if r["ship"])
    print(f"\nCheck 1 — split-date sensitivity ({len(splits)} splits):")
    for r in c1:
        tag = "SHIP" if r["ship"] else "FAIL"
        print(
            f"  {r['split']}  cell=({r['selected_cell']['sl']:.2f},{r['selected_cell']['tp']:.2f},"
            f"{r['selected_cell']['trail']:.2f})"
            f"  OOS-ΔSR={r['delta_sr_point']:+.3f}"
            f"  CI=[{r['delta_sr_ci'][0]:+.3f},{r['delta_sr_ci'][1]:+.3f}]"
            f"  p={r['p_delta_le_0']:.3f}  [{tag}]"
        )
    # Seed stability for 2025-04-15
    r_2504 = next(r for r in c1 if r["split"] == "2025-04-15")
    if "seed7" in r_2504 and "seed123" in r_2504:
        print(f"\n  Seed stability (2025-04-15 split):")
        print(f"    seed=7  : p={r_2504['seed7']['p_delta_le_0']:.4f}  "
              f"CI={r_2504['seed7']['delta_sr_ci']}")
        print(f"    seed=123: p={r_2504['seed123']['p_delta_le_0']:.4f}  "
              f"CI={r_2504['seed123']['delta_sr_ci']}")

    # Check 2 summary
    print(f"\nCheck 2 — per-coin attribution (SL=4%/TP=8% vs SL=3%/no-TP):")
    for coin, v in c2.items():
        print(f"  {coin:12s}  delta={v['delta_sr']:+.3f}  "
              f"(best={v['sr_best_cell']:+.3f}, base={v['sr_base_cell']:+.3f})")
    deltas = [v["delta_sr"] for v in c2.values()]
    n_positive = sum(1 for d in deltas if d > 0)
    print(f"  {n_positive}/{len(deltas)} coins benefit from TP=8%")

    # Check 3 summary
    print(f"\nCheck 3 — top-10 neighborhood:")
    print(f"  TP>0 cells in top-10: {c3['n_tp_positive_in_top10']}/10")
    print(f"  Beat 3% OOS: {c3['n_beat_3pct_oos']}/10")

    print(f"\nOutput written to: {out_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()

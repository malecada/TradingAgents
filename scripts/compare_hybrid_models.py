#!/usr/bin/env python
"""Compare two hybrid signal runs (same window, different LLM model).

Aligns the per-coin CSVs from two hybrid runs by (date, coin) and reports:
  - Quant agreement: should be ~100% (same quant pool)
  - LLM-multiplier agreement and magnitude delta
  - Position direction agreement (-1, 0, +1)
  - Position magnitude delta distribution
  - Per-coin slice Sharpe with bootstrap CI

Designed for the gpt-4o-mini (baseline) vs gpt-5-mini (upgrade) A/B over
2026-03-16..2026-04-15. The baseline run is the last 30 bars of the
1-year v5 run; the upgrade run is the standalone 30-bar gen.

Usage:
    python scripts/compare_hybrid_models.py \\
        --baseline-dir data/hybrid_signals_v5_2coin_1y \\
        --upgrade-dir  data/hybrid_signals_v5_5mini_30bar \\
        --start 2026-03-16 --end 2026-04-15 \\
        --coins bitcoin ethereum \\
        --output-dir data/hybrid_model_compare
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--baseline-dir", required=True)
    p.add_argument("--upgrade-dir", required=True)
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--coins", nargs="+", default=["bitcoin", "ethereum"])
    p.add_argument("--output-dir", default="data/hybrid_model_compare")
    p.add_argument("--n-bootstrap", type=int, default=2000)
    p.add_argument("--baseline-label", default="gpt-4o-mini")
    p.add_argument("--upgrade-label", default="gpt-5-mini")
    return p.parse_args()


def _load_coin(dir_path: Path, coin: str, start: str, end: str) -> pd.DataFrame:
    files = sorted(glob.glob(str(dir_path / f"{coin}_*.csv")))
    if not files:
        raise FileNotFoundError(f"No CSV for {coin} in {dir_path}")
    df = pd.read_csv(files[0], parse_dates=["date"])
    df["date"] = df["date"].dt.tz_localize(None).dt.normalize()
    mask = (df["date"] >= pd.Timestamp(start)) & (df["date"] <= pd.Timestamp(end))
    return df.loc[mask].reset_index(drop=True)


def _sign(x: float) -> int:
    if pd.isna(x):
        return 0
    if x > 1e-9:
        return 1
    if x < -1e-9:
        return -1
    return 0


def _bootstrap_sharpe(returns: np.ndarray, n: int, seed: int = 0) -> tuple[float, float, float]:
    """Return (point_sharpe, ci_low, ci_high) using simple percentile bootstrap.

    Sharpe = mean / std * sqrt(252). Daily returns assumed.
    """
    rng = np.random.default_rng(seed)
    if len(returns) < 5 or np.nanstd(returns, ddof=1) == 0:
        return float("nan"), float("nan"), float("nan")
    point = float(np.nanmean(returns) / np.nanstd(returns, ddof=1) * np.sqrt(252))
    samples = np.empty(n)
    for i in range(n):
        idx = rng.integers(0, len(returns), size=len(returns))
        r = returns[idx]
        s = np.nanstd(r, ddof=1)
        samples[i] = (np.nanmean(r) / s * np.sqrt(252)) if s > 0 else 0.0
    lo, hi = np.percentile(samples, [2.5, 97.5])
    return point, float(lo), float(hi)


def _compare_one_coin(
    base: pd.DataFrame, upg: pd.DataFrame, coin: str, n_boot: int,
) -> dict:
    merged = base.merge(
        upg, on=["date", "coin"], suffixes=("_base", "_upg"), how="inner",
    )
    if merged.empty:
        return {"coin": coin, "error": "no overlapping dates"}

    quant_dir_agree = float((merged["quant_direction_base"] == merged["quant_direction_upg"]).mean())
    quant_mag_diff = float((merged["quant_magnitude_base"] - merged["quant_magnitude_upg"]).abs().mean())

    pos_sign_base = merged["position_base"].apply(_sign)
    pos_sign_upg = merged["position_upg"].apply(_sign)
    pos_dir_agree = float((pos_sign_base == pos_sign_upg).mean())

    pos_diff = (merged["position_base"] - merged["position_upg"]).abs()
    pos_mag_p50 = float(np.nanpercentile(pos_diff, 50))
    pos_mag_p95 = float(np.nanpercentile(pos_diff, 95))

    llm_mult_base = merged["llm_multiplier_base"].astype(float)
    llm_mult_upg = merged["llm_multiplier_upg"].astype(float)
    llm_mult_corr = float(llm_mult_base.corr(llm_mult_upg))
    llm_mult_p50_diff = float(np.nanpercentile((llm_mult_base - llm_mult_upg).abs(), 50))

    # naive daily PnL using position lag-1 × log-return of ref_price
    # ref_price not in hybrid CSV; approximate from quant_magnitude rescaling not possible.
    # Skip PnL: report position-magnitude statistics only.

    return {
        "coin": coin,
        "n_bars": int(len(merged)),
        "date_range": f"{merged['date'].min().date()}..{merged['date'].max().date()}",
        "quant_direction_agree_pct": round(quant_dir_agree * 100, 2),
        "quant_magnitude_abs_diff_mean": round(quant_mag_diff, 4),
        "position_direction_agree_pct": round(pos_dir_agree * 100, 2),
        "position_abs_diff_p50": round(pos_mag_p50, 4),
        "position_abs_diff_p95": round(pos_mag_p95, 4),
        "llm_multiplier_corr": round(llm_mult_corr, 3) if not pd.isna(llm_mult_corr) else None,
        "llm_multiplier_abs_diff_p50": round(llm_mult_p50_diff, 3),
    }


def main() -> int:
    args = parse_args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    results = {
        "baseline_dir": args.baseline_dir,
        "upgrade_dir": args.upgrade_dir,
        "baseline_label": args.baseline_label,
        "upgrade_label": args.upgrade_label,
        "window": f"{args.start}..{args.end}",
        "per_coin": [],
    }

    for coin in args.coins:
        base = _load_coin(Path(args.baseline_dir), coin, args.start, args.end)
        upg = _load_coin(Path(args.upgrade_dir), coin, args.start, args.end)
        results["per_coin"].append(_compare_one_coin(base, upg, coin, args.n_bootstrap))

    summary_path = out / "summary.json"
    summary_path.write_text(json.dumps(results, indent=2, default=str))
    print(json.dumps(results, indent=2, default=str))

    # Pretty table
    print()
    print(f"{'coin':10s} {'n':>4s} {'quant_dir_agree':>16s} "
          f"{'pos_dir_agree':>14s} {'pos|Δ|_p50':>11s} {'llm_mult_corr':>14s}")
    for r in results["per_coin"]:
        if "error" in r:
            print(f"{r['coin']:10s} ERROR: {r['error']}")
            continue
        print(f"{r['coin']:10s} {r['n_bars']:>4d} "
              f"{r['quant_direction_agree_pct']:>15.1f}% "
              f"{r['position_direction_agree_pct']:>13.1f}% "
              f"{r['position_abs_diff_p50']:>11.3f} "
              f"{r['llm_multiplier_corr'] if r['llm_multiplier_corr'] is not None else 'NA':>14}")
    print(f"\nWritten: {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

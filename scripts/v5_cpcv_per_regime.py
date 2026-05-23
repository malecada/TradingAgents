#!/usr/bin/env python
"""V5 MIX per-regime CPCV breakdown.

Extends the §21.5 CPCV (100% folds SR>2, PBO 0.000) with regime-conditional
slicing. Each of the 28 test folds is classified by its dominant heuristic
regime (computed on BTC prices over the fold window), then fold Sharpes are
aggregated per regime class.

Tests whether V5 MIX positive performance is uniform across regimes or
concentrated in a particular regime cluster.

Outputs:
  data/v5_validation/per_regime_cpcv.json   — per-regime fold aggregates
  data/v5_validation/per_regime_cpcv.csv    — long-format fold-level detail
  stdout                                    — formatted tables

Usage:
    python scripts/v5_cpcv_per_regime.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.baseline_v5_mix import (  # noqa: E402
    ANN, DEFAULT_ROUTING,
)
from tradingagents.dataflows.coingecko_binance import _load_crypto_ohlcv  # noqa: E402
from tradingagents.strategies.v3.backtest.cpcv import cpcv_splits  # noqa: E402
from tradingagents.strategies.v3.regime.hmm_v2 import heuristic_label  # noqa: E402

START, END = "2021-11-07", "2026-04-15"


def _sharpe(r: np.ndarray) -> float:
    s = r.std()
    return float(r.mean() / s * ANN) if s > 0 else 0.0


def _load_portfolio_returns() -> pd.Series:
    """Load the canonical V5 MIX portfolio daily-return series."""
    path = PROJECT_ROOT / "data" / "v5_mix_production" / "daily_returns.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found — run scripts/baseline_v5_mix.py first"
        )
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    return df["portfolio"]


def _btc_regime_per_day(end: str) -> pd.Series:
    """Heuristic regime label per trading day using BTC prices as market proxy."""
    ohlcv = _load_crypto_ohlcv("bitcoin", end)
    ohlcv["Date"] = pd.to_datetime(ohlcv["Date"]).dt.tz_localize(None).dt.normalize()
    prices = ohlcv.set_index("Date").sort_index()["Close"]
    labels: dict[pd.Timestamp, str] = {}
    for d in prices.index:
        sub = prices[prices.index <= d]
        labels[d] = "sideways" if len(sub) < 30 else heuristic_label(sub)[0]
    return pd.Series(labels)


def _dominant_regime(fold_dates: pd.DatetimeIndex,
                     regime_series: pd.Series) -> tuple[str, float]:
    """Return (regime_label, share) for the dominant regime over the fold."""
    aligned = regime_series.reindex(fold_dates, method="ffill").dropna()
    if len(aligned) == 0:
        return "unknown", 0.0
    counts = Counter(aligned.values)
    regime, count = counts.most_common(1)[0]
    return regime, count / len(aligned)


def main() -> None:
    out_dir = PROJECT_ROOT / "data" / "v5_validation"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'=' * 84}")
    print(f"  V5 MIX — Per-regime CPCV breakdown")
    print(f"  window: {START} → {END}")
    print(f"{'=' * 84}\n")

    port = _load_portfolio_returns()
    port = port[(port.index >= START) & (port.index <= END)]
    print(f"  Loaded portfolio: {len(port)} bars from {port.index.min().date()} "
          f"to {port.index.max().date()}")

    btc_regime = _btc_regime_per_day(END)
    print(f"  BTC regime labels: {len(btc_regime)} bars; "
          f"distribution: {dict(Counter(btc_regime.values))}")

    # Build CPCV splits identical to §21.5
    port_arr = port.values
    n = len(port_arr)
    splits = list(cpcv_splits(
        n_samples=n, n_groups=8, test_groups=2, embargo=14, min_train=252,
    ))

    rows: list[dict] = []
    print(f"\n  Per-fold detail ({len(splits)} folds):")
    print(f"  {'fold':>4}  {'n_bars':>6}  {'start':<12} {'end':<12}  "
          f"{'regime':<9} {'share':>6}  {'SR':>8}  {'ret':>8}")
    print(f"  {'-' * 78}")
    for idx, sp in enumerate(splits):
        test_idx = sp.test_idx
        if len(test_idx) < 2:
            continue
        test_dates = port.index[test_idx]
        test_r = port_arr[test_idx]
        sr = _sharpe(test_r)
        regime, share = _dominant_regime(test_dates, btc_regime)
        total_ret = float((1 + pd.Series(test_r)).prod() - 1)
        rows.append({
            "fold": idx, "n_bars": int(len(test_r)),
            "start": str(test_dates.min().date()),
            "end": str(test_dates.max().date()),
            "dominant_regime": regime, "regime_share": float(share),
            "sharpe": sr, "total_ret": total_ret,
        })
        print(f"  {idx:>4}  {len(test_r):>6}  {test_dates.min().date()!s:<12} "
              f"{test_dates.max().date()!s:<12}  "
              f"{regime:<9} {share:>6.2f}  {sr:>+8.3f}  {total_ret:>+8.1%}")

    df = pd.DataFrame(rows)
    df.to_csv(out_dir / "per_regime_cpcv.csv", index=False)

    # ── Per-regime aggregates ──
    print(f"\n  {'=' * 78}")
    print(f"  Per-regime aggregates (folds classified by dominant BTC regime):")
    print(f"  {'=' * 78}")
    print(f"  {'regime':<10} {'n_folds':>8}  {'mean_SR':>8}  {'median_SR':>10}  "
          f"{'min_SR':>8}  {'max_SR':>8}  {'SR>0':>5}  {'SR>2':>5}")
    print(f"  {'-' * 78}")

    regime_summary: dict[str, dict] = {}
    for regime in ("bull", "sideways", "bear"):
        sub = df[df["dominant_regime"] == regime]
        if len(sub) == 0:
            continue
        srs = sub["sharpe"].values
        regime_summary[regime] = {
            "n_folds": int(len(sub)),
            "mean_sr": float(srs.mean()),
            "median_sr": float(np.median(srs)),
            "std_sr": float(srs.std(ddof=1)) if len(srs) > 1 else 0.0,
            "min_sr": float(srs.min()),
            "max_sr": float(srs.max()),
            "frac_sr_gt_0": float((srs > 0).mean()),
            "frac_sr_gt_1": float((srs > 1).mean()),
            "frac_sr_gt_2": float((srs > 2).mean()),
            "mean_total_ret": float(sub["total_ret"].mean()),
        }
        print(f"  {regime:<10} {len(sub):>8}  {srs.mean():>+8.3f}  "
              f"{np.median(srs):>+10.3f}  "
              f"{srs.min():>+8.3f}  {srs.max():>+8.3f}  "
              f"{(srs > 0).mean() * 100:>4.0f}%  "
              f"{(srs > 2).mean() * 100:>4.0f}%")

    # ── Headline reproduction (§21.5 reference) ──
    all_srs = df["sharpe"].values
    overall = {
        "n_folds": int(len(all_srs)),
        "mean_sr": float(all_srs.mean()),
        "median_sr": float(np.median(all_srs)),
        "std_sr": float(all_srs.std(ddof=1)),
        "min_sr": float(all_srs.min()),
        "max_sr": float(all_srs.max()),
        "frac_sr_gt_0": float((all_srs > 0).mean()),
        "frac_sr_gt_2": float((all_srs > 2).mean()),
    }
    print(f"\n  Overall (matches §21.5 reproduction):")
    print(f"    mean={overall['mean_sr']:+.3f}  median={overall['median_sr']:+.3f}  "
          f"std={overall['std_sr']:.3f}  "
          f"min={overall['min_sr']:+.3f}  max={overall['max_sr']:+.3f}")
    print(f"    %SR>0={overall['frac_sr_gt_0'] * 100:.0f}%  "
          f"%SR>2={overall['frac_sr_gt_2'] * 100:.0f}%")

    summary = {
        "window": {"start": START, "end": END},
        "cpcv_params": {
            "n_groups": 8, "test_groups": 2, "embargo": 14, "min_train": 252,
        },
        "overall": overall,
        "per_regime": regime_summary,
        "regime_distribution_all_bars": dict(Counter(btc_regime.values)),
    }
    with open(out_dir / "per_regime_cpcv.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"\n  Wrote: {out_dir / 'per_regime_cpcv.csv'}")
    print(f"  Wrote: {out_dir / 'per_regime_cpcv.json'}")


if __name__ == "__main__":
    main()

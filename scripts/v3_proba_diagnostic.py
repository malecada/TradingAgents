#!/usr/bin/env python
"""V3 LGB probability diagnostic — raw vs isotonic-calibrated.

Replays the V3 model state on the 88-bar window (2026-01-16 → 2026-04-15) for
BTC. Compares raw ensemble probabilities (from the nocalib checkpoint) against
isotonic-calibrated probabilities (from the canonical checkpoint).

This produces F-4.4.3 of THESIS_FIGURES_PLAN.md — the calibration-collapse
visualisation that was previously missing from the figure set.

Outputs:
  data/figures/F-4.4.3-v3-calibration-collapse.{png,svg}
  data/diagnostics/v3_proba_diagnostic_btc.csv

Usage:
    python scripts/v3_proba_diagnostic.py
"""

from __future__ import annotations

import pickle
import sys
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", message="Trying to unpickle")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.dataflows.coingecko_binance import _load_crypto_ohlcv  # noqa
from tradingagents.strategies.v3.backtest.runner_v3 import build_global_features  # noqa

START, END = pd.Timestamp("2026-01-16"), pd.Timestamp("2026-04-15")
COIN = "bitcoin"

FIG_DIR = PROJECT_ROOT / "data" / "figures"
DIAG_DIR = PROJECT_ROOT / "data" / "diagnostics"
FIG_DIR.mkdir(parents=True, exist_ok=True)
DIAG_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "figure.dpi": 100, "savefig.dpi": 300, "savefig.bbox": "tight",
    "font.family": "DejaVu Serif", "font.size": 10,
    "axes.titlesize": 11, "axes.labelsize": 10,
    "axes.grid": True, "grid.alpha": 0.3, "legend.fontsize": 9,
    "legend.frameon": False,
})


def _build_features() -> pd.DataFrame:
    """Build the V3 9-column feature matrix over full BTC history."""
    ohlcv = _load_crypto_ohlcv(COIN, str(END.date()))
    ohlcv["Date"] = pd.to_datetime(ohlcv["Date"]).dt.tz_localize(None).dt.normalize()
    prices = ohlcv.set_index("Date")["Close"].astype(float).sort_index()

    micro = pd.read_parquet(PROJECT_ROOT / "data" / "microstructure" / f"{COIN}.parquet")
    micro.index = pd.to_datetime(micro.index).tz_localize(None).normalize()
    deriv = pd.read_parquet(PROJECT_ROOT / "data" / "derivatives" / f"{COIN}.parquet")
    deriv.index = pd.to_datetime(deriv.index).tz_localize(None).normalize()

    feats = build_global_features(prices, micro, deriv)
    return feats


def main() -> None:
    print("\n" + "=" * 78)
    print("  V3 LGB probability diagnostic — BTC, 88-bar window (2026-01-16 → 2026-04-15)")
    print("=" * 78 + "\n")

    feats = _build_features()
    window_mask = (feats.index >= START) & (feats.index <= END)
    feats_window = feats.loc[window_mask]
    print(f"  Feature matrix: {feats_window.shape} (88 bars × 9 features expected)")
    print(f"  Columns: {list(feats_window.columns)}")

    with open(PROJECT_ROOT / "data/checkpoints/v3_models_bitcoin.pkl", "rb") as f:
        canon = pickle.load(f)
    with open(PROJECT_ROOT / "data/checkpoints/v3_models_nocalib_bitcoin.pkl", "rb") as f:
        nocal = pickle.load(f)
    print(f"  Loaded canonical (calibrated) + nocalib (raw) checkpoints")

    probas_canon = canon.predict_proba(feats_window)
    probas_nocal = nocal.predict_proba(feats_window)
    horizons = sorted(probas_canon.keys())
    print(f"  Horizons: {horizons}")

    rows = []
    for h in horizons:
        for kind, arr in (("calibrated", probas_canon[h]),
                          ("raw", probas_nocal[h])):
            for d, p in zip(feats_window.index, arr):
                rows.append({"date": d, "horizon": h, "kind": kind, "proba": p})
    df = pd.DataFrame(rows)
    df.to_csv(DIAG_DIR / "v3_proba_diagnostic_btc.csv", index=False)
    print(f"  Wrote: {DIAG_DIR / 'v3_proba_diagnostic_btc.csv'}")

    print(f"\n  Summary statistics:\n")
    print(f"  {'horizon':>7}  {'kind':<11}  {'median':>7}  {'std':>7}  "
          f"{'pct_bullish':>11}  {'min':>6}  {'max':>6}")
    print(f"  {'-' * 72}")
    summary = []
    for h in horizons:
        for kind in ("calibrated", "raw"):
            sub = df[(df["horizon"] == h) & (df["kind"] == kind)]["proba"]
            row = {
                "horizon": h, "kind": kind,
                "median": float(sub.median()), "std": float(sub.std()),
                "pct_up": float((sub > 0.5).mean()),
                "min": float(sub.min()), "max": float(sub.max()),
            }
            summary.append(row)
            print(f"  {h:>7}  {kind:<11}  {row['median']:>7.4f}  "
                  f"{row['std']:>7.4f}  {row['pct_up']*100:>10.1f}%  "
                  f"{row['min']:>6.3f}  {row['max']:>6.3f}")

    # ── Paired histogram plot ──
    fig, axes = plt.subplots(2, 4, figsize=(14, 6.5), sharex=False)
    fig.suptitle("F-4.4.3  V3 LGB probability distribution — BTC, 88-bar window "
                 "(2026-01-16 → 2026-04-15)\n"
                 "Top row: raw ensemble probabilities (nocalib checkpoint).  "
                 "Bottom row: after isotonic calibration (canonical checkpoint).",
                 fontsize=11)

    for col, h in enumerate(horizons):
        for row_idx, (kind, color) in enumerate(
            (("raw", "#1F77B4"), ("calibrated", "#D62728"))
        ):
            ax = axes[row_idx, col]
            sub = df[(df["horizon"] == h) & (df["kind"] == kind)]["proba"]
            ax.hist(sub.values, bins=20, range=(0.30, 0.85),
                    color=color, alpha=0.75, edgecolor="white")
            ax.axvline(0.5, color="black", linestyle="--", linewidth=0.8)
            med, std = sub.median(), sub.std()
            pct_up = (sub > 0.5).mean() * 100
            ax.text(0.97, 0.95,
                    f"median={med:.3f}\nstd={std:.3f}\n%bullish={pct_up:.0f}%",
                    transform=ax.transAxes, ha="right", va="top", fontsize=8.5,
                    bbox=dict(boxstyle="round", facecolor="white",
                              edgecolor="gray", alpha=0.85))
            ax.set_title(f"h={h}  ({kind})", fontsize=10)
            ax.set_xlim(0.30, 0.85)
            ax.set_xlabel("P(up) probability" if row_idx == 1 else "")
            ax.set_ylabel("Frequency" if col == 0 else "")

    fig.tight_layout(rect=[0, 0, 1, 0.93])
    for ext in ("png", "svg"):
        out = FIG_DIR / f"F-4.4.3-v3-calibration-collapse.{ext}"
        fig.savefig(out, format=ext)
        print(f"\n  wrote {out}")
    plt.close(fig)

    print(f"\n{'=' * 78}\n")


if __name__ == "__main__":
    main()

"""Compare real VPIN (aggTrades) vs klines-proxy microstructure features.

Reads data/microstructure/{coin}.parquet (proxy) and
data/microstructure_real/{coin}.parquet (real aggTrades VPIN) for the
88-bar eval window 2026-01-16 → 2026-04-15, then prints detailed
summary statistics and correlation analysis.

Usage:
    python scripts/compare_vpin_proxy_vs_real.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

WORKTREE = Path(__file__).parent.parent
PROXY_DIR = WORKTREE / "data" / "microstructure"
REAL_DIR = WORKTREE / "data" / "microstructure_real"

EVAL_START = "2026-01-16"
EVAL_END = "2026-04-15"

COINS = ["bitcoin", "ethereum"]


def window(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    idx = df.index
    if hasattr(idx, "tz") and idx.tz is not None:
        start_ts = pd.Timestamp(start, tz="UTC")
        end_ts = pd.Timestamp(end, tz="UTC")
    else:
        start_ts = pd.Timestamp(start)
        end_ts = pd.Timestamp(end)
    return df[(idx >= start_ts) & (idx <= end_ts)]


def describe_col(series: pd.Series) -> dict:
    return {
        "count": int(series.count()),
        "mean": float(series.mean()),
        "std": float(series.std()),
        "min": float(series.min()),
        "p25": float(series.quantile(0.25)),
        "median": float(series.median()),
        "p75": float(series.quantile(0.75)),
        "max": float(series.max()),
    }


def main() -> None:
    results: dict = {}

    for coin in COINS:
        proxy_file = PROXY_DIR / f"{coin}.parquet"
        real_file = REAL_DIR / f"{coin}.parquet"

        if not proxy_file.exists():
            print(f"[{coin}] Proxy file not found: {proxy_file}")
            continue
        if not real_file.exists():
            print(f"[{coin}] Real VPIN file not found: {real_file}")
            continue

        proxy = window(pd.read_parquet(proxy_file), EVAL_START, EVAL_END)
        real = window(pd.read_parquet(real_file), EVAL_START, EVAL_END)

        print(f"\n{'='*60}")
        print(f"  {coin.upper()}  —  Eval window: {EVAL_START} → {EVAL_END}")
        print(f"{'='*60}")
        print(f"  Proxy rows: {len(proxy)},  columns: {list(proxy.columns)}")
        print(f"  Real rows:  {len(real)},  columns: {list(real.columns)}")

        print("\n--- PROXY microstructure ---")
        print(proxy.describe().to_string())

        print("\n--- REAL aggTrades VPIN ---")
        print(real.describe().to_string())

        # OFI comparison (ofi_proxy ↔ ofi_d; both are daily OFI in [-1, +1] space)
        print("\n--- OFI comparison (proxy ofi_proxy_w vs real ofi_d_w) ---")
        if "ofi_proxy_w" in proxy.columns and "ofi_d_w" in real.columns:
            aligned = pd.DataFrame(
                {"proxy_ofi_w": proxy["ofi_proxy_w"], "real_ofi_d_w": real["ofi_d_w"]}
            ).dropna()
            if len(aligned) >= 2:
                corr = aligned.corr().iloc[0, 1]
                sign_agree = (
                    np.sign(aligned["proxy_ofi_w"]) == np.sign(aligned["real_ofi_d_w"])
                ).mean()
                print(f"  Pearson r:   {corr:.4f}")
                print(f"  Sign agree:  {sign_agree:.2%}")
                print(f"  Proxy mean:  {aligned['proxy_ofi_w'].mean():.4f}")
                print(f"  Real mean:   {aligned['real_ofi_d_w'].mean():.4f}")
                print(f"  Proxy std:   {aligned['proxy_ofi_w'].std():.4f}")
                print(f"  Real std:    {aligned['real_ofi_d_w'].std():.4f}")

        # VPIN stats
        if "vpin_50" in real.columns:
            vpin = real["vpin_50"]
            print(f"\n--- REAL VPIN_50 distribution ---")
            print(f"  mean  = {vpin.mean():.4f}")
            print(f"  std   = {vpin.std():.4f}")
            print(f"  min   = {vpin.min():.4f}")
            print(f"  p25   = {vpin.quantile(0.25):.4f}")
            print(f"  p50   = {vpin.quantile(0.50):.4f}")
            print(f"  p75   = {vpin.quantile(0.75):.4f}")
            print(f"  max   = {vpin.max():.4f}")

        # Vol dispersion vs VPIN_50 as "information asymmetry proxy" comparison
        if "vol_dispersion" in proxy.columns and "vpin_50" in real.columns:
            aligned2 = pd.DataFrame(
                {"vol_disp": proxy["vol_dispersion"], "vpin": real["vpin_50"]}
            ).dropna()
            if len(aligned2) >= 2:
                corr2 = aligned2.corr().iloc[0, 1]
                print(f"\n--- vol_dispersion (proxy) vs vpin_50 (real) ---")
                print(f"  Pearson r:  {corr2:.4f}  (expected positive; both proxy stress)")
                print(f"  proxy vol_dispersion mean: {aligned2['vol_disp'].mean():.4f}")
                print(f"  real vpin_50 mean:         {aligned2['vpin'].mean():.4f}")

        results[coin] = {
            "proxy_rows": len(proxy),
            "real_rows": len(real),
            "proxy_cols": list(proxy.columns),
            "real_cols": list(real.columns),
            "proxy_stats": {c: describe_col(proxy[c]) for c in proxy.columns},
            "real_stats": {c: describe_col(real[c]) for c in real.columns},
        }
        if "ofi_proxy_w" in proxy.columns and "ofi_d_w" in real.columns:
            aligned = pd.DataFrame(
                {"proxy_ofi_w": proxy["ofi_proxy_w"], "real_ofi_d_w": real["ofi_d_w"]}
            ).dropna()
            if len(aligned) >= 2:
                results[coin]["ofi_correlation"] = float(aligned.corr().iloc[0, 1])
                results[coin]["ofi_sign_agree"] = float(
                    (
                        np.sign(aligned["proxy_ofi_w"]) == np.sign(aligned["real_ofi_d_w"])
                    ).mean()
                )

    out_file = WORKTREE / "data" / "microstructure_real" / "comparison_stats.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n\nStats saved to {out_file}")


if __name__ == "__main__":
    main()

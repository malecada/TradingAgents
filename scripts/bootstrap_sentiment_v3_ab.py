"""Paired bootstrap 10k CI for sentiment v3 A/B (BTC + ETH, 90 bars).

For each (coin, variant_pair):
    - resample bar indices with replacement
    - compute SR_var1 - SR_var2 on resample
    - 10000 iterations
    - report mean, 95% CI, P(diff > 0)
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/tmp/v3ab")
VARIANTS = ["A_pure_quant", "B_legacy_sentiment", "C_v3_features_only", "D_v3_full"]
COINS = ["bitcoin", "ethereum"]
N_BOOT = 10_000
ANN = 365.0
SEED = 2026


def sharpe(rets: np.ndarray) -> float:
    if rets.size == 0 or rets.std(ddof=0) == 0:
        return 0.0
    return float(rets.mean() / rets.std(ddof=0) * np.sqrt(ANN))


def paired_bootstrap(a: np.ndarray, b: np.ndarray, n_boot: int = N_BOOT) -> dict:
    rng = np.random.default_rng(SEED)
    diffs = np.empty(n_boot, dtype=np.float64)
    n = len(a)
    for i in range(n_boot):
        idx = rng.integers(0, n, n)
        diffs[i] = sharpe(a[idx]) - sharpe(b[idx])
    return {
        "delta_mean": float(diffs.mean()),
        "ci_lo_95": float(np.quantile(diffs, 0.025)),
        "ci_hi_95": float(np.quantile(diffs, 0.975)),
        "p_positive": float((diffs > 0).mean()),
    }


def load(variant: str, coin: str) -> np.ndarray:
    df = pd.read_csv(ROOT / variant / f"{coin}.csv")
    return df["hybrid_ret"].to_numpy(dtype=np.float64)


def main():
    sr_table = {v: {} for v in VARIANTS}
    for v in VARIANTS:
        for c in COINS:
            r = load(v, c)
            sr_table[v][c] = sharpe(r)

    print("=" * 88)
    print("SR TABLE (point estimate, 90 bars 2026-01-16 → 2026-04-15)")
    print("=" * 88)
    print(f"{'variant':<22}{'BTC SR':>12}{'ETH SR':>12}{'avg SR':>12}")
    for v in VARIANTS:
        btc, eth = sr_table[v]["bitcoin"], sr_table[v]["ethereum"]
        print(f"{v:<22}{btc:>12.3f}{eth:>12.3f}{(btc+eth)/2:>12.3f}")

    print()
    print("=" * 88)
    print(f"PAIRED BOOTSTRAP {N_BOOT:,} (delta SR, 95% CI, P(delta > 0))")
    print("=" * 88)

    pairs = [
        ("D_v3_full", "A_pure_quant", "D vs A (full v3 vs pure quant)"),
        ("D_v3_full", "B_legacy_sentiment", "D vs B (full v3 vs legacy)"),
        ("D_v3_full", "C_v3_features_only", "D vs C (LLM analyst increment)"),
        ("C_v3_features_only", "A_pure_quant", "C vs A (structured-only vs pure quant)"),
        ("C_v3_features_only", "B_legacy_sentiment", "C vs B (structured-only vs legacy)"),
        ("B_legacy_sentiment", "A_pure_quant", "B vs A (legacy vs pure quant)"),
    ]

    results = {}
    for v1, v2, label in pairs:
        print(f"\n{label}")
        print("-" * 88)
        results[f"{v1}__vs__{v2}"] = {}
        for c in COINS:
            a = load(v1, c)
            b = load(v2, c)
            r = paired_bootstrap(a, b)
            sig = "*" if abs(r["delta_mean"]) > 0 and (r["p_positive"] < 0.05 or r["p_positive"] > 0.95) else ""
            print(
                f"  {c:<10} delta={r['delta_mean']:>+7.3f}  "
                f"95% CI [{r['ci_lo_95']:>+6.2f}, {r['ci_hi_95']:>+6.2f}]  "
                f"P(>0)={r['p_positive']:.3f} {sig}"
            )
            results[f"{v1}__vs__{v2}"][c] = r

    # Save
    out = {
        "sr_point": sr_table,
        "bootstrap": results,
        "n_boot": N_BOOT,
        "window": "2026-01-16 → 2026-04-15 (90 bars)",
        "seed": SEED,
    }
    Path("/tmp/v3ab_bootstrap.json").write_text(json.dumps(out, indent=2))
    print(f"\nSaved: /tmp/v3ab_bootstrap.json")


if __name__ == "__main__":
    main()

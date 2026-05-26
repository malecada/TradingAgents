"""Fit per-coin isotonic calibrators from logged market-v2 convictions.

Reads CSVs produced by ``generate_hybrid_signals.py`` under
``--market-mode v2`` (which writes the ``market_llm_conviction_raw`` and
the realised forward return per bar), groups by coin, fits one
``IsotonicCalibrator`` per coin, and pickles to
``data/checkpoints/market_isotonic_{coin}.pkl``.
"""
from __future__ import annotations

import argparse
import glob
import os
from pathlib import Path

import numpy as np
import pandas as pd

from tradingagents.strategies.market_calibration import fit_market_calibrator


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--signals-glob",
        required=True,
        help=(
            "Glob of CSVs containing market_llm_conviction_raw and "
            "forward_return columns, e.g. "
            "'data/market_v2_ab/D_v2_full/*.csv'"
        ),
    )
    p.add_argument("--horizon-days", type=int, default=7)
    p.add_argument("--output-dir", default="data/checkpoints")
    p.add_argument("--min-samples", type=int, default=30)
    args = p.parse_args()

    paths = sorted(glob.glob(args.signals_glob))
    if not paths:
        raise SystemExit(f"No CSVs matched {args.signals_glob}")

    per_coin: dict[str, list[tuple[float, int]]] = {}
    for path in paths:
        coin = Path(path).stem.split("_")[0]
        df = pd.read_csv(path)
        if "market_llm_conviction_raw" not in df.columns:
            print(f"skip {path}: no market_llm_conviction_raw column")
            continue
        if "forward_return" not in df.columns:
            print(f"skip {path}: no forward_return column")
            continue
        df = df.dropna(subset=["market_llm_conviction_raw", "forward_return"])
        for _, row in df.iterrows():
            outcome = 1 if row["forward_return"] > 0 else 0
            per_coin.setdefault(coin, []).append(
                (float(row["market_llm_conviction_raw"]), int(outcome))
            )

    os.makedirs(args.output_dir, exist_ok=True)
    for coin, pairs in per_coin.items():
        if len(pairs) < args.min_samples:
            print(
                f"{coin}: only {len(pairs)} samples; "
                f"skipping (need >= {args.min_samples})"
            )
            continue
        raw = np.array([p[0] for p in pairs], dtype=float)
        outc = np.array([p[1] for p in pairs], dtype=float)
        fit_market_calibrator(raw, outc, coin=coin, root=args.output_dir)
        print(f"fit calibrator for {coin}: n={len(pairs)}")


if __name__ == "__main__":
    main()

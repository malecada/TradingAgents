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

from tradingagents.dataflows.coingecko_binance import _load_crypto_ohlcv
from tradingagents.strategies.market_calibration import fit_market_calibrator


def _compute_forward_returns(
    coin: str, dates: pd.Series, horizon_days: int
) -> np.ndarray:
    """Compute forward H-day returns by looking up close[t+H] / close[t] - 1."""
    if dates.empty:
        return np.array([], dtype=float)
    last_date = pd.Timestamp(dates.max())
    fetch_curr = (last_date + pd.Timedelta(days=horizon_days + 5)).strftime("%Y-%m-%d")
    ohlcv = _load_crypto_ohlcv(coin, fetch_curr)
    ohlcv["Date"] = pd.to_datetime(ohlcv["Date"])
    ohlcv = ohlcv.set_index("Date").sort_index()
    out = np.full(len(dates), np.nan, dtype=float)
    for i, d in enumerate(dates):
        d = pd.Timestamp(d)
        try:
            c0 = float(ohlcv.loc[d, "Close"])
        except KeyError:
            continue
        target = d + pd.Timedelta(days=horizon_days)
        future = ohlcv.loc[ohlcv.index >= target]
        if future.empty:
            continue
        c1 = float(future.iloc[0]["Close"])
        out[i] = c1 / c0 - 1.0
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--signals-glob",
        required=True,
        help=(
            "Glob of CSVs containing market_llm_conviction_raw and date "
            "columns, e.g. 'data/market_v2_ab/D_v2_full/*.csv'"
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
        df = pd.read_csv(path, parse_dates=["date"])
        if "market_llm_conviction_raw" not in df.columns:
            print(f"skip {path}: no market_llm_conviction_raw column")
            continue
        df = df.dropna(subset=["market_llm_conviction_raw", "date"])
        if df.empty:
            continue
        forward = _compute_forward_returns(coin, df["date"], args.horizon_days)
        df = df.assign(forward_return=forward)
        df = df.dropna(subset=["forward_return"])
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

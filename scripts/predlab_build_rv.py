"""Build 1h + 1d realized-measure stores from the predlab 5m klines.

Reads data/predlab/klines_5m/{SYM}.parquet (DatetimeIndex store), feeds the
ts-ms-column contract of tradingagents.predlab.rv.aggregate_rv, writes
data/predlab/rv_1h/{SYM}.parquet and data/predlab/rv_1d/{SYM}.parquet.
Prints coverage + sanity numbers (honest denominators).

Usage: python scripts/predlab_build_rv.py --symbols BTCUSDT ETHUSDT
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.predlab import rv  # noqa: E402

DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))
IN_DIR = DATA_ROOT / "predlab" / "klines_5m"


def build_symbol(sym: str) -> None:
    store = pd.read_parquet(IN_DIR / f"{sym}.parquet")
    df = store.reset_index()
    df["ts"] = df["ts"].astype("int64") // 10**6  # DatetimeIndex ns -> ms column
    for freq, sub in (("1h", "rv_1h"), ("1d", "rv_1d")):
        out = rv.aggregate_rv(df, freq)
        out_dir = DATA_ROOT / "predlab" / sub
        out_dir.mkdir(parents=True, exist_ok=True)
        out.to_parquet(out_dir / f"{sym}.parquet")
        n = len(out)
        n_nan = int(out["rv"].isna().sum())
        print(f"{sym} {freq}: {n} periods ({out.index.min()} -> {out.index.max()}), "
              f"nan-rv {n_nan}/{n} ({100.0 * n_nan / n:.2f}%)")
        if freq == "1d":
            _sanity_daily(sym, out)


def _sanity_daily(sym: str, out: pd.DataFrame) -> None:
    d21 = out[(out.index >= "2021-01-01") & (out.index < "2022-01-01")]
    ann_vol = float(np.sqrt(365.0 * np.nanmedian(d21["rv"])))
    print(f"  sanity {sym}: median annualized 5m-RV vol 2021 = {ann_vol:.3f} "
          f"(plausible band 0.5-1.2)")
    # 21d rolling: sqrt(mean RV) vs std of daily close-to-close rets
    rv_vol = np.sqrt(out["rv"].rolling(21).mean())
    cc_vol = out["ret"].rolling(21).std(ddof=1)
    ratio = (rv_vol / cc_vol).replace([np.inf, -np.inf], np.nan).dropna()
    frac_ok = float(((ratio > 0.7) & (ratio < 1.3)).mean())
    print(f"  sanity {sym}: RV/CC 21d vol ratio in [0.7,1.3] for "
          f"{100.0 * frac_ok:.1f}% of {len(ratio)} windows (need >80%)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--symbols", nargs="+", default=["BTCUSDT", "ETHUSDT"])
    args = ap.parse_args()
    for sym in args.symbols:
        build_symbol(sym)


if __name__ == "__main__":
    main()

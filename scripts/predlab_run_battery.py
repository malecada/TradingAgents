"""Run a registered Phase-1 battery tier over cells.

Usage:
  python scripts/predlab_run_battery.py --tier t0 --cells all
  python scripts/predlab_run_battery.py --tier t0 --cells 'BTCUSDT|24h*'

Loads each cell's series from the predlab stores (clipped at MAX_LOAD_END —
the sealed holdout is never read), builds the tier's model set, and delegates
to runner.run_cell (cards + forecasts + ledger rows).

Series convention (matches the stores' labeling): row ts = period START t,
y[t] realized over (t, t+h] — rv/ret/volume rows already carry it; funding is
re-labeled accordingly (8h: next print; 24h: UTC-day sum).

Tier-0 comparison base per cell (baselines are the null; the REGISTERED
strong baseline arrives with its tier): T1 rw_zero, T2 base_rate,
T3 ewma_0.94, T4 seasonal_naive, T6 persistence.
"""
from __future__ import annotations

import argparse
import fnmatch
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.predlab import baselines, registry, runner  # noqa: E402

DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))
FUND_DIR = DATA_ROOT / "predlab" / "funding"  # copied from the 799-sym xsect store

SEASONAL_M = {"1h": 24, "24h": 7, "7d": 1}
HORIZON_BARS = {"1h": 1, "24h": 1, "7d": 7, "8h": 1}


def _clip(df: pd.DataFrame) -> pd.DataFrame:
    return df[df.index <= pd.Timestamp(registry.MAX_LOAD_END, tz="UTC")]


def _rv_store(symbol: str, horizon: str) -> pd.DataFrame:
    sub = "rv_1h" if horizon == "1h" else "rv_1d"
    return _clip(pd.read_parquet(DATA_ROOT / "predlab" / sub / f"{symbol}.parquet"))


def _season_bin(idx: pd.DatetimeIndex, horizon: str) -> np.ndarray:
    if horizon == "1h":
        return idx.hour.to_numpy(dtype=float)
    return idx.dayofweek.to_numpy(dtype=float)


def _agg7(s: pd.Series) -> pd.Series:
    # y7[t] = value over (t, t+7d] on the daily grid (overlapping, step 1)
    return s.rolling(7).sum().shift(-6)


def load_series(symbol: str, horizon: str, target: str) -> pd.DataFrame:
    if target == "T6_funding":
        raw = pd.read_parquet(FUND_DIR / f"{symbol}.parquet")
        rate = raw["fundingRate"].astype(float).sort_index()  # DatetimeIndex fundingTime (UTC)
        if horizon == "8h":
            y = rate.shift(-1)  # target = next print, realized (t, t+8h]
        else:  # 24h: UTC-day sum, row = day start, realized at day end
            y = rate.groupby(rate.index.floor("D")).sum()
        y = _clip(y.to_frame("y")).dropna()
        return y

    store = _rv_store(symbol, horizon)
    if target in ("T1_ret", "T2_dir"):
        base = store["ret"]
    elif target == "T3_rv":
        base = store["rv"]
    elif target == "T4_vol":
        base = np.log(store["quote_volume"].replace(0.0, np.nan))
    else:
        raise ValueError(target)

    if horizon == "7d":
        base = _agg7(base)
    df = base.to_frame("y").dropna()
    df["bin"] = _season_bin(df.index, horizon)
    return df


def tier0_models(target: str, horizon: str) -> "tuple[list, str]":
    m = SEASONAL_M[horizon] if horizon in SEASONAL_M else 1
    if target == "T1_ret":
        return [baselines.RWZero(), baselines.HistMean(), baselines.Persistence()], "rw_zero"
    if target == "T2_dir":
        return [baselines.BaseRate()], "base_rate"
    if target == "T3_rv":
        return [baselines.EWMA(lam=0.94), baselines.Persistence(), baselines.HistMean()], "ewma_0.94"
    if target == "T4_vol":
        sn = baselines.SeasonalNaive(m=m)
        return [sn, baselines.Persistence(), baselines.HistMean(),
                baselines.Climatology(bin_col=0)], sn.name
    if target == "T6_funding":
        return [baselines.Persistence(), baselines.HistMean()], "persistence"
    raise ValueError(target)


def run_tier0(gates_key: str, pattern: str) -> None:
    entry = registry.get_experiment(gates_key)
    proto = entry["protocol"]
    cells = [c for c in entry["cells"] if fnmatch.fnmatch(c["cell"], pattern)]
    print(f"tier t0: {len(cells)} cells matching {pattern!r}")
    for c in cells:
        sym, hz, tgt = c["symbol"], c["horizon"], c["target"]
        series = load_series(sym, hz, tgt)
        models, base = tier0_models(tgt, hz)
        loss = proto["loss"][tgt.split("_")[0]]
        cell = {
            "cell": c["cell"],
            "target": tgt,
            "horizon_bars": HORIZON_BARS[hz],
            "strong_baseline": base,
            "loss": loss,
            "min_train": proto["min_train"].get(hz, 365),
            "step": 1,
            "refit_every": 1,
            "embargo": 0,
            "mase_m": SEASONAL_M.get(hz, 1),
            "eval_start": entry["dev_window"][0],  # earlier bars = burn-in only
        }
        out = runner.run_cell(cell, series, models, gates_key=gates_key, tier="t0")
        best = out.sort_values("loss_mean").iloc[0]
        print(f"  {c['cell']}: n={int(out['n_origins'].max())} base={base} "
              f"best={best['model']} loss={best['loss_mean']:.6g}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gates-key", default="predlab_p1_classical")
    ap.add_argument("--tier", required=True, choices=["t0"])
    ap.add_argument("--cells", default="all")
    args = ap.parse_args()
    pattern = "*" if args.cells == "all" else args.cells
    if args.tier == "t0":
        run_tier0(args.gates_key, pattern)


if __name__ == "__main__":
    main()

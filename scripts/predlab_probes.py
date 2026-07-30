"""Pre-battery plumbing probes (charter §7): run BEFORE any Phase-1 battery.

P0  — timestamp/plumbing reconciliation: recompute sampled days of BTC daily
      RV with an independent groupby directly from the raw 5m parquet and
      require equality with the store at 1e-12; assert strictly-increasing
      UTC index on the 5m store.
P-canary — leakage canary: a deliberately leaky model (reads the origin's own
      future target) must crush honest baselines on the real BTC|24h|T3 cell
      with DM p < 1e-6. Proves the harness CAN expose leakage, making honest
      models' non-leaking informative. (Plan wrote "beats HAR"; HAR ships in
      Task 12, so the canary is checked against EWMA + persistence — same
      intent, honest models available at probe time.)

Writes data/predlab/probes_p1.json. Any FAIL => stop, fix plumbing first.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.predlab import baselines, registry, runner  # noqa: E402

DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))
SAMPLE_DAYS = ["2021-06-15", "2023-03-11", "2024-11-05"]


def probe_p0() -> dict:
    k5 = pd.read_parquet(DATA_ROOT / "predlab" / "klines_5m" / "BTCUSDT.parquet")
    store = pd.read_parquet(DATA_ROOT / "predlab" / "rv_1d" / "BTCUSDT.parquet")
    monotonic = bool(k5.index.is_monotonic_increasing)
    tz_utc = str(k5.index.tz) == "UTC"
    # independent recompute: global log-close diffs, grouped by UTC day of bar open
    r = np.log(k5["close"]).diff()
    daily_rv = (r**2).groupby(k5.index.floor("D")).sum()
    max_err = 0.0
    for day in SAMPLE_DAYS:
        ts = pd.Timestamp(day, tz="UTC")
        err = abs(float(daily_rv.loc[ts]) - float(store.loc[ts, "rv"]))
        max_err = max(max_err, err)
    ok = monotonic and tz_utc and max_err < 1e-12
    return {"pass": ok, "monotonic": monotonic, "tz_utc": tz_utc,
            "max_recompute_err": max_err, "sample_days": SAMPLE_DAYS}


class LeakyCanary(baselines.Forecaster):
    """Reads the origin's own (future) target — must dominate honest models."""

    name = "leaky_canary"

    def __init__(self, y_by_origin: "list[float]", noise: float = 1e-6, seed: int = 0):
        self._vals = iter(y_by_origin)
        self._rng = np.random.default_rng(seed)
        self._noise = noise

    def predict(self, y_hist, x_now=None):
        return float(next(self._vals) * (1.0 + self._rng.normal(0, self._noise)))


def probe_canary() -> dict:
    store = pd.read_parquet(DATA_ROOT / "predlab" / "rv_1d" / "BTCUSDT.parquet")
    dev = store[store.index <= pd.Timestamp(registry.MAX_LOAD_END, tz="UTC")]
    series = pd.DataFrame({"y": dev["rv"].to_numpy()}, index=dev.index)
    cell = {
        "cell": "BTCUSDT|24h|T3_rv", "target": "T3_rv", "horizon_bars": 1,
        "strong_baseline": "ewma_0.94", "loss": "qlike",
        "min_train": 365, "step": 1, "refit_every": 1, "embargo": 0,
    }
    from tradingagents.predlab.splits import rolling_origin
    y = series["y"].to_numpy()
    origins = [sp.origin for sp in rolling_origin(len(y), 365, 1)]
    canary = LeakyCanary([y[o] for o in origins])
    out = runner.run_cell(
        cell, series,
        [baselines.EWMA(lam=0.94), baselines.Persistence(), canary],
        gates_key="predlab_p1_classical", tier="probe", dry=True,
    )
    can = out[out.model == "leaky_canary"].iloc[0]
    ew = out[out.model == "ewma_0.94"].iloc[0]
    ok = (can["dm_p"] < 1e-6) and (can["loss_mean"] < 0.01 * ew["loss_mean"])
    return {"pass": bool(ok), "canary_dm_p": float(can["dm_p"]),
            "canary_qlike": float(can["loss_mean"]),
            "ewma_qlike": float(ew["loss_mean"]),
            "persistence_qlike": float(out[out.model == "persistence"].iloc[0]["loss_mean"])}


def main() -> None:
    res = {"p0": probe_p0(), "canary": probe_canary()}
    out_path = DATA_ROOT / "predlab" / "probes_p1.json"
    out_path.write_text(json.dumps(res, indent=1))
    for name, r in res.items():
        print(f"{name}: {'PASS' if r['pass'] else 'FAIL'} {json.dumps({k: v for k, v in r.items() if k != 'pass'})[:200]}")
    if not all(r["pass"] for r in res.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()

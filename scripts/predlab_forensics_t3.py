"""Forensic kill-tests for the Tier-1 T3 HARQ result (charter §5).

K1 shuffled-target: row-shuffle the daily series (temporal structure
   destroyed) — HARQ's edge over HAR must vanish (dm_p not small).
K2 rq-leak mutation: feed HARQ CONTEMPORANEOUS rq (unshifted = future info)
   instead of rq.shift(1) — the leaked variant must improve markedly and
   differ from the honest forecasts, proving the rq channel is live and the
   shift(1) is what keeps it honest.

Writes data/predlab/forensics_t3.json.
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

from tradingagents.predlab import har, registry, runner  # noqa: E402

DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))


def _series(sym: str) -> pd.DataFrame:
    store = pd.read_parquet(DATA_ROOT / "predlab" / "rv_1d" / f"{sym}.parquet")
    store = store[store.index <= pd.Timestamp(registry.MAX_LOAD_END, tz="UTC")]
    return pd.DataFrame({
        "y": store["rv"],
        "rq_lag": store["rq"].shift(1),
        "rq_leak": store["rq"],  # contemporaneous — the deliberate leak
    }).dropna(subset=["y"])


def _cell(**over):
    cell = {
        "cell": "BTCUSDT|24h|T3_rv", "target": "T3_rv", "horizon_bars": 1,
        "strong_baseline": "har_levels", "loss": "qlike",
        "min_train": 365, "step": 1, "refit_every": 1, "embargo": 0,
        "eval_start": "2021-01-01",
    }
    cell.update(over)
    return cell


def k1_shuffled(sym: str) -> dict:
    s = _series(sym)
    rng = np.random.default_rng(99)
    shuffled = s.sample(frac=1.0, replace=False, random_state=99).reset_index(drop=True)
    shuffled.index = s.index  # keep the calendar, destroy the dynamics
    out = runner.run_cell(
        _cell(cell=f"{sym}|24h|T3_rv"), shuffled,
        [har.HarForecaster("har_levels"), har.HarForecaster("harq", rq_col=0)],
        gates_key="predlab_p1_classical", tier="forensic", dry=True)
    p = float(out[out.model == "harq"].iloc[0]["dm_p"])
    return {"pass": bool(np.isnan(p) or p > 0.05), "harq_dm_p_on_shuffled": p}


def k2_rq_leak(sym: str) -> dict:
    s = _series(sym)
    honest_cell = _cell(cell=f"{sym}|24h|T3_rv")
    _, ph = runner.run_cell(
        honest_cell, s[["y", "rq_lag"]].copy(),
        [har.HarForecaster("har_levels"), har.HarForecaster("harq", rq_col=0)],
        gates_key="predlab_p1_classical", tier="forensic", dry=True,
        return_forecasts=True)
    leak_df = s[["y", "rq_leak"]].rename(columns={"rq_leak": "rq_lag"})
    out_l, pl = runner.run_cell(
        _cell(cell=f"{sym}|24h|T3_rv"), leak_df,
        [har.HarForecaster("har_levels"), har.HarForecaster("harq", rq_col=0)],
        gates_key="predlab_p1_classical", tier="forensic", dry=True,
        return_forecasts=True)
    differs = not np.allclose(ph["harq"], pl["harq"])
    leak_p = float(out_l[out_l.model == "harq"].iloc[0]["dm_p"])
    return {"pass": bool(differs and leak_p < 1e-4),
            "leaked_dm_p": leak_p, "forecasts_differ": bool(differs)}


def main() -> None:
    res = {}
    for sym in ("BTCUSDT", "ETHUSDT"):
        res[sym] = {"k1_shuffled": k1_shuffled(sym), "k2_rq_leak": k2_rq_leak(sym)}
    (DATA_ROOT / "predlab" / "forensics_t3.json").write_text(json.dumps(res, indent=1))
    for sym, r in res.items():
        for k, v in r.items():
            print(f"{sym} {k}: {'PASS' if v['pass'] else 'FAIL'} {v}")
    if not all(v["pass"] for r in res.values() for v in r.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()

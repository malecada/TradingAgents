"""Forensics v2 for the Tier-1 T3 HARQ pass — replaces the v1 probe set.

v1 findings that motivated v2 (recorded in data/predlab/forensics_t3.json):
  - K1 ETH: HARQ "beat" har_levels on SHUFFLED data (p 0.001) — the levels-OLS
    baseline is fragile under ETH's RV outliers + QLIKE asymmetry, so margins
    vs har_levels can measure baseline fragility, not skill.
  - K2 (leak-must-improve) was mis-designed: contemporaneous rq enters only
    via the sqrt(rq)*rv_lag interaction — indirect and outlier-destabilized,
    so a leak need not improve forecasts. Pipeline honesty is already pinned
    by truncation-equivalence tests and the Task-9 train-on-future canary.

v2 probes:
  A2 rq alignment audit (deterministic): battery's rq_lag column must equal
     rq shifted by exactly one period, everywhere.
  K3 strongest-baseline pairwise DM on REAL data: HARQ vs log_har and vs
     EWMA. Charter A1: a skill claim must beat the strongest sensible
     baseline, which on ETH is not levels-HAR.
  K4 shuffled-null vs ROBUST reference: on shuffled data HARQ must NOT beat
     log_har (if it does, the artifact is deeper than baseline fragility).

Writes data/predlab/forensics_t3_v2.json; exit 1 on any FAIL.
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

from tradingagents.predlab import dm as dmod  # noqa: E402
from tradingagents.predlab import har, losses, registry, runner  # noqa: E402

DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))


def _store(sym: str) -> pd.DataFrame:
    st = pd.read_parquet(DATA_ROOT / "predlab" / "rv_1d" / f"{sym}.parquet")
    return st[st.index <= pd.Timestamp(registry.MAX_LOAD_END, tz="UTC")]


def _series(sym: str) -> pd.DataFrame:
    st = _store(sym)
    return pd.DataFrame({"y": st["rv"], "rq_lag": st["rq"].shift(1)}).dropna(subset=["y"])


def _cell(sym: str) -> dict:
    return {
        "cell": f"{sym}|24h|T3_rv", "target": "T3_rv", "horizon_bars": 1,
        "strong_baseline": "log_har", "loss": "qlike",
        "min_train": 365, "step": 1, "refit_every": 1, "embargo": 0,
        "eval_start": "2021-01-01",
    }


def a2_alignment(sym: str) -> dict:
    st = _store(sym)
    lagged = st["rq"].shift(1)
    rebuilt = st["rq"].to_numpy()[:-1]
    ok = np.allclose(lagged.to_numpy()[1:], rebuilt, equal_nan=True)
    return {"pass": bool(ok)}


def _pairwise(sym: str, shuffled: bool):
    s = _series(sym)
    if shuffled:
        s = s.sample(frac=1.0, replace=False, random_state=99).reset_index(drop=True).set_axis(
            s.index)
    models = [har.HarForecaster("log_har"), har.HarForecaster("har_levels"),
              har.HarForecaster("harq", rq_col=0)]
    from tradingagents.predlab.baselines import EWMA

    models.append(EWMA(lam=0.94))
    out, preds = runner.run_cell(_cell(sym), s, models,
                                 gates_key="predlab_p1_classical", tier="forensic",
                                 dry=True, return_forecasts=True)
    y = s["y"].to_numpy()
    # rebuild y_true over evaluated origins from the runner's forecast lengths:
    n = len(preds["harq"])
    y_true = y[-n:]
    l_harq = losses.qlike(preds["harq"], y_true)
    res = {}
    for ref in ("log_har", "ewma_0.94"):
        l_ref = losses.qlike(preds[ref], y_true)
        ok = ~(np.isnan(l_ref) | np.isnan(l_harq))
        r = dmod.dm_test(l_ref[ok], l_harq[ok], h=1)
        res[ref] = {"dm_p": float(r.pvalue), "dqlike_pct":
                    float(100 * (np.nanmean(l_ref) - np.nanmean(l_harq)) / np.nanmean(l_ref))}
    return res


def main() -> None:
    out = {}
    all_pass = True
    for sym in ("BTCUSDT", "ETHUSDT"):
        a2 = a2_alignment(sym)
        real = _pairwise(sym, shuffled=False)
        shuf = _pairwise(sym, shuffled=True)
        k4_pass = not (shuf["log_har"]["dm_p"] < 0.05)
        out[sym] = {
            "a2_alignment": a2,
            "k3_real_vs_strongest": real,
            "k4_shuffled_vs_log_har": {"pass": k4_pass, **shuf["log_har"]},
        }
        all_pass &= a2["pass"] and k4_pass
    (DATA_ROOT / "predlab" / "forensics_t3_v2.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()

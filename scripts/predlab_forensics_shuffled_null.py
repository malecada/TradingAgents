"""Corrected shuffled-null forensics for the T3 (HARQ) and T4 (seasonal-AR) passes.

Design lesson from v1/v2 (recorded in forensics_t3.json / forensics_t3_v2.json /
forensics_t4.json): a shuffled-target comparison is only FAIR between models
that collapse to the SAME unconditional forecast on exchangeable data.
Regression models collapse to the arithmetic mean; naive/seasonal-naive stay
2x-variance random draws; log-space models collapse to the geometric mean
(systematic QLIKE under-forecast on heavy-tailed RV). Any cross-class shuffled
comparison is structurally biased and says nothing about leakage or skill.

The honest shuffled check, per model under test:
    model  vs  hist_mean  on shuffled data must be ~EQUAL (|dm| not small-p in
    EITHER direction). A significant win over hist_mean on shuffled data would
    indicate a harness leak; a significant loss just reflects estimation noise
    and is reported but not gated.

Writes data/predlab/forensics_shuffled_null.json; exit 1 only if a model BEATS
hist_mean on shuffled data at p < 0.01 (leak signature).
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

from tradingagents.predlab import baselines, har, registry, runner, tier1  # noqa: E402

DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))


def _shuffled(df: pd.DataFrame, seed: int = 7) -> pd.DataFrame:
    out = df.sample(frac=1.0, replace=False, random_state=seed).reset_index(drop=True)
    out.index = df.index
    return out


def _store(sym: str) -> pd.DataFrame:
    st = pd.read_parquet(DATA_ROOT / "predlab" / "rv_1d" / f"{sym}.parquet")
    return st[st.index <= pd.Timestamp(registry.MAX_LOAD_END, tz="UTC")]


def t3_check(sym: str) -> dict:
    st = _store(sym)
    s = _shuffled(pd.DataFrame({"y": st["rv"], "rq_lag": st["rq"].shift(1)}).dropna(subset=["y"]))
    cell = {
        "cell": f"{sym}|24h|T3_rv", "target": "T3_rv", "horizon_bars": 1,
        "strong_baseline": "hist_mean", "loss": "qlike",
        "min_train": 365, "step": 1, "refit_every": 1, "embargo": 0,
        "eval_start": "2021-01-01",
    }
    out = runner.run_cell(cell, s, [baselines.HistMean(), har.HarForecaster("harq", rq_col=0)],
                          gates_key="predlab_p1_classical", tier="forensic", dry=True)
    p = float(out[out.model == "harq"].iloc[0]["dm_p"])
    return {"pass": bool(np.isnan(p) or p > 0.01), "harq_vs_mean_shuffled_dm_p": p}


def t4_check(sym: str) -> dict:
    st = _store(sym)
    y = np.log(st["quote_volume"].replace(0.0, np.nan))
    s = _shuffled(y.to_frame("y").dropna())
    cell = {
        "cell": f"{sym}|24h|T4_vol", "target": "T4_vol", "horizon_bars": 1,
        "strong_baseline": "hist_mean", "loss": "mase", "mase_m": 7,
        "min_train": 365, "step": 1, "refit_every": 1, "embargo": 0,
        "eval_start": "2021-01-01",
    }
    out = runner.run_cell(cell, s, [baselines.HistMean(), tier1.SeasonalAR(m=7)],
                          gates_key="predlab_p1_classical", tier="forensic", dry=True)
    p = float(out[out.model == "seasonal_ar_m7"].iloc[0]["dm_p"])
    return {"pass": bool(np.isnan(p) or p > 0.01), "sar_vs_mean_shuffled_dm_p": p}


def main() -> None:
    res = {}
    for sym in ("BTCUSDT", "ETHUSDT"):
        res[sym] = {"t3_harq_vs_mean": t3_check(sym), "t4_sar_vs_mean": t4_check(sym)}
    (DATA_ROOT / "predlab" / "forensics_shuffled_null.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))
    sys.exit(0 if all(v["pass"] for r in res.values() for v in r.values()) else 1)


if __name__ == "__main__":
    main()

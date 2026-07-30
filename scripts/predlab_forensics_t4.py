"""Kill-test for the Tier-1 T4 seasonal-AR pass: shuffled-target must destroy it.

Row-shuffling the daily log-volume series removes both persistence and weekly
seasonality; seasonal_ar must NOT beat seasonal-naive afterwards. (Both models
degrade to noise; unlike the T3 case the baseline here is scale-stable under
MASE, so the shuffled null is clean.) Writes data/predlab/forensics_t4.json.
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

from tradingagents.predlab import baselines, registry, runner, tier1  # noqa: E402

DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))


def check(sym: str) -> dict:
    store = pd.read_parquet(DATA_ROOT / "predlab" / "rv_1d" / f"{sym}.parquet")
    store = store[store.index <= pd.Timestamp(registry.MAX_LOAD_END, tz="UTC")]
    y = np.log(store["quote_volume"].replace(0.0, np.nan))
    s = y.to_frame("y").dropna()
    shuffled = s.sample(frac=1.0, replace=False, random_state=7).reset_index(drop=True)
    shuffled.index = s.index
    cell = {
        "cell": f"{sym}|24h|T4_vol", "target": "T4_vol", "horizon_bars": 1,
        "strong_baseline": "seasonal_naive_m7", "loss": "mase", "mase_m": 7,
        "min_train": 365, "step": 1, "refit_every": 1, "embargo": 0,
        "eval_start": "2021-01-01",
    }
    out = runner.run_cell(cell, shuffled,
                          [baselines.SeasonalNaive(m=7), tier1.SeasonalAR(m=7)],
                          gates_key="predlab_p1_classical", tier="forensic", dry=True)
    p = float(out[out.model == "seasonal_ar_m7"].iloc[0]["dm_p"])
    return {"pass": bool(np.isnan(p) or p > 0.05), "shuffled_dm_p": p}


def main() -> None:
    res = {sym: check(sym) for sym in ("BTCUSDT", "ETHUSDT")}
    (DATA_ROOT / "predlab" / "forensics_t4.json").write_text(json.dumps(res, indent=1))
    for sym, r in res.items():
        print(f"{sym}: {'PASS' if r['pass'] else 'FAIL'} {r}")
    sys.exit(0 if all(r["pass"] for r in res.values()) else 1)


if __name__ == "__main__":
    main()

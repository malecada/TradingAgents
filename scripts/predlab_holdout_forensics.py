"""P5-02 forensics on holdout PASSes (registered in predlab_p5):

1. Multi-seed (5) permute-y nulls — permute the target series (marginal
   preserved, dynamics destroyed), re-run champion + baseline causally on the
   holdout window, expect the effect to collapse. Same-collapse fairness: each
   pair (champion, its baseline) shares the y-lag information channel, so both
   collapse together under permutation; exog features (T4 LGB) stay REAL —
   the permute-y-only pattern from the Phase-2 forensics.
2. Sub-period table — quarterly mean loss differential from the STORED
   holdout forecasts (descriptive, no re-evaluation).

Verdicts are never modified here; output -> data/predlab/p5_holdout_forensics.json.
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
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from tradingagents.predlab import baselines, har, registry, runner, tier1, tier2  # noqa: E402
from tradingagents.predlab import losses as L  # noqa: E402
import predlab_holdout as H  # noqa: E402  (reuses _store/_t4_series; HOLDOUT const)

DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))
OUT = DATA_ROOT / "predlab" / "p5_holdout_forensics.json"
N_SEEDS = 5


def _models_for(cell_id: str, champ_name: str, entry_ml: dict):
    """Same configs as the spend (predlab_holdout._cell_run), minus the run."""
    sym, hz, tgt = cell_id.split("|")
    st = H._store(sym, hz)
    mase_m, cols = 1, None
    if tgt == "T3_rv":
        series = pd.DataFrame({"y": st["rv"], "ret": st["ret"],
                               "rq_lag": st["rq"].shift(1)}).dropna(subset=["y", "ret"])
        hl = (1, 24, 168) if hz == "1h" else (1, 5, 22)
        base = har.HarForecaster("har_levels", lags=hl, refit_every=1)
        if champ_name == "harq":
            champ = har.HarForecaster("harq", rq_col=1, lags=hl, refit_every=1)
        else:
            champ = tier1.GarchForecaster("egarch11", ret_col=0,
                                          refit_every=24 if hz == "1h" else 5,
                                          window_cap=4320 if hz == "1h" else None)
        cell_refit, loss = (24 if hz == "1h" else 5), "qlike"
    elif tgt == "T4_vol":
        series, cols = H._t4_series(sym, hz, entry_ml)
        m = 24 if hz == "1h" else 7
        mase_m = m
        base = baselines.SeasonalNaive(m=m)
        cell_refit = int(entry_ml["protocol"]["refit_every"][hz])
        champ = tier2.LGBForecaster(refit_every=cell_refit, n_features=len(cols))
        loss = "mase"
    else:
        series = st["ret"].to_frame("y").dropna()
        base = baselines.BaseRate()
        champ = tier1.LogitLags()
        cell_refit, loss = 24, "brier"
    min_train = 2160 if hz == "1h" else 365
    cell = {"cell": cell_id, "target": tgt, "horizon_bars": 1,
            "strong_baseline": base.name, "loss": loss, "mase_m": mase_m,
            "min_train": min_train, "step": 1, "refit_every": cell_refit,
            "embargo": 0, "eval_start": H.HOLDOUT[0], "allow_holdout": True}
    return series, base, champ, cell


def permute_null(cell_id: str, champ_name: str) -> list:
    entry_ml = registry.get_experiment("predlab_p2_ml")
    rows = []
    for seed in range(N_SEEDS):
        series, base, champ, cell = _models_for(cell_id, champ_name, entry_ml)
        rng = np.random.default_rng(seed)
        yv = series["y"].to_numpy().copy()
        series["y"] = rng.permutation(yv)
        out = runner.run_cell(cell, series, [base, champ],
                              gates_key="forensic", tier="permute", dry=True)
        r = out[out.model == champ.name].iloc[0]
        rb = out[out.model == base.name].iloc[0]
        eff = float(100 * (rb["loss_mean"] - r["loss_mean"]) / rb["loss_mean"])
        rows.append({"seed": seed, "effect_pct": eff, "dm_p": float(r["dm_p"])})
        print(f"  {cell_id} permute seed {seed}: eff {eff:+.2f}% "
              f"dm_p={r['dm_p']:.3g}", flush=True)
    return rows


def subperiods(cell_id: str, champ_name: str, base_name: str, loss: str) -> dict:
    fdir = DATA_ROOT / "predlab" / "forecasts" / "predlab_p5_holdout" / cell_id.replace("|", "_")
    a = pd.read_parquet(fdir / f"{champ_name}.parquet").set_index("ts")
    b = pd.read_parquet(fdir / f"{base_name}.parquet").set_index("ts")
    y = a["y_true"].to_numpy()
    if loss == "qlike":
        la = L.qlike(np.maximum(a["pred"].to_numpy(), 1e-12), y)
        lb = L.qlike(np.maximum(b["pred"].to_numpy(), 1e-12), y)
    elif loss == "mase":
        la, lb = L.ae(y, a["pred"].to_numpy()), L.ae(y, b["pred"].to_numpy())
    else:
        la = L.brier(a["pred"].to_numpy(), (y > 0).astype(float))
        lb = L.brier(b["pred"].to_numpy(), (y > 0).astype(float))
    d = pd.Series(lb - la, index=a.index)  # >0 = champion better
    q = d.groupby(pd.PeriodIndex(d.index, freq="Q")).agg(["mean", "count"])
    return {str(k): {"mean_gain": float(v["mean"]), "n": int(v["count"])}
            for k, v in q.iterrows()}


def main() -> None:
    verdicts = json.loads((DATA_ROOT / "predlab" / "p5_holdout_verdicts.json").read_text())
    loss_of = {"T3": "qlike", "T4": "mase", "T2": "brier"}
    out = {}
    for cell_id, v in verdicts.items():
        if cell_id.startswith("T7") or v["verdict"] != "PASS":
            continue
        loss = loss_of[cell_id.split("|")[2][:2]]
        base_name = {"qlike": "har_levels",
                     "mase": f"seasonal_naive_m{24 if '|1h|' in cell_id else 7}",
                     "brier": "base_rate"}[loss]
        print(f"{cell_id} [{v['champion']}] real eff {v['effect_pct']:+.1f}%:", flush=True)
        subs = subperiods(cell_id, v["champion"], base_name, loss)
        pos = sum(1 for s in subs.values() if s["mean_gain"] > 0)
        nulls = permute_null(cell_id, v["champion"])
        max_null = max(abs(r["effect_pct"]) for r in nulls)
        out[cell_id] = {"real_effect_pct": v["effect_pct"], "permute_nulls": nulls,
                        "max_abs_null_effect_pct": max_null,
                        "sub_periods": subs,
                        "sub_periods_positive": f"{pos}/{len(subs)}",
                        "null_collapsed": bool(max_null < 0.5 * abs(v["effect_pct"]))}
        print(f"  subs positive {pos}/{len(subs)}, max |null eff| {max_null:.2f}% "
              f"vs real {v['effect_pct']:+.1f}%", flush=True)
    OUT.write_text(json.dumps(out, indent=1, default=float))
    print(f"\nforensics -> {OUT}", flush=True)


if __name__ == "__main__":
    main()

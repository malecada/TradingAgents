"""Corrected T4 permute-y null (same-collapse pairing).

The primary forensics pair LGB against the cell's registered baseline
(seasonal-naive). Under permuted y that pairing is structurally unfair —
the Phase-1 lesson: a regression model collapses to the unconditional
center, a naive lag predicts a random draw, so the regression "wins" on
noise. The honest null for exog models pairs the permuted-y champion with
a SAME-COLLAPSE reference (HistMean). Expect ~0 effect if LGB's real-data
advantage comes from dynamics, not collapse class.

Appends results into data/predlab/p5_holdout_forensics.json under
"corrected_t4_nulls". Verdicts untouched.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from tradingagents.predlab import baselines, registry, runner, tier2  # noqa: E402
import predlab_holdout as H  # noqa: E402

DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))
OUT = DATA_ROOT / "predlab" / "p5_holdout_forensics.json"
N_SEEDS = 5


def main() -> None:
    entry_ml = registry.get_experiment("predlab_p2_ml")
    results = {}
    for cell_id in ("BTCUSDT|1h|T4_vol", "ETHUSDT|1h|T4_vol",
                    "BTCUSDT|24h|T4_vol", "ETHUSDT|24h|T4_vol"):
        sym, hz, _ = cell_id.split("|")
        rows = []
        for seed in range(N_SEEDS):
            series, cols = H._t4_series(sym, hz, entry_ml)
            rng = np.random.default_rng(seed)
            series["y"] = rng.permutation(series["y"].to_numpy())
            refit = int(entry_ml["protocol"]["refit_every"][hz])
            base = baselines.HistMean()
            champ = tier2.LGBForecaster(refit_every=refit, n_features=len(cols))
            cell = {"cell": cell_id, "target": "T4_vol", "horizon_bars": 1,
                    "strong_baseline": "hist_mean", "loss": "mase",
                    "mase_m": 24 if hz == "1h" else 7,
                    "min_train": 2160 if hz == "1h" else 365, "step": 1,
                    "refit_every": refit, "embargo": 0,
                    "eval_start": H.HOLDOUT[0], "allow_holdout": True}
            out = runner.run_cell(cell, series, [base, champ],
                                  gates_key="forensic", tier="permute_t4fix",
                                  dry=True)
            r = out[out.model == "lgb"].iloc[0]
            rb = out[out.model == "hist_mean"].iloc[0]
            eff = float(100 * (rb["loss_mean"] - r["loss_mean"]) / rb["loss_mean"])
            rows.append({"seed": seed, "effect_vs_histmean_pct": eff,
                         "dm_p": float(r["dm_p"])})
            print(f"{cell_id} t4fix seed {seed}: eff vs hist_mean {eff:+.2f}% "
                  f"dm_p={r['dm_p']:.3g}", flush=True)
        results[cell_id] = rows
    data = json.loads(OUT.read_text()) if OUT.exists() else {}
    data["corrected_t4_nulls"] = {
        "design": "permuted-y LGB vs HistMean (same-collapse pair; see "
                  "module docstring)", "cells": results}
    OUT.write_text(json.dumps(data, indent=1, default=float))
    print(f"appended corrected_t4_nulls -> {OUT}", flush=True)


if __name__ == "__main__":
    main()

"""Check 3: how the persistence ``rho`` of the simulated unseen component shows in the autocorrelation of the
gate's target residual, the quantity the registered run reports. Synthetic targets on the decision-time
regressors only; no bar after a decision is read. The target side of the gate does not depend on the reader
features, so the panel is prepared with the score that needs no tree fit.

    PYTHONPATH=.:scripts python research/multiagent-v2/charter3_design/check3_persistence_scale.py PANEL
"""
import json
import sys

import numpy as np
import pandas as pd

import reader_charter3_null_gate as ng
from tradingagents.reader import charter3 as c3

SEEDS = 20
CELLS = ((0.0, "linear"), (0.3, "linear"), (0.3, "nonlinear"), (0.6, "nonlinear"))

rp = ng.RealPanel(pd.read_parquet(sys.argv[1]), "s_reader_lin")
feats, controls, squares, flexible = c3.PARTIAL_SCORES[c3.GATE_SCORE]
out = {}
for rho, shape in CELLS:
    acc = {str(lag): [] for lag in c3.AUTOCORR_LAGS}
    for seed in range(SEEDS):
        y = rp.target(seed, rho, shape, 0.0, 1.0)
        e = c3.target_residual(rp.frame, y, controls, squares, flexible)
        ac = c3.residual_autocorrelation(rp.frame, e)
        for lag in acc:
            acc[lag].append(ac[lag]["corr"])
    out[f"rho {rho} {shape}"] = {lag: round(float(np.mean(v)), 3) for lag, v in acc.items()}
print(json.dumps({"seeds": SEEDS, "mean_residual_autocorrelation_by_lag_in_weeks": out}, indent=1))

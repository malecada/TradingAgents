"""Charter 3, stage V0, check 1: does a curved relation of the target to the price history leak into the reader
gate, and which way of removing the controls stops it? Decision-time regressors of the panel and synthetic targets
only; no forward bar is read. The flexible fits of this check are cross-fitted over blocks of weeks (they see
later weeks), which the registered design does not do; check 2 has the fits on earlier weeks only.

    PYTHONPATH=.:scripts python research/multiagent-v2/charter3_design/check1_control_designs.py PANEL FIRST LAST OUT

PANEL is the decision-time panel written by ``scripts/reader_charter3_null_gate.py panel``; FIRST and LAST are
the seed range of every cell; OUT takes one row per cell, seed and variant."""
import json
import sys
import time

import lightgbm as lgb
import numpy as np
import pandas as pd

import reader_charter3_null_gate as ng
from tradingagents.reader import charter3 as c3, model

rp = ng.RealPanel(pd.read_parquet(sys.argv[1]), "s_reader_lin")           # regressors and synthetic targets only; no tree step here
frame, dates = rp.frame, rp.dates
controls = c3.HIST + c3.BLOCK_A
Z = c3.feature_ranks(frame, controls)
V = c3.feature_ranks(frame, c3.BLOCK_V)
design_lin = c3.control_matrix(frame, controls, ())
design_sq = c3.control_matrix(frame, controls, tuple(c3.HIST_BARS))
weeks = np.unique(dates)


def cross_fit_resid(V, Z, params, rounds, n_blocks=6):
    out = np.full(V.shape, np.nan)
    order = np.arange(len(weeks))
    for block in np.array_split(order, n_blocks):
        test = np.isin(dates, weeks[block])
        train = ~test
        for j in range(V.shape[1]):
            booster = lgb.train(dict(params), lgb.Dataset(Z[train], label=V[train, j]), num_boost_round=rounds)
            out[test, j] = V[test, j] - booster.predict(Z[test])
    return out


weak = dict(model.GBM_PARAMS)
strong = {**model.GBM_PARAMS, "learning_rate": 0.05, "num_leaves": 8, "max_depth": 3, "min_data_in_leaf": 50}
t0 = time.time()
V_weak = cross_fit_resid(V, Z, weak, model.GBM_ROUNDS)
V_strong = cross_fit_resid(V, Z, strong, 300)
print("cross-fit seconds", round(time.time() - t0, 1), flush=True)
for name, R in (("weak", V_weak), ("strong", V_strong)):
    print(name, "variance share left by the flexible fit", np.round(R.var(axis=0) / V.var(axis=0), 3).tolist(), flush=True)

variants = {
    "base": (c3.residuals(V, design_lin, dates), design_lin),
    "sq": (c3.residuals(V, design_sq, dates), design_sq),
    "gbm_weak": (c3.residuals(V_weak, design_lin, dates), design_lin),
    "gbm_strong": (c3.residuals(V_strong, design_lin, dates), design_lin),
    "gbm_strong_sq": (c3.residuals(V_strong, design_sq, dates), design_sq),
}
for name, (X, _) in variants.items():
    print(name, "share of rank variance left", np.round(np.nanvar(X, axis=0) / V.var(axis=0), 3).tolist(), flush=True)

first, last = int(sys.argv[2]), int(sys.argv[3])
cells = [("linear", 0.0, 0.0), ("nonlinear", 0.0, 0.0), ("linear", 0.0, 0.075), ("nonlinear", 0.3, 0.0)]
out = open(sys.argv[4], "w")
for shape, rho, signal in cells:
    for seed in range(first, last):
        y = rp.target(seed, rho, shape, signal, 1.0)
        for name, (X, design) in variants.items():
            resid = c3.residuals(y[:, None], design, dates)[:, 0]
            score, _ = c3.walk_forward(X, resid, dates)
            row = {"variant": name, "shape": shape, "rho": rho, "signal": signal, "seed": seed, **ng.gate_row(dates, score, resid)}
            out.write(json.dumps(row) + "\n")
        out.flush()

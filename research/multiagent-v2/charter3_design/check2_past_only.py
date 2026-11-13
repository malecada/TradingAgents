"""Charter 3, stage V0, check 2: removal of the controls by fits on earlier weeks only, on the reader features
(quadratic surface or boosted trees) and on the target (quadratic surface). Decision-time regressors of the panel
and synthetic targets only; no forward bar is read. The variant ``gbm_past_feat_quad_target`` is the design the
charter registers (``tradingagents/reader/charter3.py``: ``past_trees``, ``past_surface``).

    PYTHONPATH=.:scripts python research/multiagent-v2/charter3_design/check2_past_only.py PANEL FIRST LAST OUT

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
widx = np.searchsorted(weeks, dates)
FIRST = 26


def quad_basis(Z):
    k = Z.shape[1]
    cross = [Z[:, i] * Z[:, j] for i in range(k) for j in range(i + 1, k)]
    return np.column_stack([np.ones(len(Z)), Z, Z ** 2 - 1.0 / 12.0, *cross])


Q = quad_basis(Z)


ALPHA = 1.0
_eye = ALPHA * np.eye(Q.shape[1]); _eye[0, 0] = 0.0
_week_rows = [np.flatnonzero(widx == w) for w in range(len(weeks))]
_grams = np.cumsum(np.stack([Q[r].T @ Q[r] for r in _week_rows]), axis=0)          # gram of weeks 0..w
_solvers = {w: np.linalg.inv(_grams[w - 1] + _eye) for w in range(FIRST, len(weeks))}
_solvers["head"] = np.linalg.inv(_grams[FIRST - 1] + _eye)


def past_quad(values):
    """values minus a quadratic-surface ridge fit on earlier weeks (the first FIRST weeks: on themselves). No missing values."""
    vals = values if values.ndim == 2 else values[:, None]
    assert np.isfinite(vals).all()
    moments = np.cumsum(np.stack([Q[r].T @ vals[r] for r in _week_rows]), axis=0)   # Q'y of weeks 0..w
    res = np.empty(vals.shape)
    beta = _solvers["head"] @ moments[FIRST - 1]
    for w in range(FIRST):
        res[_week_rows[w]] = vals[_week_rows[w]] - Q[_week_rows[w]] @ beta
    for w in range(FIRST, len(weeks)):
        beta = _solvers[w] @ moments[w - 1]
        res[_week_rows[w]] = vals[_week_rows[w]] - Q[_week_rows[w]] @ beta
    return res if values.ndim == 2 else res[:, 0]


strong = {**model.GBM_PARAMS, "learning_rate": 0.05, "num_leaves": 8, "max_depth": 3, "min_data_in_leaf": 50}


def past_gbm(values, every=13):
    res = np.full(values.shape, np.nan)
    def fit(rows):
        return [lgb.train(dict(strong), lgb.Dataset(Z[rows], label=values[rows, j]), num_boost_round=300) for j in range(values.shape[1])]
    boosters = fit(widx < FIRST)
    cur = widx < FIRST
    res[cur] = values[cur] - np.column_stack([b.predict(Z[cur]) for b in boosters])
    for w in range(FIRST, len(weeks)):
        if (w - FIRST) % every == 0:
            boosters = fit(widx < w)
        cur = widx == w
        res[cur] = values[cur] - np.column_stack([b.predict(Z[cur]) for b in boosters])
    return res


t0 = time.time(); Vq = past_quad(V); print("quad seconds", round(time.time() - t0, 1), flush=True)
t0 = time.time(); Vg = past_gbm(V); print("gbm past seconds", round(time.time() - t0, 1), flush=True)
for name, R in (("quad", Vq), ("gbm_past", Vg)):
    print(name, "variance share left, test weeks", np.round(R[widx >= 52].var(axis=0) / V[widx >= 52].var(axis=0), 3).tolist(), flush=True)

variants = {
    "base": (c3.residuals(V, design_lin, dates), False),
    "quad_feat": (c3.residuals(Vq, design_lin, dates), False),
    "gbm_past_feat": (c3.residuals(Vg, design_lin, dates), False),
    "quad_both": (c3.residuals(Vq, design_lin, dates), True),
    "gbm_past_feat_quad_target": (c3.residuals(Vg, design_lin, dates), True),
}
for name, (X, _) in variants.items():
    print(name, "share of rank variance left", np.round(np.nanvar(X, axis=0) / V.var(axis=0), 3).tolist(), flush=True)

first, last = int(sys.argv[2]), int(sys.argv[3])
cells = [("linear", 0.0, 0.0), ("nonlinear", 0.0, 0.0), ("linear", 0.0, 0.075), ("nonlinear", 0.3, 0.0)]
out = open(sys.argv[4], "w")
for shape, rho, signal in cells:
    for seed in range(first, last):
        y = rp.target(seed, rho, shape, signal, 1.0)
        e_lin = c3.residuals(y[:, None], design_lin, dates)[:, 0]
        e_quad = c3.residuals(past_quad(y)[:, None], design_lin, dates)[:, 0]
        for name, (X, flexible_target) in variants.items():
            resid = e_quad if flexible_target else e_lin
            score, _ = c3.walk_forward(X, resid, dates)
            row = {"variant": name, "shape": shape, "rho": rho, "signal": signal, "seed": seed, **ng.gate_row(dates, score, resid)}
            out.write(json.dumps(row) + "\n")
        out.flush()

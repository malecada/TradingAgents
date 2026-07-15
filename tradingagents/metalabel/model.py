"""Meta-model layer: constant / logistic baselines + LightGBM with inner
purged chronological CV over the frozen 8-combo grid, isotonic calibration
on the last 20% of train (time-ordered). G1 evaluation per gates.json."""
from __future__ import annotations

import itertools

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score

LGB_GRID = {
    "num_leaves": [15, 31],
    "min_child_samples": [20, 50],
    "feature_fraction": [0.7, 1.0],
}
LGB_FIXED = {"learning_rate": 0.05, "n_estimators": 300, "objective": "binary",
             "verbosity": -1, "seed": 7}


def _fit_lgb(X, y, w, params):
    import lightgbm as lgb
    model = lgb.LGBMClassifier(**LGB_FIXED, **params)
    model.fit(X, y, sample_weight=w)
    return model


def _inner_cv_select(X, y, w):
    """Chronological 3-fold on train (row order = time order within events)."""
    n = len(X)
    edges = [0, n // 3, 2 * n // 3, n]
    best, best_auc = None, -np.inf
    for combo in itertools.product(*LGB_GRID.values()):
        params = dict(zip(LGB_GRID.keys(), combo))
        aucs = []
        for k in (1, 2):  # expanding: train [0:e_k), validate [e_k:e_{k+1})
            tr = slice(0, edges[k])
            va = slice(edges[k], edges[k + 1])
            if len(set(y.iloc[va])) < 2 or len(set(y.iloc[tr])) < 2:
                continue
            m = _fit_lgb(X.iloc[tr], y.iloc[tr], w.iloc[tr], params)
            aucs.append(roc_auc_score(y.iloc[va], m.predict_proba(X.iloc[va])[:, 1],
                                      sample_weight=w.iloc[va]))
        score = np.mean(aucs) if aucs else -np.inf
        if score > best_auc:
            best, best_auc = params, score
    return best or {k: v[0] for k, v in LGB_GRID.items()}


def _calibrated(raw_fit, X_tr, y_tr, w_tr, X_te):
    """Fit on first 80% (time order), isotonic on last 20%, predict test."""
    n = len(X_tr)
    cut = int(n * 0.8)
    model = raw_fit(X_tr.iloc[:cut], y_tr.iloc[:cut], w_tr.iloc[:cut])
    p_cal = model(X_tr.iloc[cut:])
    iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
    if len(set(y_tr.iloc[cut:])) < 2:
        return np.clip(model(X_te), 0.0, 1.0)  # cannot calibrate; raw probs
    iso.fit(p_cal, y_tr.iloc[cut:], sample_weight=w_tr.iloc[cut:])
    return iso.predict(model(X_te))


def fit_predict_fold(X_tr, y_tr, w_tr, X_te, model_type: str) -> np.ndarray:
    if model_type == "constant":
        return np.full(len(X_te), float(np.average(y_tr, weights=w_tr)))

    if model_type == "logit":
        med = X_tr.median()
        mu, sd = X_tr.mean(), X_tr.std().replace(0, 1)

        def _fit(Xa, ya, wa):
            Z = ((Xa.fillna(med) - mu) / sd).fillna(0.0)
            clf = LogisticRegression(max_iter=1000)
            clf.fit(Z, ya, sample_weight=wa)
            return lambda Xb: clf.predict_proba(
                ((Xb.fillna(med) - mu) / sd).fillna(0.0))[:, 1]

        return _calibrated(_fit, X_tr, y_tr, w_tr, X_te)

    if model_type == "lgb":
        params = _inner_cv_select(X_tr, y_tr, w_tr)

        def _fit(Xa, ya, wa):
            m = _fit_lgb(Xa, ya, wa, params)
            return lambda Xb: m.predict_proba(Xb)[:, 1]

        return _calibrated(_fit, X_tr, y_tr, w_tr, X_te)

    raise ValueError(f"unknown model_type {model_type!r}")


def run_walk_forward(X, y, w, meta, folds, model_type: str) -> pd.DataFrame:
    rows = []
    for tr, te in folds:
        # time-order train rows for chronological inner CV / calib split
        order = np.argsort(meta.iloc[tr]["event_date"].values)
        tr_sorted = np.asarray(tr)[order]
        p = fit_predict_fold(
            X.iloc[tr_sorted], y.iloc[tr_sorted], w.iloc[tr_sorted],
            X.iloc[te], model_type,
        )
        block = meta.iloc[te].copy()
        block["p"], block["y"], block["w"] = p, y.iloc[te].values, w.iloc[te].values
        rows.append(block)
    return pd.concat(rows, ignore_index=True)


def evaluate_g1(preds_by_model: dict, n_boot: int = 2000, seed: int = 7) -> dict:
    lgb_df = preds_by_model["lgb"]
    out = {}
    for name, df in preds_by_model.items():
        out[f"{name}_auc"] = (
            roc_auc_score(df["y"], df["p"], sample_weight=df["w"])
            if len(set(df["y"])) > 1 and df["p"].nunique() > 1 else 0.5
        )
        out[f"{name}_brier"] = brier_score_loss(df["y"], df["p"], sample_weight=df["w"])

    rng = np.random.default_rng(seed)
    n = len(lgb_df)
    aucs = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        s = lgb_df.iloc[idx]
        if len(set(s["y"])) < 2 or s["p"].nunique() < 2:
            continue
        aucs.append(roc_auc_score(s["y"], s["p"], sample_weight=s["w"]))
    lo, hi = (np.percentile(aucs, [2.5, 97.5]) if aucs else (0.0, 1.0))
    out["auc_ci_low"], out["auc_ci_high"] = float(lo), float(hi)
    out["n_events"] = n
    out["g1_pass"] = bool(
        lo > 0.5
        and out["lgb_auc"] > out["logit_auc"]
        and out["lgb_brier"] <= out["constant_brier"]
    )
    return out

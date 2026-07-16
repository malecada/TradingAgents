"""Meta-model layer: constant / logistic baselines + LightGBM with inner
purged chronological CV over the frozen 8-combo grid, isotonic calibration
on the last 20% of train (time-ordered). G1 evaluation per gates.json.

Inner-CV hyperparameter selection is embargo-purged whenever event metadata
(``event_date``/``touch_date``) is supplied to ``fit_predict_fold`` /
``_inner_cv_select`` via the optional ``meta_tr`` argument: any inner-fold
training row whose label window (``touch_date``) extends within
``EMBARGO_CAL_DAYS`` of the inner validation block's start is excluded, so
train events cannot leak information about outcomes that resolve inside (or
just before) the validation block. When ``meta_tr`` is omitted, no purge is
applied (unembargoed chronological CV) — ``run_walk_forward`` always
supplies it, so the real pipeline is purged; callers that only have X/y/w
(e.g. quick unit tests) fall back to the unpurged mode.
"""
from __future__ import annotations

import itertools

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score

from tradingagents.metalabel.wf import EMBARGO_CAL_DAYS

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


def _inner_cv_select(X, y, w, meta_tr: pd.DataFrame | None = None):
    """Select the best LGB hyperparameter combo via chronological 3-fold CV.

    Row order of ``X``/``y``/``w`` (and ``meta_tr``, if given) must already
    be time-ordered. Two expanding-window folds are evaluated: train
    ``[0:e_k)``, validate ``[e_k:e_{k+1})`` for the two internal edges.

    When ``meta_tr`` is provided (columns ``event_date`` and ``touch_date``,
    row-aligned with ``X``), each inner fold's training slice is purged: any
    row whose ``touch_date`` falls on or after
    ``meta_tr["event_date"].iloc[e_k] - EMBARGO_CAL_DAYS`` days is dropped
    before fitting, so training events whose label window extends into (or
    within the embargo of) the validation block cannot bias hyperparameter
    selection. When ``meta_tr`` is ``None``, no purge is applied — plain
    unembargoed chronological CV.

    Args:
        X: Train feature frame, time-ordered.
        y: Train binary labels, aligned with ``X``.
        w: Train sample weights, aligned with ``X``.
        meta_tr: Optional event metadata (``event_date``, ``touch_date``)
            aligned row-wise with ``X``, used to embargo-purge inner folds.
            Defaults to ``None`` (no purge).

    Returns:
        The hyperparameter dict (subset of ``LGB_GRID``) with the highest
        mean validation AUC across evaluable inner folds; falls back to the
        first grid combo if no fold was evaluable.
    """
    n = len(X)
    edges = [0, n // 3, 2 * n // 3, n]
    best, best_auc = None, -np.inf
    for combo in itertools.product(*LGB_GRID.values()):
        params = dict(zip(LGB_GRID.keys(), combo))
        aucs = []
        for k in (1, 2):  # expanding: train [0:e_k), validate [e_k:e_{k+1})
            tr = slice(0, edges[k])
            va = slice(edges[k], edges[k + 1])
            tr_idx = np.arange(tr.start, tr.stop)
            if meta_tr is not None:
                cutoff = meta_tr["event_date"].iloc[edges[k]] - pd.Timedelta(
                    days=EMBARGO_CAL_DAYS)
                keep = meta_tr["touch_date"].iloc[tr_idx].values < cutoff
                tr_idx = tr_idx[keep]
            if len(tr_idx) == 0 or len(set(y.iloc[va])) < 2 or len(set(y.iloc[tr_idx])) < 2:
                continue
            m = _fit_lgb(X.iloc[tr_idx], y.iloc[tr_idx], w.iloc[tr_idx], params)
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
    if len(set(y_tr.iloc[:cut])) < 2:
        # Fit slice is single-class: no decision boundary to learn. Fall
        # back to a constant base-rate prediction over the full weighted
        # train set rather than raising inside raw_fit.
        base_rate = float(np.average(y_tr, weights=w_tr))
        return np.full(len(X_te), base_rate)
    model = raw_fit(X_tr.iloc[:cut], y_tr.iloc[:cut], w_tr.iloc[:cut])
    p_cal = model(X_tr.iloc[cut:])
    iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
    if len(set(y_tr.iloc[cut:])) < 2:
        return np.clip(model(X_te), 0.0, 1.0)  # cannot calibrate; raw probs
    iso.fit(p_cal, y_tr.iloc[cut:], sample_weight=w_tr.iloc[cut:])
    return iso.predict(model(X_te))


def fit_predict_fold(
    X_tr, y_tr, w_tr, X_te, model_type: str,
    *, meta_tr: pd.DataFrame | None = None,
) -> np.ndarray:
    """Fit one of the three meta-model types on a train fold and predict test.

    ``X_tr``/``y_tr``/``w_tr`` (and ``meta_tr``, if given) must already be
    time-ordered by row. For ``model_type="lgb"``, hyperparameters are
    selected via ``_inner_cv_select`` (embargo-purged when ``meta_tr`` is
    supplied — see that function's docstring), then the winning combo is
    calibrated via ``_calibrated`` (80/20 time-ordered split, isotonic
    regression on the last 20%). ``model_type="logit"`` follows the same
    calibration path with a standardized logistic regression base learner.
    ``model_type="constant"`` returns the weighted train base rate for
    every test row, with no calibration step.

    Args:
        X_tr: Train feature frame, time-ordered.
        y_tr: Train binary labels, aligned with ``X_tr``.
        w_tr: Train sample weights, aligned with ``X_tr``.
        X_te: Test feature frame to predict on.
        model_type: One of ``"constant"``, ``"logit"``, ``"lgb"``.
        meta_tr: Optional event metadata (``event_date``, ``touch_date``)
            aligned row-wise with ``X_tr``. Only consulted by the ``"lgb"``
            path's inner CV, to embargo-purge hyperparameter selection.
            Defaults to ``None`` (unpurged inner CV).

    Returns:
        Array of predicted probabilities in ``[0, 1]``, one per row of
        ``X_te``.

    Raises:
        ValueError: If ``model_type`` is not one of the supported values.
    """
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
        params = _inner_cv_select(X_tr, y_tr, w_tr, meta_tr=meta_tr)

        def _fit(Xa, ya, wa):
            m = _fit_lgb(Xa, ya, wa, params)
            return lambda Xb: m.predict_proba(Xb)[:, 1]

        return _calibrated(_fit, X_tr, y_tr, w_tr, X_te)

    raise ValueError(f"unknown model_type {model_type!r}")


def run_walk_forward(X, y, w, meta, folds, model_type: str) -> pd.DataFrame:
    """Run a full walk-forward evaluation of one meta-model type over folds.

    For each ``(train_idx, test_idx)`` fold, train rows are sorted into
    time order by ``meta["event_date"]``, the corresponding event metadata
    (``event_date``, ``touch_date``) is passed through to
    ``fit_predict_fold`` so that ``model_type="lgb"``'s inner CV is
    embargo-purged, and predictions are produced for the (unsorted) test
    rows.

    Args:
        X: Full feature frame, indexed consistently with ``meta``.
        y: Full binary label series, aligned with ``X``.
        w: Full sample weight series, aligned with ``X``.
        meta: Event-level metadata with ``event_date`` and ``touch_date``
            columns, aligned row-wise with ``X``.
        folds: List of ``(train_idx, test_idx)`` integer index-array pairs.
        model_type: One of ``"constant"``, ``"logit"``, ``"lgb"``, passed
            through to ``fit_predict_fold``.

    Returns:
        A concatenated DataFrame of all test-fold rows (one row per
        out-of-fold prediction), with ``meta`` columns plus ``p``
        (predicted probability), ``y`` (true label), and ``w`` (weight).
    """
    rows = []
    for tr, te in folds:
        # time-order train rows for chronological inner CV / calib split
        order = np.argsort(meta.iloc[tr]["event_date"].values)
        tr_sorted = np.asarray(tr)[order]
        meta_tr = meta.iloc[tr_sorted][["event_date", "touch_date"]].reset_index(drop=True)
        p = fit_predict_fold(
            X.iloc[tr_sorted], y.iloc[tr_sorted], w.iloc[tr_sorted],
            X.iloc[te], model_type, meta_tr=meta_tr,
        )
        block = meta.iloc[te].copy()
        block["p"], block["y"], block["w"] = p, y.iloc[te].values, w.iloc[te].values
        rows.append(block)
    return pd.concat(rows, ignore_index=True)


def evaluate_g1(
    preds_by_model: dict, n_boot: int = 2000, seed: int = 7,
    clusters: pd.Series | None = None,
) -> dict:
    """Evaluate the G1 gate (LGB beats logit/constant with a positive CI).

    Computes AUC and Brier score per model in ``preds_by_model``, plus a
    percentile bootstrap 95% CI on the LGB model's AUC. The gate passes iff
    the LGB AUC's bootstrap CI lower bound exceeds 0.5, LGB AUC beats logit
    AUC, and LGB Brier is no worse than the constant baseline's Brier.

    Args:
        preds_by_model: Mapping of model name to the out-of-fold prediction
            DataFrame returned by ``run_walk_forward`` (must contain a
            ``"lgb"`` key plus columns ``y``, ``p``, ``w``).
        n_boot: Number of bootstrap resamples for the LGB AUC CI.
        seed: Seed for the bootstrap RNG (reproducibility).
        clusters: Optional cluster id per row of the LGB predictions frame
            (row-aligned; values are arbitrary hashable ids, e.g. a
            coin-month key). When given, each bootstrap draw is a two-stage
            cluster bootstrap: resample unique cluster ids with
            replacement, then resample each picked cluster's member rows
            with replacement (same cluster size) — honest under both
            cross-cluster and within-cluster overlap from the dense in-bar
            event scheme, where naive whole-block duplication would damp
            AUC's rank-statistic variance below the iid case. When ``None``
            (default), the bootstrap is iid over rows — v1 behavior,
            bit-identical (same rng consumption pattern:
            ``rng.integers(0, n, n)`` per draw).

    Returns:
        Dict with per-model ``{name}_auc`` / ``{name}_brier`` keys,
        ``auc_ci_low`` / ``auc_ci_high`` (LGB bootstrap CI), ``n_events``
        (LGB fold row count), and the boolean ``g1_pass`` gate result.
    """
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
    uniq, members = None, None
    if clusters is not None:
        cluster_ids = np.asarray(clusters)
        uniq = np.unique(cluster_ids)
        members = {c: np.where(cluster_ids == c)[0] for c in uniq}
    aucs = []
    for _ in range(n_boot):
        if clusters is not None:
            picked = rng.choice(uniq, size=len(uniq), replace=True)
            # Two-stage: resample cluster ids, then resample member rows
            # within each picked cluster (with replacement) so overlap
            # within a cluster (dense in-bar events, same coin-month) is
            # reflected in CI width rather than damped by verbatim
            # whole-block duplication.
            idx = np.concatenate([
                rng.choice(members[c], size=len(members[c]), replace=True)
                for c in picked
            ])
        else:
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

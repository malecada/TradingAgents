import numpy as np
import pandas as pd

from tradingagents.metalabel.model import (
    evaluate_g1, fit_predict_fold, run_walk_forward,
)


def _learnable(n=800, seed=3):
    rng = np.random.default_rng(seed)
    X = pd.DataFrame(rng.normal(size=(n, 5)), columns=[f"f{i}" for i in range(5)])
    logit = 1.5 * X["f0"] - 1.0 * X["f1"]
    y = pd.Series((rng.random(n) < 1 / (1 + np.exp(-logit))).astype(int))
    w = pd.Series(np.ones(n))
    return X, y, w


def test_constant_baseline_predicts_base_rate():
    X, y, w = _learnable()
    p = fit_predict_fold(X[:600], y[:600], w[:600], X[600:], "constant")
    assert np.allclose(p, y[:600].mean())


def test_lgb_beats_chance_on_learnable_data():
    X, y, w = _learnable()
    from sklearn.metrics import roc_auc_score
    p = fit_predict_fold(X[:600], y[:600], w[:600], X[600:], "lgb")
    assert roc_auc_score(y[600:], p) > 0.65
    assert (p >= 0).all() and (p <= 1).all()


def test_lgb_handles_nan_features():
    X, y, w = _learnable()
    X.loc[::3, "f2"] = np.nan
    p = fit_predict_fold(X[:600], y[:600], w[:600], X[600:], "lgb")
    assert np.isfinite(p).all()


def test_run_walk_forward_and_g1():
    X, y, w = _learnable()
    ev = pd.date_range("2021-07-01", periods=len(X), freq="D")
    meta = pd.DataFrame({"event_date": ev, "touch_date": ev + pd.Timedelta(days=10),
                         "coin": "bitcoin"})
    folds = [(np.arange(0, 500), np.arange(500, 650)),
             (np.arange(0, 620), np.arange(650, 800))]
    preds = {m: run_walk_forward(X, y, w, meta, folds, m)
             for m in ("constant", "logit", "lgb")}
    g1 = evaluate_g1(preds, n_boot=200)
    assert {"lgb_auc", "auc_ci_low", "auc_ci_high", "logit_auc",
            "constant_brier", "lgb_brier", "g1_pass"} <= set(g1)
    assert g1["g1_pass"] in (True, False)
    assert g1["lgb_auc"] > 0.6  # learnable synthetic


def test_inner_cv_purge_runs_with_overlapping_touch_dates():
    # Many events' label windows (touch_date) extend 30 days past event_date,
    # i.e. well past the neighboring inner-CV validation block boundaries —
    # this is exactly the leakage scenario the embargo purge guards against.
    # We don't assert which combo wins (seed-dependent); this is a
    # behavioral smoke test that purging doesn't break the selection path.
    X, y, w = _learnable()
    X_tr, y_tr, w_tr, X_te = X[:600], y[:600], w[:600], X[600:650]
    ev = pd.date_range("2021-07-01", periods=len(X_tr), freq="D")
    meta = pd.DataFrame({"event_date": ev, "touch_date": ev + pd.Timedelta(days=30)})
    p = fit_predict_fold(X_tr, y_tr, w_tr, X_te, "lgb", meta_tr=meta)
    assert np.isfinite(p).all()
    assert (p >= 0).all() and (p <= 1).all()


def test_calibrated_single_class_fit_slice_does_not_raise():
    X, y, w = _learnable()
    X_tr, y_tr, w_tr, X_te = X[:600].copy(), y[:600].copy(), w[:600].copy(), X[600:650]
    cut = int(len(y_tr) * 0.8)
    y_tr.iloc[:cut] = 0  # first-80% fit slice becomes single-class
    tail_n = len(y_tr) - cut
    y_tr.iloc[cut:] = np.array([0, 1] * (tail_n // 2 + 1))[:tail_n]
    p = fit_predict_fold(X_tr, y_tr, w_tr, X_te, "lgb")
    assert np.isfinite(p).all()
    assert (p >= 0).all() and (p <= 1).all()


def test_g1_fails_on_noise():
    rng = np.random.default_rng(0)
    n = 600
    X = pd.DataFrame(rng.normal(size=(n, 5)), columns=[f"f{i}" for i in range(5)])
    y = pd.Series(rng.integers(0, 2, n))
    w = pd.Series(np.ones(n))
    ev = pd.date_range("2021-07-01", periods=n, freq="D")
    meta = pd.DataFrame({"event_date": ev, "touch_date": ev + pd.Timedelta(days=10),
                         "coin": "bitcoin"})
    folds = [(np.arange(0, 400), np.arange(400, 600))]
    preds = {m: run_walk_forward(X, y, w, meta, folds, m)
             for m in ("constant", "logit", "lgb")}
    assert evaluate_g1(preds, n_boot=200)["g1_pass"] is False

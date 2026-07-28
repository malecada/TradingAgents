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


def test_cluster_bootstrap_point_estimates_and_determinism():
    X, y, w = _learnable()
    ev = pd.date_range("2021-07-01", periods=len(X), freq="D")
    meta = pd.DataFrame({"event_date": ev, "touch_date": ev + pd.Timedelta(days=10),
                         "coin": "bitcoin"})
    folds = [(np.arange(0, 500), np.arange(500, 800))]
    preds = {m: run_walk_forward(X, y, w, meta, folds, m)
             for m in ("constant", "logit", "lgb")}
    iid = evaluate_g1(preds, n_boot=300)
    lgb_df = preds["lgb"]
    clusters = lgb_df["event_date"].dt.to_period("M").astype(str) + "_" + lgb_df["coin"]
    clu = evaluate_g1(preds, n_boot=300, clusters=clusters)

    # point estimates (computed once on the full frame, before the
    # bootstrap loop) are identical regardless of CI method
    assert clu["lgb_auc"] == iid["lgb_auc"]
    assert clu["logit_auc"] == iid["logit_auc"]
    assert clu["constant_auc"] == iid["constant_auc"]
    assert clu["lgb_brier"] == iid["lgb_brier"]
    assert clu["logit_brier"] == iid["logit_brier"]
    assert clu["constant_brier"] == iid["constant_brier"]

    # cluster CI is a well-formed interval
    assert np.isfinite(clu["auc_ci_low"]) and np.isfinite(clu["auc_ci_high"])
    assert 0.0 <= clu["auc_ci_low"] < clu["auc_ci_high"] <= 1.0
    assert "g1_pass" in clu

    # determinism: same seed, same call twice -> identical CI
    clu2 = evaluate_g1(preds, n_boot=300, clusters=clusters)
    assert clu2["auc_ci_low"] == clu["auc_ci_low"]
    assert clu2["auc_ci_high"] == clu["auc_ci_high"]


def test_cluster_bootstrap_wider_under_cluster_correlation():
    # Build predictions with REAL within-cluster correlation: 40 clusters
    # (coin-months), each with 20 rows that are near-duplicates (same y,
    # nearly-same p) because they share one latent cluster-level draw.
    # Under this design the cluster CI must be materially wider than an
    # iid CI computed on the same data, since the effective sample size
    # is ~40 clusters, not ~800 rows.
    rng = np.random.default_rng(11)
    n_clusters, rows_per_cluster = 40, 20
    ev0 = pd.Timestamp("2021-07-01")

    rows = []
    for c in range(n_clusters):
        u = rng.normal()
        y_cluster = int(rng.random() < 1 / (1 + np.exp(-u)))
        p_cluster = 1 / (1 + np.exp(-(u + rng.normal(scale=0.05))))
        coin = "bitcoin" if c % 2 == 0 else "ethereum"
        month_date = ev0 + pd.DateOffset(months=c // 2)
        for r in range(rows_per_cluster):
            rows.append({
                "event_date": month_date + pd.Timedelta(days=r),
                "y": y_cluster,
                "p": float(np.clip(p_cluster, 1e-6, 1 - 1e-6)),
                "w": 1.0,
                "coin": coin,
            })
    lgb_df = pd.DataFrame(rows)

    # constant/logit baselines only need >1 unique value and both classes
    # present; their exact values don't matter for this test.
    base_rate = lgb_df["y"].mean()
    const_df = lgb_df.copy()
    const_df["p"] = np.clip(
        base_rate + rng.normal(scale=0.01, size=len(const_df)), 1e-6, 1 - 1e-6)
    logit_df = lgb_df.copy()
    logit_df["p"] = np.clip(
        lgb_df["p"] * 0.8 + rng.normal(scale=0.02, size=len(logit_df)), 1e-6, 1 - 1e-6)

    preds = {"constant": const_df, "logit": logit_df, "lgb": lgb_df}

    iid = evaluate_g1(preds, n_boot=1000, seed=5)
    clusters = lgb_df["event_date"].dt.to_period("M").astype(str) + "_" + lgb_df["coin"]
    clu = evaluate_g1(preds, n_boot=1000, seed=5, clusters=clusters)

    iid_width = iid["auc_ci_high"] - iid["auc_ci_low"]
    clu_width = clu["auc_ci_high"] - clu["auc_ci_low"]
    assert clu_width > iid_width * 1.15


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

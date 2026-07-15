import numpy as np
import pandas as pd

from tradingagents.metalabel.primary import compute_votes, extract_events
from tradingagents.metalabel.labeler import triple_barrier_labels, uniqueness_weights
from tradingagents.metalabel.features import (
    OC_FEATURES, price_trend_features, assemble_dataset,
)


def _trendy_ohlcv(n=200, seed=1):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2022-01-01", periods=n, freq="D")
    ret = rng.normal(0.002, 0.03, n)
    c = 100 * np.exp(np.cumsum(ret))
    return pd.DataFrame({
        "Date": idx, "Open": c, "High": c * 1.02, "Low": c * 0.98,
        "Close": c, "Volume": 1.0,
    })


def _coin_blob(seed):
    ohlcv = _trendy_ohlcv(seed=seed)
    votes = compute_votes(ohlcv)
    events = extract_events(votes)
    labels = triple_barrier_labels(ohlcv, events)
    weights = uniqueness_weights(labels, pd.DatetimeIndex(ohlcv["Date"]))
    return {"ohlcv": ohlcv, "votes": votes, "labels": labels,
            "weights": weights, "onchain": None, "fng": None}


def test_price_trend_features_causal_and_complete():
    blob = _coin_blob(1)
    ev = blob["labels"].index
    f = price_trend_features(blob["ohlcv"], blob["votes"], ev)
    assert list(f.index) == list(ev)
    for col in ("f_vote", "f_trend_age", "f_dist_20d_high", "f_ret_20d",
                "f_ret_60d", "f_sigma_level", "f_sigma_pctl_60d", "f_volvol"):
        assert col in f.columns
    # causality: mutate bars after the first event -> its features unchanged
    first = ev[0]
    base = f.loc[first].copy()
    df2 = blob["ohlcv"].copy()
    df2.loc[df2["Date"] > first, "Close"] = 9999.0
    f2 = price_trend_features(df2, blob["votes"], ev[:1])
    pd.testing.assert_series_equal(f2.loc[first], base, check_names=False)


def test_assemble_dataset_shapes_and_onehots():
    per_coin = {"bitcoin": _coin_blob(1), "ethereum": _coin_blob(2)}
    X, y, w, meta = assemble_dataset(per_coin)
    assert len(X) == len(y) == len(w) == len(meta)
    assert len(X) == len(per_coin["bitcoin"]["labels"]) + len(per_coin["ethereum"]["labels"])
    assert "coin_bitcoin" in X.columns and "coin_ethereum" in X.columns
    assert set(y.unique()) <= {0, 1}
    # missing onchain/fng -> NaN columns present (LGB-native handling), not dropped
    for c in OC_FEATURES + ["f_fng"]:
        assert c in X.columns
        assert X[c].isna().all()
    assert "f_breadth" in X.columns
    assert X["f_breadth"].between(0, 1).all()


def test_assemble_dataset_normalizes_tz_aware_onchain_index():
    # build_pit_onchain_features returns a UTC tz-AWARE DatetimeIndex in
    # production; event dates (labels.index) are tz-naive. Regression for
    # C1: reindexing a tz-aware series against tz-naive dates silently
    # returns all-NaN (no error) unless assemble_dataset normalizes tz
    # itself as defense-in-depth against a caller that forgot to.
    blob = _coin_blob(1)
    ev = blob["labels"].index
    col = OC_FEATURES[0]
    known_values = np.arange(len(ev), dtype=float)
    oc = pd.DataFrame(
        {col: known_values},
        index=pd.DatetimeIndex(ev, tz="UTC"),
    )
    blob["onchain"] = oc

    X, y, w, meta = assemble_dataset({"bitcoin": blob})

    assert not X[col].isna().any()
    np.testing.assert_array_equal(X[col].to_numpy(), known_values)

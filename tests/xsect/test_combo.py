"""combo_c1 — pure combination engine (tradingagents.xsect.combo).

Registered mechanics (docs/superpowers/specs/2026-09-02-combo-c1-charter.md):
fixed capital weights on daily sleeve net returns (constant-mix book), W1
inverse-vol from dev-window daily SDs, W2 equal; zero-fill on days a sleeve
does not cover; per-sleeve contribution = w_i * mean_i; pooled top-name share;
drawdown on compounded simple returns; dual-family weight-path placebos;
holdout verdict-file lock.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from tradingagents.xsect.combo import (
    HoldoutAlreadySpent, align_sleeves, assert_holdout_unspent, combine,
    equal_weights, gate_verdict, indep_shift, inverse_vol_weights, maxdd_simple,
    shared_shift, sleeve_contributions, top_name_share,
)


def _idx(n, start="2021-01-01"):
    return pd.date_range(start, periods=n, freq="D", tz="UTC")


def test_align_sleeves_zero_fills_uncovered_days():
    idx = _idx(6)
    a = pd.Series([0.01, 0.02, 0.03], index=idx[1:4])
    b = pd.Series([0.1, -0.1], index=idx[4:6])
    df = align_sleeves({"a": a, "b": b}, idx)
    assert list(df.columns) == ["a", "b"] and len(df) == 6
    assert df.loc[idx[0], "a"] == 0.0 and df.loc[idx[5], "a"] == 0.0
    assert df.loc[idx[4], "b"] == pytest.approx(0.1) and df.loc[idx[0], "b"] == 0.0
    assert not df.isna().any().any()


def test_align_rejects_series_with_days_outside_index():
    idx = _idx(3)
    a = pd.Series([0.01, 0.02], index=_idx(2, start="2021-01-05"))
    with pytest.raises(ValueError):
        align_sleeves({"a": a}, idx)


def test_inverse_vol_weights_sum_to_one_and_scale_inversely():
    idx = _idx(400)
    rng = np.random.default_rng(0)
    dev = pd.DataFrame({"lo": rng.normal(0, 0.01, 400), "hi": rng.normal(0, 0.02, 400)}, index=idx)
    w = inverse_vol_weights(dev)
    assert sum(w.values()) == pytest.approx(1.0)
    assert w["lo"] / w["hi"] == pytest.approx(dev["hi"].std(ddof=1) / dev["lo"].std(ddof=1))
    assert all(v > 0 for v in w.values())


def test_inverse_vol_refuses_zero_variance_sleeve():
    idx = _idx(50)
    dev = pd.DataFrame({"a": np.zeros(50), "b": np.ones(50) * 0.01}, index=idx)
    dev.loc[idx[0], "b"] = 0.02
    with pytest.raises(ValueError):
        inverse_vol_weights(dev)


def test_equal_weights():
    w = equal_weights(["a", "b", "c", "d"])
    assert w == {"a": 0.25, "b": 0.25, "c": 0.25, "d": 0.25}


def test_combine_is_fixed_weight_constant_mix_and_contributions_sum():
    idx = _idx(5)
    df = pd.DataFrame({"a": [0.01, -0.02, 0.0, 0.03, 0.01],
                       "b": [0.0, 0.01, 0.01, -0.01, 0.02]}, index=idx)
    w = {"a": 0.7, "b": 0.3}
    c = combine(df, w)
    assert np.allclose(c.to_numpy(), 0.7 * df["a"].to_numpy() + 0.3 * df["b"].to_numpy())
    contrib = sleeve_contributions(df, w)
    assert sum(contrib.values()) == pytest.approx(c.mean())
    assert contrib["a"] == pytest.approx(0.7 * df["a"].mean())


def test_combine_rejects_weights_not_matching_columns():
    idx = _idx(3)
    df = pd.DataFrame({"a": [0.0, 0.0, 0.0]}, index=idx)
    with pytest.raises(ValueError):
        combine(df, {"a": 0.5, "b": 0.5})
    with pytest.raises(ValueError):
        combine(df, {"a": 0.9})  # must sum to 1


def test_top_name_share_pools_across_sleeves_by_symbol():
    pnl = {"s1": {"BTCUSDT": 1.0, "ETHUSDT": -0.5}, "s2": {"BTCUSDT": 0.5, "SOLUSDT": 0.5}}
    name, share = top_name_share(pnl)
    assert name == "BTCUSDT"
    assert share == pytest.approx(1.5 / (1.5 + 0.5 + 0.5))


def test_top_name_share_empty():
    assert top_name_share({}) == (None, 0.0)


def test_maxdd_simple_compounds():
    idx = _idx(3)
    s = pd.Series([0.5, -0.5, 0.0], index=idx)  # 1 -> 1.5 -> 0.75: dd = 50%
    assert maxdd_simple(s) == pytest.approx(0.5)
    assert maxdd_simple(pd.Series([0.01, 0.01], index=idx[:2])) == pytest.approx(0.0)


def test_indep_shift_rolls_each_column_independently_preserving_sums():
    idx = _idx(200)
    rng = np.random.default_rng(1)
    W = pd.DataFrame(rng.random((200, 3)), index=idx, columns=list("abc"))
    S = indep_shift(W, np.random.default_rng(5), min_shift=30)
    assert S.index.equals(W.index) and list(S.columns) == list(W.columns)
    assert np.allclose(S.sum(axis=0), W.sum(axis=0))
    # not all columns share one offset (with overwhelming probability)
    offs = []
    for c in W.columns:
        k = next(k for k in range(200) if np.allclose(np.roll(W[c].to_numpy(), k), S[c].to_numpy()))
        offs.append(k)
        assert 30 <= k <= 170
    assert len(set(offs)) > 1


def test_shared_shift_uses_one_offset_for_all_columns_and_scales_hourly():
    idx = _idx(100)
    rng = np.random.default_rng(1)
    W = pd.DataFrame(rng.random((100, 2)), index=idx, columns=list("ab"))
    S = shared_shift(W, offset_days=7)
    assert np.allclose(S.to_numpy(), np.roll(W.to_numpy(), 7, axis=0))
    hidx = pd.date_range("2021-01-01", periods=100 * 24, freq="h", tz="UTC")
    Wh = pd.DataFrame(rng.random((2400, 2)), index=hidx, columns=list("ab"))
    Sh = shared_shift(Wh, offset_days=7)
    assert np.allclose(Sh.to_numpy(), np.roll(Wh.to_numpy(), 7 * 24, axis=0))


def test_gate_verdict_all_required():
    m = {"sr_h": 0.9, "sr_dev": 1.4, "placebo_p_worse": 0.02, "min_contrib": 0.0001,
         "maxdd": 0.12, "top_name_share": 0.3, "convention_swap_flips": False}
    g = {"sr_ratio_min": 0.5, "sr_abs_min": 0.5, "placebo_p_max": 0.10,
         "sleeve_contribution_min": 0.0, "maxdd_max": 0.25, "top_name_share_max": 0.5}
    v = gate_verdict(m, g)
    assert v["pass"] is True and all(v["checks"].values())
    v2 = gate_verdict({**m, "sr_h": 0.6}, g)          # 0.6 < 0.5*1.4 = 0.7
    assert v2["pass"] is False and v2["checks"]["sr_ratio"] is False
    v3 = gate_verdict({**m, "sr_h": -0.9, "sr_dev": -1.4}, g)  # same sign but negative
    assert v3["pass"] is False and v3["checks"]["sr_abs"] is False and v3["checks"]["same_sign"] is True
    v4 = gate_verdict({**m, "convention_swap_flips": True}, g)
    assert v4["pass"] is False and v4["checks"]["convention_swap"] is False
    v5 = gate_verdict({**m, "min_contrib": -1e-9}, g)
    assert v5["pass"] is False and v5["checks"]["sleeve_contribution"] is False


def test_holdout_lock(tmp_path):
    lock = tmp_path / "holdout_verdict.json"
    assert_holdout_unspent(lock)  # absent -> fine
    lock.write_text(json.dumps({"verdict": "FAIL"}))
    with pytest.raises(HoldoutAlreadySpent):
        assert_holdout_unspent(lock)

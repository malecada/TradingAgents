import numpy as np
import pandas as pd
import pytest

from tradingagents.xsect.ls_common import ls_weights, sharpe_365, zero_funding


def _days(n=21):
    return pd.date_range("2022-01-03", periods=n, freq="D", tz="UTC")


def test_weights_are_dollar_neutral_and_legs_disjoint():
    days = _days()
    cols = [f"S{i}" for i in range(10)]
    S = pd.DataFrame(np.tile(np.arange(10.0), (len(days), 1)), index=days, columns=cols)
    valid = pd.DataFrame(True, index=days, columns=cols)
    rb = days[days.dayofweek == 0]
    W = ls_weights(days, S, valid, rb, leg_frac=0.2)
    row = W.loc[rb[0]]
    assert row.sum() == pytest.approx(0.0, abs=1e-12)
    assert (row > 0).sum() == 2 and (row < 0).sum() == 2
    # highest signal is shorted, lowest is longed
    assert row["S9"] < 0 and row["S0"] > 0
    assert set(row[row > 0].index).isdisjoint(row[row < 0].index)


def test_weights_held_constant_between_rebalances():
    days = _days()
    cols = [f"S{i}" for i in range(10)]
    # signal flips sign every day -- weights must NOT follow it intra-week
    base = np.arange(10.0)
    S = pd.DataFrame([base if i % 2 == 0 else base[::-1] for i in range(len(days))],
                     index=days, columns=cols)
    valid = pd.DataFrame(True, index=days, columns=cols)
    rb = days[days.dayofweek == 0]
    W = ls_weights(days, S, valid, rb, leg_frac=0.2)
    seg = W.loc[rb[0]:rb[1] - pd.Timedelta(days=1)]
    assert (seg.nunique() == 1).all()


def test_all_tied_signal_still_disjoint_legs():
    days = _days()
    cols = [f"S{i}" for i in range(10)]
    S = pd.DataFrame(1.0, index=days, columns=cols)
    valid = pd.DataFrame(True, index=days, columns=cols)
    rb = days[days.dayofweek == 0]
    W = ls_weights(days, S, valid, rb, leg_frac=0.2)
    row = W.loc[rb[0]]
    assert set(row[row > 0].index).isdisjoint(row[row < 0].index)
    assert row.sum() == pytest.approx(0.0, abs=1e-12)


def test_flat_when_breadth_below_minimum():
    days = _days()
    cols = [f"S{i}" for i in range(10)]
    S = pd.DataFrame(np.tile(np.arange(10.0), (len(days), 1)), index=days, columns=cols)
    valid = pd.DataFrame(False, index=days, columns=cols)
    valid.iloc[:, :3] = True          # only 3 valid names, below MIN_VALID
    rb = days[days.dayofweek == 0]
    W = ls_weights(days, S, valid, rb, leg_frac=0.2)
    assert (W == 0.0).all().all()


def test_invalid_names_never_get_weight():
    days = _days()
    cols = [f"S{i}" for i in range(10)]
    S = pd.DataFrame(np.tile(np.arange(10.0), (len(days), 1)), index=days, columns=cols)
    valid = pd.DataFrame(True, index=days, columns=cols)
    valid["S9"] = False
    rb = days[days.dayofweek == 0]
    W = ls_weights(days, S, valid, rb, leg_frac=0.2)
    assert (W["S9"] == 0.0).all()


def test_sharpe_365_conventions():
    r = pd.Series([0.01, -0.005, 0.02, 0.0, 0.007])
    expected = r.mean() / r.std(ddof=1) * np.sqrt(365)
    assert sharpe_365(r) == pytest.approx(expected)
    assert sharpe_365(pd.Series([0.01] * 5)) == 0.0     # zero variance -> 0.0
    assert sharpe_365(pd.Series([0.01])) == 0.0          # too short -> 0.0
    assert sharpe_365(pd.Series(dtype=float)) == 0.0


def test_zero_funding_shape():
    days = _days(3)
    F = zero_funding(days, ["A", "B"])
    assert F.shape == (3, 2) and (F == 0.0).all().all()
    assert list(F.columns) == ["A", "B"]


def test_leg_frac_half_is_rejected():
    days = _days()
    cols = [f"S{i}" for i in range(10)]
    S = pd.DataFrame(1.0, index=days, columns=cols)
    valid = pd.DataFrame(True, index=days, columns=cols)
    rb = days[days.dayofweek == 0]
    with pytest.raises(ValueError, match="leg_frac"):
        ls_weights(days, S, valid, rb, leg_frac=0.5)
    with pytest.raises(ValueError, match="leg_frac"):
        ls_weights(days, S, valid, rb, leg_frac=0.0)

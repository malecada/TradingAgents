"""Unit tests for the llm_c2_veto_ovl engine (synthetic data — no stores)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from llm_veto_engine import (  # noqa: E402
    apply_budget, book_metrics, cvar5, o4_scale, oracle_m, overlay_net,
)


@pytest.fixture()
def base():
    rng = np.random.default_rng(7)
    idx = pd.date_range("2021-01-01", "2022-12-31", freq="D", tz="UTC")
    net = pd.Series(rng.normal(0.001, 0.01, len(idx)), index=idx)
    net.iloc[400] = -0.09  # planted crash day
    return pd.DataFrame({"net": net, "turnover": 0.3}, index=idx)


@pytest.fixture()
def breadth(base):
    return pd.Series(150, index=base.index)


def test_scale_zero_below_breadth_floor(base):
    thin = pd.Series(150, index=base.index)
    thin.iloc[:50] = 50
    s = o4_scale(base, thin)
    assert (s.iloc[:50] == 0.0).all()


def test_m_all_ones_is_identity(base, breadth):
    s = o4_scale(base, breadth)
    m = pd.Series(1.0, index=base.index)
    pd.testing.assert_series_equal(overlay_net(base, s * m), overlay_net(base, s))


def test_budget_enforced_calendar_order():
    idx = pd.date_range("2021-01-01", "2021-12-31", freq="D", tz="UTC")
    m = pd.Series(1.0, index=idx)
    m.iloc[5:20] = 0.0  # 15 veto days requested
    out = apply_budget(m, budget=10)
    assert int((out < 1.0).sum()) == 10
    assert (out.iloc[5:15] == 0.0).all()      # first 10 kept
    assert (out.iloc[15:20] == 1.0).all()     # overflow reverted


def test_oracle_flags_worst_days_and_respects_k(base, breadth):
    s = o4_scale(base, breadth)
    ovl = overlay_net(base, s)
    m = oracle_m(ovl, "2021-01-01", "2022-12-31", k=10)
    assert int((m == 0.0).sum()) == 20  # 10 per calendar year
    crash_day = base.index[400]
    assert m.loc[crash_day] == 0.0


def test_oracle_veto_improves_drawdown_and_cvar(base, breadth):
    s = o4_scale(base, breadth)
    ovl = overlay_net(base, s)
    m = oracle_m(ovl, "2021-01-01", "2022-12-31", k=10)
    vet = overlay_net(base, s * m)
    b0 = book_metrics(ovl, "2021-01-01", "2022-12-31")
    b1 = book_metrics(vet, "2021-01-01", "2022-12-31")
    assert b1["maxdd"] < b0["maxdd"]
    assert b1["cvar5"] > b0["cvar5"]  # less negative tail


def test_veto_transitions_are_charged(base, breadth):
    s = o4_scale(base, breadth)
    m = pd.Series(1.0, index=base.index)
    t = 500
    m.iloc[t] = 0.0
    vet = overlay_net(base, s * m)
    ovl = overlay_net(base, s)
    # day after the veto pays re-risking turnover: strictly worse than no-veto
    assert vet.iloc[t + 1] < ovl.iloc[t + 1]


def test_cvar5_is_tail_mean(base):
    x = base["net"]
    q = np.quantile(x.dropna(), 0.05)
    assert cvar5(x) == pytest.approx(float(x[x <= q].mean()))

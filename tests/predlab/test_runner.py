from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tradingagents.predlab import baselines, runner


def _cell(**over):
    cell = {
        "cell": "SYN|24h|T1_ret",
        "target": "T1_ret",
        "horizon_bars": 1,
        "strong_baseline": "rw_zero",
        "loss": "se",
        "min_train": 100,
        "step": 1,
        "refit_every": 1,
        "embargo": 0,
    }
    cell.update(over)
    return cell


def _series(n=600, phi=0.4, seed=0, start="2021-01-01"):
    rng = np.random.default_rng(seed)
    y = np.zeros(n)
    for t in range(1, n):
        y[t] = phi * y[t - 1] + rng.normal(0, 1)
    idx = pd.date_range(start, periods=n, freq="D", tz="UTC")
    return pd.DataFrame({"y": y}, index=idx)


class _AR1(baselines.Forecaster):
    name = "ar1_true"

    def fit(self, y_train, X_train=None):
        self.phi = 0.4

    def predict(self, y_hist, x_now=None):
        return self.phi * y_hist[-1]


def test_runner_detects_planted_predictability():
    out = runner.run_cell(_cell(), _series(), [baselines.RWZero(), _AR1()],
                          gates_key="predlab_p1_classical", tier="t0", dry=True)
    ar = out[out.model == "ar1_true"].iloc[0]
    rw = out[out.model == "rw_zero"].iloc[0]
    assert ar["dm_p"] < 0.01
    assert ar["loss_mean"] < rw["loss_mean"]
    assert ar["n_origins"] == rw["n_origins"] > 400


def test_runner_no_skill_on_white_noise():
    s = _series(phi=0.0, seed=1)
    out = runner.run_cell(_cell(), s, [baselines.RWZero(), baselines.Persistence()],
                          gates_key="predlab_p1_classical", tier="t0", dry=True)
    assert out[out.model == "persistence"].iloc[0]["dm_p"] > 0.05


def test_runner_baseline_row_is_degenerate_vs_itself():
    out = runner.run_cell(_cell(), _series(), [baselines.RWZero()],
                          gates_key="predlab_p1_classical", tier="t0", dry=True)
    assert bool(out.iloc[0]["degenerate"]) is True  # baseline vs itself


def test_runner_eval_start_filters_origins():
    s = _series(n=600, start="2020-06-01")  # history begins before dev window
    out = runner.run_cell(_cell(eval_start="2021-01-01"), s,
                          [baselines.RWZero(), _AR1()],
                          gates_key="predlab_p1_classical", tier="t0", dry=True)
    # 600 daily rows from 2020-06-01 end 2022-01-21; origins must start 2021-01-01,
    # not at min_train (2020-09-09): 386 origins (2021-01-01..2022-01-21)
    assert int(out.iloc[0]["n_origins"]) == 386


def test_runner_refuses_holdout_dates():
    s = _series(n=1700)  # daily from 2021-01-01 runs past 2025-04-01
    with pytest.raises(RuntimeError):
        runner.run_cell(_cell(), s, [baselines.RWZero()],
                        gates_key="predlab_p1_classical", tier="t0", dry=True)


def test_baselines_basic_semantics():
    y = np.array([1.0, 2.0, 3.0, 4.0])
    assert baselines.RWZero().predict(y) == 0.0
    assert baselines.Persistence().predict(y) == 4.0
    assert baselines.HistMean().predict(y) == 2.5
    assert baselines.SeasonalNaive(m=2).predict(y) == 3.0
    ew = baselines.EWMA(lam=0.5)
    # recursion seeded at y[0]: 1 -> .5*1+.5*2=1.5 -> .5*1.5+.5*3=2.25 -> .5*2.25+.5*4=3.125
    assert np.isclose(ew.predict(y), 3.125)
    br = baselines.BaseRate()
    assert np.isclose(br.predict(np.array([1.0, -1.0, 1.0, 1.0])), 0.75)


def test_ewma_incremental_matches_full_recompute():
    rng = np.random.default_rng(7)
    y = rng.gamma(2.0, 0.5, 500)
    inc = baselines.EWMA(lam=0.94)
    seq = [inc.predict(y[:n]) for n in range(10, 501, 7)]
    fresh = [baselines.EWMA(lam=0.94).predict(y[:n]) for n in range(10, 501, 7)]
    assert np.allclose(seq, fresh)
    # shrinking history triggers clean recompute
    assert np.isclose(inc.predict(y[:50]), baselines.EWMA(lam=0.94).predict(y[:50]))


def test_climatology_uses_season_bin():
    y_train = np.array([10.0, 0.0, 10.0, 0.0, 10.0, 0.0])
    X_train = np.array([[0.0], [1.0], [0.0], [1.0], [0.0], [1.0]])
    c = baselines.Climatology(bin_col=0)
    c.fit(y_train, X_train)
    assert c.predict(y_train, np.array([0.0])) == 10.0
    assert c.predict(y_train, np.array([1.0])) == 0.0
    assert c.predict(y_train, np.array([9.0])) == 5.0  # unseen bin -> global mean

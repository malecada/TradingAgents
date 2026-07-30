from __future__ import annotations

import numpy as np
import pandas as pd

from tradingagents.predlab import baselines, runner, tier1


def _ar1_series(n=420, phi=0.5, seed=0, start="2021-01-01"):
    rng = np.random.default_rng(seed)
    y = np.zeros(n)
    for t in range(1, n):
        y[t] = phi * y[t - 1] + rng.normal(0, 1)
    idx = pd.date_range(start, periods=n, freq="D", tz="UTC")
    return pd.DataFrame({"y": y}, index=idx)


def _cell(**over):
    cell = {
        "cell": "SYN|24h|T1_ret", "target": "T1_ret", "horizon_bars": 1,
        "strong_baseline": "rw_zero", "loss": "se",
        "min_train": 120, "step": 1, "refit_every": 5, "embargo": 0,
    }
    cell.update(over)
    return cell


def test_arima_beats_rw_on_planted_ar1():
    out = runner.run_cell(_cell(), _ar1_series(), [baselines.RWZero(), tier1.ArimaForecaster()],
                          gates_key="predlab_p1_classical", tier="t1", dry=True)
    ar = out[out.model == "arima_aic"].iloc[0]
    assert ar["dm_p"] < 0.01
    assert ar["loss_mean"] < out[out.model == "rw_zero"].iloc[0]["loss_mean"]


def test_ets_beats_rw_on_persistent_level():
    # random-walk-with-noise level series: ETS-ANN should track it, RW-zero (forecast 0) cannot
    rng = np.random.default_rng(4)
    level = np.cumsum(rng.normal(0, 0.3, 420)) + 5.0
    y = level + rng.normal(0, 0.5, 420)
    s = pd.DataFrame({"y": y}, index=pd.date_range("2021-01-01", periods=420, freq="D", tz="UTC"))
    out = runner.run_cell(_cell(), s, [baselines.RWZero(), tier1.EtsForecaster("ANN")],
                          gates_key="predlab_p1_classical", tier="t1", dry=True)
    ets = out[out.model == "ets_ann"].iloc[0]
    assert ets["dm_p"] < 1e-6


def test_ets_aan_tracks_trend_better_than_ann():
    rng = np.random.default_rng(5)
    y = 0.05 * np.arange(420) + rng.normal(0, 0.3, 420)
    s = pd.DataFrame({"y": y}, index=pd.date_range("2021-01-01", periods=420, freq="D", tz="UTC"))
    out = runner.run_cell(_cell(strong_baseline="ets_ann"), s,
                          [tier1.EtsForecaster("ANN"), tier1.EtsForecaster("AAN")],
                          gates_key="predlab_p1_classical", tier="t1", dry=True)
    aan = out[out.model == "ets_aan"].iloc[0]
    ann = out[out.model == "ets_ann"].iloc[0]
    assert aan["loss_mean"] < ann["loss_mean"]


def test_logit_lags_learns_sign_persistence():
    rng = np.random.default_rng(6)
    n = 600
    y = np.zeros(n)
    for t in range(1, n):  # strong sign-AR process
        y[t] = (1.0 if y[t - 1] > 0 else -1.0) * 0.8 + rng.normal(0, 1)
    s = pd.DataFrame({"y": y}, index=pd.date_range("2021-01-01", periods=n, freq="D", tz="UTC"))
    cell = _cell(target="T2_dir", loss="brier", strong_baseline="base_rate")
    out = runner.run_cell(cell, s, [baselines.BaseRate(), tier1.LogitLags()],
                          gates_key="predlab_p1_classical", tier="t1", dry=True)
    lg = out[out.model == "logit_lags5"].iloc[0]
    assert lg["dm_p"] < 1e-4  # Brier beats climatology
    assert lg["pt_p"] < 1e-4  # direction skill via PT


def test_arima_pipeline_no_future_leak():
    # truncation equivalence: forecasts for common origins must be identical
    # whether or not the future part of the series exists at all
    full = _ar1_series(n=300, seed=7)
    trunc = full.iloc[:-40]
    ca = _cell(min_train=120, refit_every=10)
    _, preds_full = runner.run_cell(
        ca, full, [baselines.RWZero(), tier1.ArimaForecaster(refit_every=10)],
        gates_key="predlab_p1_classical", tier="t1", dry=True, return_forecasts=True)
    _, preds_trunc = runner.run_cell(
        ca, trunc, [baselines.RWZero(), tier1.ArimaForecaster(refit_every=10)],
        gates_key="predlab_p1_classical", tier="t1", dry=True, return_forecasts=True)
    n_common = len(preds_trunc["arima_aic"])
    assert n_common > 100
    assert np.allclose(preds_full["arima_aic"][:n_common], preds_trunc["arima_aic"])

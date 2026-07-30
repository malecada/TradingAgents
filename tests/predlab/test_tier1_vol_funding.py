from __future__ import annotations

import numpy as np
import pandas as pd

from tradingagents.predlab import baselines, runner, tier1


def test_seasonal_ar_beats_persistence_on_planted_seasonality():
    rng = np.random.default_rng(1)
    n = 700
    m = 7
    season = np.tile([2.0, 0.0, 0.5, 1.5, -1.0, 0.2, 3.0], n // m + 1)[:n]
    y = season + 0.3 * np.r_[0.0, season[:-1]] + rng.normal(0, 0.3, n)
    s = pd.DataFrame({"y": y},
                     index=pd.date_range("2021-01-01", periods=n, freq="D", tz="UTC"))
    cell = {
        "cell": "SYN|24h|T4_vol", "target": "T4_vol", "horizon_bars": 1,
        "strong_baseline": "persistence", "loss": "mase", "mase_m": m,
        "min_train": 120, "step": 1, "refit_every": 1, "embargo": 0,
    }
    out = runner.run_cell(cell, s, [baselines.Persistence(), tier1.SeasonalAR(m=m)],
                          gates_key="predlab_p1_classical", tier="t1", dry=True)
    sa = out[out.model == f"seasonal_ar_m{m}"].iloc[0]
    assert sa["dm_p"] < 1e-6
    assert sa["loss_mean"] < out[out.model == "persistence"].iloc[0]["loss_mean"]


def test_ar1_recovers_phi():
    rng = np.random.default_rng(2)
    n = 2000
    y = np.zeros(n)
    for t in range(1, n):
        y[t] = 0.001 + 0.7 * y[t - 1] + rng.normal(0, 0.01)
    f = tier1.Ar1()
    f.fit(y)
    assert abs(f._phi - 0.7) < 0.05
    assert np.isclose(f.predict(y[:100]), f._c + f._phi * y[99])


def test_dar1_recovers_phi_under_heteroskedasticity():
    rng = np.random.default_rng(3)
    n = 3000
    y = np.zeros(n)
    omega, alpha, phi = 1e-6, 0.5, 0.6
    for t in range(1, n):
        y[t] = phi * y[t - 1] + rng.normal() * np.sqrt(omega + alpha * y[t - 1] ** 2)
    f = tier1.Dar1()
    f.fit(y)
    assert abs(f._phi - phi) < 0.08
    # mean forecast is phi * last value
    assert np.isclose(f.predict(y[:500]), f._phi * y[499], atol=1e-12)


def test_funding_like_series_ar1_beats_histmean():
    # sticky mean-reverting series clamped like funding rates
    rng = np.random.default_rng(4)
    n = 900
    y = np.zeros(n)
    for t in range(1, n):
        y[t] = np.clip(0.85 * y[t - 1] + rng.normal(0, 2e-4), -7.5e-3, 7.5e-3)
    s = pd.DataFrame({"y": y},
                     index=pd.date_range("2021-01-01", periods=n, freq="8h", tz="UTC"))
    cell = {
        "cell": "SYN|8h|T6_funding", "target": "T6_funding", "horizon_bars": 1,
        "strong_baseline": "hist_mean", "loss": "se",
        "min_train": 200, "step": 1, "refit_every": 1, "embargo": 0,
    }
    out = runner.run_cell(cell, s, [baselines.HistMean(), tier1.Ar1()],
                          gates_key="predlab_p1_classical", tier="t1", dry=True)
    ar = out[out.model == "ar1"].iloc[0]
    assert ar["dm_p"] < 1e-6

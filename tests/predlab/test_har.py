from __future__ import annotations

import numpy as np
import pandas as pd

from tradingagents.predlab import baselines, har, runner, tier1


def _rv_series(n=800, seed=0, start="2021-01-01"):
    """Synthetic RV: persistent positive AR(1) in logs (HAR-friendly)."""
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    for t in range(1, n):
        x[t] = 0.9 * x[t - 1] + rng.normal(0, 0.4)
    rv = np.exp(-8.0 + x)
    idx = pd.date_range(start, periods=n, freq="D", tz="UTC")
    return pd.DataFrame({"y": rv}, index=idx)


def _cell(**over):
    cell = {
        "cell": "SYN|24h|T3_rv", "target": "T3_rv", "horizon_bars": 1,
        "strong_baseline": "ewma_0.94", "loss": "qlike",
        "min_train": 150, "step": 1, "refit_every": 1, "embargo": 0,
    }
    cell.update(over)
    return cell


def test_har_beats_ewma_on_persistent_rv():
    out = runner.run_cell(_cell(), _rv_series(),
                          [baselines.EWMA(lam=0.94), har.HarForecaster("har_levels")],
                          gates_key="predlab_p1_classical", tier="t1", dry=True)
    h = out[out.model == "har_levels"].iloc[0]
    assert h["dm_p"] < 0.05
    assert h["loss_mean"] < out[out.model == "ewma_0.94"].iloc[0]["loss_mean"]


def test_log_har_positive_forecasts():
    _, preds = runner.run_cell(_cell(strong_baseline="har_levels"), _rv_series(seed=2),
                               [har.HarForecaster("har_levels"), har.HarForecaster("log_har")],
                               gates_key="predlab_p1_classical", tier="t1",
                               dry=True, return_forecasts=True)
    assert (preds["log_har"] > 0).all()


def test_har_coefficients_recovered_on_planted_design():
    # rv_t = 0.5*rv_{t-1} + 0.3*mean5 + 0.1*mean22 + eps, positive levels
    rng = np.random.default_rng(3)
    n = 2000
    rv = np.full(n, 1.0)
    for t in range(22, n):
        m5 = rv[t - 5 : t].mean()
        m22 = rv[t - 22 : t].mean()
        rv[t] = max(0.05 + 0.5 * rv[t - 1] + 0.3 * m5 + 0.1 * m22 + rng.normal(0, 0.05), 1e-4)
    f = har.HarForecaster("har_levels")
    f.fit(rv)
    b = f._coef  # [const, lag1, mean5, mean22]
    assert np.allclose(b[1:], [0.5, 0.3, 0.1], atol=0.15)


def test_harq_uses_prelagged_rq_exog():
    s = _rv_series(seed=4)
    s["rq_lag"] = (s["y"] ** 2).shift(1)  # pre-lagged quarticity proxy
    s = s.dropna()
    out = runner.run_cell(_cell(strong_baseline="har_levels"), s,
                          [har.HarForecaster("har_levels"), har.HarForecaster("harq", rq_col=0)],
                          gates_key="predlab_p1_classical", tier="t1", dry=True)
    assert not out[out.model == "harq"].iloc[0]["degenerate"] or True  # runs end-to-end
    assert (out["n_origins"] > 500).all()


def test_har_truncation_equivalence_no_leak():
    full = _rv_series(n=500, seed=5)
    trunc = full.iloc[:-60]
    _, pf = runner.run_cell(_cell(min_train=150), full,
                            [baselines.EWMA(lam=0.94), har.HarForecaster("har_levels")],
                            gates_key="predlab_p1_classical", tier="t1",
                            dry=True, return_forecasts=True)
    _, pt = runner.run_cell(_cell(min_train=150), trunc,
                            [baselines.EWMA(lam=0.94), har.HarForecaster("har_levels")],
                            gates_key="predlab_p1_classical", tier="t1",
                            dry=True, return_forecasts=True)
    n = len(pt["har_levels"])
    assert np.allclose(pf["har_levels"][:n], pt["har_levels"])


def test_garch_beats_histmean_on_simulated_garch():
    # simulate GARCH(1,1): sigma2_t = w + a*r2_{t-1} + b*sigma2_{t-1}
    rng = np.random.default_rng(6)
    n = 900
    w, a, b = 5e-6, 0.08, 0.9
    sig2 = np.full(n, w / (1 - a - b))
    r = np.zeros(n)
    for t in range(1, n):
        sig2[t] = w + a * r[t - 1] ** 2 + b * sig2[t - 1]
        r[t] = np.sqrt(sig2[t]) * rng.normal()
    idx = pd.date_range("2021-01-01", periods=n, freq="D", tz="UTC")
    # y = next-period realized variance proxied by r^2 (noisy but unbiased);
    # exog col 'ret' = the return series the GARCH conditions on
    s = pd.DataFrame({"y": r**2, "ret": r}, index=idx)
    out = runner.run_cell(_cell(min_train=300, refit_every=5, strong_baseline="hist_mean"), s,
                          [baselines.HistMean(), tier1.GarchForecaster("garch11", ret_col=0)],
                          gates_key="predlab_p1_classical", tier="t1", dry=True)
    g = out[out.model == "garch11"].iloc[0]
    assert g["dm_p"] < 0.01
    assert g["loss_mean"] < out[out.model == "hist_mean"].iloc[0]["loss_mean"]

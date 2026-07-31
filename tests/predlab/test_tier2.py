from __future__ import annotations

import numpy as np
import pandas as pd

from tradingagents.predlab import baselines, runner, tier2


def _linear_cell_series(n=900, seed=0, noise=1.0):
    """y[t] = 0.8*x1[t] - 0.5*x2[t] + noise; features PRE-LAGGED (usable at t)."""
    rng = np.random.default_rng(seed)
    x1 = rng.normal(0, 1, n)
    x2 = rng.normal(0, 1, n)
    y = 0.8 * x1 - 0.5 * x2 + rng.normal(0, noise, n)
    idx = pd.date_range("2021-06-01", periods=n, freq="h", tz="UTC")
    return pd.DataFrame({"y": y, "x1": x1, "x2": x2, "junk": rng.normal(0, 1, n)}, index=idx)


def _cell(**over):
    cell = {"cell": "SYN|1h|T1_ret", "target": "T1_ret", "horizon_bars": 1,
            "strong_baseline": "rw_zero", "loss": "se",
            "min_train": 300, "step": 1, "refit_every": 24, "embargo": 0}
    cell.update(over)
    return cell


def test_elastic_net_recovers_planted_linear_signal():
    out = runner.run_cell(_cell(), _linear_cell_series(),
                          [baselines.RWZero(), tier2.ElasticNetForecaster(refit_every=24)],
                          gates_key="predlab_p1_classical", tier="probe", dry=True)
    en = out[out.model == "enet"].iloc[0]
    assert en["dm_p"] < 1e-10
    assert en["loss_mean"] < 0.75 * out[out.model == "rw_zero"].iloc[0]["loss_mean"]


def test_lgb_recovers_planted_signal():
    out = runner.run_cell(_cell(), _linear_cell_series(seed=1),
                          [baselines.RWZero(), tier2.LGBForecaster(refit_every=24)],
                          gates_key="predlab_p1_classical", tier="probe", dry=True)
    lgb = out[out.model == "lgb"].iloc[0]
    assert lgb["dm_p"] < 1e-6


def test_tier2_no_signal_on_pure_noise():
    rng = np.random.default_rng(7)
    n = 900
    idx = pd.date_range("2021-06-01", periods=n, freq="h", tz="UTC")
    s = pd.DataFrame({"y": rng.normal(0, 1, n),
                      "x1": rng.normal(0, 1, n), "x2": rng.normal(0, 1, n)}, index=idx)
    out = runner.run_cell(_cell(), s,
                          [baselines.RWZero(), tier2.ElasticNetForecaster(refit_every=24)],
                          gates_key="predlab_p1_classical", tier="probe", dry=True)
    assert out[out.model == "enet"].iloc[0]["dm_p"] > 0.05


def test_tier2_truncation_equivalence_no_leak():
    full = _linear_cell_series(seed=3)
    trunc = full.iloc[:-100]
    _, p_full = runner.run_cell(_cell(), full,
                                [baselines.RWZero(), tier2.LGBForecaster(refit_every=24)],
                                gates_key="predlab_p1_classical", tier="probe",
                                dry=True, return_forecasts=True)
    _, p_trunc = runner.run_cell(_cell(), trunc,
                                 [baselines.RWZero(), tier2.LGBForecaster(refit_every=24)],
                                 gates_key="predlab_p1_classical", tier="probe",
                                 dry=True, return_forecasts=True)
    n = len(p_trunc["lgb"])
    assert np.allclose(p_full["lgb"][:n], p_trunc["lgb"])


def test_enet_deterministic():
    s = _linear_cell_series(seed=4)
    outs = []
    for _ in range(2):
        _, p = runner.run_cell(_cell(), s,
                               [baselines.RWZero(), tier2.ElasticNetForecaster(refit_every=24)],
                               gates_key="predlab_p1_classical", tier="probe",
                               dry=True, return_forecasts=True)
        outs.append(p["enet"])
    assert np.array_equal(outs[0], outs[1])

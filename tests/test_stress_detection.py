import numpy as np
import pandas as pd
from tradingagents.stress.detection import detection_metrics, placebo_pvalue


def _warn(days_on, n=200, start="2022-01-01"):
    idx = pd.date_range(start, periods=n, freq="D", tz="UTC")
    s = pd.Series(False, index=idx)
    s.iloc[days_on] = True
    return s


def _episodes(starts):
    return pd.DataFrame(
        {"start": [pd.Timestamp(s, tz="UTC") for s in starts],
         "end": [pd.Timestamp(s, tz="UTC") for s in starts],
         "trough_ret": [-0.2] * len(starts)}
    )


def test_perfect_hit():
    warn = _warn([40, 41, 42])  # 2022-02-10..12
    eps = _episodes(["2022-02-20"])  # start 8 days after last warn day
    m = detection_metrics(warn, eps)
    assert m["hit_rate"] == 1.0
    assert m["n_hits"] == 1
    assert m["median_lead_days"] == 10  # first warn 2022-02-10, start 2022-02-20


def test_miss_and_false_alarm():
    warn = _warn([100, 101])  # far from episode
    eps = _episodes(["2022-02-01"])
    m = detection_metrics(warn, eps)
    assert m["hit_rate"] == 0.0
    assert m["n_warn_clusters"] == 1
    assert m["false_alarm_clusters_per_year"] > 0


def test_placebo_p_not_significant_for_random_warn():
    rng = np.random.default_rng(1)
    warn = _warn(list(rng.choice(500, 30, replace=False)), n=520)
    eps = _episodes(["2022-06-01", "2023-01-15"])
    p = placebo_pvalue(warn, eps, n=99, seed=2)
    assert 0.0 < p["p_hit_rate"] <= 1.0

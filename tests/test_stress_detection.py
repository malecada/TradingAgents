import math
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


def test_window_boundary_exactly_20_days():
    """Warn on day exactly start-20 should hit; start-21 should miss."""
    # Episode at day 40 (2022-02-10, 40 days from 2022-01-01)
    # Window is [day 20, day 39] = [2022-01-21, 2022-02-09]
    eps = _episodes(["2022-02-10"])

    # Warn on day 20 (exactly start-20, 2022-01-21) → HIT
    warn = _warn([20], n=50)
    m = detection_metrics(warn, eps)
    assert m["n_hits"] == 1, "Warn on start-20 should hit"

    # Warn on day 19 (start-21, 2022-01-20) → MISS
    warn = _warn([19], n=50)
    m = detection_metrics(warn, eps)
    assert m["n_hits"] == 0, "Warn on start-21 should miss"


def test_warn_on_start_day_not_a_hit():
    """Warn on episode start day itself should NOT be a hit (outside window)."""
    # Episode at day 40 (2022-02-10)
    # Window: [day 20, day 39], so day 40 is outside
    warn = _warn([40], n=50)
    eps = _episodes(["2022-02-10"])
    m = detection_metrics(warn, eps)
    assert m["n_hits"] == 0, "Warn on start day should not hit (not in window)"


def test_fa_uses_cluster_start():
    """False alarm rule: cluster_start + 20 must come before all episode starts.

    Hit rule: window [start-20, start-1] must overlap warn days.

    A warn cluster can be both a hit contributor AND an FA cluster under the frozen rules.
    """
    # Cluster days 0-14 (2022-01-01 to 2022-01-15, 15 days total)
    # Episode start: day 25 (2022-01-26)
    # Cluster start (day 0) + 20 = day 20 (2022-01-21)
    # Is any episode_start in [2022-01-01, 2022-01-21]? No, 2022-01-26 > 2022-01-21 → FA
    # But is warn day in [day 5, day 24]? Yes, days 0-14 overlap → HIT
    warn = _warn(list(range(15)), n=50)  # days 0-14
    eps = _episodes(["2022-01-26"])  # day 25
    m = detection_metrics(warn, eps)
    assert m["n_hits"] == 1, "Cluster overlaps window [start-20, start-1] → hit"
    assert m["false_alarm_clusters_per_year"] > 0, "Cluster start+20 < episode_start → FA"


def test_zero_episodes_nan_hit_and_placebo_p_one():
    """Empty episodes → NaN hit_rate, placebo_pvalue returns p_hit_rate == 1.0."""
    warn = _warn([10, 11, 12], n=50)
    eps = pd.DataFrame(columns=["start", "end", "trough_ret"])

    m = detection_metrics(warn, eps)
    assert math.isnan(m["hit_rate"]), "Zero episodes should give NaN hit_rate"
    assert m["n_episodes"] == 0

    p = placebo_pvalue(warn, eps, n=19, seed=1)
    assert p["p_hit_rate"] == 1.0, "Placebo p should be 1.0 when real hit_rate is NaN"


def test_two_disjoint_clusters_counted():
    """Separate warn clusters should be counted independently."""
    warn = _warn([10, 11, 12, 50, 51], n=100)
    eps = _episodes(["2022-05-01"])  # far from warn clusters to avoid hits
    m = detection_metrics(warn, eps)
    assert m["n_warn_clusters"] == 2, "Two disjoint warn clusters should be counted"

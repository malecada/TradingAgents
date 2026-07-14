import numpy as np
import pandas as pd
from tradingagents.stress.episodes import build_episodes


def _close(vals):
    idx = pd.date_range("2022-01-01", periods=len(vals), freq="D", tz="UTC")
    return pd.Series(vals, index=idx, dtype=float)


def test_flat_series_no_episodes():
    eps = build_episodes(_close([100.0] * 100))
    assert len(eps) == 0


def test_single_crash_detected():
    vals = [100.0] * 30 + list(np.linspace(100, 70, 10)) + [70.0] * 30
    eps = build_episodes(_close(vals))
    assert len(eps) == 1
    # first day whose 10-day-forward return breaches -15% is before the fall completes
    assert eps.iloc[0]["start"] <= pd.Timestamp("2022-01-31", tz="UTC")


def test_nearby_crashes_merged():
    fall1 = list(np.linspace(100, 80, 8))
    fall2 = list(np.linspace(82, 60, 8))
    vals = [100.0] * 30 + fall1 + [80, 81, 82, 82, 82] + fall2 + [60.0] * 30
    eps = build_episodes(_close(vals), merge_gap=10)
    assert len(eps) == 1  # gap of 5 non-crash days < 10 -> merged

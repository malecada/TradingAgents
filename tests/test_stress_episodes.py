import numpy as np
import pandas as pd
import pytest
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


def test_empty_result_has_schema():
    """Verify that even when no episodes exist, the schema is preserved."""
    eps = build_episodes(_close([100.0] * 100))
    assert list(eps.columns) == ["start", "end", "trough_ret"]
    assert len(eps) == 0


def test_gap_boundary_exactly_merge_gap_separates():
    """Boundary condition on the frozen merge rule (gates.json stress_ews):
    a gap of exactly `merge_gap` (10) non-crash days between two crash runs
    keeps them as 2 separate episodes; a gap of merge_gap - 1 (9) merges
    them into 1.

    Construction (inverts the forward-return definition instead of hoping a
    hand-picked price path happens to land on the boundary):
    fwd[i] = log(close[i+10]/close[i]) is chosen directly, then
    y[i+10] = y[i] + fwd[i], close = exp(y). With
    fwd = [0]*10 + [log(0.7)]*10 + [0]*gap + [log(0.7)]*10 + [0]*20
    the two log(0.7) blocks are always crash days (0.7 < 0.85) and the
    0 blocks are always non-crash (1.0 > 0.85), so `gap` controls exactly
    the non-crash run length between the two crash runs.
    """
    horizon = 10
    merge_gap = 10
    drop_log = np.log(0.85)
    fall = np.log(0.7)

    def _close_from_fwd(fwd):
        y = np.zeros(len(fwd) + horizon)
        for i, f in enumerate(fwd):
            y[i + horizon] = y[i] + f
        idx = pd.date_range("2022-01-01", periods=len(y), freq="D", tz="UTC")
        return pd.Series(np.exp(y), index=idx, dtype=float)

    def _non_crash_gap_between_first_two_runs(close):
        crash = (np.log(close.shift(-horizon) / close) <= drop_log).to_numpy()
        crash_idx = np.flatnonzero(crash)
        breaks = np.flatnonzero(np.diff(crash_idx) > 1)
        assert breaks.size == 1, "construction must yield exactly two crash runs"
        run1_end = crash_idx[breaks[0]]
        run2_start = crash_idx[breaks[0] + 1]
        return run2_start - run1_end - 1

    # Case 1: gap of exactly merge_gap (10) non-crash days -> 2 separate episodes
    fwd_separates = [0.0] * 10 + [fall] * 10 + [0.0] * 10 + [fall] * 10 + [0.0] * 20
    close_separates = _close_from_fwd(fwd_separates)
    assert _non_crash_gap_between_first_two_runs(close_separates) == 10
    eps_separates = build_episodes(close_separates, merge_gap=merge_gap)
    assert len(eps_separates) == 2

    # Case 2: gap of merge_gap - 1 (9) non-crash days -> merged into 1 episode
    fwd_merges = [0.0] * 10 + [fall] * 10 + [0.0] * 9 + [fall] * 10 + [0.0] * 20
    close_merges = _close_from_fwd(fwd_merges)
    assert _non_crash_gap_between_first_two_runs(close_merges) == 9
    eps_merges = build_episodes(close_merges, merge_gap=merge_gap)
    assert len(eps_merges) == 1


def test_trough_ret_value():
    """Verify trough_ret computation: minimum 10-day forward log-return in an episode."""
    # Construct a simple crash series where we know the exact minimum forward return
    # Series: 100 for 5 days, then drop to 80 for 5 days, then back to 100
    close_vals = [100.0] * 5 + [80.0] * 10 + [100.0] * 15
    close_series = _close(close_vals)

    # Compute expected trough_ret manually
    fwd = np.log(close_series.shift(-10) / close_series)
    expected_trough = fwd.dropna().min()

    eps = build_episodes(close_series)
    assert len(eps) > 0, "Expected at least one episode"
    assert eps.iloc[0]["trough_ret"] == pytest.approx(expected_trough)

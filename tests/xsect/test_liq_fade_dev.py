"""Unit tests for the liq_fade_i1 dev runner's pure helpers (scripts/liq_fade_dev.py):
membership_mask_hourly (monthly PIT universe -> hourly bool mask) and
event_forward_sum (P2's forward-return-at-trigger extraction). Both are
testable on synthetic data without touching the (partial, still-fetching)
1h kline store."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location(
    "liq_fade_dev", Path(__file__).parents[2] / "scripts" / "liq_fade_dev.py")
liq_fade_dev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(liq_fade_dev)


def _hourly_index(start, hours):
    return pd.date_range(start, periods=hours, freq="1h", tz="UTC")


# ── membership_mask_hourly ──────────────────────────────────────────────────

def test_membership_mask_hourly_basic_month_boundaries():
    idx = _hourly_index("2021-01-01", 24 * 62)  # Jan 1 -> Mar 3
    universe = {
        "2021-01-01": ["AAA", "BBB"],
        "2021-02-01": ["BBB", "CCC"],
    }
    mask = liq_fade_dev.membership_mask_hourly(universe, ["AAA", "BBB", "CCC"], idx)

    jan_15 = pd.Timestamp("2021-01-15 00:00", tz="UTC")
    feb_15 = pd.Timestamp("2021-02-15 00:00", tz="UTC")
    assert bool(mask.loc[jan_15, "AAA"]) is True
    assert bool(mask.loc[jan_15, "BBB"]) is True
    assert bool(mask.loc[jan_15, "CCC"]) is False   # not a member yet in January
    assert bool(mask.loc[feb_15, "AAA"]) is False   # dropped at the February re-selection
    assert bool(mask.loc[feb_15, "BBB"]) is True
    assert bool(mask.loc[feb_15, "CCC"]) is True


def test_membership_mask_hourly_last_month_extends_to_index_end():
    idx = _hourly_index("2021-01-01", 24 * 45)  # Jan 1 -> mid-Feb
    universe = {"2021-01-01": ["AAA"]}
    mask = liq_fade_dev.membership_mask_hourly(universe, ["AAA"], idx)
    assert bool(mask.iloc[-1]["AAA"]) is True   # last bar still covered by the sole month


def test_membership_mask_hourly_symbol_not_in_columns_is_ignored():
    idx = _hourly_index("2021-01-01", 24)
    universe = {"2021-01-01": ["AAA", "ZZZ"]}   # ZZZ not in the requested columns
    mask = liq_fade_dev.membership_mask_hourly(universe, ["AAA"], idx)
    assert list(mask.columns) == ["AAA"]
    assert bool(mask.iloc[0]["AAA"]) is True


def test_membership_mask_hourly_boolean_dtype():
    idx = _hourly_index("2021-01-01", 24)
    universe = {"2021-01-01": ["AAA"]}
    mask = liq_fade_dev.membership_mask_hourly(universe, ["AAA", "BBB"], idx)
    assert mask.dtypes.eq(bool).all()


# ── event_forward_sum ────────────────────────────────────────────────────────

def test_event_forward_sum_extracts_sum_t1_to_tH():
    idx = _hourly_index("2021-01-01", 10)
    # constant 1% return each bar -> forward sum over H bars is exactly H * 0.01
    R = pd.DataFrame({"AAA": 0.01}, index=idx)
    trig = pd.DataFrame({"AAA": False}, index=idx)
    trig.iloc[2, 0] = True   # single trigger at row 2
    H = 3
    vals = liq_fade_dev.event_forward_sum(R, trig, H)
    assert len(vals) == 1
    assert np.isclose(vals[0], H * 0.01)


def test_event_forward_sum_drops_events_too_close_to_the_end():
    idx = _hourly_index("2021-01-01", 5)
    R = pd.DataFrame({"AAA": 0.01}, index=idx)
    trig = pd.DataFrame({"AAA": False}, index=idx)
    trig.iloc[-1, 0] = True   # last bar: no room for a forward window of H=3
    vals = liq_fade_dev.event_forward_sum(R, trig, H=3)
    assert len(vals) == 0


def test_event_forward_sum_multiple_symbols_and_events_flattened():
    idx = _hourly_index("2021-01-01", 8)
    R = pd.DataFrame({"AAA": [0.01] * 8, "BBB": [0.02] * 8}, index=idx)
    trig = pd.DataFrame({"AAA": [False] * 8, "BBB": [False] * 8}, index=idx)
    trig.iloc[1, 0] = True   # AAA triggers at row 1
    trig.iloc[3, 1] = True   # BBB triggers at row 3
    H = 2
    vals = sorted(liq_fade_dev.event_forward_sum(R, trig, H))
    assert len(vals) == 2
    assert np.isclose(vals[0], H * 0.01)  # AAA event
    assert np.isclose(vals[1], H * 0.02)  # BBB event


def test_event_forward_sum_uses_t1_to_tH_not_t_to_tHminus1():
    """Non-constant return path: with constant returns, the correct window
    t+1..t+H and the off-by-one mutant t..t+H-1 (e.g. an errant
    `.shift(-H+1)` instead of `.shift(-H)`) sum to the identical value and
    the bug is invisible. Use a strictly increasing return path so the two
    windows disagree, and hand-compute the correct answer."""
    idx = _hourly_index("2021-01-01", 6)
    R = pd.DataFrame({"AAA": [0.01, 0.02, 0.03, 0.04, 0.05, 0.06]}, index=idx)
    trig = pd.DataFrame({"AAA": [False] * 6}, index=idx)
    trig.iloc[1, 0] = True   # trigger at t=1 (row index 1, return 0.02)
    H = 3
    vals = liq_fade_dev.event_forward_sum(R, trig, H)
    assert len(vals) == 1
    # correct: sum(R[t+1..t+H]) = R[2]+R[3]+R[4] = 0.03+0.04+0.05
    assert np.isclose(vals[0], 0.12)
    # off-by-one mutant (t..t+H-1, i.e. includes the trigger bar itself):
    # R[1]+R[2]+R[3] = 0.02+0.03+0.04 = 0.09 -- must NOT match
    assert not np.isclose(vals[0], 0.09)


# ── load_symbols smoke restriction (pure filesystem check, no parquet reads) ─

def test_load_symbols_smoke_restricts_to_symbols_on_disk():
    all_syms = liq_fade_dev.load_symbols(smoke=False)
    on_disk = {p.stem for p in liq_fade_dev.KLINES_1H_DIR.glob("*.parquet")}
    smoke_syms = liq_fade_dev.load_symbols(smoke=True)
    assert set(smoke_syms) == set(all_syms) & on_disk
    assert set(smoke_syms).issubset(on_disk)

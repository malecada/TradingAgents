import json

import numpy as np
import pandas as pd
import pytest

from tradingagents.xsect.unlock_xs import (
    STABLE_EXCLUDE, amendment_exposure, build_matrices, cliff_events,
    daily_unlock_series, map_slugs_to_perps, schedule_start,
)

TS0 = pd.Timestamp("2021-01-01", tz="UTC")


def _ts(s):
    return int(pd.Timestamp(s, tz="UTC").timestamp())


def _cliff(day, amount, cat="insiders"):
    return {"unlockType": "cliff", "timestamp": _ts(day),
            "noOfTokens": [amount], "category": cat}


def _linear(day, weekly, cat="staking"):
    return {"unlockType": "linear", "timestamp": _ts(day),
            "noOfTokens": [0, weekly], "category": cat}


def test_cliff_lands_whole_on_its_day():
    s = daily_unlock_series([_cliff("2021-01-05", 700.0)],
                            TS0, pd.Timestamp("2021-01-10", tz="UTC"))
    assert s.loc["2021-01-05"] == 700.0
    assert s.drop(pd.Timestamp("2021-01-05", tz="UTC")).sum() == 0.0


def test_linear_rate_is_tokens_per_week():
    ev = [_linear("2021-01-01", 70.0),
          _cliff("2021-01-15", 0.0)]  # extends max_ts so the rate stays live
    s = daily_unlock_series(ev, TS0, pd.Timestamp("2021-01-14", tz="UTC"))
    assert s.loc["2021-01-02"] == pytest.approx(10.0)  # 70 / 7 per day
    assert s.sum() == pytest.approx(140.0)             # 14 days x 10


def test_linear_rate_change_takes_over_at_its_timestamp():
    ev = [_linear("2021-01-01", 70.0), _linear("2021-01-08", 140.0),
          _cliff("2021-01-15", 0.0)]
    s = daily_unlock_series(ev, TS0, pd.Timestamp("2021-01-14", tz="UTC"))
    assert s.loc["2021-01-07"] == pytest.approx(10.0)
    assert s.loc["2021-01-08"] == pytest.approx(20.0)


def test_linear_accrual_stops_at_schedule_end():
    ev = [_linear("2021-01-01", 70.0), _linear("2021-01-08", 0.0)]
    s = daily_unlock_series(ev, TS0, pd.Timestamp("2021-01-31", tz="UTC"))
    assert s.sum() == pytest.approx(70.0)   # 7 days x 10, then rate 0


def test_categories_do_not_bleed_rates():
    ev = [_linear("2021-01-01", 70.0, cat="staking"),
          _linear("2021-01-08", 0.0, cat="insiders"),
          _cliff("2021-01-15", 0.0)]
    s = daily_unlock_series(ev, TS0, pd.Timestamp("2021-01-14", tz="UTC"))
    # staking's rate must NOT be terminated by insiders' event
    assert s.loc["2021-01-10"] == pytest.approx(10.0)


def test_empty_events_gives_zero_series():
    s = daily_unlock_series([], TS0, pd.Timestamp("2021-01-03", tz="UTC"))
    assert len(s) == 3 and s.sum() == 0.0


def _write_emissions(tmp_path, slug, events, gecko_id="tok-a"):
    (tmp_path / f"{slug}.json").write_text(json.dumps(
        {"gecko_id": gecko_id, "metadata": {"events": events}}))


def test_burden_is_forward_window_over_supply(tmp_path):
    # supply 1000 unlocked pre-window; one 100-token cliff on Jan 10
    ev = [_cliff("2020-06-01", 1000.0), _cliff("2021-01-10", 100.0)]
    _write_emissions(tmp_path, "toka", ev)
    days = pd.date_range("2021-01-01", "2021-01-20", freq="D", tz="UTC")
    m = build_matrices(tmp_path, {"toka": "TOKAUSDT"}, days, lookaheads=(5,))
    b = m["burden"][5]["TOKAUSDT"]
    # Jan 5: window (Jan 5, Jan 10] catches the cliff; supply still 1000
    assert b.loc["2021-01-05"] == pytest.approx(100.0 / 1000.0)
    # Jan 10: cliff now in supply, window (Jan 10, Jan 15] is empty
    assert b.loc["2021-01-10"] == pytest.approx(0.0)
    # Jan 4: window (Jan 4, Jan 9] misses the Jan 10 cliff
    assert b.loc["2021-01-04"] == pytest.approx(0.0)
    assert m["supply"]["TOKAUSDT"].loc["2021-01-10"] == pytest.approx(1100.0)


def test_burden_nan_before_token_launch(tmp_path):
    _write_emissions(tmp_path, "toka", [_cliff("2021-01-10", 100.0)])
    days = pd.date_range("2021-01-01", "2021-01-20", freq="D", tz="UTC")
    m = build_matrices(tmp_path, {"toka": "TOKAUSDT"}, days, lookaheads=(5,))
    assert np.isnan(m["burden"][5]["TOKAUSDT"].loc["2021-01-05"])


def test_burden_uses_schedule_beyond_days_end(tmp_path):
    # cliff 3 days past the end of `days` must appear in the forward window
    ev = [_cliff("2020-06-01", 1000.0), _cliff("2021-01-23", 50.0)]
    _write_emissions(tmp_path, "toka", ev)
    days = pd.date_range("2021-01-01", "2021-01-20", freq="D", tz="UTC")
    m = build_matrices(tmp_path, {"toka": "TOKAUSDT"}, days, lookaheads=(5,))
    assert m["burden"][5]["TOKAUSDT"].loc["2021-01-20"] == pytest.approx(0.05)


def test_map_excludes_stables_and_missing_perps(tmp_path):
    em = tmp_path / "em"
    em.mkdir()
    _write_emissions(em, "toka", [], gecko_id="tok-a")
    _write_emissions(em, "usdc", [], gecko_id="usd-coin")
    _write_emissions(em, "nope", [], gecko_id="no-perp")
    glist = tmp_path / "gecko.json"
    glist.write_text(json.dumps([
        {"id": "tok-a", "symbol": "toka"},
        {"id": "usd-coin", "symbol": "usdc"},
        {"id": "no-perp", "symbol": "zzz"},
    ]))
    perps = {"TOKAUSDT", "USDCUSDT"}
    assert "USDCUSDT" in STABLE_EXCLUDE
    out = map_slugs_to_perps(em, glist, perps)
    assert out == {"toka": "TOKAUSDT"}


def test_map_asserts_injectivity(tmp_path):
    em = tmp_path / "em"
    em.mkdir()
    _write_emissions(em, "proto-a", [], gecko_id="a-id")
    _write_emissions(em, "proto-b", [], gecko_id="b-id")
    glist = tmp_path / "gecko.json"
    glist.write_text(json.dumps([{"id": "a-id", "symbol": "tok"},
                                 {"id": "b-id", "symbol": "tok"}]))
    with pytest.raises(AssertionError, match="not injective"):
        map_slugs_to_perps(em, glist, {"TOKUSDT"})


def test_map_memecoin_prefix(tmp_path):
    em = tmp_path / "em"
    em.mkdir()
    _write_emissions(em, "pepe", [], gecko_id="pepe")
    glist = tmp_path / "gecko.json"
    glist.write_text(json.dumps([{"id": "pepe", "symbol": "pepe"}]))
    out = map_slugs_to_perps(em, glist, {"1000PEPEUSDT"})
    assert out == {"pepe": "1000PEPEUSDT"}


def test_cliff_events_groups_same_day():
    df = cliff_events([_cliff("2021-01-05", 10.0), _cliff("2021-01-05", 5.0),
                       _linear("2021-01-01", 7.0)])
    assert len(df) == 1
    assert df["amount"].iloc[0] == 15.0


def test_schedule_start_is_min_event():
    assert schedule_start([_cliff("2021-02-01", 1.0),
                           _cliff("2021-01-05", 1.0)]) == \
        pd.Timestamp("2021-01-05", tz="UTC")
    assert schedule_start([]) is None


def test_amendment_exposure_flags_midstream_rate_change():
    dev0 = pd.Timestamp("2021-01-01", tz="UTC")
    dev1 = pd.Timestamp("2021-01-14", tz="UTC")
    stable = [_linear("2021-01-01", 70.0), _cliff("2021-01-14", 0.0)]
    assert amendment_exposure(stable, dev0, dev1)["amended_share"] == 0.0
    amended = [_linear("2021-01-01", 70.0), _linear("2021-01-08", 140.0),
               _cliff("2021-01-14", 0.0)]
    r = amendment_exposure(amended, dev0, dev1)
    assert r["amended_share"] > 0.0
    assert r["n_linear_rate_changes"] == 1

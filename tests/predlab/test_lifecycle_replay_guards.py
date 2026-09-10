"""Synthetic clocks and books for the separately registered recovered replay."""
import importlib
import json
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from scripts import audit_reevaluate_accounting_2026_09_09 as wrapper


def lifecycle():
    spec = importlib.util.find_spec("tradingagents.xsect.lifecycle")
    assert spec is not None, "pure lifecycle replay guard is absent"
    return importlib.import_module("tradingagents.xsect.lifecycle")


def weights(values):
    return pd.DataFrame({"OLD": values}, index=pd.date_range("2022-05-12 13:00", periods=len(values), freq="h", tz="UTC"))


def event(close="2022-05-12T15:30:00Z", restriction=None):
    return {"symbol": "OLD", "closure_utc": close, "new_position_restriction_utc": restriction}


@pytest.mark.parametrize("schedule,closure", [
    ([0, .1, .1, 0], "2022-05-12T15:30:00Z"),
    ([0, .1, 0, 0], "2022-05-12T15:00:00Z"),
    ([0, 0, 0, .1], "2022-05-12T15:30:00Z"),
    ([0, 0, .1], "2022-05-12T16:00:00Z"),
])
def test_schedule_guard_blocks_straddle_incoming_postclosure_and_final_exit(schedule, closure):
    mod = lifecycle()
    with pytest.raises(mod.LifecycleUnavailable):
        mod.guard_target_schedule(weights(schedule), [event(closure)])


def test_genuine_pre_event_flatten_and_absent_policy_keep_existing_behavior():
    mod = lifecycle()
    mod.guard_target_schedule(weights([.1, 0, 0, 0]), [event()])
    mod.guard_target_schedule(weights([.1, .1, .1, .1]), [])


def test_nonzero_restricted_decision_is_unknown_quantity_even_when_weight_unchanged():
    mod = lifecycle()
    with pytest.raises(mod.LifecycleUnavailable, match="restricted"):
        mod.guard_target_schedule(weights([.1, .1, 0, 0]),
                                  [event("2022-05-12T16:30:00Z", "2022-05-12T13:30:00Z")])
    mod.guard_target_schedule(weights([.1, 0, 0, 0]),
                              [event("2022-05-12T16:30:00Z", "2022-05-12T13:30:00Z")])


def test_unknown_or_compressed_schedule_fails_closed():
    mod = lifecycle()
    with pytest.raises(mod.LifecycleUnavailable):
        mod.guard_target_schedule(weights([0, np.nan, 0, 0]), [event()])
    with pytest.raises(mod.LifecycleUnavailable):
        mod.guard_target_schedule(weights([0, 0, 0, 0]).iloc[[0, 2, 3]], [event()])


@pytest.mark.parametrize("closure", ["2022-05-12T15:30:00Z", "2022-05-12T16:00:00Z", "2022-05-12T13:00:00Z"])
def test_p2_window_blocks_intrabar_final_availability_and_already_closed_entry(closure):
    ix = weights([0] * 6).index
    returns = pd.DataFrame({"OLD": .01}, index=ix)
    trig = pd.DataFrame({"OLD": [True, False, False, False, False, False]}, index=ix)
    # Trigger13:00 -> entry14:00 -> H2 valuations through16:00.
    out = wrapper.forward_probe(returns, trig, 2, lifecycle_events=[event(closure)])
    assert out["status"] == "unavailable" and out["n_events"] == 1
    assert out["n_lifecycle_unavailable_window"] == 1 and out["n_scoreable"] == 0
    assert out["gate_value"] is None


def test_p2_keeps_censor_missing_and_lifecycle_denominators_disjoint():
    ix = weights([0] * 6).index
    returns = pd.DataFrame({"OLD": [0, .01, np.nan, .01, .01, .01]}, index=ix)
    trig = pd.DataFrame({"OLD": [True, True, False, False, False, True]}, index=ix)
    out = wrapper.forward_probe(returns, trig, 2, lifecycle_events=[event("2022-05-12T17:00:00Z")])
    assert out["n_events"] == 3
    assert out["n_endpoint_censored"] == 1
    assert out["n_missing_internal_window"] == 1
    assert out["n_lifecycle_unavailable_window"] == 1
    assert out["n_scoreable"] == 0
    assert out["n_missing_return_and_lifecycle"] == 1


def test_p2_restriction_prevents_new_hypothetical_entry_and_no_policy_is_unchanged():
    ix = weights([0] * 6).index
    returns = pd.DataFrame({"OLD": .01}, index=ix)
    trig = pd.DataFrame({"OLD": [True, False, False, False, False, False]}, index=ix)
    old = wrapper.forward_probe(returns, trig, 2)
    same = wrapper.forward_probe(returns, trig, 2, lifecycle_events=[])
    assert old == same and old["status"] == "computed"
    out = wrapper.forward_probe(returns, trig, 2,
        lifecycle_events=[event("2022-05-12T18:00:00Z", "2022-05-12T14:00:00Z")])
    assert out["status"] == "unavailable"


def test_p2_fixed_quantity_horizon_has_no_intermediate_maintenance_order():
    ix = weights([0] * 6).index
    returns = pd.DataFrame({"OLD": .01}, index=ix)
    trig = pd.DataFrame({"OLD": [True, False, False, False, False, False]}, index=ix)
    # Entry14:00 and valuation16:00; restriction15:00 allows the existing fixed
    # quantity to remain held. Actual hourly target schedules are different.
    out = wrapper.forward_probe(returns, trig, 2,
        lifecycle_events=[event("2022-05-12T18:00:00Z", "2022-05-12T15:00:00Z")])
    assert out["status"] == "computed" and out["n_lifecycle_unavailable_window"] == 0
    assert out["gate_value"] == pytest.approx(.0201)


def test_p2_unknown_cells_never_pass_on_scoreable_subset():
    ix = weights([0] * 6).index
    returns = pd.DataFrame({"OLD": .1, "LIVE": .1}, index=ix)
    trig = pd.DataFrame({"OLD": [True, False, False, False, False, False],
                         "LIVE": [True, False, False, False, False, False]}, index=ix)
    out = wrapper.forward_probe(returns, trig, 2, lifecycle_events=[event()])
    assert out["n_scoreable"] == 1 and out["mean_compounded_return"] > .0025
    assert out["gate_value"] is None
    assert wrapper.p2_gate({"one": out})["pass"] is None


@pytest.mark.parametrize("cost", [0, 10, 20])
@pytest.mark.parametrize("convention", ["simple", "log"])
def test_every_hourly_book_path_checks_lifecycle_before_pnl(cost, convention, monkeypatch):
    mod = lifecycle()
    w = weights([0, .1, 0, 0])
    returns = pd.DataFrame(.01, index=w.index, columns=w.columns)
    def forbidden(*args, **kwargs):
        pytest.fail("portfolio PnL was computed before lifecycle rejection")
    monkeypatch.setattr(wrapper.liq_fade, "run_hourly_portfolio", forbidden)
    with pytest.raises(mod.LifecycleUnavailable):
        wrapper.hourly_book(w, returns if convention == "simple" else np.log1p(returns), cost,
                            lifecycle_events=[event("2022-05-12T15:00:00Z")])


def test_prepared_placebo_guard_keeps_failed_draw_and_advances_remaining_rng(tmp_path, monkeypatch):
    mod = lifecycle()
    monkeypatch.setattr(wrapper, "DEV", ("2021-01-01", "2021-01-05"))
    monkeypatch.setattr(wrapper, "N_PLACEBO", 2)
    folder = tmp_path / "xsect"
    folder.mkdir()
    (folder / "liq_fade_symbols.txt").write_text("OLD\n")
    (folder / "liq_fade_universe.json").write_text(json.dumps({"2021-01-01": ["OLD"]}))
    ix = pd.date_range("2020-12-01", "2021-01-05 23:00", freq="h", tz="UTC")
    close = 100 + np.arange(len(ix)) * .01 + np.sin(np.arange(len(ix))) * .1
    hourly = pd.DataFrame({"close": close, "quote_volume": 100.}, index=ix)
    daily = hourly.resample("D").last()
    declared_event = event("2021-01-03T01:00:00Z")
    ctx = SimpleNamespace(gate={"source_roots": [str(tmp_path)], "lifecycle_events": [declared_event]},
        family_gate={"warmup_start": "2020-12-01", "hourly_end": "2021-01-05T23:00:00Z",
                     "cells": [{"id": "one", "thr": 2.5, "H": 2}], "cost_bps": 10., "rf_annual": .045},
        track=lambda p: p,
        read_market=lambda p, **kwargs: daily if p.parent.name == "klines" else hourly)
    def trigger(frame, *_args):
        out = pd.DataFrame(False, index=frame.index, columns=frame.columns)
        out.loc[pd.Timestamp("2021-01-01T00:00:00Z"), "OLD"] = True
        return out
    monkeypatch.setattr(wrapper.liq_fade, "cascade_triggers", trigger)
    monkeypatch.setattr(wrapper, "p1_probe", lambda *args: {"pass": True})
    monkeypatch.setattr(wrapper, "p2_gate", lambda *args: {"pass": True})
    draws = []
    def shifted(trig, member, rng, family, materialize=True):
        draws.append((family, materialize, int(rng.integers(1000000))))
        if not materialize:
            return None
        out = pd.DataFrame(False, index=trig.index, columns=trig.columns)
        out.loc[pd.Timestamp("2021-01-03T00:00:00Z"), "OLD"] = True
        return out
    monkeypatch.setattr(wrapper, "draw_liq_placebo", shifted)
    prepared = wrapper.prepare_liq_fade(ctx)
    assert prepared.metadata["lifecycle"]["events"] == [declared_event]
    with pytest.raises(mod.LifecycleUnavailable):
        prepared.placebo(ctx.family_gate["cells"][0], True)
    assert [(family, materialize) for family, materialize, _ in draws] == [
        ("shift", True), ("shift", False), ("random", False), ("random", False)]
    assert [draw for _, _, draw in draws] == np.random.default_rng(48).integers(1000000, size=4).tolist()

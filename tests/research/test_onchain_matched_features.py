"""Invented source aggregates; no network or retained data imports."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


PATH = Path(__file__).resolve().parents[2] / "research/onchain-graph-2026-09-16/comparison/features.py"
SPEC = importlib.util.spec_from_file_location("matched_features", PATH)
features = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(features)


def sources():
    days = pd.date_range("2000-01-01", periods=50, tz="UTC")
    market = pd.DataFrame(dict(day=days, open=np.arange(50)+100., close=np.exp(np.arange(50)*.01),
                              quote_volume=np.arange(50)*10., available_at=days))
    graph = pd.DataFrame(dict(day=days, events=np.arange(50)+10, nodes=4, directed_pairs=3,
                             stars=2, dyads=4, triangles=6, overlap_nodes=5, nonzero_nodes=2, available_at=days))
    return market, graph


def build(market, graph, start="2000-02-10", end="2000-02-13"):
    return features.build_panel(market, graph, start=start, end=end)


def test_exact_features_clock_floors_and_hand_values():
    market, graph = sources()
    panel, arms = build(market, graph)
    assert [len(arms[m]) for m in ("M0", "M1", "M2")] == [7, 13, 20]
    first = panel.iloc[0]  # February10 -> source February8 = row38
    assert first.return_1 == pytest.approx(.01)
    assert first.return_7 == pytest.approx(.07)
    assert first.return_30 == pytest.approx(.30)
    assert first.volatility_7 == pytest.approx(0, abs=1e-14)
    assert first.volatility_30 == pytest.approx(0, abs=1e-14)
    assert first.log_quote_volume == pytest.approx(np.log(381))
    assert first.relative_quote_volume_7 == pytest.approx(np.log(381/351))
    assert first.events_log_count == pytest.approx(np.log(49))
    assert first.events_relative_7 == pytest.approx(np.log(49/46))
    assert first.triangles_per_event == pytest.approx(6/49)
    assert first.nonzero_fraction == .4
    assert first.return_30__available_at == pd.Timestamp("2000-02-09T00:05Z")
    assert first.triangles_per_event__available_at == first.decision_at
    assert panel.y.tolist() == [1., 1., 1.]


def test_future_source_rows_and_current_open_never_change_features():
    market, graph = sources()
    before, arms = build(market, graph, end="2000-02-11")
    market.loc[market.day >= "2000-02-09", ["open", "close", "quote_volume"]] = 9999
    graph.loc[graph.day >= "2000-02-09", "stars"] = 9999
    after, _ = build(market, graph, end="2000-02-11")
    pd.testing.assert_frame_equal(before[arms["M2"]], after[arms["M2"]])
    assert after.y.iloc[0] == 0  # Equal opening endpoints are zero.


def test_missing_calendar_day_breaks_windows_without_compression():
    market, graph = sources()
    market = market.drop(index=35)
    graph = graph.drop(index=36)
    panel, _ = build(market, graph)
    assert panel.return_7.isna().all()
    assert panel.events_relative_7.isna().all()
    assert panel.return_1.notna().all()
    assert panel.return_7__available_at.isna().all()


def test_warmup_and_missing_label_remain_unknown():
    market, graph = sources()
    panel, _ = build(market, graph, start="2000-01-03", end="2000-01-04")
    assert np.isnan(panel.return_30.iloc[0])
    assert pd.isna(panel.return_30__available_at.iloc[0])
    market = market.drop(index=41)
    panel, _ = build(market, graph)
    assert panel.y.iloc[:2].isna().all()


def test_late_input_clock_propagates_across_rolling_window():
    market, graph = sources()
    late = pd.Timestamp("2000-03-01T00:00Z")
    market.loc[35, "available_at"] = late
    graph.loc[34, "available_at"] = late
    panel, _ = build(market, graph)
    assert (panel.return_7__available_at == late).all()
    assert (panel.events_relative_7__available_at == late).all()
    assert (panel.return_1__available_at < panel.decision_at).all()


@pytest.mark.parametrize("kind", ["duplicate", "negative_price", "fractional_count", "bad_denominator", "infinite"])
def test_malformed_sources_fail(kind):
    market, graph = sources()
    if kind == "duplicate":
        graph = pd.concat([graph, graph.iloc[[0]]])
    elif kind == "negative_price":
        market.loc[0, "close"] = -1
    elif kind == "fractional_count":
        graph["events"] = graph.events.astype(float)
        graph.loc[0, "events"] = 2.5
    elif kind == "bad_denominator":
        graph.loc[0, "nonzero_nodes"] = 6
    else:
        market.loc[0, "quote_volume"] = np.inf
    with pytest.raises(ValueError):
        build(market, graph)


def test_empty_overlap_and_missing_actual_clock_are_not_imputed():
    market, graph = sources()
    graph.loc[38, features.COUNTS] = 0
    market.loc[38, "available_at"] = pd.NaT
    panel, _ = build(market, graph)
    assert np.isnan(panel.nonzero_fraction.iloc[0])
    assert pd.isna(panel.return_1__available_at.iloc[0])

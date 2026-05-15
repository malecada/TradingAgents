"""Tests for per-coin pool_map routing in the V2 quant engine."""

from __future__ import annotations

import pandas as pd
import pytest


def test_candidate_pred_dirs_pool_map_overrides_altcoin_default():
    from tradingagents.strategies.quant_engine import _candidate_pred_dirs

    out = _candidate_pred_dirs(
        "ethereum",
        base_dir="data/multi_2coins_v2",
        pool_map={"ethereum": "data/multi_2coins_pit_wf"},
    )
    assert out[0] == "data/multi_2coins_pit_wf", \
        f"pool_map override must be first candidate, got {out}"


def test_candidate_pred_dirs_pool_map_misses_coin_falls_back():
    from tradingagents.strategies.quant_engine import _candidate_pred_dirs

    out = _candidate_pred_dirs(
        "bitcoin",
        base_dir="data/multi_2coins_v2",
        pool_map={"ethereum": "data/multi_2coins_pit_wf"},
    )
    # BTC not in map -> normal candidates only
    assert "data/multi_2coins_v2" in out
    assert "data/multi_2coins_pit_wf" not in out


def test_candidate_pred_dirs_pool_map_none_is_back_compat():
    from tradingagents.strategies.quant_engine import _candidate_pred_dirs

    out_old = _candidate_pred_dirs("bitcoin", base_dir="data/multi_2coins_v2")
    out_new = _candidate_pred_dirs("bitcoin", base_dir="data/multi_2coins_v2", pool_map=None)
    assert out_old == out_new


def test_v5_provider_passes_pool_map(monkeypatch):
    from tradingagents.strategies import quant_signal_provider as qsp
    from tradingagents.strategies.contracts import QuantSignal

    captured = {}
    def _fake_impl(coin, date, base_dir=None, pool_map=None):
        captured["call"] = (coin, date, base_dir, pool_map)
        return QuantSignal(
            coin=coin, direction="long", magnitude=0.5,
            regime="bull", regime_confidence=0.7, hurst=0.55,
            deterministic_signals={}, as_of_date=date,
        )
    monkeypatch.setattr(
        "tradingagents.strategies.quant_engine.get_quant_signal",
        _fake_impl,
    )

    provider = qsp.build_provider(
        "v5",
        pool_map={"ethereum": "data/multi_2coins_pit_wf"},
    )
    sig = provider.signal("ethereum", pd.Timestamp("2025-06-01"))
    assert sig.direction == "long"
    assert captured["call"][3] == {"ethereum": "data/multi_2coins_pit_wf"}


def test_build_provider_v5_requires_pool_map():
    from tradingagents.strategies.quant_signal_provider import build_provider
    with pytest.raises(ValueError, match="pool_map"):
        build_provider("v5")


def test_get_active_quant_signal_v5_uses_pool_map(monkeypatch):
    from tradingagents.strategies import quant_signal_provider as qsp
    from tradingagents.strategies.contracts import QuantSignal

    captured = {}
    def _fake_impl(coin, date, base_dir=None, pool_map=None):
        captured["pool_map"] = pool_map
        return QuantSignal(
            coin=coin, direction="flat", magnitude=0.0,
            regime="sideways", regime_confidence=0.5, hurst=0.5,
            deterministic_signals={}, as_of_date=date,
        )
    monkeypatch.setattr(
        "tradingagents.strategies.quant_engine.get_quant_signal",
        _fake_impl,
    )

    qsp.set_active_quant_version("v5", pool_map={"bitcoin": "p1", "ethereum": "p2"})
    try:
        qsp.get_active_quant_signal("bitcoin", pd.Timestamp("2025-06-01"))
        assert captured["pool_map"] == {"bitcoin": "p1", "ethereum": "p2"}
    finally:
        qsp.set_active_quant_version("v2")

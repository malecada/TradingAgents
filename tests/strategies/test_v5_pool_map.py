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

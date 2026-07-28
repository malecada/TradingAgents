"""Guard the modulator prompt-version flag.

v1 is the frozen thesis prompt (multiplier 0.0 == "trust quant only");
v2 realigns the semantics with the composition formula (neutral == 1.0).
These tests pin the contract so a future edit can't silently swap them.
"""

from __future__ import annotations

from tradingagents.agents.modulator import _build_prompt
from tradingagents.strategies.contracts import QuantSignal


def _quant_signal() -> QuantSignal:
    return QuantSignal(
        coin="bitcoin",
        as_of_date="2026-06-16",
        direction="long",
        magnitude=0.5,
        regime="bull",
        regime_confidence=0.7,
        hurst=0.55,
        deterministic_signals={"unlock_flag": False, "lgb_h7": 0.01},
    )


def _sys_text(version: str) -> str:
    msgs = _build_prompt(
        coin_alias="ASSET-X",
        quant_signal=_quant_signal(),
        trader_plan="hold",
        factual_report="",
        subjective_report="",
        regime_note="",
        prompt_version=version,
    )
    assert msgs[0]["role"] == "system"
    return msgs[0]["content"]


def test_default_is_v1():
    # No version arg → frozen v1 semantics.
    msgs = _build_prompt(
        coin_alias="ASSET-X",
        quant_signal=_quant_signal(),
        trader_plan="",
        factual_report="",
        subjective_report="",
        regime_note="",
    )
    assert "trust quant only" in msgs[0]["content"]
    assert "0.0  — fully damp" in msgs[0]["content"]


def test_v1_labels_zero_as_trust_quant():
    sys = _sys_text("v1")
    assert "0.0  — fully damp the LLM signal; trust quant only." in sys


def test_v2_labels_one_as_neutral_not_zero():
    sys = _sys_text("v2")
    # Neutral / defer is 1.0 in v2.
    assert "1.0  — neutral; defer entirely to quant" in sys
    # v2 must NOT carry the v1 mislabel.
    assert "0.0  — fully damp the LLM signal; trust quant only." not in sys


def test_v2_explains_zero_is_a_shrink_not_a_noop():
    sys = _sys_text("v2")
    assert "0.0 is the maximal shrink" in sys


def test_unknown_version_falls_back_to_v1():
    assert _sys_text("v9") == _sys_text("v1")

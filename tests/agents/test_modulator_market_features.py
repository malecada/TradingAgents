from unittest.mock import MagicMock

from tradingagents.agents.modulator import _build_prompt
from tradingagents.strategies.contracts import QuantSignal


def _qs():
    return QuantSignal(
        coin="bitcoin",
        direction="long",
        magnitude=0.4,
        regime="bull",
        regime_confidence=0.7,
        hurst=0.55,
        deterministic_signals={"lgb_h7": 0.6, "lgb_h14": 0.55},
        as_of_date="2026-01-15",
    )


def test_build_prompt_includes_market_block_when_features_present():
    market_feats = {
        "market_regime": "TREND_UP",
        "market_conflict_score": 0.25,
        "market_default_direction": "LONG",
        "market_llm_direction": "LONG",
        "market_llm_conviction_calibrated": 0.62,
    }
    msgs = _build_prompt(
        coin_alias="Asset_A",
        quant_signal=_qs(),
        trader_plan="",
        factual_report="",
        subjective_report="",
        regime_note="",
        sentiment_features=None,
        market_features=market_feats,
    )
    sys = msgs[0]["content"]
    assert "MarketSnapshot features" in sys
    assert "market_llm_conviction_calibrated" in sys
    assert "0.62" in sys


def test_build_prompt_omits_market_block_when_no_features():
    msgs = _build_prompt(
        coin_alias="Asset_A",
        quant_signal=_qs(),
        trader_plan="", factual_report="",
        subjective_report="", regime_note="",
        sentiment_features=None,
        market_features=None,
    )
    sys = msgs[0]["content"]
    assert "MarketSnapshot features" not in sys

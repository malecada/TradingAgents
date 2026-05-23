"""Tests for Task 13: sentiment_features injection into modulator LLM prompt.

Imports modulator._build_prompt directly, stubbing all heavy transitive
dependencies so the test only exercises _build_prompt's pure string-building
logic, with no LLM, dataflow, or model code executed.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock


_WDIR = Path(__file__).parent.parent.parent


def _stub(name: str, **attrs) -> types.ModuleType:
    """Register a stub module in sys.modules if not already present."""
    if name in sys.modules:
        return sys.modules[name]
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m
    return m


def _make_package_stub(name: str) -> types.ModuleType:
    """Make a stub that looks like a package (has __path__)."""
    parts = name.split(".")
    # Ensure all parent packages exist
    for i in range(1, len(parts)):
        parent = ".".join(parts[:i])
        if parent not in sys.modules:
            p = types.ModuleType(parent)
            p.__path__ = []
            p.__package__ = parent
            sys.modules[parent] = p
    m = types.ModuleType(name)
    m.__path__ = []
    m.__package__ = name
    sys.modules[name] = m
    return m


def _load_build_prompt():
    """
    Load _build_prompt from tradingagents.agents.modulator by stubbing
    every heavy transitive dependency.  Called once per test (the function
    is cheap; module is cached in sys.modules after the first call).
    """
    # ------------------------------------------------------------------
    # 1. Stub the tradingagents.agents package so __init__.py is bypassed
    # ------------------------------------------------------------------
    if "tradingagents.agents" not in sys.modules:
        pkg = types.ModuleType("tradingagents.agents")
        pkg.__path__ = [str(_WDIR / "tradingagents" / "agents")]
        pkg.__package__ = "tradingagents.agents"
        sys.modules["tradingagents.agents"] = pkg

    # ------------------------------------------------------------------
    # 2. Stub every sub-import that modulator.py pulls in
    # ------------------------------------------------------------------
    # agent_utils  — only need build_instrument_context
    if "tradingagents.agents.utils" not in sys.modules:
        _make_package_stub("tradingagents.agents.utils")
    if "tradingagents.agents.utils.agent_utils" not in sys.modules:
        m = types.ModuleType("tradingagents.agents.utils.agent_utils")
        m.build_instrument_context = lambda coin: f"[{coin}]"
        sys.modules["tradingagents.agents.utils.agent_utils"] = m

    # anonymizer
    if "tradingagents.agents.utils.anonymizer" not in sys.modules:
        m = types.ModuleType("tradingagents.agents.utils.anonymizer")
        m.unmask = lambda text, coin: text
        m.is_enabled = lambda: False
        m.mask = lambda coin: coin
        sys.modules["tradingagents.agents.utils.anonymizer"] = m

    # beliefs_store
    if "tradingagents.dataflows" not in sys.modules:
        _make_package_stub("tradingagents.dataflows")
    if "tradingagents.dataflows.beliefs_store" not in sys.modules:
        m = types.ModuleType("tradingagents.dataflows.beliefs_store")
        m.latest_belief = lambda coin: None
        sys.modules["tradingagents.dataflows.beliefs_store"] = m

    # llm_clients
    if "tradingagents.llm_clients" not in sys.modules:
        _make_package_stub("tradingagents.llm_clients")
    if "tradingagents.llm_clients.multi_sample" not in sys.modules:
        m = types.ModuleType("tradingagents.llm_clients.multi_sample")
        m.MultiSampleCachedChatModel = MagicMock
        sys.modules["tradingagents.llm_clients.multi_sample"] = m

    # strategies — use real __path__ so contracts.py can be found
    if "tradingagents.strategies" not in sys.modules:
        pkg = types.ModuleType("tradingagents.strategies")
        pkg.__path__ = [str(_WDIR / "tradingagents" / "strategies")]
        pkg.__package__ = "tradingagents.strategies"
        sys.modules["tradingagents.strategies"] = pkg
    if "tradingagents.strategies.calibration" not in sys.modules:
        m = types.ModuleType("tradingagents.strategies.calibration")
        m.load_or_identity = MagicMock(return_value=MagicMock(transform=lambda x: x))
        sys.modules["tradingagents.strategies.calibration"] = m

    # strategies.modulator
    if "tradingagents.strategies.modulator" not in sys.modules:
        m = types.ModuleType("tradingagents.strategies.modulator")
        m.apply_modulator = MagicMock()
        sys.modules["tradingagents.strategies.modulator"] = m

    # strategies.quant_signal_provider
    if "tradingagents.strategies.quant_signal_provider" not in sys.modules:
        m = types.ModuleType("tradingagents.strategies.quant_signal_provider")
        m.get_active_quant_signal = MagicMock()
        sys.modules["tradingagents.strategies.quant_signal_provider"] = m

    # numpy (usually installed, but just in case)
    # ------------------------------------------------------------------
    # 3. Import the real modulator module
    # ------------------------------------------------------------------
    if "tradingagents.agents.modulator" not in sys.modules:
        import importlib.util  # noqa: PLC0415
        spec = importlib.util.spec_from_file_location(
            "tradingagents.agents.modulator",
            str(_WDIR / "tradingagents" / "agents" / "modulator.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        mod.__package__ = "tradingagents.agents"
        sys.modules["tradingagents.agents.modulator"] = mod
        spec.loader.exec_module(mod)

    return sys.modules["tradingagents.agents.modulator"]._build_prompt


def _make_quant_signal():
    from tradingagents.strategies.contracts import QuantSignal  # noqa: PLC0415
    return QuantSignal(
        coin="BTC",
        as_of_date="2026-01-01",
        direction="long",
        magnitude=0.5,
        regime="bull",
        regime_confidence=0.8,
        hurst=0.55,
        deterministic_signals={"lgb_h7": 0.6, "lgb_h14": 0.55},
    )


def test_prompt_includes_sentiment_block_when_features_provided():
    """sentiment_features dict must appear verbatim in the system prompt."""
    _build_prompt = _load_build_prompt()
    qs = _make_quant_signal()
    sentiment_features = {"polarity_news": 65.0, "fng_level": 55.0}

    messages = _build_prompt(
        coin_alias="Asset-A",
        quant_signal=qs,
        trader_plan="Buy and hold.",
        factual_report="On-chain looks healthy.",
        subjective_report="Sentiment is positive.",
        regime_note="Bull market regime.",
        sentiment_features=sentiment_features,
    )

    full = " ".join(m["content"] for m in messages)
    assert "polarity_news" in full, "Expected 'polarity_news' key in prompt"
    assert "65.0" in full or "65" in full, "Expected sentiment value '65' in prompt"
    assert "Layer-2 SentimentSnapshot" in full, (
        "Expected sentinel header 'Layer-2 SentimentSnapshot' in prompt"
    )


def test_prompt_omits_sentiment_block_when_features_absent():
    """Without sentiment_features, the block must not appear in the prompt."""
    _build_prompt = _load_build_prompt()
    qs = _make_quant_signal()

    messages = _build_prompt(
        coin_alias="Asset-A",
        quant_signal=qs,
        trader_plan="Buy and hold.",
        factual_report="On-chain looks healthy.",
        subjective_report="Sentiment is positive.",
        regime_note="Bull market regime.",
    )

    full = " ".join(m["content"] for m in messages)
    assert "Layer-2 SentimentSnapshot" not in full, (
        "Sentinel header must not appear when sentiment_features is absent"
    )

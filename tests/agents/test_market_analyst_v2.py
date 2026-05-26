from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from tradingagents.agents.analysts.market_analyst import create_market_analyst


def _state():
    return {
        "trade_date": "2026-01-15",
        "company_of_interest": "bitcoin",
        "messages": [],
    }


def _fake_snapshot(direction="LONG", conflict=0.25):
    from tradingagents.market.snapshot import (
        IndicatorReading, MarketSnapshot,
    )
    now = datetime(2026, 1, 15, tzinfo=timezone.utc)
    return MarketSnapshot(
        asset="Asset_A", as_of_ts=now, trade_date=now,
        horizon_days=7,
        regime="TREND_UP", regime_confidence=0.7,
        adx=28.0, atr_percentile=0.6, return_30d=0.05,
        indicators=[IndicatorReading(
            name="rsi", value=60.0, category="momentum", direction=1,
        )],
        category_votes={"trend": 1, "momentum": 1, "volatility": 0, "volume": 1},
        conflict_score=conflict, default_direction=direction,
    )


def test_legacy_mode_unchanged():
    fake_llm = MagicMock()
    fake_response = MagicMock(content="legacy text", tool_calls=[])
    fake_llm.bind_tools.return_value.invoke.return_value = fake_response
    with patch("tradingagents.agents.analysts.market_analyst.get_config",
               return_value={"market_mode": "legacy", "asset_class": "crypto"}):
        node = create_market_analyst(fake_llm)
        out = node(_state())
    assert "market_report" in out
    assert out.get("market_features", {}) == {}


def test_v2_skip_llm_emits_snapshot_only():
    fake_llm = MagicMock()
    with patch("tradingagents.agents.analysts.market_analyst.build_market_snapshot",
               return_value=_fake_snapshot()), \
         patch("tradingagents.agents.analysts.market_analyst.get_config",
               return_value={
                   "market_mode": "v2", "market_skip_llm": True,
                   "market_anonymize": False, "market_horizon_days": 7,
                   "asset_class": "crypto",
               }):
        node = create_market_analyst(fake_llm)
        out = node(_state())
    assert "MarketSnapshot" in out["market_report"]
    feats = out["market_features"]
    assert "market_conflict_score" in feats
    assert feats["market_default_direction"] == "LONG"
    assert "market_llm_direction" not in feats


def test_v2_full_parses_llm_output_and_calibrates():
    fake_llm = MagicMock()
    llm_response = MagicMock(
        content=(
            '{"direction": "LONG", "conviction": 0.8, '
            '"conflict_score": 0.25, '
            '"indicators_used": ["rsi"], '
            '"dissenting_indicators": [], '
            '"rationale": "Trend and momentum aligned."}'
        ),
        tool_calls=[],
    )
    fake_llm.invoke.return_value = llm_response

    def fake_calibrator(coin, root="data/checkpoints"):
        from tradingagents.strategies.calibration import IsotonicCalibrator
        import numpy as np
        return IsotonicCalibrator().fit(
            np.linspace(0.0, 1.0, 50),
            np.where(np.linspace(0.0, 1.0, 50) > 0.5, 1, 0),
            coin=coin,
        )

    with patch("tradingagents.agents.analysts.market_analyst.build_market_snapshot",
               return_value=_fake_snapshot()), \
         patch("tradingagents.agents.analysts.market_analyst.load_market_calibrator",
               side_effect=fake_calibrator), \
         patch("tradingagents.agents.analysts.market_analyst.get_config",
               return_value={
                   "market_mode": "v2", "market_skip_llm": False,
                   "market_anonymize": False, "market_horizon_days": 7,
                   "asset_class": "crypto",
               }):
        node = create_market_analyst(fake_llm)
        out = node(_state())

    feats = out["market_features"]
    assert feats["market_llm_direction"] == "LONG"
    assert feats["market_llm_conviction_raw"] == pytest.approx(0.8)
    assert 0.0 <= feats["market_llm_conviction_calibrated"] <= 1.0


def test_v2_unparseable_llm_falls_back_to_default():
    fake_llm = MagicMock()
    fake_llm.invoke.return_value = MagicMock(
        content="this is not JSON at all", tool_calls=[],
    )
    with patch("tradingagents.agents.analysts.market_analyst.build_market_snapshot",
               return_value=_fake_snapshot(direction="FLAT", conflict=0.5)), \
         patch("tradingagents.agents.analysts.market_analyst.load_market_calibrator",
               return_value=MagicMock(transform=lambda x: x)), \
         patch("tradingagents.agents.analysts.market_analyst.get_config",
               return_value={
                   "market_mode": "v2", "market_skip_llm": False,
                   "market_anonymize": False, "market_horizon_days": 7,
                   "asset_class": "crypto",
               }):
        node = create_market_analyst(fake_llm)
        out = node(_state())
    feats = out["market_features"]
    assert feats["market_llm_direction"] == "FLAT"
    assert feats["market_llm_conviction_raw"] == 0.0
    assert feats["market_llm_conviction_calibrated"] == 0.0

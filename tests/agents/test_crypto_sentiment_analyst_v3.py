from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from tradingagents.agents.analysts.crypto_sentiment_analyst import (
    create_crypto_sentiment_analyst,
)


def _state():
    return {
        "trade_date": "2026-01-15",
        "company_of_interest": "bitcoin",
        "messages": [],
    }


def test_v3_mode_calls_build_snapshot(monkeypatch):
    fake_snap = MagicMock()
    fake_snap.to_prompt_table.return_value = "## Snapshot table"
    fake_snap.to_modulator_features.return_value = {
        "polarity_news": 0.1, "agg_signal": 0.2,
    }

    fake_llm = MagicMock()
    fake_response = MagicMock(content="bullish events", tool_calls=[])
    fake_llm.bind_tools.return_value.invoke.return_value = fake_response
    fake_llm.invoke.return_value = fake_response

    with patch("tradingagents.agents.analysts.crypto_sentiment_analyst.build_snapshot",
               return_value=fake_snap), \
         patch("tradingagents.agents.analysts.crypto_sentiment_analyst.get_config",
               return_value={"sentiment_mode": "v3", "sentiment_anonymize": False,
                             "deep_think_llm": "gpt-4o-mini",
                             "quick_think_llm": "gpt-4o-mini"}):
        node = create_crypto_sentiment_analyst(fake_llm)
        out = node(_state())

    assert "sentiment_report" in out
    assert "## Snapshot table" in out["sentiment_report"] or "Snapshot" in out["sentiment_report"]
    assert "sentiment_features" in out
    assert out["sentiment_features"]["agg_signal"] == 0.2


def test_legacy_mode_unchanged(monkeypatch):
    fake_llm = MagicMock()
    fake_response = MagicMock(content="legacy text", tool_calls=[])
    fake_llm.bind_tools.return_value.invoke.return_value = fake_response

    with patch("tradingagents.agents.analysts.crypto_sentiment_analyst.get_config",
               return_value={"sentiment_mode": "legacy"}):
        node = create_crypto_sentiment_analyst(fake_llm)
        out = node(_state())

    assert "sentiment_report" in out
    # Legacy returns features as empty dict (or absent).
    assert out.get("sentiment_features", {}) == {}

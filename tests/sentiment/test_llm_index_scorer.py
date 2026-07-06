"""Tests for LLM 0-4 index scorer."""
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tradingagents.sentiment import llm_index_scorer


class TestParseIndex:
    """Parser tests for the LLM output contract."""

    def test_parses_relevant_with_index(self):
        assert llm_index_scorer.parse_index("Relevant. BTC ETF inflows surge, Index: 3") == 3

    def test_parses_index_with_label_suffix(self):
        assert llm_index_scorer.parse_index("Relevant. Exchange hacked. Index: 0 (Very Negative)") == 0

    def test_not_relevant_returns_none(self):
        assert llm_index_scorer.parse_index("Not relevant. Article is about equities.") is None

    def test_garbage_returns_none(self):
        assert llm_index_scorer.parse_index("I cannot determine this.") is None

    def test_out_of_range_clamped_to_none(self):
        assert llm_index_scorer.parse_index("Relevant. Something, Index: 7") is None


class TestLlmIndexScorer:
    """Integration tests for LlmIndexScorer with cache."""

    def test_score_article_caches_result(self, tmp_path, monkeypatch):
        """Test that second call to score_article with same text+coin does not call _chat again."""
        # Patch the CACHE_PATH before importing/constructing scorer
        cache_db = tmp_path / "llm_score_cache.sqlite"
        monkeypatch.setattr(llm_index_scorer, "CACHE_PATH", cache_db)

        scorer = llm_index_scorer.LlmIndexScorer(model="gpt-4o-mini")

        # Monkeypatch _chat to return fixed string and track calls
        call_count = {"count": 0}

        def mock_chat(prompt: str) -> str:
            call_count["count"] += 1
            return "Relevant. Test article summary, Index: 3"

        scorer._chat = MagicMock(side_effect=mock_chat)

        # First call should invoke _chat
        result1 = scorer.score_article(
            text="This is a test article about Bitcoin",
            coin="bitcoin",
            coin_name="Bitcoin",
            symbol="BTC",
        )
        assert result1["relevant"] is True
        assert result1["idx"] == 3
        assert result1["raw"] == "Relevant. Test article summary, Index: 3"
        assert call_count["count"] == 1

        # Second call with same text+coin should use cache, not call _chat
        result2 = scorer.score_article(
            text="This is a test article about Bitcoin",
            coin="bitcoin",
            coin_name="Bitcoin",
            symbol="BTC",
        )
        assert result2["relevant"] is True
        assert result2["idx"] == 3
        assert result2["raw"] == "Relevant. Test article summary, Index: 3"
        assert call_count["count"] == 1  # Should not have incremented

        # Third call with different coin should call _chat again
        result3 = scorer.score_article(
            text="This is a test article about Bitcoin",
            coin="ethereum",
            coin_name="Ethereum",
            symbol="ETH",
        )
        assert result3["relevant"] is True
        assert result3["idx"] == 3
        assert call_count["count"] == 2  # Should have incremented

"""Unit tests for sentiment scorer cache behavior."""
import numpy as np
from tradingagents.sentiment import scorers


class FakeScorer(scorers._BertScorer):
    """Fake scorer that returns fixed predictions without model loading."""

    MODEL_ID = "fake/model"
    calls = 0

    def _infer(self, texts):
        """Return fixed predictions without loading any model."""
        FakeScorer.calls += len(texts)
        return np.tile(np.array([[0.2, 0.3, 0.5]]), (len(texts), 1))


def test_cache_hit_avoids_reinference(tmp_path, monkeypatch):
    """Cache hit should not invoke _infer a second time."""
    monkeypatch.setattr(scorers, "CACHE_PATH", tmp_path / "cache.sqlite")
    FakeScorer.calls = 0  # Reset call count

    s = FakeScorer()
    r1 = s.score(["hello world"])
    n = FakeScorer.calls
    assert n == 1, "First score should call _infer once"

    s2 = FakeScorer()
    r2 = s2.score(["hello world"])
    assert FakeScorer.calls == n, "Second score should be served from cache"
    assert np.allclose(r1, r2), "Results should match"


def test_polarity_mean_is_bull_minus_bear(tmp_path, monkeypatch):
    """score_polarity_mean should return p_bull - p_bear."""
    monkeypatch.setattr(scorers, "CACHE_PATH", tmp_path / "cache.sqlite")
    FakeScorer.calls = 0

    s = FakeScorer()
    result = s.score_polarity_mean(["x"])
    expected = 0.5 - 0.2  # p_bull - p_bear
    assert abs(result - expected) < 1e-9, f"Expected {expected}, got {result}"

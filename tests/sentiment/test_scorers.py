import numpy as np
import pytest

from tradingagents.sentiment.scorers import (
    CryptoBertScorer,
    FinBertCryptoScorer,
    score_polarity_mean,
)


# These tests touch HuggingFace model download — skip in CI without HF cache.
pytestmark = pytest.mark.skipif(
    not pytest.importorskip("transformers", reason="transformers not installed"),
    reason="needs transformers",
)


def test_cryptobert_scores_have_shape_n_by_3():
    scorer = CryptoBertScorer()
    out = scorer.score(["Bitcoin to the moon!", "Crypto crash imminent."])
    assert out.shape == (2, 3)
    assert np.allclose(out.sum(axis=1), 1.0, atol=1e-3)


def test_cryptobert_deterministic():
    scorer = CryptoBertScorer()
    a = scorer.score(["Ethereum upgrade is a success."])
    b = scorer.score(["Ethereum upgrade is a success."])
    np.testing.assert_allclose(a, b, atol=1e-6)


def test_score_polarity_mean_collapses_to_scalar():
    scorer = CryptoBertScorer()
    probs = scorer.score(["bullish", "bearish", "neutral"])
    mean = score_polarity_mean(probs)
    assert -1.0 <= mean <= 1.0


def test_finbert_scores_have_shape_n_by_3():
    scorer = FinBertCryptoScorer()
    out = scorer.score(["The exchange was hacked."])
    assert out.shape == (1, 3)

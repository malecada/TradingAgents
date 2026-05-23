from tradingagents.default_config import DEFAULT_CONFIG


def test_sentiment_mode_default_is_legacy():
    assert DEFAULT_CONFIG["sentiment_mode"] == "legacy"


def test_sentiment_anonymize_default_true():
    assert DEFAULT_CONFIG["sentiment_anonymize"] is True

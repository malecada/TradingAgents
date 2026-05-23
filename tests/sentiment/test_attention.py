from datetime import datetime, timezone

import pandas as pd

from tradingagents.sentiment.attention import compute_attention_features


def test_returns_default_when_empty():
    df = pd.DataFrame(columns=["coin", "query", "event_ts", "as_of_ts",
                                "value", "value_z90", "value_z365"])
    feats = compute_attention_features(
        df, coin="bitcoin",
        trade_date=datetime(2026, 1, 5, tzinfo=timezone.utc),
    )
    assert feats["google_search_z"] == 0.0
    assert feats["google_neg_attention_ratio"] == 0.0
    assert feats["twitter_volume_z"] == 0.0


def test_uses_latest_value_z90_for_search():
    df = pd.DataFrame([
        {"coin": "bitcoin", "query": "bitcoin",
         "event_ts": datetime(2026, 1, 3, tzinfo=timezone.utc),
         "as_of_ts": datetime(2026, 1, 4, tzinfo=timezone.utc),
         "value": 70.0, "value_z90": 1.2, "value_z365": 0.8},
    ])
    feats = compute_attention_features(
        df, coin="bitcoin",
        trade_date=datetime(2026, 1, 5, tzinfo=timezone.utc),
    )
    assert feats["google_search_z"] == 1.2


def test_neg_attention_ratio_uses_hack_query():
    df = pd.DataFrame([
        {"coin": "bitcoin", "query": "bitcoin",
         "event_ts": datetime(2026, 1, 3, tzinfo=timezone.utc),
         "as_of_ts": datetime(2026, 1, 4, tzinfo=timezone.utc),
         "value": 100.0, "value_z90": 0.0, "value_z365": 0.0},
        {"coin": "bitcoin", "query": "bitcoin hack",
         "event_ts": datetime(2026, 1, 3, tzinfo=timezone.utc),
         "as_of_ts": datetime(2026, 1, 4, tzinfo=timezone.utc),
         "value": 5.0, "value_z90": 1.8, "value_z365": 1.0},
    ])
    feats = compute_attention_features(
        df, coin="bitcoin",
        trade_date=datetime(2026, 1, 5, tzinfo=timezone.utc),
    )
    assert feats["google_neg_attention_ratio"] > 0

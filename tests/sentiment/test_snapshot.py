from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from tradingagents.sentiment.snapshot import (
    CryptoEventType,
    EventFlag,
    SentimentSnapshot,
)


def _now():
    return datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_event_type_enum_has_required_members():
    assert CryptoEventType.EXCHANGE_HACK.value == "exchange_hack"
    assert CryptoEventType.ETF_APPROVAL_DENIAL.value == "etf_approval_denial"
    assert CryptoEventType.NONE.value == "none"


def test_event_flag_round_trip():
    flag = EventFlag(
        event_type=CryptoEventType.EXCHANGE_HACK,
        asset="BTC",
        direction_hint=-1,
        severity=0.7,
        event_ts=_now(),
        as_of_ts=_now(),
        half_life_days=3.0,
        confidence=0.8,
    )
    assert flag.event_type == CryptoEventType.EXCHANGE_HACK
    assert flag.direction_hint == -1
    dumped = flag.model_dump_json()
    EventFlag.model_validate_json(dumped)


def test_event_flag_rejects_out_of_range_direction():
    with pytest.raises(ValidationError):
        EventFlag(
            event_type=CryptoEventType.NONE,
            asset="BTC",
            direction_hint=2,
            severity=0.0,
            event_ts=_now(),
            as_of_ts=_now(),
            confidence=0.0,
        )


def test_event_flag_rejects_bad_asset():
    with pytest.raises(ValidationError):
        EventFlag(
            event_type=CryptoEventType.NONE,
            asset="DOGE",
            direction_hint=0,
            severity=0.0,
            event_ts=_now(),
            as_of_ts=_now(),
            confidence=0.0,
        )


def test_snapshot_minimal_construction():
    snap = SentimentSnapshot(
        asset="BTC",
        as_of_ts=_now(),
        trade_date=_now(),
        horizon_days=14,
        polarity_news=0.1,
        polarity_social=0.0,
        polarity_news_n=10,
        polarity_social_n=0,
        google_search_z=0.5,
        google_neg_attention_ratio=0.02,
        twitter_volume_z=0.0,
        fng_level=55.0,
        fng_ema24w=50.0,
        fng_extreme_flag=0,
        agg_signal=0.2,
        agg_signal_lo95=-0.1,
        agg_signal_hi95=0.5,
        model_version="v3-2026-05",
    )
    assert snap.events == []


def test_snapshot_to_modulator_features_returns_dict():
    snap = SentimentSnapshot(
        asset="BTC", as_of_ts=_now(), trade_date=_now(), horizon_days=14,
        polarity_news=0.1, polarity_social=0.0,
        polarity_news_n=10, polarity_social_n=0,
        google_search_z=0.5, google_neg_attention_ratio=0.02, twitter_volume_z=0.0,
        fng_level=55.0, fng_ema24w=50.0, fng_extreme_flag=0,
        agg_signal=0.2, agg_signal_lo95=-0.1, agg_signal_hi95=0.5,
        model_version="v3-2026-05",
    )
    feats = snap.to_modulator_features()
    assert isinstance(feats, dict)
    for key in ("polarity_news", "polarity_event", "attention_search_z",
                "fng_level", "fng_ema24w", "fng_extreme_flag",
                "n_events_regulatory_3d", "n_events_security_3d",
                "n_events_etf_3d", "agg_signal"):
        assert key in feats


def test_snapshot_to_prompt_table_returns_markdown():
    snap = SentimentSnapshot(
        asset="BTC", as_of_ts=_now(), trade_date=_now(), horizon_days=14,
        polarity_news=0.1, polarity_social=0.0,
        polarity_news_n=10, polarity_social_n=0,
        google_search_z=0.5, google_neg_attention_ratio=0.02, twitter_volume_z=0.0,
        fng_level=55.0, fng_ema24w=50.0, fng_extreme_flag=0,
        agg_signal=0.2, agg_signal_lo95=-0.1, agg_signal_hi95=0.5,
        model_version="v3-2026-05",
    )
    md = snap.to_prompt_table()
    assert "|" in md
    assert "Polarity" in md or "polarity" in md

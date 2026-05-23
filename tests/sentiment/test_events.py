from datetime import datetime, timezone

import pandas as pd

from tradingagents.sentiment.events import (
    classify_event_rule,
    extract_events,
    THEME_TO_EVENT,
)
from tradingagents.sentiment.snapshot import CryptoEventType


def test_theme_to_event_known_mappings():
    assert CryptoEventType.SEC_ENFORCEMENT in THEME_TO_EVENT.values()
    assert CryptoEventType.EXCHANGE_HACK in THEME_TO_EVENT.values()


def test_classify_rule_picks_security_for_hack_theme():
    et, conf = classify_event_rule(
        themes="ECON_CRYPTO;CYBER_ATTACK;EXCHANGE",
        headline="Major exchange hacked, funds drained",
    )
    assert et == CryptoEventType.EXCHANGE_HACK
    assert conf > 0.5


def test_classify_rule_picks_regulatory_for_legislation_theme():
    et, conf = classify_event_rule(
        themes="ECON_CRYPTO;LEGISLATION;ECON_GOVCRYPTO",
        headline="SEC files enforcement action against issuer",
    )
    assert et in {
        CryptoEventType.SEC_ENFORCEMENT,
        CryptoEventType.SEC_RULEMAKING,
        CryptoEventType.NATIONAL_REG,
    }


def test_classify_rule_returns_none_for_irrelevant():
    et, conf = classify_event_rule(
        themes="ENV_CLIMATECHANGE",
        headline="Weather report",
    )
    assert et == CryptoEventType.NONE


def test_extract_events_filters_by_as_of():
    now = datetime(2026, 1, 5, tzinfo=timezone.utc)
    df = pd.DataFrame([
        {"headline": "SEC charges exchange", "themes": "LEGISLATION",
         "event_ts": datetime(2026, 1, 3, tzinfo=timezone.utc),
         "as_of_ts": datetime(2026, 1, 3, 12, tzinfo=timezone.utc),
         "url": ""},
        {"headline": "Future leak", "themes": "LEGISLATION",
         "event_ts": datetime(2026, 1, 5, tzinfo=timezone.utc),
         "as_of_ts": datetime(2026, 1, 5, 23, tzinfo=timezone.utc),
         "url": ""},
    ])
    flags = extract_events(df, coin="BTC", as_of=now)
    assert all(f.as_of_ts < now for f in flags)

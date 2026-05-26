import pytest

from tradingagents.market.category_vote import (
    aggregate_category_votes,
    asymmetric_default_direction,
    conflict_score,
)


def test_aggregate_unanimous_bullish():
    directions = {
        "close_30_sma": 1, "close_50_sma": 1,
        "rsi": 1, "macd": 1, "macds": 1, "macdh": 1,
        "boll": 1, "atr": 0, "boll_ub": 0, "boll_lb": 0, "close_200_sma": 1, "close_10_ema": 1,
        "vwma": 1,
    }
    cats = aggregate_category_votes(directions)
    assert cats["trend"] == 1
    assert cats["momentum"] == 1
    assert cats["volume"] == 1
    assert cats["volatility"] == 1


def test_aggregate_split_trend_and_momentum():
    directions = {
        "close_30_sma": 1, "close_50_sma": 1, "close_200_sma": -1, "close_10_ema": -1,
        "macd": -1, "macds": -1, "macdh": 1, "rsi": 1,
        "boll": 0, "boll_ub": 0, "boll_lb": 0, "atr": 0,
        "vwma": 0,
    }
    cats = aggregate_category_votes(directions)
    assert cats["trend"] == 0
    assert cats["momentum"] == 0
    assert cats["volatility"] == 0
    assert cats["volume"] == 0


def test_conflict_score_all_agree_is_zero():
    cats = {"trend": 1, "momentum": 1, "volatility": 1, "volume": 1}
    assert conflict_score(cats) == 0.0


def test_conflict_score_half_disagree_is_half():
    cats = {"trend": 1, "momentum": 1, "volatility": -1, "volume": -1}
    assert conflict_score(cats) == 0.5


def test_conflict_score_no_signal_is_zero():
    cats = {"trend": 0, "momentum": 0, "volatility": 0, "volume": 0}
    assert conflict_score(cats) == 0.0


def test_asymmetric_long_threshold_two_positive_no_negative():
    cats = {"trend": 1, "momentum": 1, "volatility": 0, "volume": 0}
    assert asymmetric_default_direction(cats) == "LONG"


def test_asymmetric_long_blocked_by_any_negative():
    cats = {"trend": 1, "momentum": 1, "volatility": -1, "volume": 0}
    assert asymmetric_default_direction(cats) == "FLAT"


def test_asymmetric_short_requires_three_negatives():
    cats = {"trend": -1, "momentum": -1, "volatility": 0, "volume": 0}
    assert asymmetric_default_direction(cats) == "FLAT"
    cats = {"trend": -1, "momentum": -1, "volatility": -1, "volume": 0}
    assert asymmetric_default_direction(cats) == "SHORT"


def test_asymmetric_short_blocked_by_any_positive():
    cats = {"trend": -1, "momentum": -1, "volatility": -1, "volume": 1}
    assert asymmetric_default_direction(cats) == "FLAT"


def test_asymmetric_all_zero_is_flat():
    assert asymmetric_default_direction(
        {"trend": 0, "momentum": 0, "volatility": 0, "volume": 0}
    ) == "FLAT"

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from tradingagents.market.snapshot import (
    CategoryDirection,
    DirectionLabel,
    IndicatorReading,
    MarketAnalystOutput,
    MarketCategory,
    MarketSnapshot,
    RegimeLabel,
)


def _now():
    return datetime(2026, 1, 15, tzinfo=timezone.utc)


def test_market_snapshot_minimum_valid():
    snap = MarketSnapshot(
        asset="BTC",
        as_of_ts=_now(),
        trade_date=_now(),
        horizon_days=7,
        regime="TREND_UP",
        regime_confidence=0.7,
        adx=28.0,
        atr_percentile=0.6,
        return_30d=0.05,
        indicators=[
            IndicatorReading(name="close_30_sma", value=20000.0,
                             category="trend", direction=1),
            IndicatorReading(name="rsi", value=62.0,
                             category="momentum", direction=1),
            IndicatorReading(name="atr", value=900.0,
                             category="volatility", direction=0),
            IndicatorReading(name="vwma", value=20100.0,
                             category="volume", direction=1),
        ],
        category_votes={
            "trend": 1, "momentum": 1, "volatility": 0, "volume": 1,
        },
        conflict_score=0.25,
        default_direction="LONG",
    )
    assert snap.asset == "BTC"
    assert snap.conflict_score == 0.25
    assert snap.default_direction == "LONG"


def test_market_snapshot_horizon_bounds_enforced():
    with pytest.raises(ValidationError):
        MarketSnapshot(
            asset="BTC", as_of_ts=_now(), trade_date=_now(),
            horizon_days=0,  # < 1
            regime="RANGE", regime_confidence=0.5,
            adx=10.0, atr_percentile=0.5, return_30d=0.0,
            indicators=[], category_votes={},
            conflict_score=0.0, default_direction="FLAT",
        )


def test_market_snapshot_conflict_score_bounds_enforced():
    with pytest.raises(ValidationError):
        MarketSnapshot(
            asset="BTC", as_of_ts=_now(), trade_date=_now(),
            horizon_days=7,
            regime="RANGE", regime_confidence=0.5,
            adx=10.0, atr_percentile=0.5, return_30d=0.0,
            indicators=[], category_votes={},
            conflict_score=1.5,  # > 1
            default_direction="FLAT",
        )


def test_market_analyst_output_min_valid():
    out = MarketAnalystOutput(
        direction="LONG",
        conviction=0.6,
        conflict_score=0.2,
        indicators_used=["close_30_sma", "rsi", "atr"],
        dissenting_indicators=[],
        rationale="Trend aligned with momentum; volatility neutral.",
    )
    assert out.direction == "LONG"
    assert 0.0 <= out.conviction <= 1.0


def test_market_analyst_output_dissenting_must_be_subset_of_used():
    with pytest.raises(ValidationError):
        MarketAnalystOutput(
            direction="LONG", conviction=0.5, conflict_score=0.4,
            indicators_used=["rsi", "macd"],
            dissenting_indicators=["macd", "boll"],  # boll not in used
            rationale="x",
        )


def test_market_snapshot_to_prompt_table_includes_all_blocks():
    snap = MarketSnapshot(
        asset="ASSET_A", as_of_ts=_now(), trade_date=_now(),
        horizon_days=7,
        regime="TREND_UP", regime_confidence=0.7,
        adx=28.0, atr_percentile=0.6, return_30d=0.05,
        indicators=[
            IndicatorReading(name="close_30_sma", value=20000.0,
                             category="trend", direction=1),
        ],
        category_votes={"trend": 1, "momentum": 0, "volatility": 0, "volume": 0},
        conflict_score=0.25, default_direction="LONG",
    )
    md = snap.to_prompt_table()
    assert "Regime: TREND_UP" in md
    assert "conflict_score" in md.lower()
    assert "category" in md.lower()
    assert "Trend:" in md
    assert "ASSET_A" in md


def test_market_snapshot_to_modulator_features_keys():
    snap = MarketSnapshot(
        asset="BTC", as_of_ts=_now(), trade_date=_now(),
        horizon_days=7,
        regime="RANGE", regime_confidence=0.6,
        adx=15.0, atr_percentile=0.4, return_30d=0.01,
        indicators=[],
        category_votes={"trend": 0, "momentum": 1, "volatility": 0, "volume": -1},
        conflict_score=0.5, default_direction="FLAT",
    )
    feats = snap.to_modulator_features()
    assert set(feats.keys()) >= {
        "market_regime", "market_regime_confidence",
        "market_adx", "market_atr_percentile", "market_return_30d",
        "market_conflict_score", "market_default_direction",
        "market_cat_trend", "market_cat_momentum",
        "market_cat_volatility", "market_cat_volume",
    }
    assert feats["market_default_direction"] == "FLAT"

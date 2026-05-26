"""Pydantic schemas for the v2 market analyst pipeline.

Mirrors the v3 sentiment pipeline at tradingagents/sentiment/snapshot.py:
a deterministic structured snapshot is the LLM's only input on indicator
content, and the LLM emits a structured directional output. The modulator
consumes ``to_modulator_features()`` exactly the way it consumes the
sentiment features dict today.
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal

from pydantic import BaseModel, Field, conint, confloat, validator

RegimeLabel = Literal["TREND_UP", "TREND_DOWN", "RANGE", "HIGH_VOL"]
DirectionLabel = Literal["LONG", "SHORT", "FLAT"]
MarketCategory = Literal["trend", "momentum", "volatility", "volume"]
CategoryDirection = conint(ge=-1, le=1)


class IndicatorReading(BaseModel):
    name: str
    value: float
    category: MarketCategory
    direction: CategoryDirection  # -1 bearish, 0 neutral, +1 bullish


class MarketSnapshot(BaseModel):
    asset: str = Field(min_length=1)
    as_of_ts: datetime
    trade_date: datetime
    horizon_days: conint(ge=1, le=30)

    regime: RegimeLabel
    regime_confidence: confloat(ge=0.0, le=1.0)
    adx: confloat(ge=0.0)
    atr_percentile: confloat(ge=0.0, le=1.0)
    return_30d: float

    indicators: List[IndicatorReading]
    category_votes: Dict[MarketCategory, CategoryDirection]
    conflict_score: confloat(ge=0.0, le=1.0)
    default_direction: DirectionLabel

    def to_prompt_table(self) -> str:
        """Compact Markdown table for the narrow LLM analyst prompt."""
        cv = self.category_votes
        ind_rows = "\n".join(
            f"| {r.name} | {r.category} | {r.value:.6g} | {r.direction:+d} |"
            for r in self.indicators
        ) or "| (none) | | | |"
        return (
            f"### MarketSnapshot for {self.asset} @ {self.trade_date.date()}\n\n"
            f"Regime: {self.regime} (confidence {self.regime_confidence:.2f})\n"
            f"ADX: {self.adx:.2f} | ATR pct: {self.atr_percentile:.2f} | "
            f"30d return: {self.return_30d:+.2%}\n\n"
            f"Category votes — Trend: {cv.get('trend', 0):+d}, "
            f"Momentum: {cv.get('momentum', 0):+d}, "
            f"Volatility: {cv.get('volatility', 0):+d}, "
            f"Volume: {cv.get('volume', 0):+d}\n"
            f"conflict_score: {self.conflict_score:.2f} | "
            f"default_direction: {self.default_direction}\n\n"
            f"| indicator | category | value | direction |\n"
            f"|---|---|---|---|\n{ind_rows}\n"
        )

    def to_modulator_features(self) -> dict:
        """Numeric feature dict consumed by the modulator agent's prompt context."""
        cv = self.category_votes
        return {
            "market_regime": self.regime,
            "market_regime_confidence": self.regime_confidence,
            "market_adx": self.adx,
            "market_atr_percentile": self.atr_percentile,
            "market_return_30d": self.return_30d,
            "market_conflict_score": self.conflict_score,
            "market_default_direction": self.default_direction,
            "market_cat_trend": int(cv.get("trend", 0)),
            "market_cat_momentum": int(cv.get("momentum", 0)),
            "market_cat_volatility": int(cv.get("volatility", 0)),
            "market_cat_volume": int(cv.get("volume", 0)),
        }


class MarketAnalystOutput(BaseModel):
    direction: DirectionLabel
    conviction: confloat(ge=0.0, le=1.0)
    conflict_score: confloat(ge=0.0, le=1.0)
    indicators_used: List[str]
    dissenting_indicators: List[str]
    rationale: str = Field(min_length=1)

    @validator("dissenting_indicators")
    def dissent_subset_of_used(cls, v, values):  # noqa: N805
        used = set(values.get("indicators_used") or [])
        bad = [x for x in v if x not in used]
        if bad:
            raise ValueError(
                f"dissenting_indicators must be subset of indicators_used; "
                f"unknown: {bad}"
            )
        return v

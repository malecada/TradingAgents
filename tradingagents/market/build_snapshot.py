"""Build a MarketSnapshot for one (coin, trade_date) pair.

This is the deterministic, training-free, LLM-free half of the v2 market
analyst. The analyst node passes the snapshot to a narrow LLM via
``snapshot.to_prompt_table()``; the modulator consumes
``snapshot.to_modulator_features()``.

OHLCV is fetched via the same path the legacy analyst's tool delegates
to. We call it directly here to skip the LangChain tool round-trip.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

import pandas as pd

from tradingagents.market.category_vote import (
    aggregate_category_votes,
    asymmetric_default_direction,
    conflict_score,
)
from tradingagents.market.indicators import (
    INDICATOR_CATEGORY,
    INDICATOR_WHITELIST,
    compute_indicator_directions,
    compute_indicator_values,
)
from tradingagents.market.regime_tag import deterministic_regime
from tradingagents.market.snapshot import IndicatorReading, MarketSnapshot


def _load_ohlcv(coin: str, trade_date: datetime, lookback_days: int = 300) -> pd.DataFrame:
    """Defer to the package's OHLCV loader. Mocked in tests.

    Wraps ``tradingagents.dataflows.coingecko_binance._load_crypto_ohlcv``
    which takes ``curr_date`` as a YYYY-mm-dd string and returns a frame
    already filtered to ``Date <= curr_date`` (look-ahead-safe).
    """
    from tradingagents.dataflows.coingecko_binance import _load_crypto_ohlcv

    curr_date = trade_date.strftime("%Y-%m-%d")
    df = _load_crypto_ohlcv(coin, curr_date)
    cutoff = pd.Timestamp(trade_date).tz_localize(None) - pd.Timedelta(days=lookback_days)
    df = df[df["Date"] >= cutoff]
    return df


def build_market_snapshot(
    coin: str,
    trade_date: datetime,
    horizon_days: int = 7,
    anonymize: bool = False,
    lookback_days: int = 300,
    df: Optional[pd.DataFrame] = None,
) -> MarketSnapshot:
    from tradingagents.agents.utils.anonymizer import mask

    df = df if df is not None else _load_ohlcv(coin, trade_date, lookback_days)
    if len(df) < 60:
        raise ValueError(
            f"build_market_snapshot: only {len(df)} bars for {coin} "
            f"<= {trade_date}; need >= 60"
        )

    values = compute_indicator_values(df)
    directions = compute_indicator_directions(df, values)
    regime, regime_conf, feats = deterministic_regime(df)
    cat_votes = aggregate_category_votes(directions)
    cs = conflict_score(cat_votes)
    direction = asymmetric_default_direction(cat_votes)

    indicators = [
        IndicatorReading(
            name=name,
            value=float(values.get(name, float("nan"))),
            category=INDICATOR_CATEGORY[name],
            direction=int(directions.get(name, 0)),
        )
        for name in INDICATOR_WHITELIST
    ]

    asset_label = mask(coin) if anonymize else coin

    return MarketSnapshot(
        asset=asset_label,
        as_of_ts=pd.Timestamp(df["Date"].iloc[-1]).to_pydatetime().replace(
            tzinfo=trade_date.tzinfo
        ),
        trade_date=trade_date,
        horizon_days=int(horizon_days),
        regime=regime,
        regime_confidence=float(regime_conf),
        adx=float(feats.adx),
        atr_percentile=float(feats.atr_percentile),
        return_30d=float(feats.return_30d),
        indicators=indicators,
        category_votes=cat_votes,
        conflict_score=float(cs),
        default_direction=direction,
    )

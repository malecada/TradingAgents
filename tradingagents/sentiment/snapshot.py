"""Pydantic schemas for the v3 sentiment pipeline."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, confloat, conint


class CryptoEventType(str, Enum):
    # Regulatory
    SEC_ENFORCEMENT = "sec_enforcement"
    SEC_RULEMAKING = "sec_rulemaking"
    CFTC_ACTION = "cftc_action"
    MICA_EU = "mica_eu"
    NATIONAL_REG = "national_reg"
    # Market structure
    ETF_FLOW = "etf_flow"
    ETF_APPROVAL_DENIAL = "etf_approval_denial"
    EXCHANGE_LISTING = "exchange_listing"
    EXCHANGE_DELISTING = "exchange_delisting"
    PROOF_OF_RESERVES = "proof_of_reserves"
    # Security
    EXCHANGE_HACK = "exchange_hack"
    PROTOCOL_EXPLOIT = "protocol_exploit"
    BRIDGE_EXPLOIT = "bridge_exploit"
    # Network
    NETWORK_UPGRADE = "network_upgrade"
    HALVING = "halving"
    HARD_FORK = "hard_fork"
    # On-chain
    WHALE_MOVEMENT = "whale_movement"
    EXCHANGE_NETFLOW_EXTREME = "exchange_netflow_extreme"
    # Macro
    FED_FOMC = "fed_fomc"
    CPI_PRINT = "cpi_print"
    DXY_EXTREME = "dxy_extreme"
    NONE = "none"


_REGULATORY = {
    CryptoEventType.SEC_ENFORCEMENT, CryptoEventType.SEC_RULEMAKING,
    CryptoEventType.CFTC_ACTION, CryptoEventType.MICA_EU,
    CryptoEventType.NATIONAL_REG,
}
_SECURITY = {
    CryptoEventType.EXCHANGE_HACK, CryptoEventType.PROTOCOL_EXPLOIT,
    CryptoEventType.BRIDGE_EXPLOIT,
}
_ETF = {CryptoEventType.ETF_FLOW, CryptoEventType.ETF_APPROVAL_DENIAL}


class EventFlag(BaseModel):
    event_type: CryptoEventType
    asset: str = Field(pattern="^(BTC|ETH|MULTI|MACRO)$")
    direction_hint: conint(ge=-1, le=1)
    severity: confloat(ge=0.0, le=1.0)
    event_ts: datetime
    as_of_ts: datetime
    half_life_days: confloat(ge=0.0) = 3.0
    source_url: Optional[str] = None
    confidence: confloat(ge=0.0, le=1.0)


class SentimentSnapshot(BaseModel):
    asset: str = Field(pattern="^(BTC|ETH|MULTI)$")
    as_of_ts: datetime
    trade_date: datetime
    horizon_days: conint(ge=1, le=30)
    # Polarity
    polarity_news: confloat(ge=-1.0, le=1.0)
    polarity_social: confloat(ge=-1.0, le=1.0)
    polarity_news_n: conint(ge=0)
    polarity_social_n: conint(ge=0)
    # Attention
    google_search_z: float
    google_neg_attention_ratio: float
    twitter_volume_z: float
    # Regime
    fng_level: confloat(ge=0.0, le=100.0)
    fng_ema24w: confloat(ge=0.0, le=100.0)
    fng_extreme_flag: conint(ge=0, le=1)
    # Events
    events: List[EventFlag] = []
    # LLM analyst (optional)
    llm_event_summary: Optional[str] = None
    llm_event_conf: confloat(ge=0.0, le=1.0) = 0.0
    # Aggregate
    agg_signal: float
    agg_signal_lo95: float
    agg_signal_hi95: float
    model_version: str

    def _count_events(self, group: set, within_days: int = 3) -> int:
        from datetime import timedelta
        cutoff = self.trade_date - timedelta(days=within_days)
        return sum(
            1 for e in self.events
            if e.event_type in group and e.event_ts >= cutoff
        )

    def to_modulator_features(self) -> dict:
        """Numeric feature dict for the modulator LLM agent's prompt context."""
        polarity_event = (
            sum(e.direction_hint * e.severity * e.confidence for e in self.events)
            / max(len(self.events), 1)
        )
        return {
            "polarity_news": float(self.polarity_news),
            "polarity_event": float(polarity_event),
            "polarity_news_n": int(self.polarity_news_n),
            "attention_search_z": float(self.google_search_z),
            "attention_neg_ratio_z": float(self.google_neg_attention_ratio),
            "fng_level": float(self.fng_level),
            "fng_ema24w": float(self.fng_ema24w),
            "fng_extreme_flag": int(self.fng_extreme_flag),
            "n_events_regulatory_3d": self._count_events(_REGULATORY, 3),
            "n_events_security_3d": self._count_events(_SECURITY, 3),
            "n_events_etf_3d": self._count_events(_ETF, 3),
            "agg_signal": float(self.agg_signal),
        }

    def to_prompt_table(self) -> str:
        """Compact Markdown for the narrow LLM analyst prompt (≤ ~1500 tokens)."""
        feats = self.to_modulator_features()
        lines = [
            f"# SentimentSnapshot — {self.asset} @ {self.trade_date.date()}",
            "",
            "| Feature | Value |",
            "|---|---|",
        ]
        lines.extend(f"| {k} | {v} |" for k, v in feats.items())
        lines.append("")
        if self.events:
            lines.append("## Recent Event Flags")
            lines.append("| Type | Direction | Severity | Event Date | Confidence |")
            lines.append("|---|---|---|---|---|")
            for e in self.events[-10:]:
                lines.append(
                    f"| {e.event_type.value} | {e.direction_hint:+d} | "
                    f"{e.severity:.2f} | {e.event_ts.date()} | {e.confidence:.2f} |"
                )
        lines.append("")
        lines.append(
            f"**Aggregate signal:** {self.agg_signal:+.3f} "
            f"(95% CI [{self.agg_signal_lo95:+.3f}, {self.agg_signal_hi95:+.3f}])"
        )
        return "\n".join(lines)


# --- Orchestrator -----------------------------------------------------------

import logging
from datetime import timedelta
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

MODEL_VERSION = "v3-2026-05"


def _coin_to_asset(coin: str) -> str:
    c = coin.upper()
    if c in {"BTC", "BITCOIN"}: return "BTC"
    if c in {"ETH", "ETHEREUM"}: return "ETH"
    return "MULTI"


def _query_alpaca_headlines(coin: str, trade_date: datetime,
                             lookback_days: int) -> pd.DataFrame:
    from tradingagents.dataflows import sentiment_store
    start = trade_date - timedelta(days=lookback_days)
    ts_end = trade_date + timedelta(days=1) - timedelta(microseconds=1)
    coin_l = coin.lower()
    if coin_l not in sentiment_store.COIN_TO_SYMBOL:
        return pd.DataFrame()
    try:
        return sentiment_store.query_news(
            coin=coin_l, ts_start=start, ts_end=ts_end, as_of=trade_date,
            limit=100, root=sentiment_store.DEFAULT_ROOT,
        )
    except Exception as e:
        logger.warning("Alpaca query failed: %s", e)
        return pd.DataFrame()


def _query_gdelt_rows(coin: str, trade_date: datetime,
                      lookback_days: int) -> pd.DataFrame:
    from tradingagents.dataflows import sentiment_store
    from tradingagents.dataflows.crypto_sentiment_pit import GDELT_ROOT
    start = trade_date - timedelta(days=lookback_days)
    ts_end = trade_date + timedelta(days=1) - timedelta(microseconds=1)
    coin_l = coin.lower()
    if not Path(GDELT_ROOT).exists():
        return pd.DataFrame()
    try:
        df = sentiment_store.query_news(
            coin=coin_l, ts_start=start, ts_end=ts_end, as_of=trade_date,
            limit=200, root=GDELT_ROOT,
        )
        # The GDELT store also carries themes if it was ingested with them.
        return df
    except Exception as e:
        logger.warning("GDELT query failed: %s", e)
        return pd.DataFrame()


def _query_fng_series(trade_date: datetime, lookback_days: int) -> pd.DataFrame:
    from tradingagents.dataflows import fng_store
    try:
        return fng_store.query_fng(
            trade_date=trade_date, lookback_days=lookback_days,
            root=fng_store.DEFAULT_ROOT,
        )
    except Exception as e:
        logger.warning("F&G query failed: %s", e)
        return pd.DataFrame()


def _query_gtrends_rows(coin: str, trade_date: datetime,
                        lookback_days: int) -> pd.DataFrame:
    from tradingagents.dataflows import gtrends_store
    try:
        return gtrends_store.query_attention(
            coin=coin.lower(), trade_date=trade_date,
            lookback_days=lookback_days, root=gtrends_store.DEFAULT_ROOT,
        )
    except Exception as e:
        logger.warning("gtrends query failed: %s", e)
        return pd.DataFrame()


def _score_polarity(texts: list[str], scorer) -> tuple[float, int]:
    if not texts:
        return 0.0, 0
    probs = scorer.score(texts)
    if probs.shape[0] == 0:
        return 0.0, 0
    direction = probs[:, 2] - probs[:, 0]
    return float(direction.mean()), int(probs.shape[0])


def _fng_extreme_flag(level: float) -> int:
    return int(level < 25 or level > 75)


def _bootstrap_ci(values: list[float], n_boot: int = 200,
                  alpha: float = 0.05) -> tuple[float, float]:
    import numpy as np
    if not values:
        return -0.5, 0.5
    arr = np.asarray(values, dtype=float)
    rng = np.random.default_rng(42)
    boots = [arr[rng.integers(0, len(arr), len(arr))].mean()
             for _ in range(n_boot)]
    lo = float(np.quantile(boots, alpha / 2))
    hi = float(np.quantile(boots, 1 - alpha / 2))
    return lo, hi


def _get_cryptobert_default():
    from tradingagents.sentiment.scorers import get_cryptobert as _gc
    return _gc()


def _get_finbert_crypto_default():
    from tradingagents.sentiment.scorers import get_finbert_crypto as _gf
    return _gf()


# Module-level references so tests can patch snap_mod.get_cryptobert / get_finbert_crypto
get_cryptobert = _get_cryptobert_default
get_finbert_crypto = _get_finbert_crypto_default


def build_snapshot(
    coin: str,
    trade_date: datetime,
    horizon_days: int = 14,
) -> SentimentSnapshot:
    """Assemble a SentimentSnapshot for one (coin, trade_date) tuple.

    All queries are PIT-locked. Returns a zero-default snapshot if every
    upstream source is empty.
    """
    from tradingagents.sentiment.attention import compute_attention_features
    from tradingagents.sentiment.events import extract_events
    import tradingagents.sentiment.snapshot as _self
    _get_cryptobert = _self.get_cryptobert
    _get_finbert_crypto = _self.get_finbert_crypto

    lookback = max(horizon_days * 4, 30)

    alpaca_df = _query_alpaca_headlines(coin, trade_date, lookback)
    gdelt_df = _query_gdelt_rows(coin, trade_date, lookback)
    fng_df = _query_fng_series(trade_date, lookback_days=24 * 7)  # 24 weeks for EMA
    gtrends_df = _query_gtrends_rows(coin, trade_date, lookback)

    # Polarity — news (CryptoBERT scorer)
    cryptobert = _get_cryptobert()
    news_texts: list[str] = []
    if not alpaca_df.empty:
        news_texts.extend(
            f"{h} {s or ''}".strip()
            for h, s in zip(alpaca_df["headline"], alpaca_df.get("summary", [""] * len(alpaca_df)))
        )
    if not gdelt_df.empty:
        news_texts.extend(gdelt_df["headline"].tolist())
    pol_news, pol_news_n = _score_polarity(news_texts, cryptobert)

    # Polarity — social (placeholder; Reddit PIT not built in P3)
    pol_social, pol_social_n = 0.0, 0

    # Attention
    att = compute_attention_features(gtrends_df, coin, trade_date)

    # Regime — F&G
    if not fng_df.empty:
        fng_level = float(fng_df["value"].iloc[-1])
        # 24w EMA
        fng_ema24w = float(fng_df["value"].ewm(span=24 * 7, adjust=False).mean().iloc[-1])
    else:
        fng_level, fng_ema24w = 50.0, 50.0
    fng_extreme = _fng_extreme_flag(fng_level)

    # Events
    events = extract_events(gdelt_df, coin=coin, as_of=trade_date)

    # Aggregate signal — simple weighted combination
    polarity_event = (
        sum(e.direction_hint * e.severity * e.confidence for e in events)
        / max(len(events), 1)
    )
    agg = (
        0.30 * pol_news
        + 0.20 * polarity_event
        + 0.20 * att["google_search_z"]
        - 0.20 * att["google_neg_attention_ratio"]
        + 0.10 * (fng_level - 50.0) / 50.0
    )
    component_values = [
        pol_news,
        polarity_event,
        att["google_search_z"],
        -att["google_neg_attention_ratio"],
        (fng_level - 50.0) / 50.0,
    ]
    lo, hi = _bootstrap_ci(component_values)

    return SentimentSnapshot(
        asset=_coin_to_asset(coin),
        as_of_ts=trade_date,
        trade_date=trade_date,
        horizon_days=horizon_days,
        polarity_news=pol_news,
        polarity_social=pol_social,
        polarity_news_n=pol_news_n,
        polarity_social_n=pol_social_n,
        google_search_z=att["google_search_z"],
        google_neg_attention_ratio=att["google_neg_attention_ratio"],
        twitter_volume_z=att["twitter_volume_z"],
        fng_level=fng_level,
        fng_ema24w=fng_ema24w,
        fng_extreme_flag=fng_extreme,
        events=events,
        agg_signal=agg,
        agg_signal_lo95=lo,
        agg_signal_hi95=hi,
        model_version=MODEL_VERSION,
    )

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

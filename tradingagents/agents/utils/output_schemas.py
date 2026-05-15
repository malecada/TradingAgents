"""Pydantic output schemas for agent decision pipelines (Tier B4).

These supersede free-text + regex parsing of analyst, trader, and PM
output. The 5-tier rating scale matches TradingAgents v0.2.4 and the
existing backtest engine's ``FiveLevelSignal`` enum (``BUY |
OVERWEIGHT | HOLD | UNDERWEIGHT | SELL``).

Phase 3 lands the schemas. Phase 4 wires them into the graph via
``with_structured_output()`` and updates the Portfolio Manager prompt
to emit ``PMDecision`` directly.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Rating = Literal["BUY", "OVERWEIGHT", "HOLD", "UNDERWEIGHT", "SELL"]


class AnalystReport(BaseModel):
    """Schema for any analyst-side report (market, on-chain, sentiment, etc.)."""

    coin_alias: str = Field(
        description="Anonymized alias used in this report (e.g. Asset_X)."
    )
    summary: str = Field(description="One-paragraph executive summary.")
    findings: list[str] = Field(
        default_factory=list,
        description="Bulleted observations grounded in retrieved data.",
    )
    confidence: int = Field(
        ge=0, le=100,
        description="Confidence in the findings on a 0-100 scale.",
    )


class DebateTurn(BaseModel):
    """Single bull/bear/skeptic-quant debate turn."""

    persona: Literal["bull", "bear", "skeptic_quant"]
    argument: str
    cited_evidence: list[str] = Field(default_factory=list)


class TraderProposal(BaseModel):
    """Trader synthesizes research into a directional proposal.

    The Trader still emits a 5-tier rating, but Phase 4 will add a parallel
    ``magnitude_hint ∈ [-1, 1]`` field that the Modulator consumes alongside
    the Layer 1 quant signal.
    """

    rating: Rating
    confidence: int = Field(ge=0, le=100)
    rationale: str
    risk_concerns: list[str] = Field(default_factory=list)


class PMDecision(BaseModel):
    """Final Portfolio Manager output. Replaces free-text + regex parsing."""

    coin: str = Field(description="Un-masked coingecko id (set at PM, not earlier).")
    rating: Rating
    confidence: int = Field(ge=0, le=100)
    rationale: str
    investment_thesis: str
    executive_summary: str
    # Optional fields populated by Phase 4 modulator integration
    quant_direction: Optional[Literal["long", "short", "flat"]] = None
    quant_magnitude: Optional[float] = None
    llm_multiplier: Optional[float] = None
    effective_weight: Optional[float] = None


class ModulatorDecision(BaseModel):
    """Layer 2 modulator output before composition with Layer 1 quant.

    ``multiplier`` ∈ [0.0, 1.5] is the prescribed scaling factor relative
    to the Layer 1 quant magnitude. ``narrative`` is the audit-trail
    explanation of the decision.
    """

    multiplier: float = Field(ge=0.0, le=1.5)
    confidence: int = Field(ge=0, le=100)
    narrative: str
    factual_weight: float = Field(
        ge=0.0, le=1.0,
        description="Relative weight given to factual vs subjective inputs.",
    )

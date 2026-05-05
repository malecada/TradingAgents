from __future__ import annotations

from typing import Optional

from tradingagents.strategies.contracts import RegimeLabel

DEFAULT_REGIME_WEIGHT: dict[RegimeLabel, tuple[float, float]] = {
    "bull": (0.2, 0.3),
    "sideways": (0.6, 0.8),
    "bear": (0.4, 0.4),
}


def compute_effective_weight(
    regime: RegimeLabel,
    llm_uncertainty: float,
    rolling_llm_edge: Optional[float],
    unlock_flag: bool,
    regime_weighting: dict[RegimeLabel, tuple[float, float]] = DEFAULT_REGIME_WEIGHT,
    uncertainty_dampener_k: float = 1.0,
    edge_dampener_k: float = 1.0,
) -> float:
    """Compose the data-driven LLM influence weight ∈ [0, 1].

    Phase 0 stub — returns ``0.5`` (or ``0.0`` if ``unlock_flag``). Phase 4
    implements the full formula from the plan: regime band × uncertainty
    dampener × edge dampener × unlock veto.
    """
    if unlock_flag:
        return 0.0
    return 0.5

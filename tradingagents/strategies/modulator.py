from __future__ import annotations

from tradingagents.strategies.contracts import (
    ModulatedPosition,
    ModulatorOutput,
    QuantSignal,
)
from tradingagents.strategies.effective_weight import compute_effective_weight


def apply_modulator(
    quant_signal: QuantSignal,
    llm_output: ModulatorOutput,
    rolling_llm_edge: float | None = None,
    unlock_flag: bool = False,
) -> ModulatedPosition:
    """Compose Layer 1 quant + Layer 2 LLM into a ``ModulatedPosition``.

    Phase 0 stub — passes through with a fixed effective weight. Phase 4
    wires this into the LangGraph as the new Modulator node.
    """
    effective_weight = compute_effective_weight(
        regime=quant_signal.regime,
        llm_uncertainty=llm_output.uncertainty,
        rolling_llm_edge=rolling_llm_edge,
        unlock_flag=unlock_flag,
    )
    position = quant_signal.magnitude * (
        1.0 + effective_weight * (llm_output.multiplier - 1.0)
    )
    return ModulatedPosition(
        coin=quant_signal.coin,
        quant_direction=quant_signal.direction,
        quant_magnitude=quant_signal.magnitude,
        llm_multiplier=llm_output.multiplier,
        llm_confidence=llm_output.confidence,
        llm_uncertainty=llm_output.uncertainty,
        effective_weight=effective_weight,
        position=position,
        narrative=llm_output.narrative,
        regime=quant_signal.regime,
        unlock_flag=unlock_flag,
        rolling_llm_edge=rolling_llm_edge,
    )

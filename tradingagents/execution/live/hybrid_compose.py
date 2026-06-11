# tradingagents/execution/live/hybrid_compose.py
"""Pure compose primitives for the hybrid (quant base × LLM modulator) path.

The composition mirrors the validated §23 backtest
(scripts/backtest_hybrid.py:118, scripts/ablate_hybrid.py:73):

    final = base * (1 + effective_weight * (multiplier - 1))

where ``base`` is the V5-sized quant position and (multiplier, effective_weight)
come from the modulator graph's ``modulated_position`` (NOT its ``position``,
which composed against the graph's own internal magnitude).
"""
from __future__ import annotations


def compose_final(*, base: float, multiplier: float, effective_weight: float) -> float:
    return float(base * (1.0 + effective_weight * (multiplier - 1.0)))


def extract_modulator_outputs(modulated_position: dict | None) -> tuple[float, float]:
    """Return (multiplier, effective_weight) from a modulated_position dict.

    Degrades to pure quant (1.0, 0.0) when the modulator was skipped or any
    field is missing, so a modulator failure never moves the hybrid position
    away from the quant base. Multiplier clamped to the contract bounds [0,1.5].
    """
    if not modulated_position:
        return (1.0, 0.0)
    mult = modulated_position.get("llm_multiplier")
    eff_w = modulated_position.get("effective_weight")
    if mult is None or eff_w is None:
        return (1.0, 0.0)
    mult = max(0.0, min(1.5, float(mult)))
    eff_w = max(0.0, min(1.0, float(eff_w)))
    return (mult, eff_w)

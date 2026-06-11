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

"""Pure decision logic for the S1 champion live executor.

No network, no filesystem: sizing, rounding, position diffing, risk caps,
and journal-row construction as pure functions. The CLI wrapper
(scripts/predlab_s1_live.py) owns all I/O. Spec:
docs/superpowers/specs/2026-08-21-s1-live-executor-design.md
"""
from __future__ import annotations

import math
from dataclasses import dataclass

LEG_WEIGHT_ABS = 0.025  # champion book: 40L/40S quintile-equal


@dataclass(frozen=True)
class SymbolFilter:
    min_notional: float
    step_size: float


def _round_step(qty: float, step: float) -> float:
    """Round |qty| down to the step grid without float dust."""
    n = math.floor(qty / step + 1e-9)
    # quantize via the step's decimal string to avoid 0.30000000000000004
    s = f"{step:.10f}".rstrip("0")
    decimals = len(s.split(".")[1]) if "." in s else 0
    return round(n * step, decimals)


def build_targets(weights: "dict[str, float]", scale: float, equity: float,
                  marks: "dict[str, float]", filters: "dict[str, SymbolFilter]",
                  ) -> "tuple[dict[str, float], list[dict]]":
    """Signed target quantity per symbol; drops legs that cannot trade."""
    targets: "dict[str, float]" = {}
    dropped: "list[dict]" = []

    def drop(sym: str, reason: str, notional: float) -> None:
        dropped.append({"symbol": sym, "reason": reason,
                        "target_notional": round(notional, 2)})

    for sym, w in weights.items():
        notional = abs(w) * scale * equity
        if sym not in marks or not marks[sym]:
            drop(sym, "no_mark", notional)
            continue
        if sym not in filters:
            drop(sym, "no_filter", notional)
            continue
        f = filters[sym]
        if notional < f.min_notional:
            drop(sym, "min_notional", notional)
            continue
        qty = _round_step(notional / marks[sym], f.step_size)
        if qty <= 0:
            drop(sym, "rounds_to_zero", notional)
            continue
        targets[sym] = qty if w > 0 else -qty
    return targets, dropped

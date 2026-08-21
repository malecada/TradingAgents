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


@dataclass(frozen=True)
class Order:
    symbol: str
    side: str          # "BUY" | "SELL"
    qty: float         # always positive
    reduce_only: bool


def diff_orders(targets: "dict[str, float]", positions: "dict[str, float]",
                marks: "dict[str, float]", filters: "dict[str, SymbolFilter]",
                dust_usd: float = 7.0) -> "tuple[list[Order], list[dict]]":
    """Delta market orders taking `positions` to `targets`.

    Reduce-only when the order only shrinks an existing position (exempt
    from Binance MIN_NOTIONAL rejection -4164); a sign flip is one plain
    crossing order. Dust deltas and sub-min-notional increases are skipped.
    """
    orders: "list[Order]" = []
    skipped: "list[dict]" = []
    for sym in sorted(set(targets) | set(positions)):
        tgt = targets.get(sym, 0.0)
        cur = positions.get(sym, 0.0)
        f = filters.get(sym)
        if f is None or sym not in marks:
            continue  # cannot price/round the delta; leg already logged upstream
        delta = _round_step(abs(tgt - cur), f.step_size)
        if delta <= 0:
            continue
        notional = delta * marks[sym]
        if notional < dust_usd:
            skipped.append({"symbol": sym, "reason": "dust",
                            "delta_notional": round(notional, 2)})
            continue
        reduce_only = (
            cur != 0.0
            and (tgt == 0.0 or (math.copysign(1, tgt) == math.copysign(1, cur)
                                and abs(tgt) < abs(cur)))
        )
        if not reduce_only and notional < f.min_notional:
            skipped.append({"symbol": sym,
                            "reason": "increase_below_min_notional",
                            "delta_notional": round(notional, 2)})
            continue
        side = "BUY" if tgt - cur > 0 else "SELL"
        orders.append(Order(sym, side, delta, reduce_only))
    orders.sort(key=lambda o: (not o.reduce_only, o.symbol))
    return orders, skipped

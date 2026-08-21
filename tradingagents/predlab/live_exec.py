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


def check_caps(target_notionals: "dict[str, float]", equity: float,
               gross_cap: float = 2.2, per_symbol_cap: float = 0.05,
               ) -> "list[str]":
    """Hard pre-trade caps on the post-trade book. Empty list = OK."""
    violations: "list[str]" = []
    gross = sum(abs(v) for v in target_notionals.values())
    if gross > gross_cap * equity:
        violations.append(
            f"gross {gross:.0f} > {gross_cap} x equity {equity:.0f}")
    if gross > 0:
        for sym, v in sorted(target_notionals.items()):
            if abs(v) > per_symbol_cap * gross:
                violations.append(
                    f"{sym} notional {abs(v):.0f} > "
                    f"{per_symbol_cap:.0%} of gross {gross:.0f}")
    return violations


def daily_loss_breached(equity: float, day_start_equity: float,
                        limit: float = 0.05) -> bool:
    return equity < (1.0 - limit) * day_start_equity


def build_journal_row(asof: str, executed_utc: str, equity_before: float,
                      equity_day_start: float, scale: float,
                      targets_notional: "dict[str, float]",
                      orders: "list[Order]", dropped: "list[dict]",
                      skipped: "list[dict]", halt: bool, dry_run: bool) -> dict:
    return {
        "asof": asof,
        "executed_utc": executed_utc,
        "equity_before": round(equity_before, 2),
        "equity_day_start": round(equity_day_start, 2),
        "scale": scale,
        "targets": {k: round(v, 2) for k, v in sorted(targets_notional.items())},
        "orders_placed": len(orders),
        "legs_dropped_min_notional": dropped,
        "deltas_skipped_dust": len(skipped),
        "gross_target": round(sum(abs(v) for v in targets_notional.values()), 2),
        "halt": halt,
        "dry_run": dry_run,
    }

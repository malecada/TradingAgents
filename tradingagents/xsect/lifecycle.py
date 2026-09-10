"""Fail-closed original-contract lifetime checks; no settlement is synthesized."""
from __future__ import annotations

import numpy as np
import pandas as pd

HOUR = pd.Timedelta(hours=1)


class LifecycleUnavailable(ValueError):
    """A requested trade/valuation needs unestablished lifecycle evidence."""


def _utc(value):
    stamp = pd.Timestamp(value)
    if stamp.tz is None:
        raise LifecycleUnavailable("lifecycle event must have an explicit timezone")
    return stamp.tz_convert("UTC")


def _clock(index):
    if (not isinstance(index, pd.DatetimeIndex) or index.tz is None or not len(index) or
            not index.equals(pd.date_range(index[0], index[-1], freq="h")) or
            not (index == index.floor("h")).all()):
        raise LifecycleUnavailable("lifecycle checks require a complete UTC hourly clock")
    return index.tz_convert("UTC")


def guard_target_schedule(weights, events):
    """Check full schedules before accounting, including incoming flat exits.

    W[t] is requested when the prior close becomes available at t. A carried
    position cannot be sold before an event at t using the t-1ms close label.
    """
    if not events:
        return
    clock = _clock(weights.index)
    if not weights.columns.is_unique:
        raise LifecycleUnavailable("duplicate target symbols")
    for event in events:
        symbol = event["symbol"]
        if symbol not in weights.columns:
            continue
        w = weights[symbol].to_numpy(dtype=float)
        if not np.isfinite(w).all():
            raise LifecycleUnavailable(f"unknown target allocation: {symbol}")
        closure = _utc(event["closure_utc"])
        previous = np.r_[0., w[:-1]]
        incoming = (clock == closure) & (previous != 0.)
        terminal_interval = (clock < closure) & (clock + HOUR >= closure) & (w != 0.)
        post = (clock >= closure) & (w != 0.)
        bad = incoming | terminal_interval | post
        if bad.any():
            raise LifecycleUnavailable(f"unreconciled terminal exposure: {symbol} at {clock[bad][0]} (closure {closure})")
        restriction = event.get("new_position_restriction_utc")
        if restriction is not None:
            restriction = _utc(restriction)
            if restriction > closure:
                raise LifecycleUnavailable(f"restriction follows closure: {symbol}")
            # Positive requested weights may require increases from NAV/price
            # drift even when unchanged. Quantity is unavailable to this guard.
            restricted = (clock >= restriction) & (clock < closure) & (w != 0.)
            if restricted.any():
                raise LifecycleUnavailable(f"restricted nonzero target decision: {symbol} at {clock[restricted][0]}")


def unavailable_forward_windows(index, columns, horizon, events):
    """P2 entry t+1, fixed-quantity price horizon, exit availability t+H+1.

    The price diagnostic has no intermediate target maintenance. A restriction
    blocks a new entry; a terminal event blocks a held window including its exit.
    """
    clock = _clock(index)
    if horizon < 1:
        raise LifecycleUnavailable("forward horizon must be positive")
    unavailable = pd.DataFrame(False, index=index, columns=columns)
    entry, end = clock + HOUR, clock + (horizon + 1) * HOUR
    for event in events:
        symbol = event["symbol"]
        if symbol not in columns:
            continue
        closure = _utc(event["closure_utc"])
        # This also rejects entries after the original contract has terminated.
        bad = end >= closure
        restriction = event.get("new_position_restriction_utc")
        if restriction is not None:
            restriction = _utc(restriction)
            if restriction > closure:
                raise LifecycleUnavailable(f"restriction follows closure: {symbol}")
            bad |= entry >= restriction
        unavailable[symbol] |= bad
    return unavailable

"""Purged rolling-origin walk-forward splitter.

Data convention (used by every predlab module): arrays are indexed by origin
``t`` where ``y[t]`` is the target realized over ``(t, t+h]`` and becomes known
at ``t+h``. Features/forecasts at origin ``t`` use information <= ``t``.

A train origin ``s`` is usable at forecast origin ``o`` only if its label is
fully realized and clear of the embargo: ``s + h <= o - embargo``. That purge
is what prevents label-overlap leakage for h-step targets.
"""

from __future__ import annotations

from dataclasses import dataclass

# A split whose purged train set has fewer than this many origins is dropped:
# nothing meaningful can be fit on less.
MIN_TRAIN_EFFECTIVE = 30


@dataclass
class OriginSplit:
    origin: int
    train_end: int  # exclusive: usable train origins are range(0, train_end)


def rolling_origin(
    n: int,
    min_train: int,
    horizon: int,
    step: int = 1,
    embargo: int = 0,
) -> "list[OriginSplit]":
    """Forecast origins from ``min_train`` to ``n-1`` stepping ``step``.

    ``train_end = origin - horizon - embargo + 1`` (clipped at 0), which makes
    the last usable train origin ``s = train_end - 1`` satisfy
    ``s + horizon <= origin - embargo`` exactly.
    """
    splits: "list[OriginSplit]" = []
    for origin in range(min_train, n, step):
        train_end = max(origin - horizon - embargo + 1, 0)
        if train_end < MIN_TRAIN_EFFECTIVE:
            continue
        splits.append(OriginSplit(origin=origin, train_end=train_end))
    return splits

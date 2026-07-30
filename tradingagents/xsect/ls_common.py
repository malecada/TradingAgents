"""Signal-agnostic dollar-neutral L/S weights, weekly-held.

Generalises the algorithm in ``carry_xs.carry_weights`` (which hardcodes a
funding-validity mask and recomputes daily) so value and unlock signals can
share it. ``carry_xs`` is deliberately NOT refactored onto this: its results
are published (THESIS section 46) and must stay byte-reproducible.

Tie-break and sort logic follow carry_xs exactly: two independent sorts,
short leg first (descending signal, then ascending symbol), long leg excluding
short-leg members (ascending signal, then ascending symbol). This avoids the
single-sort pitfall where desc-sort tails give (asc signal, desc symbol),
diverging from the frozen behavior.

Normalization differs from carry_xs: here each leg divides by its realized
count (to preserve dollar-neutral row sums even if legs differ in size), vs.
carry_xs's shared n_leg divisor. This is necessary for the weight builder to
remain signal-agnostic — different signals can produce imbalanced valid counts,
requiring per-leg normalization to keep Sum(w) = 0 without explicit tuning.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

MIN_VALID = 5   # fewer valid names than this on a rebalance date => flat


def ls_weights(all_days: pd.DatetimeIndex, S: pd.DataFrame, valid: pd.DataFrame,
               rebalance_dates: pd.DatetimeIndex, leg_frac: float) -> pd.DataFrame:
    """Dollar-neutral L/S weights, recomputed only on ``rebalance_dates``.

    Short the top ``leg_frac`` by signal, long the bottom ``leg_frac``.
    Weights are held constant until the next rebalance date. Rows sum to 0.

    At exactly leg_frac=0.5, banker's rounding can cause legs to become
    imbalanced (short leg larger than long leg) when valid-name count is
    n ≡ 3 (mod 4). The bound is therefore strict: leg_frac ∈ (0, 0.5).
    """
    if not 0.0 < leg_frac < 0.5:
        raise ValueError("leg_frac must be in (0, 0.5)")
    W = pd.DataFrame(0.0, index=all_days, columns=S.columns)
    days_set = set(all_days)
    rbs = [d for d in rebalance_dates if d in days_set]
    for i, t in enumerate(rbs):
        v = valid.loc[t] & S.loc[t].notna()
        names = list(v.index[v])
        hi = rbs[i + 1] if i + 1 < len(rbs) else None
        if len(names) < MIN_VALID:
            continue
        n_leg = max(1, int(round(leg_frac * len(names))))
        shorts = sorted(names, key=lambda s: (-S.loc[t, s], s))[:n_leg]
        shorts_set = set(shorts)
        longs = [s for s in sorted(names, key=lambda s: (S.loc[t, s], s))
                 if s not in shorts_set][:n_leg]
        if not longs:
            continue
        seg = W.loc[t:] if hi is None else W.loc[t:hi - pd.Timedelta(days=1)]
        W.loc[seg.index, shorts] = -0.5 / len(shorts)
        W.loc[seg.index, longs] = +0.5 / len(longs)
    return W


def sharpe_365(x: pd.Series) -> float:
    """sqrt(365)-annualized Sharpe, ddof=1. Zero variance or n<2 -> 0.0."""
    x = pd.Series(x).dropna()
    if len(x) < 2:
        return 0.0
    sd = float(x.std(ddof=1))
    if not np.isfinite(sd) or sd == 0.0:
        return 0.0
    return float(x.mean() / sd * np.sqrt(365))


def zero_funding(index: pd.DatetimeIndex, columns) -> pd.DataFrame:
    """All-zero funding frame for run_ls_portfolio's ``F`` argument."""
    return pd.DataFrame(0.0, index=index, columns=list(columns))

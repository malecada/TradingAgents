"""Mean-of-series inference: Newey-West t-stat and stationary bootstrap.

The bootstrap is Politis-Romano (1994) with geometric block lengths and
wrap-around indexing — same scheme the house uses for SR bootstraps, but
implemented locally (predlab does not import across experiment namespaces).
"""

from __future__ import annotations

import numpy as np

_MIN_OBS = 8


def nw_tstat(x: np.ndarray, lag: int) -> float:
    """t-stat of mean(x) = 0 with Bartlett-kernel long-run variance.

    lrv = g0 + 2 * sum_{k=1..lag} (1 - k/(lag+1)) * g_k with autocovariances
    g_k = sum(xc[k:] * xc[:-k]) / T (uncorrected, matching statsmodels HAC
    with use_correction=False). Returns nan if lrv <= 0 or the series is
    shorter than 8 observations.
    """
    x = np.asarray(x, dtype=np.float64)
    T = len(x)
    if T < _MIN_OBS:
        return float("nan")
    m = x.mean()
    xc = x - m
    lrv = float(np.sum(xc * xc)) / T
    for k in range(1, int(lag) + 1):
        w = 1.0 - k / (lag + 1.0)
        lrv += 2.0 * w * float(np.sum(xc[k:] * xc[:-k])) / T
    if lrv <= 0:
        return float("nan")
    return float(m / np.sqrt(lrv / T))


def stationary_bootstrap_means(
    x: np.ndarray,
    n_boot: int = 2000,
    mean_block: int = 21,
    seed: int = 0,
) -> np.ndarray:
    """Resampled means under the stationary bootstrap.

    Each resample walks the series with wrap-around: continue the current
    block with probability 1 - 1/mean_block, else restart at a uniform index.
    Vectorized across draws (one pass over T positions).
    """
    x = np.asarray(x, dtype=np.float64)
    T = len(x)
    rng = np.random.default_rng(seed)
    p = 1.0 / float(mean_block)
    idx = np.empty((n_boot, T), dtype=np.int64)
    idx[:, 0] = rng.integers(0, T, size=n_boot)
    for t in range(1, T):
        restart = rng.random(n_boot) < p
        nxt = (idx[:, t - 1] + 1) % T
        fresh = rng.integers(0, T, size=n_boot)
        idx[:, t] = np.where(restart, fresh, nxt)
    return x[idx].mean(axis=1)


def p_pos(
    x: np.ndarray,
    n_boot: int = 2000,
    mean_block: int = 21,
    seed: int = 0,
) -> float:
    """Share of stationary-bootstrap means > 0 (house p_pos convention)."""
    means = stationary_bootstrap_means(x, n_boot=n_boot, mean_block=mean_block, seed=seed)
    return float(np.mean(means > 0))

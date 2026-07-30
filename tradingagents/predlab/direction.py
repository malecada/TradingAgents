"""Directional-forecast inference: Pesaran-Timmermann test, base-rate metrics.

PT (1992) assumes serial independence of the sign series — it breaks under
serial correlation/overlapping horizons and is undefined for constant-sign
forecasts (RESEARCH.md §2). Batteries complement it with block-bootstrap
evidence on the hit series; direction gates always compare accuracy to the
CLASS BASE RATE (drift makes "always up" beat 50% on crypto), never to 0.5.
"""

from __future__ import annotations

import numpy as np
from scipy import stats as _st

from tradingagents.predlab import losses
from tradingagents.predlab.dm import TestResult

_DEGENERATE = TestResult(stat=float("nan"), pvalue=float("nan"), degenerate=True)


def _as_up(a: np.ndarray) -> np.ndarray:
    return np.asarray(a).astype(np.float64) > 0


def pt_test(y_sign: np.ndarray, x_sign: np.ndarray) -> TestResult:
    """Pesaran-Timmermann (1992) test of directional forecast skill.

    Accepts bool or +/- arrays; internally up = (value > 0). One-sided
    normal p-value. Degenerate (nan) when either series is constant-sign or
    the variance difference is non-positive.
    """
    y = _as_up(y_sign)
    x = _as_up(x_sign)
    n = len(y)
    if n < 10 or len(x) != n:
        return _DEGENERATE
    py = float(y.mean())
    px = float(x.mean())
    if px in (0.0, 1.0) or py in (0.0, 1.0):
        return _DEGENERATE
    phat = float((y == x).mean())
    pstar = py * px + (1.0 - py) * (1.0 - px)
    v_p = pstar * (1.0 - pstar) / n
    v_ps = (
        (2.0 * py - 1.0) ** 2 * px * (1.0 - px)
        + (2.0 * px - 1.0) ** 2 * py * (1.0 - py)
        + 4.0 * py * px * (1.0 - py) * (1.0 - px) / n
    ) / n
    if v_p - v_ps <= 0:
        return _DEGENERATE
    stat = (phat - pstar) / np.sqrt(v_p - v_ps)
    return TestResult(stat=float(stat), pvalue=float(_st.norm.sf(stat)))


def hit_rate_vs_base(y_sign: np.ndarray, x_sign: np.ndarray) -> dict:
    """Accuracy against the class base rate (the honest directional null)."""
    y = _as_up(y_sign)
    x = _as_up(x_sign)
    py = float(y.mean())
    acc = float((y == x).mean())
    base = max(py, 1.0 - py)
    return {"acc": acc, "base_rate": base, "edge_pp": (acc - base) * 100.0}


def brier_skill(p_up: np.ndarray, y_up: np.ndarray, p_clim: np.ndarray) -> float:
    """Brier skill score vs climatology: 1 - BS_model / BS_clim (positive = beats)."""
    bs_model = float(np.nanmean(losses.brier(p_up, _as_up(y_up).astype(np.float64))))
    bs_clim = float(np.nanmean(losses.brier(p_clim, _as_up(y_up).astype(np.float64))))
    if bs_clim == 0.0:
        return float("nan")
    return 1.0 - bs_model / bs_clim

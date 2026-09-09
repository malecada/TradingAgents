"""Forecast-comparison tests: Diebold-Mariano (HLN), Clark-West, Giacomini-White.

Sign convention everywhere: the loss differential is d = loss_base - loss_model,
so a POSITIVE statistic means the model beats the base.

- Default v2 uses Bartlett HAC with max(h-1, floor(4(T/100)^(2/9)))
  and asymptotic normal p-values. This permits dependence beyond horizon overlap.
  It is a prospective policy, not a retrospective change to registered gates.
- Explicit variance="legacy": DM (1995) + Harvey-Leybourne-Newbold (1997): rectangular autocovariance
  truncation at h-1, HLN small-sample factor, Student-t(T-1) p-values.
  Invalid for NESTED models (errors perfectly correlated under the null) —
  use clark_west for nested comparisons.
- Clark-West (2007): MSPE-adjusted statistic for nested models, one-sided
  normal p-value via a Newey-West t on the adjusted differential.
- Giacomini-White (2006), unconditional flavor: Newey-West t on d with
  two-sided normal p. Valid under rolling/finite-memory estimation schemes
  (our default walk-forward), tolerates nesting.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats as _st

from tradingagents.predlab import meanstats

_MIN_OBS = 10


@dataclass
class TestResult:
    stat: float
    pvalue: float
    degenerate: bool = False
    variance_policy: str = "hac-v2"
    hac_lag: int | None = None


_DEGENERATE = TestResult(stat=float("nan"), pvalue=float("nan"), degenerate=True)


def dm_test(
    loss_base: np.ndarray,
    loss_model: np.ndarray,
    h: int = 1,
    alternative: str = "greater",
    variance: str = "hac",
    hac_lag: int | None = None,
) -> TestResult:
    """DM test on per-observation losses; positive stat = model beats base.

    alternative="greater" tests H1: model better (one-sided);
    "two-sided" tests inequality either way.
    """
    d = np.asarray(loss_base, dtype=np.float64) - np.asarray(loss_model, dtype=np.float64)
    d = d[np.isfinite(d)]
    T = len(d)
    if T < _MIN_OBS or float(np.std(d)) == 0.0:
        return _DEGENERATE
    if h < 1 or h >= T or int(h) != h:
        raise ValueError("h must be a positive integer smaller than sample size")
    if variance not in {"hac", "legacy"}:
        raise ValueError("variance must be hac or legacy")
    if alternative not in {"greater", "two-sided"}:
        raise ValueError(f"unknown alternative: {alternative}")
    lag = _lag(T, h, hac_lag)
    if variance == "hac":
        stat = meanstats.nw_tstat(d, lag=lag)
        if not np.isfinite(stat):
            return _DEGENERATE
        p = _st.norm.sf(stat) if alternative == "greater" else 2 * _st.norm.sf(abs(stat))
        return TestResult(float(stat), float(p), hac_lag=lag)
    dbar = float(d.mean())
    dc = d - dbar
    lrv = float(np.sum(dc * dc)) / T
    gamma0 = lrv
    for k in range(1, int(h)):
        lrv += 2.0 * float(np.sum(dc[k:] * dc[:-k])) / T
    if lrv <= 0:
        lrv = gamma0
    dm_stat = dbar / np.sqrt(lrv / T)
    hln = np.sqrt((T + 1 - 2 * h + h * (h - 1) / T) / T)
    stat = float(dm_stat * hln)
    if alternative == "two-sided":
        p = float(2.0 * _st.t.sf(abs(stat), df=T - 1))
    elif alternative == "greater":
        p = float(_st.t.sf(stat, df=T - 1))
    else:
        raise ValueError(f"unknown alternative: {alternative}")
    return TestResult(stat=stat, pvalue=p, variance_policy="legacy-hln", hac_lag=h-1)


def clark_west(
    e_small: np.ndarray,
    e_big: np.ndarray,
    yhat_small: np.ndarray,
    yhat_big: np.ndarray,
    h: int = 1,
    hac_lag: int | None = None,
) -> TestResult:
    """Clark-West MSPE-adjusted test for nested models (small ⊂ big).

    f_t = e_small^2 - e_big^2 + (yhat_small - yhat_big)^2; one-sided normal
    p on the NW t-stat of mean(f) > 0 (big model genuinely better).
    """
    e_small = np.asarray(e_small, dtype=np.float64)
    e_big = np.asarray(e_big, dtype=np.float64)
    yhat_small = np.asarray(yhat_small, dtype=np.float64)
    yhat_big = np.asarray(yhat_big, dtype=np.float64)
    f = e_small**2 - e_big**2 + (yhat_small - yhat_big) ** 2
    f = f[np.isfinite(f)]
    if len(f) < _MIN_OBS or float(np.std(f)) == 0.0:
        return _DEGENERATE
    lag = _lag(len(f), h, hac_lag)
    stat = meanstats.nw_tstat(f, lag=lag)
    if np.isnan(stat):
        return _DEGENERATE
    return TestResult(stat=float(stat), pvalue=float(_st.norm.sf(stat)), hac_lag=lag)


def gw_test(loss_base: np.ndarray, loss_model: np.ndarray, h: int = 1,
            hac_lag: int | None = None) -> TestResult:
    """Unconditional Giacomini-White: NW t on d, two-sided normal p."""
    d = np.asarray(loss_base, dtype=np.float64) - np.asarray(loss_model, dtype=np.float64)
    d = d[np.isfinite(d)]
    if len(d) < _MIN_OBS or float(np.std(d)) == 0.0:
        return _DEGENERATE
    lag = _lag(len(d), h, hac_lag)
    stat = meanstats.nw_tstat(d, lag=lag)
    if np.isnan(stat):
        return _DEGENERATE
    return TestResult(stat=float(stat), pvalue=float(2.0 * _st.norm.sf(abs(stat))), hac_lag=lag)


def _lag(n: int, h: int, explicit: int | None) -> int:
    if h < 1 or int(h) != h or h >= n:
        raise ValueError("h must be a positive integer smaller than sample size")
    lag = max(h - 1, int(np.floor(4 * (n / 100) ** (2 / 9)))) if explicit is None else explicit
    if int(lag) != lag or lag < h - 1 or lag >= n:
        raise ValueError("HAC lag must cover overlap and be smaller than sample size")
    return int(lag)

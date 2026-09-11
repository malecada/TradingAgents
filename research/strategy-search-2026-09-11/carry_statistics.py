"""Frozen descriptive development uncertainty; never fresh confirmation."""
from __future__ import annotations

import numpy as np
from scipy.stats import norm
import statsmodels.api as sm


def paired_uncertainty(cash_changes):
    """Eight rows of daily cash changes / initial capital; paired block draws."""
    x = np.asarray(cash_changes, dtype=float)
    if x.shape != (8, 91) or not np.isfinite(x).all():
        raise ValueError("expected eight complete 91-day cash-change series")
    rng = np.random.default_rng(20260911)
    starts = rng.integers(0, 91, size=(2000, 13))
    indices = ((starts[:, :, None] + np.arange(7)) % 91).reshape(2000, 91)
    annual_means = x[:, indices].mean(axis=2) * 365
    lower, upper = np.quantile(annual_means, [0.003125, 0.996875], axis=1)
    se = annual_means.std(axis=1, ddof=1)
    return [{"annualized_point": float(x[i].mean() * 365),
             "annualized_lower": float(lower[i]), "annualized_upper": float(upper[i]),
             "bootstrap_standard_error": float(se[i]),
             "approximate_80pct_mde_annualized": float((norm.ppf(0.996875) + norm.ppf(.8)) * se[i]),
             "seed": 20260911, "draws": 2000, "block_days": 7,
             "observations": 91, "approximate_blocks": 13,
             "scope": "Spent development; finite-tail block/normal approximation of empirical daily mean, resampling endpoint fees/basis; not repeated trade paths or future-profit confirmation."}
            for i in range(8)]


def market_exposure(nav, capital, btc_returns, eth_returns):
    values = np.asarray(nav, dtype=float)
    btc, eth = np.asarray(btc_returns, dtype=float), np.asarray(eth_returns, dtype=float)
    if values.shape != (91,) or btc.shape != (91,) or eth.shape != (91,):
        raise ValueError("expected 91 paired observations")
    previous = np.r_[float(capital), values[:-1]]
    if not np.isfinite(np.r_[values, btc, eth, previous]).all() or np.any(previous <= 0) or np.any(values <= 0):
        return {"status": "unavailable", "reason": "invalid NAV/benchmark observation"}
    y = values / previous - 1
    design = np.column_stack((np.ones(91), btc, eth))
    if np.linalg.matrix_rank(design) != 3:
        return {"status": "unavailable", "reason": "singular BTC/ETH benchmark design"}
    result = sm.OLS(y, design).fit(cov_type="HAC", cov_kwds={"maxlags": 7}, use_t=True)
    intervals = np.asarray(result.conf_int(alpha=.025))
    if not np.isfinite(np.r_[result.params, intervals.ravel()]).all():
        return {"status": "unavailable", "reason": "undefined HAC statistics"}
    return {"status": "complete", "observations": 91, "intercept": float(result.params[0]),
            "btc_beta": float(result.params[1]), "eth_beta": float(result.params[2]),
            "btc_interval": intervals[1].tolist(), "eth_interval": intervals[2].tolist(),
            "hac_lags": 7, "individual_confidence": .975,
            "scope": "Descriptive spent development; within-book simultaneous95%, not across all searched books."}

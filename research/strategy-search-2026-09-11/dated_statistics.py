"""Exposure description for one fixed dated episode; no expected-profit inference."""
from __future__ import annotations

import numpy as np
import statsmodels.api as sm

DAYS = 56
START = 1777593600000
DAY = 86400000


def market_exposure(nav, capital, btc_returns, eth_returns):
    values = np.asarray(nav, dtype=float)
    btc, eth = np.asarray(btc_returns, dtype=float), np.asarray(eth_returns, dtype=float)
    if values.shape != (DAYS,) or btc.shape != (DAYS,) or eth.shape != (DAYS,):
        return {"status": "unavailable", "reason": "expected exactly 56 paired observations"}
    previous = np.r_[float(capital), values[:-1]]
    if not np.isfinite(np.r_[values, previous, btc, eth]).all() or np.any(previous <= 0) or np.any(values <= 0):
        return {"status": "unavailable", "reason": "invalid or nonpositive NAV/benchmark"}
    design = np.column_stack((np.ones(DAYS), btc, eth))
    if np.linalg.matrix_rank(design) != 3:
        return {"status": "unavailable", "reason": "singular BTC/ETH design"}
    result = sm.OLS(values / previous - 1, design).fit(cov_type="HAC", cov_kwds={"maxlags": 7}, use_t=True)
    intervals = np.asarray(result.conf_int(alpha=.025))
    if not np.isfinite(np.r_[result.params, intervals.ravel()]).all():
        return {"status": "unavailable", "reason": "undefined HAC statistics"}
    return {"status": "complete", "observations": DAYS, "intercept": float(result.params[0]),
            "btc_beta": float(result.params[1]), "eth_beta": float(result.params[2]),
            "btc_interval": intervals[1].tolist(), "eth_interval": intervals[2].tolist(),
            "hac_lags": 7, "individual_confidence": .975,
            "scope": "Trade-close proxy exposure on spent development; within-book 95% Bonferroni intervals only, not all-search coverage or confirmation."}


def _stamp(value):
    if type(value) is int:
        return value
    if isinstance(value, str) and len(value) == 13 and value.isascii() and value.isdigit():
        return int(value)
    raise ValueError("integer millisecond benchmark clock required")


def spot_returns(rows):
    if len(rows) != DAYS:
        raise ValueError("56 paired spot days required")
    for i, row in enumerate(rows):
        if len(row) != 12 or _stamp(row[0]) != START + i * DAY or _stamp(row[6]) != START + (i + 1) * DAY - 1:
            raise ValueError("spot calendar is not the fixed UTC episode")
    closes = np.asarray([float(row[4]) for row in rows])
    previous = np.r_[float(rows[0][1]), closes[:-1]]
    if not np.isfinite(np.r_[closes, previous]).all() or np.any(closes <= 0) or np.any(previous <= 0):
        raise ValueError("invalid spot benchmark price")
    return closes / previous - 1


def exposure_statistics(books, spot_by_asset):
    output = {}
    try:
        btc, eth = (spot_returns(spot_by_asset[asset]) for asset in ("BTC", "ETH"))
        error = None
    except (KeyError, ValueError, TypeError, IndexError, OverflowError) as exc:
        error = str(exc)
    for identity, book in books.items():
        if error is not None:
            exposure = {"status": "unavailable", "reason": "benchmark admission: " + error}
        elif book.get("status") == "unavailable":
            exposure = {"status": "unavailable", "reason": book.get("reason", "book unavailable")}
        else:
            try:
                exposure = market_exposure([row["nav"] for row in book["daily_trace"]], book["capital"], btc, eth)
            except (KeyError, ValueError, TypeError, IndexError, OverflowError, np.linalg.LinAlgError) as exc:
                exposure = {"status": "unavailable", "reason": "invalid book exposure: " + str(exc)}
        output[identity] = {"status": exposure["status"], "market_exposure": exposure,
                           "expected_return_confidence": {"status": "unavailable", "reason": "One historical convergence episode per asset; daily observations are not repeated trades."},
                           "power": {"status": "unavailable", "reason": "No independent repeated-episode sample or expected-profit test in this design."}}
    return output

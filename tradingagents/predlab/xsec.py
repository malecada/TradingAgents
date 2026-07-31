"""Cross-sectional IC engine for T7 cells.

Convention: signal frame is PRE-ALIGNED — signal.loc[d] must be computable
from information available before period d's outcome y.loc[d] (the caller
lags features; the engine only scores). Daily Spearman IC + Newey-West t on
the IC series (the registered T7 test).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from tradingagents.predlab.meanstats import nw_tstat


def daily_ic(signal: pd.DataFrame, y: pd.DataFrame,
             min_breadth: int = 5) -> pd.Series:
    """Per-day Spearman rank correlation between signal and outcome.

    Frames are (days x symbols), aligned on both axes; days with fewer than
    ``min_breadth`` joint non-nan names are nan.
    """
    signal, y = signal.align(y, join="inner")
    out = pd.Series(np.nan, index=signal.index)
    sig_rank = signal.rank(axis=1)
    y_rank = y.rank(axis=1)
    for d in signal.index:
        s, r = sig_rank.loc[d], y_rank.loc[d]
        ok = s.notna() & r.notna()
        if int(ok.sum()) < min_breadth:
            continue
        sv, rv = s[ok].to_numpy(), r[ok].to_numpy()
        sv = (sv - sv.mean()) / (sv.std() or 1.0)
        rv = (rv - rv.mean()) / (rv.std() or 1.0)
        out.loc[d] = float(np.mean(sv * rv))
    return out


def ic_summary(ics: pd.Series, nw_lag: int = 5) -> dict:
    x = ics.dropna().to_numpy()
    return {
        "n_days": int(len(x)),
        "mean_ic": float(np.mean(x)) if len(x) else float("nan"),
        "ic_std": float(np.std(x, ddof=1)) if len(x) > 1 else float("nan"),
        "nw_t": float(nw_tstat(x, lag=nw_lag)) if len(x) > 20 else float("nan"),
        "share_positive": float(np.mean(x > 0)) if len(x) else float("nan"),
    }

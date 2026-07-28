"""Cross-sectional funding-carry L/S — frozen mechanics per gates.json carry_xs_t1.

Spec: docs/superpowers/specs/2026-07-28-carry-xs-design.md. Daily funding = SUM
of the UTC day's prints (carry_sleeve lesson: mean undercounts 3x). Decision at
close t applies to bar t+1; costs 10 bps/side on |dW|; rf on full capital.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

RF_DAILY = 1.045 ** (1 / 365) - 1  # house convention, data/rebuild/carry_audit/costs.json
MIN_FUND_DAYS = 30                  # gapless trailing funding days required to trade
MIN_VALID = 5                       # fewer valid symbols than this => flat that day


def funding_daily(prints: pd.DataFrame) -> pd.Series:
    daily = prints["fundingRate"].groupby(prints.index.normalize()).sum()
    full = pd.date_range(daily.index[0], daily.index[-1], freq="D", tz="UTC")
    return daily.reindex(full)  # missing day inside span -> NaN (data gap)


def build_funding_matrix(funding: dict, all_days: pd.DatetimeIndex,
                         symbols: list) -> pd.DataFrame:
    F = pd.DataFrame(index=all_days, columns=symbols, dtype=float)
    for s in symbols:
        if s in funding and len(funding[s]):
            F[s] = funding_daily(funding[s]).reindex(all_days)
    return F


def carry_signal(F: pd.DataFrame, L: int) -> pd.DataFrame:
    return F.rolling(L, min_periods=L).mean()

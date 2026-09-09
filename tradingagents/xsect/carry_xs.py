"""Cross-sectional funding-carry L/S — frozen mechanics per gates.json carry_xs_t1.

Spec: docs/superpowers/specs/2026-07-28-carry-xs-design.md. Daily funding = SUM
of the UTC day's prints (carry_sleeve lesson: mean undercounts 3x). Decision at
close t applies to bar t+1; costs 10 bps/side on |dW|; rf on full capital.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from tradingagents.xsect.trend import _membership_mask  # shared frozen semantics

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


def carry_weights(all_days, S: pd.DataFrame, F: pd.DataFrame,
                  members_by_refresh: dict, leg_frac: float) -> pd.DataFrame:
    member = _membership_mask(all_days, S.columns, members_by_refresh)
    fund_ok = F.notna().rolling(MIN_FUND_DAYS, min_periods=MIN_FUND_DAYS).sum() \
        .eq(MIN_FUND_DAYS)
    valid = member & S.notna() & fund_ok
    W = pd.DataFrame(0.0, index=all_days, columns=S.columns)
    for t in all_days:
        v = valid.loc[t]
        names = v.index[v]
        n_valid = len(names)
        if n_valid < MIN_VALID:
            continue
        n_leg = max(1, int(round(leg_frac * n_valid)))
        # SHORT: top n_leg by (signal desc, symbol asc); LONG: bottom n_leg by
        # (signal asc, symbol asc) EXCLUDING short-leg members. Two independent
        # sorts — a single desc sort's tail gives (signal asc, symbol DESC) at
        # tie boundaries, which diverges from the frozen ascending tie-break for
        # the long leg. Under heavily tied signals (common in real funding data,
        # e.g. Binance default 1e-4/8h print -> identical trailing means across
        # many symbols) the desc and asc sorts can pick overlapping symbols —
        # in the degenerate all-tied case both sorts collapse to symbol-asc and
        # the legs would be identical, so the long leg must explicitly exclude
        # short-leg members to keep the legs disjoint (Sigma w = 0 sanity holds).
        shorts = sorted(names, key=lambda s: (-S.loc[t, s], s))[:n_leg]
        shorts_set = set(shorts)
        longs = [s for s in sorted(names, key=lambda s: (S.loc[t, s], s))
                if s not in shorts_set][:n_leg]
        W.loc[t, shorts] = -0.5 / n_leg
        W.loc[t, longs] = +0.5 / n_leg
    return W


def run_ls_portfolio(W: pd.DataFrame, R: pd.DataFrame, F: pd.DataFrame,
                     cost_bps: float = 10.0,
                     rf_daily: float = RF_DAILY) -> pd.Series:
    for X in (R, F):
        if not W.index.equals(X.index) or list(W.columns) != list(X.columns):
            raise ValueError("W, R, F must share identical index and columns")
    Wv = W.to_numpy()
    Rv = np.nan_to_num(R.to_numpy(), nan=0.0)
    Fv = np.nan_to_num(F.to_numpy(), nan=0.0)
    Wprev = np.vstack([np.zeros((1, Wv.shape[1])), Wv[:-1]])
    Wprev2 = np.vstack([np.zeros((2, Wv.shape[1])), Wv[:-2]])
    price = (Wprev * Rv).sum(axis=1)
    funding = (Wprev * Fv).sum(axis=1)          # long pays (+F drains), short receives
    cost = cost_bps / 1e4 * np.abs(Wprev - Wprev2).sum(axis=1)
    port = pd.Series(price - funding - cost - rf_daily, index=W.index)
    return port.iloc[1:]

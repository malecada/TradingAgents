"""Wide-universe long-flat trend engine — frozen mechanics per gates.json trend_wide_t1.

Spec: docs/superpowers/specs/2026-07-28-trend-wide-design.md. Decision at close t
applies to bar t+1; costs 10 bps/side on |Δw| charged on the first accrual day.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from tradingagents.xsect.trend_signal import compute_votes

ANN = 365.0
VOL_WINDOW = 30


def monthly_refresh_dates(start: str, end: str) -> pd.DatetimeIndex:
    """First Monday of each calendar month in [start, end], tz='UTC'.

    Note: groupby-min over a tz-aware Series yields tz-aware Timestamp values, but
    `.values` on such a Series strips the tz (numpy datetime64 has no tz concept),
    silently downgrading the result to naive. Sorting/wrapping the Series itself
    (not `.values`) preserves tz-aware scalars end to end.
    """
    days = pd.date_range(start, end, freq="D", tz="UTC")
    mondays = days[days.dayofweek == 0]
    first = mondays.to_series().groupby([mondays.year, mondays.month]).min()
    return pd.DatetimeIndex(sorted(first))


def build_matrices(klines: dict, symbols: list, with_simple: bool = False) -> tuple:
    """(all_days, R, VOTES, SIGMA[, R_simple]). All frames days x symbols, NaN where undefined.

    R is the LOG return matrix — it feeds SIGMA and VOTES (signal side) and is
    the only thing the pre-fix engine consumed. Lead-0 fix (2026-09-02): the
    PnL step must consume ``R_simple = expm1(R)``; pass ``with_simple=True`` to
    get it as a fifth element (the 4-tuple signature is kept for the signal
    path and existing callers).

    VOTES: computed on each symbol's own bars (native index), then reindexed to
    all_days WITHOUT filling — a day with no kline has NaN vote (=> weight 0).
    SIGMA: rolling(30, min_periods=30).std() of R on the full daily calendar,
    so any missing day inside the window yields NaN (gapless house convention).
    """
    all_days = pd.DatetimeIndex(sorted(set().union(*[klines[s].index for s in symbols])))
    R = pd.DataFrame(index=all_days, columns=symbols, dtype=float)
    VOTES = pd.DataFrame(index=all_days, columns=symbols, dtype=float)
    for s in symbols:
        close = klines[s]["close"]
        R[s] = np.log(close).diff().reindex(all_days)
        VOTES[s] = compute_votes(close).reindex(all_days)
    SIGMA = R.rolling(VOL_WINDOW, min_periods=VOL_WINDOW).std()
    if with_simple:
        return all_days, R, VOTES, SIGMA, np.expm1(R)
    return all_days, R, VOTES, SIGMA


def _membership_mask(all_days, columns, members_by_refresh) -> pd.DataFrame:
    mask = pd.DataFrame(False, index=all_days, columns=columns)
    dates = sorted(members_by_refresh)
    for i, d in enumerate(dates):
        end = dates[i + 1] if i + 1 < len(dates) else None
        rows = (all_days >= d) & ((all_days < end) if end is not None else True)
        cols = [s for s in members_by_refresh[d] if s in mask.columns]
        mask.loc[rows, cols] = True
    return mask


def trend_weights(all_days, R, VOTES, SIGMA, members_by_refresh, n_slots: int,
                  vol_target: float) -> pd.DataFrame:
    member = _membership_mask(all_days, R.columns, members_by_refresh)
    scale = (vol_target / (SIGMA * np.sqrt(ANN))).clip(upper=1.0)
    W = (1.0 / n_slots) * scale.where(np.isfinite(scale), 0.0)
    W = W.where((VOTES > 0.5) & member, 0.0)
    return W.fillna(0.0)  # defensive no-op: prior .where() already zeros all False/NaN conditions


def ew_benchmark_weights(all_days, R, members_by_refresh, n_slots: int) -> pd.DataFrame:
    member = _membership_mask(all_days, R.columns, members_by_refresh)
    return member.astype(float) / n_slots


def run_daily_portfolio(W: pd.DataFrame, R: pd.DataFrame, cost_bps: float = 10.0) -> pd.Series:
    if not W.index.equals(R.index) or list(W.columns) != list(R.columns):
        raise ValueError("W and R must share identical index and columns")
    Wv = W.to_numpy()
    Rv = np.nan_to_num(R.to_numpy(), nan=0.0)
    Wprev = np.vstack([np.zeros((1, Wv.shape[1])), Wv[:-1]])       # W[t-1]
    Wprev2 = np.vstack([np.zeros((2, Wv.shape[1])), Wv[:-2]])      # W[t-2]
    gross = (Wprev * Rv).sum(axis=1)
    cost = cost_bps / 1e4 * np.abs(Wprev - Wprev2).sum(axis=1)
    port = pd.Series(gross - cost, index=W.index)
    return port.iloc[1:]


def circular_shift_weights(W: pd.DataFrame, rng: np.random.Generator,
                            min_shift: int = 30) -> pd.DataFrame:
    """Per-column random circular roll — preserves each coin's weight
    autocorrelation and vol-scaling structure, destroys alignment with the
    market path. Costs are re-applied downstream by run_daily_portfolio."""
    n = len(W)
    out = {}
    for col in W.columns:
        k = int(rng.integers(min_shift, n - min_shift))
        out[col] = np.roll(W[col].to_numpy(), k)
    return pd.DataFrame(out, index=W.index, columns=W.columns)


def shared_shift_weights(W: pd.DataFrame, rng: np.random.Generator,
                          min_shift: int = 30) -> pd.DataFrame:
    """Single shared circular roll for ALL columns — preserves cross-coin
    co-activation (regime clustering) while destroying calendar alignment.
    Second placebo family per amended spec (gate = worse of both p's)."""
    n = len(W)
    k = int(rng.integers(min_shift, n - min_shift))
    return pd.DataFrame(np.roll(W.to_numpy(), k, axis=0), index=W.index,
                        columns=W.columns)


def placebo_srs(W: pd.DataFrame, R: pd.DataFrame, n_placebo: int,
                 cost_bps: float = 10.0) -> list:
    from tradingagents.xsect.portfolio import sr as _sr
    out = []
    for p in range(n_placebo):
        rng = np.random.default_rng(seed=p)  # reproducible per placebo index
        shifted = circular_shift_weights(W, rng)
        out.append(_sr(run_daily_portfolio(shifted, R, cost_bps=cost_bps)))
    return out

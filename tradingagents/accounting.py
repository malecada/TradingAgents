"""Executable linear-position accounting (September 2026 correction).

Notionals represent signed units marked at the previous price. Targets are
fractions of pretrade NAV. Fees reduce cash once; contracts then mark with
simple returns. Keeping a target unchanged still requires drift maintenance.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

ACCOUNTING_VERSION = 'pretrade-nav-v1'


class MissingHeldReturn(ValueError):
    """A held contract cannot be valued; no settlement was invented."""


def _step_arrays(nav, old, r, target, f, fee_rate, date, columns, capital_charge):
    if not np.isfinite(nav) or nav <= 0:
        raise ValueError(f'nonpositive_nav at {date}: {nav}')
    if not np.isfinite(old).all():
        raise ValueError(f'nonfinite_notionals at {date}')
    desired = old.copy() if target is None else target*nav
    if not np.isfinite(desired).all():
        raise ValueError(f'nonfinite_target at {date}')
    held = desired != 0.
    bad = held & ~np.isfinite(r)
    if bad.any():
        raise MissingHeldReturn(f'missing_held_return at {date}: {", ".join(map(str,np.asarray(columns)[bad]))}')
    if (held & (r < -1.)).any():
        raise ValueError(f'invalid_simple_return at {date}')
    if not np.isfinite(f[held]).all():
        raise ValueError(f'missing_held_funding at {date}: {", ".join(map(str,np.asarray(columns)[held & ~np.isfinite(f)]))}')
    turnover_dollars = float(np.abs(desired-old).sum())
    fee = fee_rate*turnover_dollars
    postfee_nav = nav-fee
    if postfee_nav <= 0:
        raise ValueError(f'nonpositive_postfee_nav at {date}')
    moves = np.where(held,r,0.)
    pnl = desired*moves
    carry_dollars = float(-(desired*np.where(held,f,0.)).sum())
    gross_dollars = float(pnl.sum())
    final_nav = nav+gross_dollars+carry_dollars-fee-nav*capital_charge
    if not np.isfinite(final_nav) or final_nav <= 0:
        raise ValueError(f'nonpositive_nav at {date}: {final_nav}')
    return {'nav':final_nav, 'notionals':desired*(1.+moves),
            'weights':desired/nav, 'postfee_weights':desired/postfee_nav,
            'gross':gross_dollars/nav, 'carry':carry_dollars/nav,
            'cost':fee/nav, 'turnover':turnover_dollars/nav,
            'net':(final_nav-nav)/nav, 'name_pnl':pnl/nav}


def accounting_step(nav: float, notionals: pd.Series, returns: pd.Series, *,
                    target_weights: pd.Series | None = None,
                    funding: pd.Series | None = None, fee_rate: float = 0.0,
                    date=None, capital_charge: float = 0.0) -> dict:
    """Trade at the opening mark, charge fees, then mark unchanged units.

    ``None`` retains contracts; an explicit zero/empty target closes them.
    PnL/cost/turnover use pretrade NAV. ``postfee_weights`` exposes fee-induced
    exposure. Only funding=None denotes the explicit zero-funding assumption;
    supplied missing funding on held positions raises an error.
    """
    columns = notionals.index.union(target_weights.index) if target_weights is not None else notionals.index
    old = notionals.reindex(columns,fill_value=0.).to_numpy(dtype=float)
    target = None if target_weights is None else target_weights.reindex(columns,fill_value=0.).to_numpy(dtype=float)
    r = returns.reindex(columns).to_numpy(dtype=float)
    f = np.zeros(len(columns)) if funding is None else funding.reindex(columns).to_numpy(dtype=float)
    row = _step_arrays(nav,old,r,target,f,fee_rate,date,columns,capital_charge)
    for key in ('notionals','weights','postfee_weights','name_pnl'):
        row[key] = pd.Series(row[key],index=columns)
        row[key] = row[key][row[key] != 0.]
    return row


def calendar_index(index: pd.DatetimeIndex, freq: str = 'D') -> pd.DatetimeIndex:
    """Preserve every period inside a supplied calendar span."""
    if not index.is_unique or not index.is_monotonic_increasing:
        raise ValueError('accounting clock must be sorted and unique')
    if len(index) == 0:
        return index
    return pd.date_range(index[0],index[-1],freq=freq)


@dataclass(eq=False)
class BookInputs:
    """Executable in-memory inputs; archival outputs omit these large panels."""
    weights: pd.DataFrame
    returns: pd.DataFrame
    funding: pd.DataFrame | None
    name_pnl: pd.Series
    targets: pd.DataFrame
    fee_rate: float
    capital_charge: float
    daily_capital_charge: float


def archive_returns(frame: pd.DataFrame | pd.Series):
    """Return a serializable artifact with light accounting/status metadata.

    Executable per-name inputs remain in the source frame for current-process
    overlay/cost replay. Archival returns are summaries, not replay inputs.
    """
    out = frame.copy(deep=False)
    out.attrs = {key:value for key,value in frame.attrs.items() if key != 'accounting_inputs'}
    return out


def run_target_book(targets: pd.DataFrame, returns: pd.DataFrame, *,
                    funding: pd.DataFrame | None = None, fee_rate: float = 0.,
                    capital_charge: float = 0.,
                    daily_capital_charge: float = 0.) -> pd.DataFrame:
    """Apply same-row targets; an all-NaN target row retains held units.

    ``capital_charge`` is a per-bar full-NAV charge. ``daily_capital_charge``
    is charged at the final bar of each date against that date's opening NAV,
    including partial dates. Both reduce the book before subsequent trading.
    """
    columns = returns.columns.union(targets.columns, sort=False)
    returns = returns.reindex(columns=columns)
    targets = targets.reindex(index=returns.index,columns=columns)
    R = returns.to_numpy(dtype=float)
    T = targets.to_numpy(dtype=float)
    F = np.zeros_like(R) if funding is None else funding.reindex(index=returns.index,columns=columns).to_numpy(dtype=float)
    nav = 1.
    notionals = np.zeros(len(columns))
    fields = ['gross','net','turnover','cost','carry','nav']
    rows = np.empty((len(returns),len(fields)))
    weights = np.empty_like(R)
    names = np.zeros(len(columns))
    day_start_nav = nav
    dates = returns.index.normalize()
    for i,d in enumerate(returns.index):
        target = None if np.isnan(T[i]).all() else np.nan_to_num(T[i],nan=0.,posinf=np.inf,neginf=-np.inf)
        if i == 0 or dates[i] != dates[i-1]:
            day_start_nav = nav
        charge = capital_charge
        if i+1 == len(returns) or dates[i+1] != dates[i]:
            charge += daily_capital_charge*day_start_nav/nav
        row = _step_arrays(nav,notionals,R[i],target,F[i],fee_rate,d,columns,charge)
        nav, notionals = row['nav'],row['notionals']
        weights[i] = row['weights']
        names += row['name_pnl']
        rows[i] = [row[k] for k in fields]
    df = pd.DataFrame(rows,index=returns.index,columns=fields)
    df.attrs['accounting_version'] = ACCOUNTING_VERSION
    df.attrs['accounting_inputs'] = BookInputs(
        pd.DataFrame(weights,index=returns.index,columns=columns), returns, funding,
        pd.Series(names,index=columns), targets, fee_rate, capital_charge, daily_capital_charge)
    return df


def scaled_overlay(base: pd.DataFrame, scale: pd.Series, *, fee_rate: float,
                   gross_exposure: float = 2.) -> pd.Series:
    """Execute a scaled book when per-name inputs are retained.

    Archived summary-only inputs support only the duplicate-fee correction;
    that result is explicitly labelled approximate, not executable evidence.
    """
    s = scale.reindex(base.index)
    if not np.isfinite(s).all():
        raise ValueError('unavailable_overlay_scale')
    inputs = base.attrs.get('accounting_inputs')
    if inputs is not None:
        result = run_target_book(inputs.weights.mul(s,axis=0), inputs.returns,
                                 funding=inputs.funding, fee_rate=fee_rate,
                                 capital_charge=inputs.capital_charge,
                                 daily_capital_charge=inputs.daily_capital_charge).net
        result.attrs['overlay_status'] = 'executable'
        return result
    # Base net already contains its fees. Only extra scale turnover remains;
    # aggregate summaries cannot reconstruct cancellation or contract drift.
    cost = fee_rate*s.diff().abs().fillna(s.abs())*gross_exposure
    result = s*base['net'] - cost
    result.attrs['overlay_status'] = 'approximate_summary_only'
    return result

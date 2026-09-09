"""Weekly EW long-only cross-sectional portfolio engine — frozen mechanics per gates.json xs_mom_p1."""
import numpy as np
import pandas as pd

from tradingagents.accounting import calendar_index, run_target_book

from tradingagents.predlab.pp import max_drawdown as maxdd  # initial-capital simple NAV
from tradingagents.stress.overlay import _sr as sr  # sqrt(365), 0.0 on zero variance


def momentum_scores(klines: dict, symbols: list, date: pd.Timestamp,
                     L: int, skip: int) -> dict:
    """Sum of daily log-returns dated within the CALENDAR window
    (date-skip-L, date-skip], i.e. return-dates in [date-skip-L+1, date-skip].
    Requires all L calendar days present (gapless) to score a symbol; any gap
    or insufficient history drops the symbol that week (conservative, frozen)."""
    out = {}
    hi = date - pd.Timedelta(days=skip)
    lo = date - pd.Timedelta(days=skip + L - 1)
    for s in symbols:
        close = klines[s]["close"].loc[:date]
        if (lo - pd.Timedelta(days=1)) not in close.index:
            continue  # anchor close missing -> first window return would fuse days
        lr = np.log(close).diff()
        window = lr.loc[lo:hi].dropna()
        if len(window) == L:
            out[s] = float(window.sum())
    return out


def returns_from_close(close: pd.Series, convention: str) -> pd.Series:
    """Per-bar return series used at the PnL step.

    ``"simple"`` (house convention since the 2026-09-02 lead-0 fix): close-to-
    close simple returns, expm1(dlog). ``"log"`` reproduces the pre-fix booking
    (sum of w*dlog), retained ONLY for the convention-swap kill-test.
    """
    dlog = np.log(close).diff()
    if convention == "simple":
        return np.expm1(dlog)
    if convention == "log":
        return dlog
    raise ValueError(f"unknown return convention {convention!r}")


def run_weekly_portfolio(klines: dict, rebalance_dates: pd.DatetimeIndex,
                          select_fn, cost_bps: float = 10.0,
                          convention: str = "simple") -> pd.Series:
    """Fixed contracts between weekly rebalances, with decisions at close t.

    Targets apply on t+1; pretrade NAV sizes contracts, actual drifted notional
    changes incur fees once. A missing held mark raises an explicit error.
    An empty member list is an explicit close instruction. The log convention
    is retained solely as a non-executable convention-swap diagnostic.
    """
    arrays = build_fast_arrays(klines, convention=convention)
    members = {d: select_fn(d) for d in rebalance_dates}
    return fast_weekly_portfolio(members, rebalance_dates, *arrays, cost_bps=cost_bps)


def _stationary_indices(n: int, block: int, rng) -> np.ndarray:
    idx = np.empty(n, dtype=int)
    i = 0
    while i < n:
        length = min(rng.geometric(1.0 / block), n - i)
        start = rng.integers(0, n)
        idx[i:i + length] = (start + np.arange(length)) % n
        i += length
    return idx


def paired_bootstrap(a: pd.Series, b: pd.Series, block: int = 21,
                      n: int = 2000, seed: int = 0) -> dict:
    """Aligned inner-join; delta_sr = sr(a) - sr(b); p_pos = fraction of resamples
    with delta > 0, via stationary block bootstrap resampling the same index
    positions for both series."""
    j = pd.concat([a, b], axis=1, join="inner").dropna()
    av, bv = j.iloc[:, 0].to_numpy(), j.iloc[:, 1].to_numpy()
    rng = np.random.default_rng(seed)
    deltas = np.empty(n)
    for k in range(n):
        ix = _stationary_indices(len(av), block, rng)
        deltas[k] = _np_sr(av[ix]) - _np_sr(bv[ix])
    return {"delta_sr": sr(j.iloc[:, 0]) - sr(j.iloc[:, 1]),
            "p_pos": float((deltas > 0).mean())}


def _np_sr(x: np.ndarray) -> float:
    sd = x.std()
    return 0.0 if sd == 0 or np.isnan(sd) else float(x.mean() / sd * np.sqrt(365))


def rank_placebo_pvalue(real_sr: float, placebo_srs: list) -> float:
    """(1 + #{placebo >= real}) / (N + 1)."""
    ge = sum(1 for p in placebo_srs if p >= real_sr)
    return (1 + ge) / (len(placebo_srs) + 1)


# ── vectorised weekly EW engine (moved from scripts/xs_mom_dev.py, lead-0 fix) ──

def build_fast_arrays(klines: dict, convention: str = "simple"):
    """(all_days, day_pos, R, sym_idx) for :func:`fast_weekly_portfolio`.

    R is days x symbols, NaN where a symbol has no kline. ``convention`` picks
    the PnL return series (see :func:`returns_from_close`).
    """
    all_days = calendar_index(pd.DatetimeIndex(sorted(set().union(*[df.index for df in klines.values()]))))
    day_pos = {d: i for i, d in enumerate(all_days)}
    sym_list = sorted(klines)
    sym_idx = {s: j for j, s in enumerate(sym_list)}
    R = np.full((len(all_days), len(sym_list)), np.nan)
    for s, j in sym_idx.items():
        R[:, j] = returns_from_close(klines[s]["close"].reindex(all_days), convention).to_numpy()
    return all_days, day_pos, R, sym_idx


def fast_weekly_portfolio(members_by_t: dict, reb_dates, all_days, day_pos, R, sym_idx,
                          cost_bps: float = 10.0) -> pd.Series:
    """Array-input twin of the fixed-contract weekly engine."""
    if len(all_days) == 0:
        return pd.Series(dtype=float, index=all_days)
    columns = sorted(sym_idx, key=sym_idx.get)
    clock = calendar_index(all_days)
    returns = pd.DataFrame(R,index=all_days,columns=columns).reindex(clock)
    targets = pd.DataFrame(np.nan,index=clock,columns=columns)
    for d in reb_dates:
        next_day = d + pd.Timedelta(days=1)
        if next_day not in clock:
            continue
        members = members_by_t.get(d, [])
        unknown = set(members) - set(columns)
        if unknown:
            raise ValueError(f'unknown_target_symbols at {d}: {sorted(unknown)}')
        targets.loc[next_day] = 0.
        if members:
            targets.loc[next_day,members] = 1./len(members)
    start = reb_dates[0] if len(reb_dates) else all_days[0]
    result = run_target_book(targets,returns,fee_rate=cost_bps/1e4)
    return result.net.loc[result.index > start]

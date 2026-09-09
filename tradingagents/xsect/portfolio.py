"""Weekly EW long-only cross-sectional portfolio engine — frozen mechanics per gates.json xs_mom_p1."""
import numpy as np
import pandas as pd

from tradingagents.stress.overlay import _maxdd as maxdd  # positive magnitude
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
    """Daily net-return series for a weekly-rebalanced EW long-only portfolio.

    Mechanics: at each rebalance date t (Monday, using close t), target = EW over
    select_fn(t) (list of symbols); positions apply from bar t+1 (no look-ahead —
    the decision bar itself never accrues the return that produced the signal).
    Daily portfolio return = weight-anchored sum: Sum_s weights[s] * r_s over
    members whose return exists that day (a member missing a kline that day
    contributes 0 — its weight is NOT redistributed to survivors intra-week;
    weights only change at the next rebalance).
    Costs: cost = cost_bps/1e4 * Sum|w_new - w_old| (one-side rate times summed
    one-side turnover across both legs of each trade), deducted on the first
    accrual day after each rebalance (even if the book is empty/flat that day).

    ``convention``: r_s is the SIMPLE close-to-close return by default (lead-0
    fix, 2026-09-02; the July xsect cycles booked Sum w*dlog, which drops
    half-sigma-squared per day on long books — AUDIT_RESEARCH_PROGRAM_2026-09-02
    section 2). ``"log"`` reproduces the registered July numbers for the
    convention-swap kill-test only.
    """
    logret = {s: returns_from_close(df["close"], convention) for s, df in klines.items()}
    all_days = sorted(set().union(*[df.index for df in klines.values()]))
    all_days = pd.DatetimeIndex(all_days)
    port = pd.Series(0.0, index=all_days)
    weights: dict = {}
    pending_cost = 0.0
    reb = set(rebalance_dates)
    for day in all_days:
        if weights:
            total = 0.0
            for s, w in weights.items():
                r = logret[s].get(day)
                if r is not None and not np.isnan(r):
                    total += w * r
            port.loc[day] = total
        if pending_cost:
            port.loc[day] -= pending_cost
            pending_cost = 0.0
        if day in reb:
            members = select_fn(day)
            new_w = {s: 1.0 / len(members) for s in members} if members else {}
            keys = set(new_w) | set(weights)
            turnover = sum(abs(new_w.get(k, 0.0) - weights.get(k, 0.0)) for k in keys)
            pending_cost += cost_bps / 1e4 * turnover
            weights = new_w
    start = rebalance_dates[0] if len(rebalance_dates) else all_days[0]
    return port.loc[port.index > start]


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
    all_days = pd.DatetimeIndex(sorted(set().union(*[df.index for df in klines.values()])))
    day_pos = {d: i for i, d in enumerate(all_days)}
    sym_list = sorted(klines)
    sym_idx = {s: j for j, s in enumerate(sym_list)}
    R = np.full((len(all_days), len(sym_list)), np.nan)
    for s, j in sym_idx.items():
        R[:, j] = returns_from_close(klines[s]["close"], convention).reindex(all_days).to_numpy()
    return all_days, day_pos, R, sym_idx


def fast_weekly_portfolio(members_by_t: dict, reb_dates, all_days, day_pos, R, sym_idx,
                          cost_bps: float = 10.0) -> pd.Series:
    """Vectorised twin of :func:`run_weekly_portfolio` (same mechanics, same
    output bar-for-bar): EW over members_by_t[t] takes effect the day AFTER
    rebalance date t; turnover cost charged once on the first accrual day; a
    missing kline contributes 0 without re-weighting.
    """
    n_days = len(all_days)
    ret = np.zeros(n_days)
    events = sorted((day_pos[t], t) for t in reb_dates if t in day_pos)
    weights: dict = {}
    for i, (pos, date) in enumerate(events):
        members = members_by_t.get(date, [])
        new_w = {s: 1.0 / len(members) for s in members} if members else {}
        keys = set(new_w) | set(weights)
        turnover = sum(abs(new_w.get(k, 0.0) - weights.get(k, 0.0)) for k in keys)
        cost = cost_bps / 1e4 * turnover
        start = pos + 1
        end = events[i + 1][0] if i + 1 < len(events) else n_days - 1
        if start <= end and new_w:
            idxs = [sym_idx[s] for s in new_w]
            warr = np.array([new_w[s] for s in new_w])
            block = np.nan_to_num(R[start:end + 1, idxs], nan=0.0)
            ret[start:end + 1] = block @ warr
        if start < n_days:
            ret[start] -= cost
        weights = new_w
    port = pd.Series(ret, index=all_days)
    start_date = reb_dates[0] if len(reb_dates) else all_days[0]
    return port.loc[port.index > start_date]

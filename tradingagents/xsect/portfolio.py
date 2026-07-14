"""Weekly EW long-only cross-sectional portfolio engine — frozen mechanics per gates.json xs_mom_p1."""
import numpy as np
import pandas as pd

from tradingagents.stress.overlay import _maxdd as maxdd  # positive magnitude
from tradingagents.stress.overlay import _sr as sr  # sqrt(365), 0.0 on zero variance


def momentum_scores(klines: dict, symbols: list, date: pd.Timestamp,
                     L: int, skip: int) -> dict:
    """Sum of daily log-returns over the L days ending `skip` days before `date`
    (window (date-skip-L, date-skip]). Symbols with insufficient/NaN history are dropped."""
    out = {}
    for s in symbols:
        close = klines[s]["close"].loc[:date]
        if skip:
            close = close.iloc[:-skip] if len(close) > skip else close.iloc[:0]
        if len(close) < L + 1:
            continue
        window = np.log(close.iloc[-(L + 1):]).diff().dropna()
        if len(window) == L:
            out[s] = float(window.sum())
    return out


def run_weekly_portfolio(klines: dict, rebalance_dates: pd.DatetimeIndex,
                          select_fn, cost_bps: float = 10.0) -> pd.Series:
    """Daily log-return series for a weekly-rebalanced EW long-only portfolio.

    Mechanics: at each rebalance date t (Monday, using close t), target = EW over
    select_fn(t) (list of symbols); positions apply from bar t+1 (no look-ahead —
    the decision bar itself never accrues the return that produced the signal).
    Daily portfolio log-return = mean of members' close-to-close log-returns.
    Costs: cost = cost_bps/1e4 * Sum|w_new - w_old| (one-side rate times summed
    one-side turnover across both legs of each trade), deducted on the first
    accrual day after each rebalance. A member delisted mid-week contributes its
    last available return then weight redistributes at the next rebalance.
    """
    logret = {s: np.log(df["close"]).diff() for s, df in klines.items()}
    all_days = sorted(set().union(*[df.index for df in klines.values()]))
    all_days = pd.DatetimeIndex(all_days)
    port = pd.Series(0.0, index=all_days)
    weights: dict = {}
    pending_cost = 0.0
    reb = set(rebalance_dates)
    for day in all_days:
        if weights:
            rets = [logret[s].get(day) for s in weights]
            rets = [r for r in rets if r is not None and not np.isnan(r)]
            port.loc[day] = float(np.mean(rets)) if rets else 0.0
        if pending_cost and weights:
            port.loc[day] -= pending_cost
            pending_cost = 0.0
        if day in reb:
            members = select_fn(day)
            new_w = {s: 1.0 / len(members) for s in members} if members else {}
            keys = set(new_w) | set(weights)
            turnover = sum(abs(new_w.get(k, 0.0) - weights.get(k, 0.0)) for k in keys)
            pending_cost = cost_bps / 1e4 * turnover
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

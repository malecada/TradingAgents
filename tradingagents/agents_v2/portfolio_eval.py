"""Portfolio gates for the rule-twin book (plan §8.1 gate 5): weekly net returns after taker costs,
annualized Sharpe, and the two placebo families (shuffled dates, shuffled assets within week)."""
from __future__ import annotations

import numpy as np
import pandas as pd

COST_PER_SIDE = 0.0005   # 5 bp taker per side
WEEKS_PER_YEAR = 52


def book_returns(weights: dict[pd.Timestamp, dict[str, float]], fwd: pd.DataFrame, cost_per_side: float = COST_PER_SIDE) -> pd.Series:
    """weights: friday -> {symbol: weight}; fwd: columns date, symbol, fwd_ret (Friday close -> next Friday close)."""
    f = fwd.set_index(["date", "symbol"])["fwd_ret"]
    prev: dict[str, float] = {}
    out = {}
    for d in sorted(weights):
        w = weights[d]
        gross = sum(w.get(s, 0.0) * f.get((d, s), 0.0) for s in w)
        turnover = sum(abs(w.get(s, 0.0) - prev.get(s, 0.0)) for s in set(w) | set(prev))
        out[d] = gross - turnover * cost_per_side
        prev = w
    return pd.Series(out).sort_index()


def sharpe(returns: pd.Series) -> float:
    r = returns.dropna()
    if len(r) < 3 or r.std() == 0:
        return float("nan")
    return float(r.mean() / r.std() * np.sqrt(WEEKS_PER_YEAR))


def placebo_pvalues(weights: dict, fwd: pd.DataFrame, n: int = 500, seed: int = 20261109) -> dict:
    """Date-shuffle: weights assigned to random weeks. Asset-shuffle: weights permuted across assets within week."""
    rng = np.random.default_rng(seed)
    real = sharpe(book_returns(weights, fwd))
    dates = sorted(weights)
    date_sr, asset_sr = [], []
    for _ in range(n):
        perm = rng.permutation(len(dates))
        shuffled = {dates[i]: weights[dates[perm[i]]] for i in range(len(dates))}
        date_sr.append(sharpe(book_returns(shuffled, fwd)))
        within = {}
        for d in dates:
            syms = list(weights[d]); vals = [weights[d][s] for s in syms]
            rng.shuffle(vals)
            within[d] = dict(zip(syms, vals))
        asset_sr.append(sharpe(book_returns(within, fwd)))
    date_sr, asset_sr = np.array(date_sr), np.array(asset_sr)
    return {"sharpe": real,
            "p_date_shuffle": float(np.mean(date_sr >= real)) if np.isfinite(real) else None,
            "p_asset_shuffle": float(np.mean(asset_sr >= real)) if np.isfinite(real) else None,
            "n": n}


def summarize_book(weights: dict, fwd: pd.DataFrame) -> dict:
    r = book_returns(weights, fwd)
    years = {}
    for y, g in r.groupby(r.index.year):
        years[str(y)] = {"weeks": int(len(g)), "sharpe": sharpe(g), "mean_weekly_pct": float(g.mean() * 100)}
    return {"weeks": int(len(r)), "sharpe": sharpe(r), "total_return_pct": float(((1 + r).prod() - 1) * 100),
            "max_drawdown_pct": float(((1 + r).cumprod() / (1 + r).cumprod().cummax() - 1).min() * 100),
            "mean_gross": float(np.mean([sum(abs(v) for v in w.values()) for w in weights.values()])),
            "by_year": years, **placebo_pvalues(weights, fwd)}

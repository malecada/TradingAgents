"""Portfolio gates for the rule-twin book (plan §8.1 gate 5): weekly net returns after taker costs and realized
funding, annualized Sharpe, the two placebo families (shuffled dates, shuffled assets within week) and the
probabilistic Sharpe ratio. Charter 1b corrections: the funded Sharpe is the headline of ``summarize_book`` (the
placebo block no longer overwrites it), placebo books pay funding like the real book, placebo p-values carry the
+1 correction, and the funding window is aligned to the holding period."""
from __future__ import annotations

from math import erf, sqrt
from pathlib import Path

import numpy as np
import pandas as pd

COST_PER_SIDE = 0.0005   # 5 bp taker per side
WEEKS_PER_YEAR = 52
ZERO_STD = 1e-12         # weekly return series below this dispersion are treated as constant (no Sharpe)


def _lookup(frame, col: str) -> dict:
    """(date, symbol) -> value; missing values are dropped. A prepared dict is passed through."""
    if frame is None or isinstance(frame, dict):
        return frame or {}
    s = frame.set_index(["date", "symbol"])[col].dropna()
    return {k: float(v) for k, v in s.items()}


def book_components(weights: dict[pd.Timestamp, dict[str, float]], fwd, cost_per_side: float = COST_PER_SIDE,
                    funding=None) -> pd.DataFrame:
    """Weekly decomposition of the book. weights: friday -> {symbol: weight}; fwd: columns date, symbol, fwd_ret
    (close of the Friday bar -> close of the next Friday bar); ``funding``: optional columns date, symbol,
    funding_week (sum of realized perp funding rates settled inside the holding period); longs pay positive
    funding, shorts receive it. Positions without a return row earn zero and are counted in ``missing_returns``.
    Columns: gross, cost, funding, net, turnover, gross_exposure, missing_returns."""
    f, fd = _lookup(fwd, "fwd_ret"), _lookup(funding, "funding_week")
    prev: dict[str, float] = {}
    rows = {}
    for d in sorted(weights):
        w = weights[d]
        gross = sum(w.get(s, 0.0) * f.get((d, s), 0.0) for s in w)
        turnover = sum(abs(w.get(s, 0.0) - prev.get(s, 0.0)) for s in set(w) | set(prev))
        fund = sum(w.get(s, 0.0) * fd.get((d, s), 0.0) for s in w)
        cost = turnover * cost_per_side
        rows[d] = {"gross": gross, "cost": cost, "funding": fund, "net": gross - cost - fund, "turnover": turnover,
                   "gross_exposure": sum(abs(v) for v in w.values()),
                   "missing_returns": sum(1 for s, v in w.items() if v != 0.0 and (d, s) not in f)}
        prev = w
    cols = ["gross", "cost", "funding", "net", "turnover", "gross_exposure", "missing_returns"]
    return pd.DataFrame.from_dict(rows, orient="index", columns=cols).sort_index()


def book_returns(weights: dict[pd.Timestamp, dict[str, float]], fwd, cost_per_side: float = COST_PER_SIDE,
                 funding=None) -> pd.Series:
    """Weekly net return of the book: gross - turnover * cost_per_side - funding paid."""
    return book_components(weights, fwd, cost_per_side, funding)["net"]


def sharpe(returns: pd.Series) -> float:
    r = returns.dropna()
    if len(r) < 3 or r.std() < ZERO_STD:
        return float("nan")
    return float(r.mean() / r.std() * np.sqrt(WEEKS_PER_YEAR))


def probabilistic_sharpe(returns: pd.Series, benchmark_annual: float = 0.0) -> float | None:
    """Probabilistic Sharpe ratio (Bailey and Lopez de Prado 2012) against an annualized benchmark Sharpe, with the
    skewness and kurtosis of the weekly returns. With one declared configuration the deflated Sharpe ratio reduces
    to this value against a benchmark of zero."""
    r = returns.dropna().to_numpy(dtype=float)
    n = len(r)
    if n < 8 or r.std(ddof=1) < ZERO_STD:
        return None
    sr = r.mean() / r.std(ddof=1)
    e = r - r.mean()
    s = sqrt(float((e ** 2).mean()))
    g3, g4 = float((e ** 3).mean()) / s ** 3, float((e ** 4).mean()) / s ** 4
    denom = sqrt(max(1 - g3 * sr + (g4 - 1) / 4 * sr ** 2, 1e-12))
    z = (sr - benchmark_annual / sqrt(WEEKS_PER_YEAR)) * sqrt(n - 1) / denom
    return float(0.5 * (1 + erf(z / sqrt(2))))


def placebo_pvalues(weights: dict, fwd, n: int = 500, seed: int = 20261109, funding=None) -> dict:
    """Date-shuffle: weights assigned to random weeks. Asset-shuffle: weights permuted across assets within week.
    Placebo books pay the same costs and funding as the real book; p = (1 + #{placebo >= real}) / (n + 1)."""
    rng = np.random.default_rng(seed)
    f, fd = _lookup(fwd, "fwd_ret"), _lookup(funding, "funding_week")
    real = sharpe(book_returns(weights, f, funding=fd))
    dates = sorted(weights)
    date_sr, asset_sr = [], []
    for _ in range(n):
        perm = rng.permutation(len(dates))
        shuffled = {dates[i]: weights[dates[perm[i]]] for i in range(len(dates))}
        date_sr.append(sharpe(book_returns(shuffled, f, funding=fd)))
        within = {}
        for d in dates:
            syms = list(weights[d]); vals = [weights[d][s] for s in syms]
            rng.shuffle(vals)
            within[d] = dict(zip(syms, vals))
        asset_sr.append(sharpe(book_returns(within, f, funding=fd)))
    date_sr, asset_sr = np.array(date_sr), np.array(asset_sr)
    ok = bool(np.isfinite(real))
    return {"sharpe": real if ok else None,
            "p_date_shuffle": float((1 + np.sum(date_sr >= real)) / (n + 1)) if ok else None,
            "p_asset_shuffle": float((1 + np.sum(asset_sr >= real)) / (n + 1)) if ok else None,
            "n": n}


def summarize_book(weights: dict, fwd, funding=None, n_placebo: int = 500) -> dict:
    """Headline ``sharpe`` is net of taker costs and of realized funding when ``funding`` is given; the placebo
    families are evaluated on the same net basis."""
    f, fd = _lookup(fwd, "fwd_ret"), _lookup(funding, "funding_week")
    comp = book_components(weights, f, funding=fd)
    r = comp["net"]
    years = {}
    for y, g in r.groupby(r.index.year):
        years[str(y)] = {"weeks": int(len(g)), "sharpe": sharpe(g), "mean_weekly_pct": float(g.mean() * 100)}
    placebo = placebo_pvalues(weights, f, n=n_placebo, funding=fd)
    return {"weeks": int(len(r)), "sharpe": sharpe(r), "sharpe_before_costs": sharpe(comp["gross"]),
            "sharpe_costs_no_funding": sharpe(comp["gross"] - comp["cost"]),
            "psr_vs_zero": probabilistic_sharpe(r),
            "total_return_pct": float(((1 + r).prod() - 1) * 100),
            "max_drawdown_pct": float(((1 + r).cumprod() / (1 + r).cumprod().cummax() - 1).min() * 100),
            "mean_gross": float(comp["gross_exposure"].mean()), "mean_turnover": float(comp["turnover"].mean()),
            "sum_gross_pct": float(comp["gross"].sum() * 100), "sum_cost_pct": float(comp["cost"].sum() * 100),
            "sum_funding_pct": float(comp["funding"].sum() * 100), "missing_returns": int(comp["missing_returns"].sum()),
            "funded": bool(fd), "by_year": years,
            "p_date_shuffle": placebo["p_date_shuffle"], "p_asset_shuffle": placebo["p_asset_shuffle"],
            "placebo_n": placebo["n"], "placebo_basis_sharpe": placebo["sharpe"]}


FUNDING_DIR = Path("data/dossier/funding")


def realized_funding(symbols, fridays, funding_dir: Path = FUNDING_DIR, horizon_days: int = 7,
                     offset_days: int = 1) -> pd.DataFrame:
    """Sum of realized funding rates settled inside the holding period per (date, symbol), from the store written
    by scripts/dossier_funding_fetch.py. ``fridays`` are the open stamps of the Friday daily bars (Friday 00:00
    UTC); the position is opened at that bar's close, ``offset_days`` later, and held for ``horizon_days``, so the
    window is (Friday + offset, Friday + offset + horizon]: the settlement at the entry instant is not paid, the
    one at the exit instant is. Settlement stamps carry exchange jitter of a few milliseconds and are rounded to
    the minute before the window is applied. Symbols without a file are omitted (treated as zero funding by the
    book)."""
    rows = []
    for sym in symbols:
        path = Path(funding_dir) / f"{sym}.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(path)
        if not len(df):
            continue
        t = pd.to_datetime(df["fundingTime"], utc=True).dt.round("min")
        for f in fridays:
            f = pd.Timestamp(f)
            start = f + pd.Timedelta(days=offset_days)
            m = (t > start) & (t <= start + pd.Timedelta(days=horizon_days))
            if m.any():
                rows.append((f, sym, float(df.loc[m, "fundingRate"].sum()), int(m.sum())))
    return pd.DataFrame(rows, columns=["date", "symbol", "funding_week", "n_settlements"])

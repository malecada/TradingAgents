"""Forecast-quality ladder (plan §8.1 gate 4): weekly cross-sectional rank IC of the system's
probability against 7-day forward return, residualized on volatility, 4-week momentum and
size (C3-P protocol), Newey-West t; Brier skill versus the base rate; calibration slope.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# size is controlled through 30-day dollar volume (100 % coverage); the market-cap rank covers only 24-48 %
# of the universe (none after mid-2025) and would enter as a half-filled constant
CONTROLS = ["vol_ewma20", "ret_4w", "dvol_30d"]


def residualize(day: pd.DataFrame, col: str) -> pd.Series:
    """Percentile-rank OLS residual of ``col`` on the controls within one week."""
    y = day[col].rank(pct=True)
    X = np.column_stack([np.ones(len(day))] + [day[c].rank(pct=True).fillna(0.5).to_numpy() for c in CONTROLS])
    beta, *_ = np.linalg.lstsq(X, y.to_numpy(), rcond=None)
    return pd.Series(y.to_numpy() - X @ beta, index=day.index)


def weekly_ic(panel: pd.DataFrame, prob_col: str = "p_outperform", ret_col: str = "fwd_ret") -> pd.Series:
    """Spearman IC per week of residualized probability vs residualized forward return."""
    out = {}
    for d, day in panel.groupby("date"):
        day = day.dropna(subset=[prob_col, ret_col])
        if len(day) < 10:
            continue
        rp, rr = residualize(day, prob_col), residualize(day, ret_col)
        out[d] = rp.corr(rr, method="spearman")
    return pd.Series(out).sort_index()


def newey_west_t(x: pd.Series, lag: int = 4) -> float:
    x = x.dropna().to_numpy()
    n = len(x)
    if n < 3:
        return float("nan")
    mean = x.mean()
    e = x - mean
    var = e @ e / n
    for k in range(1, lag + 1):
        w = 1 - k / (lag + 1)
        var += 2 * w * (e[k:] @ e[:-k]) / n
    return float(mean / np.sqrt(var / n))


def brier(panel: pd.DataFrame, prob_col: str = "p_outperform", ret_col: str = "fwd_ret") -> dict:
    """Outcome = beat the week's median return. Skill = 1 - Brier / Brier(base rate 0.5)."""
    rows = []
    for d, day in panel.groupby("date"):
        day = day.dropna(subset=[prob_col, ret_col])
        if len(day) < 10:
            continue
        y = (day[ret_col] > day[ret_col].median()).astype(float)
        rows.append(pd.DataFrame({"p": day[prob_col].to_numpy(), "y": y.to_numpy()}))
    if not rows:
        return {"brier": None, "skill": None, "n": 0}
    all_ = pd.concat(rows)
    b = float(((all_["p"] - all_["y"]) ** 2).mean())
    base = float(((0.5 - all_["y"]) ** 2).mean())
    return {"brier": b, "skill": 1 - b / base, "n": int(len(all_))}


def calibration_slope(panel: pd.DataFrame, prob_col: str = "p_outperform", ret_col: str = "fwd_ret", bins: int = 5) -> dict:
    rows = []
    for d, day in panel.groupby("date"):
        day = day.dropna(subset=[prob_col, ret_col])
        if len(day) < 10:
            continue
        y = (day[ret_col] > day[ret_col].median()).astype(float)
        rows.append(pd.DataFrame({"p": day[prob_col].to_numpy(), "y": y.to_numpy()}))
    if not rows:
        return {"slope": None, "bins": []}
    all_ = pd.concat(rows)
    all_["bin"] = pd.qcut(all_["p"].rank(method="first"), bins, labels=False)
    g = all_.groupby("bin").agg(p=("p", "mean"), y=("y", "mean"), n=("y", "size")).reset_index()
    slope = float(np.polyfit(g["p"], g["y"], 1)[0]) if g["p"].nunique() > 1 else float("nan")
    return {"slope": slope, "bins": g.to_dict("records")}


def evaluate_panel(panel: pd.DataFrame, prob_col: str = "p_outperform") -> dict:
    ic = weekly_ic(panel, prob_col)
    return {"weeks": int(len(ic)), "ic_mean": float(ic.mean()) if len(ic) else None,
            "ic_nw_t": newey_west_t(ic), "ic_hit_rate": float((ic > 0).mean()) if len(ic) else None,
            "brier": brier(panel, prob_col), "calibration": calibration_slope(panel, prob_col)}

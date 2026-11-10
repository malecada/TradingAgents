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


def _pooled(panel: pd.DataFrame, prob_col: str, ret_col: str) -> pd.DataFrame:
    rows = []
    for d, day in panel.groupby("date"):
        day = day.dropna(subset=[prob_col, ret_col])
        if len(day) < 10:
            continue
        y = (day[ret_col] > day[ret_col].median()).astype(float)
        rows.append(pd.DataFrame({"date": d, "p": day[prob_col].to_numpy(), "y": y.to_numpy()}))
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=["date", "p", "y"])


def _logit(p):
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def _logistic_fit(x: np.ndarray, y: np.ndarray, iters: int = 50, ridge: float = 1e-6) -> tuple[float, float]:
    """y ~ sigmoid(a + b x) by Newton iterations; returns (a, b)."""
    X = np.column_stack([np.ones(len(x)), x])
    beta = np.zeros(2)
    for _ in range(iters):
        z = X @ beta
        mu = 1 / (1 + np.exp(-z))
        W = mu * (1 - mu)
        H = X.T @ (X * W[:, None]) + ridge * np.eye(2)
        step = np.linalg.solve(H, X.T @ (y - mu))
        beta = beta + step
        if np.abs(step).max() < 1e-8:
            break
    return float(beta[0]), float(beta[1])


def cox_calibration(panel: pd.DataFrame, prob_col: str = "p_outperform", ret_col: str = "fwd_ret") -> dict:
    """Cox (1958) calibration: logistic regression of the outcome on logit(p). Slope 1 / intercept 0 = calibrated;
    tie-robust, unlike quintile binning (finding 3). Reported as a diagnostic, not a gate."""
    pooled = _pooled(panel, prob_col, ret_col)
    if len(pooled) < 50 or pooled["p"].nunique() < 3:
        return {"intercept": None, "slope": None, "n": int(len(pooled))}
    a, b = _logistic_fit(_logit(pooled["p"]), pooled["y"].to_numpy())
    return {"intercept": a, "slope": b, "n": int(len(pooled))}


def recalibrated_brier(panel: pd.DataFrame, prob_col: str = "p_outperform", ret_col: str = "fwd_ret",
                       min_train_weeks: int = 52) -> dict:
    """Walk-forward recalibration: for week t, fit y ~ logit(p) on weeks whose outcomes are known before t
    (first ``min_train_weeks`` weeks are training only), apply to week t. Brier skill of the recalibrated
    probabilities measures discrimination net of level and dispersion bias (finding 3)."""
    pooled = _pooled(panel, prob_col, ret_col)
    if pooled.empty:
        return {"brier": None, "skill": None, "n": 0, "weeks": 0}
    dates = sorted(pooled["date"].unique())
    out_p, out_y = [], []
    for i, d in enumerate(dates):
        if i < min_train_weeks:
            continue
        train = pooled[pooled["date"] < d - pd.Timedelta(days=7)]      # outcome of week d-1 realized before d
        test = pooled[pooled["date"] == d]
        if len(train) < 100 or train["p"].nunique() < 3:
            continue
        a, b = _logistic_fit(_logit(train["p"]), train["y"].to_numpy())
        out_p.append(1 / (1 + np.exp(-(a + b * _logit(test["p"])))))
        out_y.append(test["y"].to_numpy())
    if not out_p:
        return {"brier": None, "skill": None, "n": 0, "weeks": 0}
    p = np.concatenate(out_p); y = np.concatenate(out_y)
    b = float(((p - y) ** 2).mean()); base = float(((0.5 - y) ** 2).mean())
    return {"brier": b, "skill": 1 - b / base, "n": int(len(p)), "weeks": len(out_p)}


def encompassing(panel: pd.DataFrame, prob_col: str = "p_judge", quant_col: str = "p_quant", ret_col: str = "fwd_ret") -> dict:
    """Forecast-encompassing test (finding 2): weekly cross-sectional OLS of the residualized return rank on the
    residualized ranks of the quant forecast and the LLM probability (Fama-MacBeth over weeks, Newey-West t on
    the mean coefficients). A positive, significant LLM coefficient means the LLM adds information the quant
    forecast does not carry; the sign of the quant coefficient shows whether it survives the LLM."""
    rows = []
    for d, day in panel.groupby("date"):
        day = day.dropna(subset=[prob_col, quant_col, ret_col])
        if len(day) < 15:
            continue
        rr = residualize(day, ret_col).to_numpy()
        rq = residualize(day, quant_col).to_numpy()
        rp = residualize(day, prob_col).to_numpy()
        X = np.column_stack([np.ones(len(day)), rq, rp])
        beta, *_ = np.linalg.lstsq(X, rr, rcond=None)
        rows.append((d, beta[1], beta[2]))
    if len(rows) < 3:
        return {"weeks": len(rows), "beta_quant": None, "t_quant": None, "beta_llm": None, "t_llm": None}
    df = pd.DataFrame(rows, columns=["date", "bq", "bp"]).set_index("date").sort_index()
    return {"weeks": int(len(df)), "beta_quant": float(df["bq"].mean()), "t_quant": newey_west_t(df["bq"]),
            "beta_llm": float(df["bp"].mean()), "t_llm": newey_west_t(df["bp"])}


def centered(panel: pd.DataFrame, prob_col: str = "p_outperform") -> pd.Series:
    """Weekly-centered probability p - mean_week + 0.5 (finding 7: level bias on a relative target)."""
    return panel[prob_col] - panel.groupby("date")[prob_col].transform("mean") + 0.5


def evaluate_panel(panel: pd.DataFrame, prob_col: str = "p_outperform") -> dict:
    ic = weekly_ic(panel, prob_col)
    out = {"weeks": int(len(ic)), "ic_mean": float(ic.mean()) if len(ic) else None,
           "ic_nw_t": newey_west_t(ic), "ic_hit_rate": float((ic > 0).mean()) if len(ic) else None,
           "brier": brier(panel, prob_col), "brier_recalibrated": recalibrated_brier(panel, prob_col),
           "calibration_cox": cox_calibration(panel, prob_col), "calibration": calibration_slope(panel, prob_col)}
    if len(panel):
        c = panel.assign(_c=centered(panel, prob_col))
        out["brier_centered"] = brier(c, "_c")
    return out

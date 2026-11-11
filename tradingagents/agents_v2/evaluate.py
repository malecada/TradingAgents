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


# ---------------------------------------------------------------- Charter 1b additions
def subperiod_sign_gate(ic: pd.Series, required: int = 2) -> dict:
    """Sub-period gate of Charter 1 (§5, §6a): the mean weekly IC per calendar year present in the completed
    window; passes when at least ``min(required, years present)`` years share the sign of their mean IC. With
    three years present the rule cannot fail (two of three signs always agree); with two years present both must
    agree; with one year present it is passed by construction. The result records which case applies."""
    ic = ic.dropna()
    means = {str(y): float(g.mean()) for y, g in ic.groupby(ic.index.year)} if len(ic) else {}
    weeks = {str(y): int(len(g)) for y, g in ic.groupby(ic.index.year)} if len(ic) else {}
    pos, neg = sum(v > 0 for v in means.values()), sum(v < 0 for v in means.values())
    need = min(required, len(means))
    return {"mean_ic_by_year": means, "weeks_by_year": weeks, "years_present": len(means), "n_positive": int(pos),
            "n_negative": int(neg), "required_same_sign": int(need),
            "binding": bool(1 < len(means) < 2 * required - 1),
            "pass": bool(len(means) > 0 and max(pos, neg) >= need)}


def _residual_pairs(panel: pd.DataFrame, col: str, ret_col: str = "fwd_ret") -> pd.DataFrame:
    """Per row: residual rank of ``col`` and of the return, both computed within the week on the FULL cross-section
    (every row with a forecast and a return), the raw value of ``col`` and the outcome against the week's
    full-cross-section median. Indexed like ``panel``."""
    parts = []
    for d, day in panel.groupby("date"):
        day = day.dropna(subset=[col, ret_col])
        if len(day) < 10:
            continue
        parts.append(pd.DataFrame({"date": d, "rp": residualize(day, col).to_numpy(), "rr": residualize(day, ret_col).to_numpy(),
                                   "p": day[col].to_numpy(dtype=float),
                                   "y": (day[ret_col] > day[ret_col].median()).astype(float).to_numpy()}, index=day.index))
    return pd.concat(parts) if parts else pd.DataFrame(columns=["date", "rp", "rr", "p", "y"])


def _corr(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 3 or a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def _skill(p: np.ndarray, y: np.ndarray) -> float:
    base = float(((0.5 - y) ** 2).mean()) if len(y) else 0.0
    return float(1 - ((p - y) ** 2).mean() / base) if base > 0 else float("nan")


def subset_gaps(panel: pd.DataFrame, cols=("p_hybrid", "p_judge", "p_quant"), flag_col: str = "identified",
                ret_col: str = "fwd_ret", contrast: tuple[str, str] = ("p_judge", "p_quant"), n_boot: int = 2000,
                seed: int = 20261111, min_rows: int = 30) -> dict:
    """Identified-subset estimator (Charter 1 §4, fixed in Charter 1b before unblinding). Rows with
    ``flag_col`` True form the identified subset, rows with False the not-identified subset, rows without a flag
    are in neither. Per forecast column: the pooled correlation of the within-week residual ranks (forecast vs
    return, both residualized on the full cross-section) inside each subset, the gap identified minus
    not-identified, and the Brier skill of the raw value per subset with the outcome defined on the full
    cross-section median. Intervals and two-sided p-values come from a week-block bootstrap. ``contrast``
    reports the gap of the first column minus the gap of the second (difference-in-differences: a memorization
    effect should load on the LLM column and not on the quant column)."""
    flag = panel[flag_col]
    fields = ("rp", "rr", "p", "y", "flag")
    frames = {}
    for c in cols:
        fr = _residual_pairs(panel, c, ret_col).join(flag.rename("flag"), how="left")
        fr = fr[fr["flag"].notna()]
        frames[c] = fr.assign(flag=fr["flag"].astype(bool))
    weeks = sorted(set().union(*[set(fr["date"]) for fr in frames.values()])) if frames else []
    nan_stats = {"ic_identified": float("nan"), "ic_not_identified": float("nan"), "gap": float("nan"),
                 "brier_skill_identified": float("nan"), "brier_skill_not_identified": float("nan"), "brier_gap": float("nan")}

    def _stats(rp, rr, p, y, flag) -> dict:
        a, b = flag, ~flag
        if a.sum() < min_rows or b.sum() < min_rows:
            return dict(nan_stats)
        ia, ib = _corr(rp[a], rr[a]), _corr(rp[b], rr[b])
        sa, sb = _skill(p[a], y[a]), _skill(p[b], y[b])
        return {"ic_identified": ia, "ic_not_identified": ib, "gap": ia - ib,
                "brier_skill_identified": sa, "brier_skill_not_identified": sb, "brier_gap": sa - sb}

    def _arrays(fr: pd.DataFrame) -> tuple:
        return tuple(fr[k].to_numpy(dtype=bool if k == "flag" else float) for k in fields)

    point = {c: _stats(*_arrays(fr)) for c, fr in frames.items()}
    by_week = {c: {d: _arrays(g) for d, g in fr.groupby("date")} for c, fr in frames.items()}
    rng = np.random.default_rng(seed)
    draws = {c: {"gap": [], "brier_gap": []} for c in cols}
    did = []
    for _ in range(n_boot if weeks else 0):
        pick = rng.integers(0, len(weeks), len(weeks))
        stat = {}
        for c in cols:
            parts = [by_week[c][weeks[i]] for i in pick if weeks[i] in by_week[c]]
            stat[c] = _stats(*[np.concatenate([part[j] for part in parts]) for j in range(len(fields))]) if parts else dict(nan_stats)
            draws[c]["gap"].append(stat[c]["gap"]); draws[c]["brier_gap"].append(stat[c]["brier_gap"])
        if contrast[0] in stat and contrast[1] in stat:
            did.append(stat[contrast[0]]["gap"] - stat[contrast[1]]["gap"])

    def _interval(values) -> dict:
        v = np.asarray(values, dtype=float)
        v = v[np.isfinite(v)]
        if len(v) < 100:
            return {"ci95": None, "p_two_sided": None, "draws": int(len(v))}
        p = 2 * min((1 + np.sum(v <= 0)) / (len(v) + 1), (1 + np.sum(v >= 0)) / (len(v) + 1))
        return {"ci95": [float(np.quantile(v, 0.025)), float(np.quantile(v, 0.975))], "p_two_sided": float(min(1.0, p)),
                "draws": int(len(v))}

    out = {"weeks": len(weeks), "n_boot": n_boot, "seed": seed, "columns": {}}
    for c, fr in frames.items():
        out["columns"][c] = {"n_identified": int(fr["flag"].sum()), "n_not_identified": int((~fr["flag"]).sum()), **point[c],
                             "gap_bootstrap": _interval(draws[c]["gap"]), "brier_gap_bootstrap": _interval(draws[c]["brier_gap"])}
    if contrast[0] in point and contrast[1] in point:
        out["difference_in_differences"] = {"columns": list(contrast), "gap_difference": point[contrast[0]]["gap"] - point[contrast[1]]["gap"],
                                            **_interval(did)}
    return out

"""Prediction component for the dossier (plan §7.3 option 1): a pre-registered-shape
cross-sectional ridge forecast of next-week return rank from card fields, walk-forward,
with its own trailing calibration record so agents see how (un)reliable it has been.

Honest by construction: fitted only on Fridays strictly before the decision Friday,
targets realized from klines, skill reported as trailing rank IC and hit rate.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from tradingagents.dossier.numeric_card import KLINES

FEATURES = ["ret_4w", "ret_12w", "dist_26w_high", "vol_ewma20", "volvol_20", "funding_3d", "funding_30d",
            "d_adract_30d", "d_txcnt_30d", "unlock_next30_pct", "size_rank", "age_weeks"]
BURN_IN_WEEKS = 52
CALIB_WEEKS = 26
RIDGE_ALPHA = 10.0
HORIZON_DAYS = 7


def forward_returns(symbols, fridays, klines_dir: Path = KLINES, horizon_days: int = HORIZON_DAYS) -> pd.DataFrame:
    """Realized return from Friday close to Friday+horizon close, per (date, symbol)."""
    rows = []
    for sym in symbols:
        path = Path(klines_dir) / f"{sym}.parquet"
        if not path.exists():
            continue
        k = pd.read_parquet(path)
        close = k["close"].astype(float)
        close.index = pd.to_datetime(close.index, utc=True)
        last_bar = close.index.max()
        for f in fridays:
            end = f + pd.Timedelta(days=horizon_days)
            if f not in close.index:
                continue
            if end in close.index:
                rows.append((f, sym, close.loc[end] / close.loc[f] - 1, False))
            elif last_bar < end and last_bar > f:
                # the contract stopped trading inside the week (delisting): book the last available close,
                # so the week is kept in the target and in the book instead of vanishing
                rows.append((f, sym, close.loc[last_bar] / close.loc[f] - 1, True))
    return pd.DataFrame(rows, columns=["date", "symbol", "fwd_ret", "delisted"])


def _xs_rank(s: pd.Series) -> pd.Series:
    return s.rank(pct=True) - 0.5


def _design(day: pd.DataFrame) -> pd.DataFrame:
    X = day[FEATURES].copy()
    for c in FEATURES:
        X[c] = _xs_rank(X[c]).fillna(0.0)
    return X


def fit_predict(cards: pd.DataFrame, fwd: pd.DataFrame, friday: pd.Timestamp) -> pd.DataFrame:
    """Ridge on all Fridays < friday with known forward returns; predict friday's cross-section.
    Returns per-symbol predicted rank percentile for ``friday``; empty before burn-in."""
    hist = cards[cards["date"] < friday].merge(fwd, on=["date", "symbol"])
    hist = hist[hist["date"] + pd.Timedelta(days=HORIZON_DAYS) <= friday]   # target realized before decision
    if hist["date"].nunique() < BURN_IN_WEEKS:
        return pd.DataFrame(columns=["symbol", "pred_rank_pct"])
    Xs, ys = [], []
    for d, day in hist.groupby("date"):
        Xs.append(_design(day).to_numpy())
        ys.append(_xs_rank(day["fwd_ret"]).to_numpy())
    X = np.vstack(Xs); y = np.concatenate(ys)
    beta = np.linalg.solve(X.T @ X + RIDGE_ALPHA * np.eye(X.shape[1]), X.T @ y)
    today = cards[cards["date"] == friday]
    pred = _design(today).to_numpy() @ beta
    out = pd.DataFrame({"symbol": today["symbol"].to_numpy(), "score": pred})
    out["pred_rank_pct"] = out["score"].rank(pct=True)
    return out[["symbol", "pred_rank_pct"]]


def calibration(preds: pd.DataFrame, fwd: pd.DataFrame, friday: pd.Timestamp, weeks: int = CALIB_WEEKS) -> dict:
    """Trailing realized skill of past predictions whose outcomes are known at ``friday``."""
    merged = preds.merge(fwd, on=["date", "symbol"])
    merged = merged[(merged["date"] + pd.Timedelta(days=HORIZON_DAYS) <= friday) & (merged["date"] >= friday - pd.Timedelta(weeks=weeks))]
    if merged.empty:
        return {"weeks": 0, "rank_ic_mean": None, "hit_rate_top_vs_bottom": None}
    ics, hits = [], []
    for d, day in merged.groupby("date"):
        if len(day) < 10:
            continue
        ics.append(day["pred_rank_pct"].corr(day["fwd_ret"], method="spearman"))
        top = day[day["pred_rank_pct"] >= 0.8]["fwd_ret"].mean()
        bottom = day[day["pred_rank_pct"] <= 0.2]["fwd_ret"].mean()
        hits.append(float(top > bottom))
    return {"weeks": len(ics), "rank_ic_mean": round(float(np.nanmean(ics)), 4) if ics else None,
            "hit_rate_top_vs_bottom": round(float(np.mean(hits)), 2) if hits else None}


def render_forecast(pred_rank_pct, calib: dict, horizon_days: int = HORIZON_DAYS) -> str:
    if pred_rank_pct is None or pd.isna(pred_rank_pct):
        return f"Quant forecast: unavailable for this asset this week (model needs {BURN_IN_WEEKS} weeks of history)."
    skill = ("no calibration record yet" if not calib["weeks"] else
             f"over the last {calib['weeks']} weeks its rank correlation with realized {horizon_days}-day returns averaged "
             f"{calib['rank_ic_mean']:+.3f} and its top quintile beat its bottom quintile in {round(calib['hit_rate_top_vs_bottom'] * 100)}% of weeks")
    return (f"Quant forecast: a cross-sectional ridge model ranks this asset at percentile {round(pred_rank_pct * 100)} "
            f"of the universe for expected {horizon_days}-day return; {skill}.")

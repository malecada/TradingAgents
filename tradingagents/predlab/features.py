"""PIT-safe feature builders for Tier-2 ML cells.

Convention: a feature row at index t is computable from store rows <= t-1
only (strict lag — the origin's information set under the runner's y[t] =
target over (t, t+h] convention). Pinned by a mutation test: changing store
row t must not change feature row t.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

_WINDOWS = {"1h": (24, 168), "24h": (7, 22)}


def build_features(store: pd.DataFrame, grid: str) -> pd.DataFrame:
    """Features from an rv-store frame (rv/ret/quote_volume/taker columns)."""
    if grid not in _WINDOWS:
        raise ValueError(f"grid must be one of {sorted(_WINDOWS)}, got {grid!r}")
    w_short, w_long = _WINDOWS[grid]

    rv = store["rv"].astype(np.float64)
    ret = store["ret"].astype(np.float64)
    qv = store["quote_volume"].astype(np.float64)
    taker = store["taker_buy_quote_volume"].astype(np.float64)

    lag = lambda s, k=1: s.shift(k)  # noqa: E731
    roll_mean = lambda s, w: s.shift(1).rolling(w).mean()  # noqa: E731

    out = pd.DataFrame(index=store.index)
    # realized-vol block
    out["rv_lag1"] = lag(rv)
    out[f"rv_mean{w_short}"] = roll_mean(rv, w_short)
    out[f"rv_mean{w_long}"] = roll_mean(rv, w_long)
    out[f"rv_ratio_1_{w_short}"] = out["rv_lag1"] / out[f"rv_mean{w_short}"]
    out["bv_share_lag1"] = lag(store["bv"] / store["rv"].replace(0.0, np.nan))
    out["rq_lag1"] = lag(store["rq"])
    # return block
    out["ret_lag1"] = lag(ret)
    out["ret_lag2"] = lag(ret, 2)
    out["ret_lag3"] = lag(ret, 3)
    out[f"ret_mean{w_short}"] = roll_mean(ret, w_short)
    out["absret_lag1"] = lag(ret.abs())
    # volume / flow block
    out["logqv_lag1"] = lag(np.log(qv.replace(0.0, np.nan)))
    out[f"logqv_mean{w_short}"] = roll_mean(np.log(qv.replace(0.0, np.nan)), w_short)
    out["ti_lag1"] = lag(2.0 * (taker / qv.replace(0.0, np.nan)) - 1.0)
    out[f"ti_mean{w_short}"] = roll_mean(2.0 * (taker / qv.replace(0.0, np.nan)) - 1.0, w_short)
    # calendar (deterministic functions of the timestamp — in the info set)
    hod = store.index.hour.to_numpy()
    dow = store.index.dayofweek.to_numpy()
    out["hod_sin"] = np.sin(2 * np.pi * hod / 24)
    out["hod_cos"] = np.cos(2 * np.pi * hod / 24)
    out["dow_sin"] = np.sin(2 * np.pi * dow / 7)
    out["dow_cos"] = np.cos(2 * np.pi * dow / 7)
    return out


def funding_features(rate: pd.Series, target_index: pd.DatetimeIndex) -> pd.DataFrame:
    """Funding features aligned to an arbitrary grid.

    ``fund_last`` at t = most recent print STRICTLY before t (merge_asof on
    a shifted key); ``fund_mean3`` = mean of last 3 prints; ``fund_cum24h`` =
    sum of prints in [t-24h, t).
    """
    rate = rate.sort_index()
    prints = rate.to_frame("rate")
    prints["mean3"] = rate.rolling(3).mean()

    left = pd.DataFrame(index=target_index)
    # strictly-before: subtract an epsilon from the as-of key
    key = target_index - pd.Timedelta(nanoseconds=1)
    merged = pd.merge_asof(
        pd.DataFrame({"key": key}), prints.reset_index().rename(columns={"index": "ts"}),
        left_on="key", right_on=prints.index.name or "ts", direction="backward",
    )
    left["fund_last"] = merged["rate"].to_numpy()
    left["fund_mean3"] = merged["mean3"].to_numpy()
    cum = []
    vals = rate
    for t in target_index:
        window = vals[(vals.index >= t - pd.Timedelta(hours=24)) & (vals.index < t)]
        cum.append(float(window.sum()) if len(window) else np.nan)
    left["fund_cum24h"] = cum
    return left

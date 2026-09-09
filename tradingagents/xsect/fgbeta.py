"""F&G sentiment-beta cross-sectional sort — frozen rule gates.json fg_beta_d1."""
import numpy as np
import pandas as pd


def fng_daily_series(fng_path) -> pd.Series:
    fng = pd.read_parquet(fng_path)
    s = (fng.assign(d=pd.to_datetime(fng["event_ts"], utc=True).dt.normalize())
         .set_index("d")["value"].astype(float).sort_index())
    return s[~s.index.duplicated(keep="last")]


def fg_beta(klines: dict, fng: pd.Series, symbols: list, date: pd.Timestamp,
            window: int = 90, min_obs: int = 60) -> dict:
    dfg = fng.diff().shift(1).loc[:date].tail(window)  # causal: uses fng <= date-1
    out = {}
    for s in symbols:
        ret = np.log(klines[s]["close"]).diff().shift(1).loc[:date].tail(window)
        j = pd.concat([ret, dfg], axis=1, join="inner").dropna()
        if len(j) < min_obs:
            continue
        x, y = j.iloc[:, 1].to_numpy(), j.iloc[:, 0].to_numpy()
        vx = x.var()
        if vx == 0:
            continue
        out[s] = float(((x - x.mean()) * (y - y.mean())).mean() / vx)
    return out


def _quintile_bounds(betas: dict):
    vals = np.array(sorted(betas.values()))
    return np.quantile(vals, 0.4), np.quantile(vals, 0.6), np.quantile(vals, 0.2), np.quantile(vals, 0.8)


def middle_quintile(betas: dict) -> list:
    if not betas:
        return []
    q40, q60, _, _ = _quintile_bounds(betas)
    return sorted([s for s, b in betas.items() if q40 <= b <= q60])


def exclude_extreme_quintiles(betas: dict, members: list) -> list:
    if not betas:
        return list(members)
    _, _, q20, q80 = _quintile_bounds(betas)
    return [s for s in members if s in betas and q20 < betas[s] < q80]

"""liq_fade_i1 — intraday liquidation-cascade long-fade (spec 2026-07-28)."""
import numpy as np
import pandas as pd


def monthly_top_n(daily, start, end, n=50, lookback=30, min_age_days=60):
    months = pd.date_range(pd.Timestamp(start, tz="UTC"),
                           pd.Timestamp(end, tz="UTC"), freq="MS")
    out = {}
    for m in months:
        scores = {}
        for sym, df in daily.items():
            hist = df.loc[df.index < m]
            if len(hist) < min_age_days or (m - hist.index[-1]).days > 3:
                continue
            scores[sym] = hist["quote_volume"].iloc[-lookback:].median()
        ranked = sorted(scores, key=lambda s: -scores[s])[:n]
        out[m] = ranked
    return out


def _roll_z(x: pd.DataFrame, window: int, min_periods: int) -> pd.DataFrame:
    """Compute rolling z-score with pandas rolling."""
    mu = x.rolling(window, min_periods=min_periods).mean()
    sd = x.rolling(window, min_periods=min_periods).std(ddof=1)
    return (x - mu) / sd


def cascade_triggers(close, qvol, thr, window=2160, min_periods=1440):
    """Detect liquidation cascade 1h trigger: low return + high volume."""
    r = np.log(close).diff()
    z_ret = _roll_z(r, window, min_periods)
    z_vol = _roll_z(np.log1p(qvol), window, min_periods)
    return (z_ret <= -thr) & (z_vol >= thr)

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


def event_weights_hourly(trig, H, w_per=0.1, cap=1.0):
    """Generate position weights from liquidation cascade triggers.

    A trigger at bar t opens weight w_per for bars t+1…t+H. Retrigger during
    the hold resets the timer. A new event that would push W.sum(axis=1) above
    cap at its entry bar is ignored entirely; arrival order = column order for
    same-bar ties. Symbols already holding always reset regardless of cap.

    Args:
        trig: pd.DataFrame of bool, triggers[i,j] = True if cascade detected
        H: int, hold duration in bars (bars t+1..t+H)
        w_per: float, weight per active position (default 0.1)
        cap: float, gross cap on total position weight per bar (default 1.0)

    Returns:
        pd.DataFrame of float weights; W.iloc[i] is the position held DURING bar i
        (decided from triggers ≤ bar i-1)
    """
    T = trig.to_numpy()
    n, k = T.shape
    left = np.zeros(k, dtype=np.int64)  # bars remaining for each symbol
    W = np.zeros((n, k))
    max_slots = int(round(cap / w_per))

    for i in range(n):
        if i > 0:
            # events triggered at bar i-1 activate for bar i
            for j in range(k):
                if T[i - 1, j]:
                    active = int((left > 0).sum())
                    if left[j] > 0 or active < max_slots:
                        left[j] = H  # open or reset timer

        # Set weights based on current holdings (before decrement)
        W[i] = np.where(left > 0, w_per, 0.0)

        # Decrement hold counters
        left = np.maximum(left - 1, 0)

    return pd.DataFrame(W, index=trig.index, columns=trig.columns)

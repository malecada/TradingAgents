"""Realized-measure aggregation from 5-minute bars.

Per period (UTC hour or day, labeled by period START):
  r_i     = log-close diffs of the 5m bars whose OPEN time falls in the period
            (the first bar's return uses the previous bar's close as seed, so
            the boundary return belongs to the period it lands in; the very
            first period of a series is dropped — no seed exists)
  rv      = sum r_i^2                       (realized variance, period units)
  bv      = (pi/2) * sum |r_i||r_{i-1}|     (bipower variation, within period)
  rq      = (n/3) * sum r_i^4               (realized quarticity)
  park    = (ln(high_period/low_period))^2 / (4 ln 2)   (Parkinson range var)
  ret     = sum r_i                          (period log-return, T1/T2 target)
  n_bars  = bar count (honest denominator); rv is nan'd when the period has
            fewer than 80% of expected bars (12 per 1h, 288 per 1d)
plus summed quote_volume, taker_buy_quote_volume, n_trades.

No look-ahead by construction: every output row uses only bars inside its own
period (property-tested by mutation in tests/predlab/test_rv.py).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

_EXPECTED = {"1h": 12, "1d": 288}
_FLOOR_FRAC = 0.8


def aggregate_rv(df_5m: pd.DataFrame, freq: str) -> pd.DataFrame:
    """Aggregate a 5m kline frame (ts int64-ms column) to 1h or 1d realized measures."""
    if freq not in _EXPECTED:
        raise ValueError(f"freq must be one of {sorted(_EXPECTED)}, got {freq!r}")
    expected = _EXPECTED[freq]

    df = df_5m.sort_values("ts").reset_index(drop=True)
    times = pd.to_datetime(df["ts"].astype("int64"), unit="ms", utc=True)
    label = times.dt.floor("h" if freq == "1h" else "D")

    logc = np.log(df["close"].astype(np.float64))
    r = logc.diff()
    absr = r.abs()

    work = pd.DataFrame(
        {
            "label": label,
            "r": r,
            "r2": r**2,
            "r4": r**4,
            # bipower cross-term only where BOTH bars sit in the same period
            "bp": (absr * absr.shift(1)).where(label.eq(label.shift(1))),
            "high": df["high"].astype(np.float64),
            "low": df["low"].astype(np.float64),
            "quote_volume": df["quote_volume"].astype(np.float64),
            "taker_buy_quote_volume": df["taker_buy_quote_volume"].astype(np.float64),
            "n_trades": df["n_trades"].astype(np.float64),
        }
    )

    g = work.groupby("label", sort=True)
    n_ret = g["r"].count()
    out = pd.DataFrame(
        {
            "rv": g["r2"].sum(min_count=1),
            "bv": (np.pi / 2.0) * g["bp"].sum(min_count=1),
            "rq": (n_ret / 3.0) * g["r4"].sum(min_count=1),
            "n_bars": g["r2"].size(),
            "quote_volume": g["quote_volume"].sum(),
            "taker_buy_quote_volume": g["taker_buy_quote_volume"].sum(),
            "n_trades": g["n_trades"].sum(),
            "park": (np.log(g["high"].max() / g["low"].min()) ** 2) / (4.0 * np.log(2.0)),
            "ret": g["r"].sum(min_count=1),
        }
    )
    out.index.name = "ts"

    # first period has no return seed
    out = out.iloc[1:]

    incomplete = out["n_bars"] < _FLOOR_FRAC * expected
    out.loc[incomplete, "rv"] = np.nan
    return out

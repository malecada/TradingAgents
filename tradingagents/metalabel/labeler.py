"""Triple-barrier labels (AFML ch.3) + average-uniqueness weights (AFML §4.5).

Causality: sigma from closes <= entry-signal bar t; entry executes at Open
of bar t+1; barriers scanned from bar t+1 onward with SL-before-PT on
same-bar double touches (conservative, matches live STOP_MARKET behavior).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

PT_MULT = 2.0
SL_MULT = 1.5
VERTICAL_BARS = 15
SIGMA_SPAN = 20


def triple_barrier_labels(
    ohlcv: pd.DataFrame,
    events: pd.DatetimeIndex,
    pt_mult: float = PT_MULT,
    sl_mult: float = SL_MULT,
    vertical_bars: int = VERTICAL_BARS,
    sigma_span: int = SIGMA_SPAN,
) -> pd.DataFrame:
    df = ohlcv.set_index(pd.DatetimeIndex(ohlcv["Date"]))
    close = df["Close"].astype(float)
    sigma_series = np.log(close).diff().ewm(span=sigma_span).std()

    rows = []
    positions = {d: i for i, d in enumerate(df.index)}
    for t in events:
        i = positions.get(t)
        if i is None or i + 1 >= len(df):
            continue
        j_entry = i + 1
        j_vert = j_entry + vertical_bars
        if j_vert >= len(df):
            continue  # vertical window off the end of data
        sigma = float(sigma_series.iloc[i])
        if not np.isfinite(sigma) or sigma <= 0:
            continue
        entry_px = float(df["Open"].iloc[j_entry])
        pt_px = entry_px * (1.0 + pt_mult * sigma)
        sl_px = entry_px * (1.0 - sl_mult * sigma)

        touch_type, j_touch = "vertical", j_vert
        for j in range(j_entry, j_vert + 1):
            lo, hi = float(df["Low"].iloc[j]), float(df["High"].iloc[j])
            if lo <= sl_px:          # SL checked first (conservative)
                touch_type, j_touch = "sl", j
                break
            if hi >= pt_px:
                touch_type, j_touch = "pt", j
                break

        if touch_type == "pt":
            exit_px, label = pt_px, 1
        elif touch_type == "sl":
            exit_px, label = sl_px, 0
        else:
            exit_px = float(df["Close"].iloc[j_vert])
            label = int(exit_px > entry_px)

        rows.append({
            "event_date": t,
            "entry_exec_date": df.index[j_entry],
            "entry_px": entry_px,
            "sigma": sigma,
            "pt_px": pt_px,
            "sl_px": sl_px,
            "touch_date": df.index[j_touch],
            "touch_type": touch_type,
            "label": label,
            "ret": float(np.log(exit_px / entry_px)),
        })

    out = pd.DataFrame(rows)
    if len(out):
        out = out.set_index("event_date")
    return out


def uniqueness_weights(
    labels: pd.DataFrame, bar_index: pd.DatetimeIndex
) -> pd.Series:
    """Average uniqueness: weight_i = mean over lifespan bars of 1/concurrency."""
    if not len(labels):
        return pd.Series(dtype=float)
    conc = pd.Series(0.0, index=bar_index)
    spans = {}
    for ev, row in labels.iterrows():
        mask = (bar_index >= row["entry_exec_date"]) & (bar_index <= row["touch_date"])
        conc[mask] += 1.0
        spans[ev] = mask
    w = {}
    for ev, mask in spans.items():
        w[ev] = float((1.0 / conc[mask]).mean()) if mask.any() else 1.0
    return pd.Series(w, name="weight").reindex(labels.index)

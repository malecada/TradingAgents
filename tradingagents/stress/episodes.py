"""Mechanical crash-episode catalog — rule frozen in gates.json['stress_ews']['episode_rule']."""
import numpy as np
import pandas as pd


def build_episodes(
    close: pd.Series, drop: float = 0.15, horizon: int = 10, merge_gap: int = 10
) -> pd.DataFrame:
    close = close.dropna().sort_index()
    fwd = np.log(close.shift(-horizon) / close)
    crash = fwd <= np.log(1.0 - drop)
    rows = []
    in_ep = False
    start = end = None
    gap = 0
    for ts, is_crash in crash.items():
        if is_crash:
            if not in_ep:
                in_ep, start = True, ts
            end, gap = ts, 0
        elif in_ep:
            gap += 1
            if gap >= merge_gap:
                rows.append((start, end))
                in_ep = False
    if in_ep:
        rows.append((start, end))
    return pd.DataFrame(
        [
            {"start": s, "end": e, "trough_ret": float(fwd.loc[s:e].min())}
            for s, e in rows
        ],
        columns=["start", "end", "trough_ret"],
    )

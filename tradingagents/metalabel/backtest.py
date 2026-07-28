"""Meta-filtered replay of the trend primary. Both arms share every
convention (execution t+1 open, barrier exits, vol targeting, costs);
the ONLY difference is the per-event size multiplier from p-hat.

G2 (economic do-no-harm, gates.json): meta_sr >= primary_sr AND
p_pos >= 0.90 AND meta_dd <= 1.1 * primary_dd, where p_pos is the
paired-bootstrap probability that the meta arm's Sharpe exceeds the
primary arm's. `paired_bootstrap(a, b)` (tradingagents/rebuild/compare.py)
follows the codebase-wide convention a=baseline/incumbent, b=candidate/arm,
with p_pos = P(SR(b) > SR(a)) — see tests/rebuild/test_compare.py
(test_clearly_better_arm_wins passes the *better* series as `b`). So the
G2 call here is paired_bootstrap(primary, meta), NOT (meta, primary).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from tradingagents.rebuild.compare import paired_bootstrap

ANN = 365.0


def size_multiplier(p: float, tau: float) -> float:
    if p < tau:
        return 0.0
    return float(np.clip((p - tau) / (0.7 - tau), 0.25, 1.0))


def replay_coin(
    ohlcv: pd.DataFrame,
    votes: pd.Series,
    labels: pd.DataFrame,
    event_p: pd.Series | None,
    tau: float,
    cost_bps_rt: float = 10.0,
    vol_target: float = 0.30,
) -> pd.Series:
    df = ohlcv.set_index(pd.DatetimeIndex(ohlcv["Date"]))
    open_ = df["Open"].astype(float)
    close = df["Close"].astype(float)
    prev_close = close.shift(1)
    rets = pd.Series(0.0, index=df.index)
    half_cost = cost_bps_rt / 2.0 / 1e4

    for ev, row in labels.iterrows():
        if event_p is None:
            mult = 1.0
        else:
            if ev not in event_p.index:
                continue
            mult = size_multiplier(float(event_p.loc[ev]), tau)
        if mult <= 0.0:
            continue

        sigma = float(row["sigma"])
        if not np.isfinite(sigma) or sigma <= 0:
            continue
        weight = mult * min(1.0, vol_target / (sigma * np.sqrt(ANN)))
        if weight <= 0.0:
            continue

        entry, touch = row["entry_exec_date"], row["touch_date"]
        if entry not in df.index or touch not in df.index:
            continue
        orig_touch_type = row["touch_type"]

        # Earliest exit: barrier touch (labeler-determined) OR the first
        # bar strictly after entry where the vote drops to <= 0.5.
        window = votes.loc[entry:touch]
        weak = window[(window.index > entry) & (window <= 0.5)]
        if len(weak) and weak.index[0] < touch:
            exit_date = weak.index[0]
            is_barrier_exit = False
        else:
            exit_date = touch
            is_barrier_exit = orig_touch_type in ("pt", "sl")

        if is_barrier_exit:
            exit_px = float(row["pt_px"] if orig_touch_type == "pt" else row["sl_px"])
        else:
            exit_px = float(close.loc[exit_date])

        if exit_date == entry:
            rets.loc[entry] += weight * float(np.log(exit_px / open_.loc[entry]))
        else:
            # entry bar: open -> close
            rets.loc[entry] += weight * float(np.log(close.loc[entry] / open_.loc[entry]))
            # full close-to-close bars strictly between entry and exit
            mid = df.index[(df.index > entry) & (df.index < exit_date)]
            if len(mid):
                rets.loc[mid] += weight * np.log(close.loc[mid] / prev_close.loc[mid]).values
            # exit bar: prior close -> exit price (barrier price or close)
            rets.loc[exit_date] += weight * float(np.log(exit_px / prev_close.loc[exit_date]))

        rets.loc[entry] -= half_cost * weight
        rets.loc[exit_date] -= half_cost * weight

    return rets


def portfolio_returns(per_coin_rets: dict[str, pd.Series]) -> pd.Series:
    frame = pd.concat(per_coin_rets, axis=1).fillna(0.0)
    return frame.mean(axis=1)


def sharpe(rets: pd.Series) -> float:
    x = rets.dropna()
    if len(x) < 2 or float(x.std()) == 0.0:
        return 0.0
    return float(x.mean() / x.std() * np.sqrt(ANN))


def max_drawdown(rets: pd.Series) -> float:
    eq = rets.fillna(0.0).cumsum()
    dd = eq - eq.cummax()
    return float(-(np.exp(dd.min()) - 1.0))


def evaluate_g2(primary: pd.Series, meta: pd.Series) -> dict:
    boot = paired_bootstrap(primary, meta)  # a=primary(baseline), b=meta(candidate)
    p_sr, m_sr = sharpe(primary), sharpe(meta)
    p_dd, m_dd = max_drawdown(primary), max_drawdown(meta)
    out = {
        "primary_sr": p_sr, "meta_sr": m_sr, "delta_sr": m_sr - p_sr,
        "primary_dd": p_dd, "meta_dd": m_dd,
        "p_pos": boot["p_pos"],
    }
    out["g2_pass"] = bool(
        m_sr >= p_sr and out["p_pos"] >= 0.90 and m_dd <= 1.1 * p_dd
    )
    return out

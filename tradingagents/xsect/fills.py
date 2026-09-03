"""exec_pf — conservative passive (maker) fill model as an execution overlay on
an hourly weight path. Frozen mechanics: docs/superpowers/specs/2026-09-03-exec-pf-charter.md,
gates.json["exec_pf"].

Conventions (identical to the parent engines): W.iloc[i] is the weight held
DURING bar i, decided at the close of bar i-1; simple returns at every PnL
step; missing prices contribute 0 return (parent fillna(0)); cost is charged
on |dW|; daily aggregation by UTC day; rf accrues on every calendar day.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TICK_EPS = 1e-6   # in tick units, absorbs float dust in rounding / comparisons


# ── ticks and quotes ──────────────────────────────────────────────────────────

def infer_tick(prices: np.ndarray) -> float:
    """Minimum positive gap between sorted distinct prices (NaN if < 2 prices)."""
    p = np.unique(np.asarray(prices, dtype=float))
    p = p[np.isfinite(p)]
    if len(p) < 2:
        return float("nan")
    d = np.diff(p)
    d = d[d > 1e-12]
    return float(round(float(d.min()), 10)) if len(d) else float("nan")


def round_to_tick(x: float, tick: float, direction: str) -> float:
    q = x / tick
    n = np.floor(q + TICK_EPS) if direction == "down" else np.ceil(q - TICK_EPS)
    return float(round(n * tick, 12))


def limit_price(close: float, s_rel: float, tick: float, side: str) -> float:
    """Passive limit: join the proxied best quote. spread = max(tick, s_rel*close);
    buy = close - spread/2 rounded DOWN; sell = close + spread/2 rounded UP."""
    spread = max(tick, s_rel * close)
    if side == "buy":
        return round_to_tick(close - spread / 2.0, tick, "down")
    return round_to_tick(close + spread / 2.0, tick, "up")


def _limits_vec(close: np.ndarray, s_rel: np.ndarray, tick: np.ndarray):
    spread = np.maximum(tick, s_rel * close)
    lb = np.floor((close - spread / 2.0) / tick + TICK_EPS) * tick
    ls = np.ceil((close + spread / 2.0) / tick - TICK_EPS) * tick
    return lb, ls, spread


# ── 1-minute -> hourly execution aggregates ───────────────────────────────────

def tick_by_month(df_1m: pd.DataFrame) -> pd.Series:
    """Inferred tick per calendar month from all OHLC prices of the month."""
    month = df_1m.index.tz_convert("UTC").tz_localize(None).to_period("M")
    out = {}
    for m, g in df_1m.groupby(month):
        out[m] = infer_tick(g[["open", "high", "low", "close"]].to_numpy().ravel())
    return pd.Series(out, dtype=float)


def hourly_exec_aggregates(df_1m: pd.DataFrame) -> pd.DataFrame:
    """Per hour (open-time stamp): minlow_ex0 / maxhigh_ex0 over minutes 1..59
    (minute 0 excluded = order latency), n_min present, close_1m (last minute
    close), tick (inferred per month)."""
    idx = df_1m.index
    hour = idx.floor("h")
    minute = ((idx - hour) / pd.Timedelta(minutes=1)).astype(int)
    ex0 = minute >= 1
    g_all = df_1m.groupby(hour)
    out = pd.DataFrame(index=g_all.size().index.rename("ts"))
    out["minlow_ex0"] = df_1m.loc[ex0, "low"].groupby(hour[ex0]).min()
    out["maxhigh_ex0"] = df_1m.loc[ex0, "high"].groupby(hour[ex0]).max()
    out["n_min"] = g_all.size().astype(int)
    out["close_1m"] = g_all["close"].last()
    tbm = tick_by_month(df_1m)
    mon = out.index.tz_convert("UTC").tz_localize(None).to_period("M")
    out["tick"] = np.array([tbm.get(m, np.nan) for m in mon], dtype=float)
    return out


def first_cross_minute(df_1m: pd.DataFrame, bar_ts: pd.Timestamp, side: str,
                       threshold: float) -> int | None:
    """First minute m in 1..59 of the bar starting at bar_ts whose low <= threshold
    (buy) / high >= threshold (sell); None if never."""
    lo = bar_ts + pd.Timedelta(minutes=1)
    hi = bar_ts + pd.Timedelta(minutes=59)
    seg = df_1m.loc[lo:hi]
    if seg.empty:
        return None
    hit = seg["low"] <= threshold if side == "buy" else seg["high"] >= threshold
    if not hit.any():
        return None
    t = seg.index[np.argmax(hit.to_numpy())]
    return int((t - bar_ts) / pd.Timedelta(minutes=1))


# ── overlay ───────────────────────────────────────────────────────────────────

def _seg(a: np.ndarray, b: np.ndarray, log_booking: bool) -> np.ndarray:
    with np.errstate(invalid="ignore", divide="ignore"):
        r = np.log(b / a) if log_booking else b / a - 1.0
    return np.where(np.isfinite(r), r, 0.0)


def passive_overlay(W: pd.DataFrame, C: pd.DataFrame, ML: pd.DataFrame, MH: pd.DataFrame,
                    T: pd.DataFrame, s_rel: dict, policy: str = "LTM", maker_bp: float = 2.0,
                    taker_bp: float = 5.0, parent_cost_bp: float | None = None,
                    through_ticks: int = 1, log_booking: bool = False,
                    rf_annual: float = 0.0) -> dict:
    """Execute the parent weight path W through the frozen fill model.

    W, C (1h close), ML/MH (min low / max high over minutes 1..59 of the bar),
    T (tick) share index (hourly, bar open time) and columns. policy in
    {"LTM", "LOC", "taker"}. Returns hourly gross/cost Series, hourly_net,
    daily_net (rf subtracted), orders table, fill_rate (filled |dW| notional /
    parent-intended |dW| notional), n_orders.
    """
    if policy not in ("LTM", "LOC", "taker"):
        raise ValueError(policy)
    cols = list(W.columns)
    Wv = W.to_numpy(dtype=float)
    Cv = C.reindex(index=W.index, columns=cols).to_numpy(dtype=float)
    MLv = ML.reindex(index=W.index, columns=cols).to_numpy(dtype=float)
    MHv = MH.reindex(index=W.index, columns=cols).to_numpy(dtype=float)
    Tv = T.reindex(index=W.index, columns=cols).to_numpy(dtype=float)
    Sv = np.array([float(s_rel.get(c, 0.0)) for c in cols])
    n, k = Wv.shape
    gross = np.zeros((n, k))
    cost = np.zeros((n, k))
    rate0 = (parent_cost_bp if policy == "taker" else taker_bp) / 1e4
    cost[0] = rate0 * np.abs(Wv[0])
    intended = float(np.abs(np.diff(Wv, axis=0)).sum() + np.abs(Wv[0]).sum())
    orders: list[dict] = []
    eps_t = TICK_EPS * np.nan_to_num(Tv[1:], nan=0.0)

    if policy in ("LTM", "taker"):
        Wold, Wnew = Wv[:-1], Wv[1:]
        Cb, Cn = Cv[:-1], Cv[1:]
        dW = Wnew - Wold
        tick = Tv[1:]
        buy, sell = dW > 0, dW < 0
        has = buy | sell
        if policy == "taker":
            L = np.where(has, Cb, np.nan)
            filled = has.copy()
            cost[1:] = parent_cost_bp / 1e4 * np.abs(dW)
        else:
            lb, ls, _ = _limits_vec(Cb, Sv[None, :], tick)
            with np.errstate(invalid="ignore"):
                fb = buy & (MLv[1:] <= lb - through_ticks * tick + eps_t)
                fs = sell & (MHv[1:] >= ls + through_ticks * tick - eps_t)
            filled = fb | fs
            L = np.where(fb, lb, np.where(fs, ls, np.nan))
            half_n = np.maximum(tick, Sv[None, :] * Cn) / 2.0
            with np.errstate(invalid="ignore", divide="ignore"):
                half_rel = np.where(np.isfinite(half_n / Cn), half_n / Cn, Sv[None, :] / 2.0)
            unf = has & ~filled
            cost[1:] = np.where(filled, maker_bp / 1e4 * np.abs(dW), 0.0) \
                + np.where(unf, (taker_bp / 1e4 + half_rel) * np.abs(dW), 0.0)
        seg_full = _seg(Cb, Cn, log_booking)
        seg_a = _seg(Cb, L, log_booking)
        seg_b = _seg(L, Cn, log_booking)
        g = np.where(~has, Wnew * seg_full,
                     np.where(filled, Wold * seg_a + Wnew * seg_b, Wold * seg_full))
        gross[1:] = g
        filled_notional = float(np.abs(dW[filled]).sum()) if policy == "LTM" else float(np.abs(dW[has]).sum())
        bi, bj = np.nonzero(has)
        for i, j in zip(bi, bj):
            orders.append({"ts_place": W.index[i], "ts_bar": W.index[i + 1], "symbol": cols[j],
                           "side": "buy" if dW[i, j] > 0 else "sell", "dw": float(dW[i, j]),
                           "close_b": float(Cb[i, j]), "limit": float(L[i, j]) if np.isfinite(L[i, j]) else np.nan,
                           "filled": bool(filled[i, j]),
                           "fill_price": float(L[i, j]) if filled[i, j] else np.nan,
                           "close_n": float(Cn[i, j])})
    else:  # LOC: sequential per symbol
        filled_notional = 0.0
        for j in range(k):
            pos = Wv[0, j]
            for b in range(n - 1):
                target = Wv[b + 1, j]
                cb, cn, tick = Cv[b, j], Cv[b + 1, j], Tv[b + 1, j]
                if target == pos:
                    gross[b + 1, j] = pos * _seg(cb, cn, log_booking)
                    continue
                d = target - pos
                lb, ls, _ = _limits_vec(np.array([cb]), np.array([Sv[j]]), np.array([tick]))
                if d > 0:
                    L = float(lb[0])
                    fl = bool(np.isfinite(MLv[b + 1, j]) and MLv[b + 1, j] <= L - through_ticks * tick + TICK_EPS * tick)
                else:
                    L = float(ls[0])
                    fl = bool(np.isfinite(MHv[b + 1, j]) and MHv[b + 1, j] >= L + through_ticks * tick - TICK_EPS * tick)
                rec = {"ts_place": W.index[b], "ts_bar": W.index[b + 1], "symbol": cols[j],
                       "side": "buy" if d > 0 else "sell", "dw": float(d), "close_b": float(cb),
                       "limit": L, "filled": fl, "fill_price": L if fl else np.nan, "close_n": float(cn)}
                if fl:
                    gross[b + 1, j] = pos * _seg(cb, L, log_booking) + target * _seg(L, cn, log_booking)
                    cost[b + 1, j] = maker_bp / 1e4 * abs(d)
                    filled_notional += abs(d)
                    pos = target
                elif d < 0:   # reductions/exits: limit then market at bar end
                    gross[b + 1, j] = pos * _seg(cb, cn, log_booking)
                    half_n = max(tick, Sv[j] * cn) / 2.0
                    half_rel = half_n / cn if np.isfinite(cn) and cn > 0 else Sv[j] / 2.0
                    cost[b + 1, j] = (taker_bp / 1e4 + half_rel) * abs(d)
                    pos = target
                else:         # entry/increase unfilled: stay, re-place next boundary
                    gross[b + 1, j] = pos * _seg(cb, cn, log_booking)
                orders.append(rec)

    gross_s = pd.Series(gross.sum(axis=1), index=W.index)
    cost_s = pd.Series(cost.sum(axis=1), index=W.index)
    hourly = gross_s - cost_s
    daily = hourly.groupby(hourly.index.tz_convert("UTC").normalize()).sum()
    daily = daily.asfreq("D", fill_value=0.0)
    rf_d = (1 + rf_annual) ** (1 / 365) - 1
    daily_net = daily - rf_d
    cols_o = ["ts_place", "ts_bar", "symbol", "side", "dw", "close_b", "limit", "filled", "fill_price", "close_n"]
    orders_df = pd.DataFrame(orders, columns=cols_o)
    return {"gross": gross_s, "cost": cost_s, "hourly_net": hourly, "daily_net": daily_net,
            "orders": orders_df, "fill_rate": (filled_notional / intended) if intended > 0 else float("nan"),
            "n_orders": int(len(orders_df)), "gross_panel": pd.DataFrame(gross, index=W.index, columns=cols)}


# ── aggTrades helpers (P0 calibration) ────────────────────────────────────────

def estimate_spread_rel(trades: pd.DataFrame) -> float:
    """Median over minutes (with both sides printed) of
    (median ask-side print - median bid-side print) / mid.
    Bid-side print = is_buyer_maker True (seller aggressed into the bid)."""
    minute = trades["ts"].dt.floor("min")
    bid = trades.loc[trades["is_buyer_maker"], "price"].groupby(minute[trades["is_buyer_maker"]]).median()
    ask = trades.loc[~trades["is_buyer_maker"], "price"].groupby(minute[~trades["is_buyer_maker"]]).median()
    both = pd.concat([bid.rename("bid"), ask.rename("ask")], axis=1).dropna()
    if both.empty:
        return float("nan")
    s = (both["ask"] - both["bid"]) / ((both["ask"] + both["bid"]) / 2.0)
    return float(s.median())


def tick_level_fill(trades: pd.DataFrame, t_place: pd.Timestamp, side: str, tick: float,
                    latency_s: float = 60.0, through_ticks: int = 1,
                    horizon: pd.Timedelta = pd.Timedelta(hours=1)) -> dict:
    """Tick-level truth: quote = last same-side print at or before t_place
    (bid for a buy, ask for a sell); the limit joins the quote; fill = first
    print strictly beyond the limit by >= through_ticks, at ts >= t_place + latency
    and < t_place + horizon."""
    is_bid = trades["is_buyer_maker"].to_numpy()
    ts = trades["ts"].dt.tz_convert("UTC").astype("int64").to_numpy()
    px = trades["price"].to_numpy(dtype=float)
    side_mask = is_bid if side == "buy" else ~is_bid
    tp = int(pd.Timestamp(t_place).tz_convert("UTC").value)
    before = side_mask & (ts <= tp)
    if not before.any():
        return {"quote": np.nan, "limit": np.nan, "filled": False, "fill_ts": None}
    quote = float(px[np.nonzero(before)[0][-1]])
    L = quote
    t0 = tp + int(latency_s * 1e9)
    t1 = tp + int(horizon.value)
    win = (ts >= t0) & (ts < t1)
    eps = TICK_EPS * tick
    if side == "buy":
        hit = win & (px <= L - through_ticks * tick + eps)
    else:
        hit = win & (px >= L + through_ticks * tick - eps)
    if not hit.any():
        return {"quote": quote, "limit": L, "filled": False, "fill_ts": None}
    i = int(np.nonzero(hit)[0][0])
    return {"quote": quote, "limit": L, "filled": True, "fill_ts": pd.Timestamp(int(ts[i]), tz="UTC"),
            "fill_price": L}

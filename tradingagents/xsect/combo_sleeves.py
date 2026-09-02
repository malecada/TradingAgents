"""combo_c1 sleeve builders — the four frozen parent engines exposed as
(weight path, return matrix, engine) triples so the combination engine can
re-price them under shifted weight paths (placebos), swapped conventions and
stressed costs without touching the parents' registered code paths.

Every builder returns a :class:`Sleeve` restricted to the evaluation window
[lo, hi]; the first row of the window starts flat (weights before ``lo`` are
never carried in). Signals (z-scores, rolling means, momentum sums) are
computed on the full loaded history BEFORE the window slice so warm-up is
intact; only the PnL rows are sliced.

Return conventions: ``R`` is SIMPLE (house PnL convention since lead-0,
2026-09-02); ``R_log`` = log1p(R) exists only for the convention-swap
kill-test.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from tradingagents.xsect.carry_xs import (
    RF_DAILY, build_funding_matrix, carry_signal, carry_weights, run_ls_portfolio,
)
from tradingagents.xsect.liq_fade import (
    cascade_triggers, event_weights_hourly, run_hourly_portfolio,
)
from tradingagents.xsect.ls_common import ls_weights, zero_funding
from tradingagents.xsect.portfolio import momentum_scores, returns_from_close
from tradingagents.xsect.trend import monthly_refresh_dates, run_daily_portfolio
from tradingagents.xsect.universe import eligibility, weekly_rebalance_dates
from tradingagents.xsect.value_xs import (
    load_fundamentals, membership_mask, simple_returns, value_ratio, zscore_signal,
)

RF_ANNUAL = 0.045
COST_BPS = 10.0

# frozen parent configs (LEADS_SCOPE_2026-09-02 Lead 1 / charter table)
CFG = {
    "liq_fade": {"thr": 3.5, "H": 48, "w_per": 0.1, "cap": 1.0, "top_n": 50,
                 "z_window": 2160, "z_min_periods": 1440},
    "carry": {"L": 30, "leg_frac": 0.2, "top_n": 50},
    "momentum": {"L": 28, "skip": 0, "K": 10, "top_n": 100},
    "value": {"metric": "nvt_proxy", "leg_frac": 1 / 3, "lag_days": 2,
              "liquidity_floor_rank": 150},
}
SLEEVE_IDS = ("liq_fade", "carry", "momentum", "value")


@dataclass
class Sleeve:
    sid: str
    W: pd.DataFrame            # weight path on the window rows
    R: pd.DataFrame            # simple returns, same shape
    R_log: pd.DataFrame        # log returns, same shape (swap test only)
    F: pd.DataFrame | None     # funding (carry) or None
    engine: str                # "daily_long" | "daily_ls" | "hourly"
    first_active: pd.Timestamp  # series is reported from the bar AFTER this
    cost_bps: float = COST_BPS
    meta: dict | None = None


def sleeve_net(s: Sleeve, W: pd.DataFrame | None = None, cost_bps: float | None = None,
               convention: str = "simple") -> pd.Series:
    """Daily net return series of the sleeve under (optionally) a shifted
    weight path, a different cost, or the log convention."""
    W = s.W if W is None else W
    cost = s.cost_bps if cost_bps is None else cost_bps
    R = s.R if convention == "simple" else s.R_log
    if s.engine == "hourly":
        net = run_hourly_portfolio(W, R, cost_bps=cost, rf_annual=RF_ANNUAL)
        return net.loc[net.index > s.first_active.normalize() - pd.Timedelta(days=1)]
    if s.engine == "daily_long":
        net = run_daily_portfolio(W, R, cost_bps=cost)
    elif s.engine == "daily_ls":
        F = s.F if s.F is not None else zero_funding(W.index, W.columns)
        net = run_ls_portfolio(W, R, F, cost_bps=cost, rf_daily=RF_DAILY)
    else:
        raise ValueError(s.engine)
    return net.loc[net.index > s.first_active]


def sleeve_name_pnl(s: Sleeve) -> dict:
    """Gross per-symbol PnL (weight x return, before costs/rf) over the window."""
    Rv = np.nan_to_num(s.R.to_numpy(), nan=0.0)
    Wv = s.W.to_numpy()
    if s.engine == "hourly":
        pnl = (Wv * Rv).sum(axis=0)
    else:
        Wprev = np.vstack([np.zeros((1, Wv.shape[1])), Wv[:-1]])
        pnl = (Wprev * Rv).sum(axis=0)
    return {c: float(v) for c, v in zip(s.W.columns, pnl) if v != 0.0}


# ── S3 momentum (xs_mom_p1 L28/s0/K10) ─────────────────────────────────────

def build_momentum(klines: dict, lo: pd.Timestamp, hi: pd.Timestamp, cfg: dict | None = None) -> Sleeve:
    cfg = cfg or CFG["momentum"]
    reb = weekly_rebalance_dates(str(lo.date()), str(hi.date()))
    all_days = pd.DatetimeIndex(sorted(set().union(*[df.index for df in klines.values()])))
    days = all_days[(all_days >= lo) & (all_days <= hi)]
    members = {}
    for t in reb:
        elig = eligibility(klines, t, top_n=cfg["top_n"])
        scores = momentum_scores(klines, elig, t, cfg["L"], cfg["skip"])
        members[t] = [s for s, _ in sorted(scores.items(), key=lambda kv: -kv[1])[:cfg["K"]]]
    cols = sorted(set().union(*[set(v) for v in members.values()]))
    W = pd.DataFrame(0.0, index=days, columns=cols)
    rbs = [t for t in reb if t in W.index]
    for i, t in enumerate(rbs):
        nxt = rbs[i + 1] if i + 1 < len(rbs) else None
        seg = W.loc[t:] if nxt is None else W.loc[t:nxt - pd.Timedelta(days=1)]
        if members[t]:
            W.loc[seg.index, members[t]] = 1.0 / len(members[t])
    R = pd.DataFrame({c: returns_from_close(klines[c]["close"], "simple").reindex(days) for c in cols},
                     index=days, columns=cols)
    R_log = pd.DataFrame({c: returns_from_close(klines[c]["close"], "log").reindex(days) for c in cols},
                         index=days, columns=cols)
    n_elig = {str(t.date()): len(members[t]) for t in reb}
    return Sleeve("momentum", W, R, R_log, None, "daily_long", first_active=reb[0],
                  meta={"rebalances": len(reb), "n_members": n_elig})


# ── S2 carry (carry_xs_t1 L30/leg0.2) ──────────────────────────────────────

def build_carry(klines: dict, fund_dir: Path, lo: pd.Timestamp, hi: pd.Timestamp,
                cfg: dict | None = None) -> Sleeve:
    cfg = cfg or CFG["carry"]
    refresh = monthly_refresh_dates(str(lo.date()), str(hi.date()))
    members = {d: eligibility(klines, d, top_n=cfg["top_n"]) for d in refresh}
    union = sorted(set().union(*[set(v) for v in members.values()]))
    cdays = pd.DatetimeIndex(sorted(set().union(*[klines[s].index for s in union])))
    R_log = pd.DataFrame(index=cdays, columns=union, dtype=float)
    for s in union:
        R_log[s] = np.log(klines[s]["close"]).diff().reindex(cdays)
    funding = {s: pd.read_parquet(Path(fund_dir) / f"{s}.parquet")
               for s in union if (Path(fund_dir) / f"{s}.parquet").exists()}
    F = build_funding_matrix(funding, cdays, union)
    S = carry_signal(F, cfg["L"])
    W = carry_weights(cdays, S, F, members, cfg["leg_frac"])
    rows = (cdays >= lo) & (cdays <= hi)
    Ws, Fs, RLs = W.loc[rows], F.loc[rows], R_log.loc[rows]
    n_valid = {str(d.date()): len(members[d]) for d in refresh}
    return Sleeve("carry", Ws, np.expm1(RLs), RLs, Fs, "daily_ls", first_active=refresh[0],
                  meta={"refreshes": len(refresh), "n_members": n_valid,
                        "funding_files": len(funding)})


# ── S4 value (value_xs_t1 nvt_proxy tercile) ───────────────────────────────

def load_cm_mapping(universe_file: Path) -> dict:
    return json.loads(Path(universe_file).read_text())["mapping"]


def build_value(klines: dict, fund_dir: Path, asset_to_symbol: dict, universe: dict,
                warmup_start: str, lo: pd.Timestamp, hi: pd.Timestamp,
                cfg: dict | None = None) -> Sleeve:
    cfg = cfg or CFG["value"]
    days = pd.date_range(warmup_start, hi, freq="D", tz="UTC")
    symbols = sorted({s for v in universe.values() for s in v})
    kl = {s: d.loc[:hi] for s, d in klines.items() if s in symbols}
    fund = load_fundamentals(fund_dir, asset_to_symbol)
    fund = {s: d for s, d in fund.items() if s in symbols}
    win = days[(days >= lo) & (days <= hi)]
    R = simple_returns(kl, days, symbols).loc[win]
    M = membership_mask(days, symbols, universe).loc[win]
    S = zscore_signal(value_ratio(fund, cfg["metric"], days), cfg["lag_days"]).loc[win]
    valid = M & S.notna()
    rb = weekly_rebalance_dates(str(win[0])[:10], str(win[-1])[:10])
    W = ls_weights(win, S, valid, rb, cfg["leg_frac"])
    Rw = R.reindex_like(W)
    breadth = valid.sum(axis=1)
    return Sleeve("value", W, Rw, np.log1p(Rw), None, "daily_ls", first_active=win[0],
                  meta={"rebalances": len(rb), "breadth_median": float(breadth.median()),
                        "breadth_min": int(breadth.min()),
                        "breadth_weekly": {str(t.date()): int(breadth.loc[t]) for t in rb if t in breadth.index},
                        "n_symbols": len(symbols), "fund_symbols": len(fund)})


# ── S1 liq_fade (liq_fade_i1 thr3.5/H48) ───────────────────────────────────

def load_hourly_panel(kl1h_dir: Path, symbols: list, start: pd.Timestamp, end: pd.Timestamp):
    """1h close/quote_volume wide panels on the shared hourly grid [start, end]
    (end inclusive of its last hour). Missing bars stay NaN (not forward-filled)."""
    idx = pd.date_range(start, end, freq="h")
    close, qvol = {}, {}
    for s in symbols:
        p = Path(kl1h_dir) / f"{s}.parquet"
        if not p.exists():
            continue
        df = pd.read_parquet(p)
        df = df.loc[(df.index >= start) & (df.index <= end)]
        if df.empty:
            continue
        close[s] = df["close"]
        qvol[s] = df["quote_volume"]
    cols = sorted(close)
    C = pd.DataFrame({s: close[s].reindex(idx) for s in cols}, index=idx, columns=cols)
    Q = pd.DataFrame({s: qvol[s].reindex(idx) for s in cols}, index=idx, columns=cols)
    return C, Q


def membership_mask_hourly(universe: dict, columns: list, index: pd.DatetimeIndex) -> pd.DataFrame:
    keys = sorted(universe.keys())
    starts = [pd.Timestamp(k, tz="UTC") for k in keys]
    mask = pd.DataFrame(False, index=index, columns=columns)
    for i, (k, start) in enumerate(zip(keys, starts)):
        end = starts[i + 1] if i + 1 < len(starts) else (
            index[-1] + pd.Timedelta(hours=1) if len(index) else start)
        members = [s for s in universe[k] if s in columns]
        if not members:
            continue
        sel = (index >= start) & (index < end)
        if sel.any():
            mask.loc[sel, members] = True
    return mask


def build_liq_fade(close: pd.DataFrame, qvol: pd.DataFrame, universe: dict,
                   lo: pd.Timestamp, hi: pd.Timestamp, cfg: dict | None = None) -> Sleeve:
    """`close`/`qvol` must include the z-score warm-up BEFORE `lo`."""
    cfg = cfg or CFG["liq_fade"]
    hi_h = hi + pd.Timedelta(hours=23)
    R = close.pct_change(fill_method=None)
    mask = membership_mask_hourly(universe, close.columns.tolist(), close.index)
    trig = cascade_triggers(close, qvol, thr=cfg["thr"], window=cfg["z_window"],
                            min_periods=cfg["z_min_periods"]) & mask
    rows = (close.index >= lo) & (close.index <= hi_h)
    trig_w = trig.loc[rows]
    active = trig_w.columns[trig_w.to_numpy().any(axis=0)].tolist()
    trig_a = trig_w[active]
    W = event_weights_hourly(trig_a, cfg["H"], w_per=cfg["w_per"], cap=cfg["cap"])
    Ra = R.loc[rows, active]
    return Sleeve("liq_fade", W, Ra, np.log1p(Ra), None, "hourly", first_active=lo,
                  meta={"n_events": int(trig_a.to_numpy().sum()), "n_active_symbols": len(active),
                        "n_panel_symbols": int(close.shape[1])})

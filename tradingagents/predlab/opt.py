"""Phase-O engine (registered: predlab_opt) — parameterized generalization of
the Phase-P S1 low-vol long-short. With default `OptConfig()` this engine
reproduces `pp.run_s1(..., "eq", 1, ...)` EXACTLY (pinned in tests).

Knobs (axes O1-O3 + plumbing for O4-O7):
- signal construction: `build_signal` (park_w / cc_w / vov_w / ewma_span)
- universe: `monthly_universe(top_n)` + `apply_adv_floor`
- portfolio: quantile width `q_frac`, weighting eq|rank|ivol, holding
  smoothing, rebalance cadence, turnover buffer bands
- accounting: per-name PnL attribution (single-name concentration, §50
  lesson), explicit cost column, cost-stress recomputation

Timing conventions inherited from pp.py: signal row t is pre-shifted (info
through t-1); weights formed from row t trade the day-t log return;
turnover charged on w_t - w_{t-1}; longs pay positive funding.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from tradingagents.predlab.pp import ann_sr, max_drawdown

MIN_NAMES = 25


@dataclass(frozen=True)
class OptConfig:
    signal: str = "park_5"     # informational; sig panel is built by build_signal
    top_n: int = 200           # informational; uni mask is built by callers
    adv_floor: float = 0.0
    q_frac: float = 0.2
    weighting: str = "eq"      # eq | rank | ivol
    smooth: int = 1
    cadence: int = 1           # rebalance every k traded days
    buffer: float = 0.0        # band factor: held names stay while rank <= q*(1+buffer)
    taker_bp: float = 5.0


# ------------------------------------------------------------------ signals

def build_signal(park: pd.DataFrame, close: pd.DataFrame, kind: str) -> pd.DataFrame:
    """Low-vol proxy panels, all shifted 1 day (no row-t information).

    park_w: rolling mean of daily Parkinson variance proxy
    cc_w:   rolling std of close-to-close log returns
    vov_w:  rolling std of the Parkinson proxy (vol-of-vol)
    ewma_s: EWMA of the Parkinson proxy (span=s)
    """
    fam, _, arg = kind.partition("_")
    w = int(arg)
    if fam == "park":
        return park.rolling(w).mean().shift(1)
    if fam == "cc":
        return np.log(close).diff().rolling(w).std().shift(1)
    if fam == "vov":
        return park.rolling(w).std().shift(1)
    if fam == "ewma":
        return park.ewm(span=w).mean().shift(1)
    raise ValueError(f"unknown signal kind: {kind}")


# ------------------------------------------------------------------ universe

def monthly_universe(qv: pd.DataFrame, top_n: int = 200) -> pd.DataFrame:
    """Mask (days x syms): month m membership from month m-1 median qv (PIT).
    Identical to scripts/predlab_t7.monthly_universe (parity-pinned)."""
    med = qv.resample("MS").median()
    mask_rows = {}
    months = med.index
    for i in range(1, len(months)):
        prior = med.iloc[i - 1].dropna()
        members = set(prior.nlargest(top_n).index)
        mask_rows[months[i]] = members
    mask = pd.DataFrame(False, index=qv.index, columns=qv.columns)
    for month_start, members in mask_rows.items():
        in_month = (qv.index >= month_start) & (qv.index < month_start + pd.offsets.MonthBegin(1))
        mask.loc[in_month, list(members & set(qv.columns))] = True
    return mask


def apply_adv_floor(uni: pd.DataFrame, qv: pd.DataFrame, floor: float) -> pd.DataFrame:
    """AND the universe mask with a PIT liquidity floor: month m keeps names
    whose month m-1 median daily quote volume >= floor. Months with no prior
    information (the first month) are left untouched."""
    if floor <= 0:
        return uni
    med = qv.resample("MS").median()
    out = uni.copy()
    months = med.index
    for i in range(1, len(months)):
        ok = med.iloc[i - 1] >= floor
        in_month = (uni.index >= months[i]) & (uni.index < months[i] + pd.offsets.MonthBegin(1))
        out.loc[in_month, ~ok.reindex(uni.columns, fill_value=False)] = False
    return out


# ------------------------------------------------------------------ weights

def leg_weights(sig_row: pd.Series, q_frac: float, weighting: str,
                buffer: float = 0.0, held_long: "set | None" = None,
                held_short: "set | None" = None) -> pd.Series:
    """Long bottom-signal quantile / short top-signal quantile; each leg sums
    to 1 (gross 2). With `buffer` > 0, names already held stay in their leg
    while ranked inside q*(1+buffer). weighting: eq | rank | ivol (risk
    parity: weight proportional to 1/signal within each leg)."""
    s = sig_row.dropna()
    n = len(s)
    if n < MIN_NAMES:
        return pd.Series(dtype=np.float64)
    q = max(int(np.floor(n * q_frac + 1e-9)), 1)
    order = s.sort_values()
    if buffer > 0 and (held_long or held_short):
        q_ext = max(int(np.floor(n * q_frac * (1 + buffer) + 1e-9)), q)
        lo_band = set(order.index[:q_ext])
        hi_band = set(order.index[-q_ext:])
        lo_members = list(order.index[:q]) + [
            x for x in order.index[q:q_ext]
            if x in (held_long or set()) and x in lo_band]
        hi_members = list(order.index[-q:]) + [
            x for x in order.index[-q_ext:-q]
            if x in (held_short or set()) and x in hi_band]
        lo = order.loc[[x for x in order.index if x in set(lo_members)]].index
        hi = order.loc[[x for x in order.index if x in set(hi_members)]].index
    else:
        lo, hi = order.index[:q], order.index[-q:]
    w = pd.Series(0.0, index=s.index)
    nl, nh = len(lo), len(hi)
    if weighting == "eq":
        w[lo] = 1.0 / nl
        w[hi] = -1.0 / nh
    elif weighting == "rank":
        rl = np.arange(nl, 0, -1, dtype=np.float64)
        w[lo] = rl / rl.sum()               # lowest signal = largest long
        rh = np.arange(nh, 0, -1, dtype=np.float64)
        w[hi] = -(rh / rh.sum())[::-1]      # highest signal = largest short
    elif weighting == "ivol":
        inv_lo = 1.0 / np.maximum(s[lo].to_numpy(), 1e-12)
        w[lo] = inv_lo / inv_lo.sum()
        inv_hi = 1.0 / np.maximum(s[hi].to_numpy(), 1e-12)
        w[hi] = -(inv_hi / inv_hi.sum())
    else:
        raise ValueError(f"unknown weighting: {weighting}")
    return w


# ------------------------------------------------------------------ backtest

def run_ls(sig: pd.DataFrame, ret: pd.DataFrame, uni: pd.DataFrame,
           fund_daily: "pd.DataFrame | None", cfg: OptConfig,
           start: str, end: str) -> dict:
    """Daily cross-sectional long-short generalizing pp.run_s1. Costs:
    cfg.taker_bp x turnover + funding carry (longs pay positive funding)."""
    lo_ts, hi_ts = pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC")
    sig = sig.where(uni)
    days = [d for d in ret.index if lo_ts <= d <= hi_ts]
    prev_w = pd.Series(dtype=np.float64)
    held_long: set = set()
    held_short: set = set()
    targets: "list[pd.Series]" = []
    name_pnl: "dict[str, float]" = {}
    out = []
    traded = 0
    for d in days:
        if d not in sig.index:
            continue
        rebalance = traded % cfg.cadence == 0
        if rebalance:
            w_tgt = leg_weights(sig.loc[d], cfg.q_frac, cfg.weighting,
                                cfg.buffer, held_long, held_short)
            if len(w_tgt) == 0:
                continue
            held_long = set(w_tgt.index[w_tgt > 0])
            held_short = set(w_tgt.index[w_tgt < 0])
            targets.append(w_tgt)
            if len(targets) > cfg.smooth:
                targets.pop(0)
            w = pd.concat(targets, axis=1).fillna(0.0).mean(axis=1)
        else:
            if len(prev_w) == 0:
                continue
            w = prev_w
        traded += 1
        r_row = ret.loc[d].reindex(w.index)
        contrib = (w * r_row).fillna(0.0)
        gross = float(contrib.sum())
        for sym, v in contrib[contrib != 0].items():
            name_pnl[sym] = name_pnl.get(sym, 0.0) + float(v)
        if rebalance:
            both = w.index.union(prev_w.index)
            turn = float((w.reindex(both, fill_value=0.0)
                          - prev_w.reindex(both, fill_value=0.0)).abs().sum())
        else:
            turn = 0.0
        cost = cfg.taker_bp / 1e4 * turn
        carry = 0.0
        if fund_daily is not None and d in fund_daily.index:
            f = fund_daily.loc[d].reindex(w.index).fillna(0.0)
            carry = float(-(w * f).sum())
        out.append({"date": d, "gross": gross, "net": gross - cost + carry,
                    "turnover": turn, "cost": cost, "carry": carry})
        prev_w = w
    df = pd.DataFrame(out).set_index("date")
    return {"rets": df, "sr_gross": ann_sr(df["gross"].to_numpy()),
            "sr_net": ann_sr(df["net"].to_numpy()),
            "maxdd": max_drawdown(df["net"].to_numpy()),
            "avg_turnover": float(df["turnover"].mean()),
            "n_days": int(len(df)),
            "name_pnl": pd.Series(name_pnl, dtype=np.float64).sort_values()}


def cost_stress(result: dict, mult: float = 2.0) -> pd.Series:
    """Net return series under mult x taker costs (carry unchanged)."""
    df = result["rets"]
    return df["gross"] - mult * df["cost"] + df["carry"]


# ------------------------------------------------------------------ metrics

def _window_metrics(df: pd.DataFrame, lo: str, hi: str) -> dict:
    seg = df[(df.index >= lo) & (df.index <= hi)]
    return {"sr_net": ann_sr(seg["net"].to_numpy()),
            "sr_gross": ann_sr(seg["gross"].to_numpy()),
            "maxdd": max_drawdown(seg["net"].to_numpy()) if len(seg) else 0.0,
            "avg_turnover": float(seg["turnover"].mean()) if len(seg) else 0.0,
            "n_days": int(len(seg))}


def evaluate(result: dict, design: "tuple[str, str]", validation: "tuple[str, str]",
             subperiods: "list[tuple[str, str, str]] | None" = None) -> dict:
    """Full/D/V metrics + sub-period net means + single-name concentration.

    max_name_share = max |per-name PnL| / sum |per-name PnL| (bounded [0,1]);
    the registered >50% concentration FAIL is evaluated on this measure."""
    df = result["rets"]
    ev = {"full": _window_metrics(df, str(df.index[0]), str(df.index[-1])),
          "D": _window_metrics(df, *design),
          "V": _window_metrics(df, *validation)}
    if subperiods:
        subs = {}
        for label, lo, hi in subperiods:
            seg = df["net"][(df.index >= lo) & (df.index <= hi)]
            if len(seg) >= 30:
                subs[label] = float(seg.mean())
        ev["subperiods"] = subs
    pnl = result["name_pnl"].abs()
    total = float(pnl.sum())
    ev["max_name_share"] = float(pnl.max() / total) if total > 0 else 0.0
    ev["max_name"] = str(pnl.idxmax()) if total > 0 else ""
    ev["sr_net_2x_costs"] = ann_sr(cost_stress(result, 2.0).to_numpy())
    return ev


# Phase-O registered sub-periods (spec 2026-07-31-system-optimization-design.md)
SUBPERIODS_O = [("2021-22", "2021-01-01", "2022-12-31"),
                ("2023-24", "2023-01-01", "2024-12-31"),
                ("2025H1", "2025-01-01", "2025-06-30"),
                ("2025H2+2026H1", "2025-07-01", "2026-07-01")]
DESIGN_D = ("2021-01-01", "2025-03-31")
VALIDATION_V = ("2025-04-01", "2026-07-01")

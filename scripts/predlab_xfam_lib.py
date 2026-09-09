"""Shared library for the xfam five-family hunt.

Charter: docs/superpowers/specs/2026-08-25-xfam-hunt-charter.md
Gates key: predlab_xfam (registered 2026-08-25, pre-result).

All position PnL uses simple returns (house rule). Novel engines here
(thin-panel LS, pair z-MR) are unit-tested in tests/predlab/test_xfam_lib.py
before first registered use.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from math import erf, sqrt
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MAIN_WT = ROOT.parent / "TradingAgents"  # read-only stores (1h, coinglass)
OUT_DIR = ROOT / "data" / "predlab" / "xfam"
LEDGER = ROOT / "data" / "predlab" / "trial_ledger.jsonl"

DEV = ("2021-01-01", "2025-03-31")
HOLDOUT = ("2025-04-01", "2026-07-01")
TAKER_BP = 5.0
ANN_DAYS = 365.0

# ------------------------------------------------------------------ stats


def nw_tstat(x: np.ndarray, lag: int) -> tuple[float, float, float]:
    """Mean, NW/Bartlett HAC t-stat, two-sided normal p for mean(x) != 0."""
    x = np.asarray(x, dtype=np.float64)
    x = x[~np.isnan(x)]
    n = len(x)
    if n < 10:
        return np.nan, np.nan, np.nan
    m = x.mean()
    xc = x - m
    var = float(xc @ xc) / n
    for j in range(1, min(lag, n - 1) + 1):
        w = 1.0 - j / (lag + 1.0)
        var += 2.0 * w * float(xc[j:] @ xc[:-j]) / n
    if var <= 0:
        return m, 0.0, 1.0
    t = m / np.sqrt(var / n)
    p = 2.0 * (1.0 - 0.5 * (1.0 + erf(abs(t) / sqrt(2.0))))
    return float(m), float(t), float(p)


def bh_fdr(pvals: dict[str, float], q: float = 0.10) -> set[str]:
    """Benjamini-Hochberg: returns the set of keys rejected at level q."""
    from tradingagents.predlab.rollup import bh_fdr as shared_bh
    return {k for k, passed in shared_bh(pvals, q).items() if passed}


def year_sign_consistency(series: pd.Series, years=(2021, 2022, 2023, 2024)) -> dict:
    """Per-year mean and how many of the listed years share the overall sign."""
    overall = np.sign(series.mean())
    per_year, agree = {}, 0
    for y in years:
        sub = series[series.index.year == y]
        m = float(sub.mean()) if len(sub) else np.nan
        per_year[str(y)] = m
        if not np.isnan(m) and np.sign(m) == overall:
            agree += 1
    return {"per_year": per_year, "n_agree": agree, "overall_sign": float(overall)}


def ann_sr(rets: np.ndarray, periods_per_year: float = ANN_DAYS) -> float:
    r = np.asarray(rets, dtype=np.float64)
    r = r[~np.isnan(r)]
    if len(r) == 0 or r.std(ddof=1) == 0:
        return 0.0  # house rule: SR:=0 on zero variance
    return float(r.mean() / r.std(ddof=1) * np.sqrt(periods_per_year))


def circular_shift_placebo(run_fn, sig, n_draws: int = 200, min_shift: int = 30,
                           seed: int = 7) -> list[float]:
    """Null SRs from circularly shifting the signal object (Series or DataFrame)."""
    rng = np.random.default_rng(seed)
    n = len(sig)
    out = []
    for _ in range(n_draws):
        k = int(rng.integers(min_shift, n - min_shift))
        shifted = sig.copy()
        shifted.iloc[:] = np.roll(np.asarray(sig), k, axis=0)
        out.append(run_fn(shifted))
    return out


def placebo_pvalue(real_sr: float, null_srs: list[float]) -> float:
    null = np.asarray(null_srs, dtype=np.float64)
    return float((np.sum(np.abs(null) >= abs(real_sr)) + 1) / (len(null) + 1))


# ------------------------------------------------------------------ data


def load_daily_panels() -> dict[str, pd.DataFrame]:
    import sys

    sys.path.insert(0, str(ROOT / "scripts"))
    from predlab_t7 import build_panels

    return build_panels()


def load_1h_panels(rebuild: bool = False) -> dict[str, pd.DataFrame]:
    """close + qv 1h panels from the main worktree's 333-sym store (read-only),
    cached to this worktree."""
    cache = OUT_DIR / "cache_1h"
    cache.mkdir(parents=True, exist_ok=True)
    names = ["close", "qv"]
    if not rebuild and all((cache / f"{n}.parquet").exists() for n in names):
        return {n: pd.read_parquet(cache / f"{n}.parquet") for n in names}
    closes, qvs = {}, {}
    for path in sorted((MAIN_WT / "data" / "xsect" / "klines_1h").glob("*.parquet")):
        df = pd.read_parquet(path)
        closes[path.stem] = df["close"]
        qvs[path.stem] = df["quote_volume"]
    panels = {"close": pd.DataFrame(closes), "qv": pd.DataFrame(qvs)}
    for n, p in panels.items():
        p.to_parquet(cache / f"{n}.parquet")
    return panels


def load_coinglass_ls() -> dict[str, pd.DataFrame]:
    """8-sym daily panels: ls_global ratio, ls_top_position ratio."""
    d = MAIN_WT / "data" / "derivatives_raw"
    out = {}
    for kind, col in [
        ("ls_global", "ls_global_global_account_long_short_ratio"),
        ("ls_top_position", "ls_top_position_top_position_long_short_ratio"),
    ]:
        cols = {}
        for path in sorted(d.glob(f"*_cg_{kind}.parquet")):
            sym = path.name.split("_cg_")[0]
            cols[sym] = pd.read_parquet(path)[col]
        out[kind] = pd.DataFrame(cols)
    return out


def clip_dev(obj, end: str = DEV[1]):
    hi = pd.Timestamp(end, tz="UTC")
    return obj[obj.index <= hi]


# ------------------------------------------------------------------ engines


def thin_ls_backtest(sig: pd.DataFrame, ret: pd.DataFrame, n_leg: int = 2,
                     taker_bp: float = TAKER_BP,
                     fund_daily: "pd.DataFrame | None" = None,
                     min_names: int = 4) -> pd.DataFrame:
    """Thin-panel daily LS: long n_leg highest-signal / short n_leg lowest.

    sig row t must already be PIT (shifted); it trades the day-t return.
    Each leg sums to +/-1. Costs taker_bp x turnover; longs pay positive
    funding. Returns a frame with gross/net/turnover/cost/carry per day.
    """
    from tradingagents.accounting import calendar_index, run_target_book
    clock = calendar_index(sig.index)
    targets = pd.DataFrame(np.nan,index=clock,columns=ret.columns.union(sig.columns,sort=False))
    for d in sig.index:
        s = sig.loc[d].dropna()
        if len(s) < min_names:
            continue
        order = s.sort_values()
        targets.loc[d] = 0.
        targets.loc[d,order.index[-n_leg:]] = 1./n_leg
        targets.loc[d,order.index[:n_leg]] = -1./n_leg
    return run_target_book(targets,ret.reindex(clock),funding=fund_daily,fee_rate=taker_bp/1e4)


def ar1_half_life(spread: pd.Series) -> float:
    """Half-life (trading days) from AR(1) fit of the spread."""
    s = spread.dropna()
    if len(s) < 20:
        return np.nan
    x, y = s.shift(1).dropna(), s.iloc[1:]
    x, y = x.align(y, join="inner")
    b = np.polyfit(x.to_numpy(), y.to_numpy(), 1)[0]
    if b <= 0 or b >= 1:
        return np.inf
    return float(-np.log(2) / np.log(b))


def eg_fit(log_pa: pd.Series, log_pb: pd.Series) -> tuple[float, float, pd.Series]:
    """OLS spread with the Engle-Granger (estimated residual) null distribution."""
    from statsmodels.tsa.stattools import coint
    df = pd.concat([log_pa.rename("a"), log_pb.rename("b")], axis=1).dropna()
    if len(df) < 30:
        return np.nan, np.nan, pd.Series(dtype=float)
    beta, intercept = np.polyfit(df.b, df.a, 1)
    resid = df.a - intercept - beta * df.b
    p = coint(df.a, df.b, trend="c", maxlag=10, autolag="AIC")[1]
    return float(beta), float(p), resid


def pair_zmr_backtest(log_pa: pd.Series, log_pb: pd.Series, ret_a: pd.Series,
                      ret_b: pd.Series, beta: float, trade_index: pd.DatetimeIndex,
                      z_win: int = 90, z_entry: float = 2.0, z_exit: float = 0.5,
                      z_stop: float = 4.0, max_hold: int = 20,
                      taker_bp: float = TAKER_BP) -> pd.DataFrame:
    """z-score MR on spread = log_pa - beta*log_pb, dollar-neutral unit gross.

    Rolling z stats are shift(1) (PIT). Position decided at close of day t-1
    earns day-t simple returns: +1 spread position = long a, short b (scaled
    beta on b, then legs renormed to 0.5/0.5 gross for dollar neutrality).
    Costs charged on leg turnover.
    """
    spread = (log_pa - beta * log_pb).dropna()
    mu = spread.rolling(z_win).mean().shift(1)
    sd = spread.rolling(z_win).std().shift(1)
    z = (spread - mu) / sd
    pos, hold, rows = 0, 0, []
    prev_wa = prev_wb = 0.0
    for d in trade_index:
        if d not in z.index or np.isnan(z.loc[d]):
            continue
        zt = float(z.loc[d])
        # decide position for TODAY based on yesterday's close z? charter:
        # enter when |z|>=entry; position earns from next day. Implement by
        # deciding target at d using z at d, applying to d+1 via shift below.
        if pos == 0:
            if zt >= z_entry:
                pos, hold = -1, 0  # spread rich: short a, long b
            elif zt <= -z_entry:
                pos, hold = 1, 0
        else:
            hold += 1
            if abs(zt) <= z_exit or abs(zt) >= z_stop or hold >= max_hold:
                pos = 0
        rows.append({"date": d, "pos": pos, "z": zt})
    st = pd.DataFrame(rows).set_index("date")
    # position formed at close d applies to return at d+1
    st["pos_lag"] = st["pos"].shift(1).fillna(0.0)
    out = []
    for d, r in st.iterrows():
        p = r["pos_lag"]
        wa, wb = 0.5 * p, -0.5 * p  # dollar-neutral half gross each leg
        ra = float(ret_a.get(d, np.nan))
        rb = float(ret_b.get(d, np.nan))
        if np.isnan(ra) or np.isnan(rb):
            continue
        gross = wa * ra + wb * rb
        turn = abs(wa - prev_wa) + abs(wb - prev_wb)
        cost = taker_bp / 1e4 * turn
        out.append({"date": d, "gross": gross, "net": gross - cost,
                    "turnover": turn, "cost": cost})
        prev_wa, prev_wb = wa, wb
    return pd.DataFrame(out).set_index("date") if out else pd.DataFrame(
        columns=["gross", "net", "turnover", "cost"])


# ------------------------------------------------------------------ bookkeeping


def git_commit_short() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except Exception:
        return "unknown"


def ledger_append(experiment: str, cell: str, model: str, config: dict,
                  metrics: dict, window=DEV) -> None:
    from tradingagents.predlab import registry
    registry.log_trial(experiment, cell, model, config, window, metrics)


def write_result(fam: str, payload: dict) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    p = OUT_DIR / f"{fam}_result.json"
    payload = {"ts_utc": datetime.now(timezone.utc).isoformat(),
               "git_commit": git_commit_short(), **payload}
    with p.open("x") as fh:
        fh.write(json.dumps(payload, indent=1, default=str))
    return p

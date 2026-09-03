"""exec_pf shared data layer: stores, parent weight paths, aggregates.

Every loader clips at the dev cap (2025-03-31 23:59 UTC). Nothing here reads
the sealed window.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from tradingagents.xsect.fills import hourly_exec_aggregates  # noqa: E402
from tradingagents.xsect.liq_fade import (  # noqa: E402
    cascade_triggers, event_weights_hourly, run_hourly_portfolio, sharpe_daily,
)

OUT = ROOT / "data/rebuild/exec_pf"
INPUTS = OUT / "inputs"
AGG_DIR = OUT / "agg_1h"
KL1M = ROOT / "data/xsect/klines_1m"
KL1H = ROOT / "data/xsect/klines_1h"
AGGTR = ROOT / "data/xsect/aggtrades"
SYMS_FILE = ROOT / "data/xsect/exec_pf_symbols.txt"
EVENTS_FILE = OUT / "dev_events_thr35.json"
SPREAD_FILE = OUT / "spread_model.json"

DEV = ("2021-01-01", "2025-03-31")
DEV_LO = pd.Timestamp(DEV[0], tz="UTC")
DEV_HI = pd.Timestamp(DEV[1], tz="UTC") + pd.Timedelta(hours=23)
CAP_1M = pd.Timestamp("2025-03-31 23:59", tz="UTC")
R2 = {"thr": 3.5, "H": 48, "w_per": 0.1, "cap": 1.0, "cost_bps": 10.0, "rf_annual": 0.045}
R1 = {"thresh": 0.50, "smooth": 24, "model": "logit_lags5", "cost_bps": 5.0}
FEES = {"maker_bp": 2.0, "taker_bp": 5.0, "stress_maker_bp": 3.0}


def symbols() -> list[str]:
    return [s.strip() for s in SYMS_FILE.read_text().splitlines() if s.strip()]


def load_1m(sym: str, lo=None, hi=None) -> pd.DataFrame | None:
    p = KL1M / f"{sym}.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    df = df.loc[df.index <= CAP_1M]
    if lo is not None:
        df = df.loc[df.index >= lo]
    if hi is not None:
        df = df.loc[df.index <= hi]
    return df


def build_agg(sym: str, force: bool = False) -> pd.DataFrame | None:
    AGG_DIR.mkdir(parents=True, exist_ok=True)
    p = AGG_DIR / f"{sym}.parquet"
    if p.exists() and not force:
        return pd.read_parquet(p)
    df = load_1m(sym)
    if df is None or df.empty:
        return None
    agg = hourly_exec_aggregates(df)
    agg.to_parquet(p)
    return agg


def load_agg_panel(syms: list[str], idx: pd.DatetimeIndex) -> dict:
    cols = {"minlow_ex0": {}, "maxhigh_ex0": {}, "n_min": {}, "close_1m": {}, "tick": {}}
    for s in syms:
        p = AGG_DIR / f"{s}.parquet"
        if not p.exists():
            continue
        a = pd.read_parquet(p).reindex(idx)
        for c in cols:
            cols[c][s] = a[c]
    out = {c: pd.DataFrame(v, index=idx) for c, v in cols.items()}
    for c in cols:
        out[c] = out[c].reindex(columns=syms)
    return out


# ── parent paths ─────────────────────────────────────────────────────────────

def r2_parent() -> dict:
    """Parent liq_fade_i1 thr3.5/H48 dev path on the parent 1h store (warmup 2020-06)."""
    from liq_fade_dev import (UNIVERSE_FILE, load_hourly_panel, load_symbols,
                              membership_mask_hourly)
    syms = load_symbols(False)
    close, qvol = load_hourly_panel(syms)                    # WARMUP .. DEV[1] 23:00
    uni = json.loads(UNIVERSE_FILE.read_text())
    mask = membership_mask_hourly(uni, close.columns.tolist(), close.index)
    R = close.pct_change(fill_method=None)
    row = (close.index >= DEV_LO) & (close.index <= DEV_HI)
    trig = (cascade_triggers(close, qvol, R2["thr"]) & mask).loc[row]
    active = trig.columns[trig.to_numpy().any(axis=0)].tolist()
    trig_a, R_a, mask_a, close_a = trig[active], R.loc[row, active], mask.loc[row, active], close.loc[row, active]
    W = event_weights_hourly(trig_a, R2["H"], w_per=R2["w_per"], cap=R2["cap"])
    net = run_hourly_portfolio(W, R_a, cost_bps=R2["cost_bps"], rf_annual=R2["rf_annual"])
    pin = json.loads((ROOT / "data/rebuild/liq_fade/dev_results.json").read_text())
    pin_sr = next(r["metrics"]["net_sr"] for r in pin["results"]
                  if r["config"]["thr"] == 3.5 and r["config"]["H"] == 48)
    return {"W": W, "close": close_a, "R": R_a, "trig": trig_a, "mask": mask_a,
            "parent_daily_net": net, "parent_sr": sharpe_daily(net), "pin_sr": pin_sr,
            "active": active}


def r1_parent(sym: str) -> dict:
    """R1 sign filter path: pos_t = 1{ rolling-24 mean of P(up)_t > 0.5 }, W index = bar open."""
    fc = pd.read_parquet(INPUTS / f"forecasts__predlab_p2_ml__{sym}_1h_T2_dir__logit_lags5.parquet")
    fc = fc.set_index(pd.DatetimeIndex(fc["ts"]))[["y_true", "pred"]]
    fc = fc.loc[(fc.index >= DEV_LO) & (fc.index <= DEV_HI)]
    rv = pd.read_parquet(INPUTS / f"rv_1h__{sym}.parquet")["ret"]
    common = fc.index.intersection(rv.index)
    p = fc["pred"].loc[common]
    if R1["smooth"] > 1:
        p = p.rolling(R1["smooth"], min_periods=1).mean()
    pos = (p > R1["thresh"]).astype(float)
    kl = pd.read_parquet(KL1H / f"{sym}.parquet")["close"]
    idx = common
    W = pd.DataFrame({sym: pos.to_numpy()}, index=idx)
    close = pd.DataFrame({sym: kl.reindex(idx).to_numpy()}, index=idx)
    logret = rv.loc[common]
    return {"W": W, "close": close, "logret_parent": logret, "prob": fc["pred"].loc[common],
            "y_true": fc["y_true"].loc[common], "window": [str(idx[0]), str(idx[-1])]}


def s3_parent_hourly(pos: np.ndarray, ret: np.ndarray, cost_bp: float = 5.0) -> dict:
    """Verbatim re-statement of tradingagents.predlab.pp.run_s3 arithmetic."""
    strat = pos * ret
    cost = cost_bp / 1e4 * np.abs(np.diff(pos, prepend=0.0))
    net = strat - cost
    sd = net.std(ddof=1)
    sr = float(net.mean() / sd * np.sqrt(24 * 365)) if sd > 0 else 0.0
    return {"net": net, "sr_hourly": sr}


def sharpe(x: pd.Series) -> float:
    return sharpe_daily(x)


def maxdd_simple(daily: pd.Series) -> float:
    eq = (1 + daily).cumprod()
    return float((1 - eq / eq.cummax()).max())


def yearly_sr(daily: pd.Series) -> dict:
    return {str(y): sharpe_daily(g) for y, g in daily.groupby(daily.index.year) if len(g) > 30}


def spread_model() -> dict:
    return json.loads(SPREAD_FILE.read_text())

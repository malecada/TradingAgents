"""predlab_oflow P0 — order-flow linear tests, 8 pre-named cells (charter 2026-09-04).

  nohup python scripts/predlab_oflow_p0.py > data/predlab/oflow/p0.log 2>&1 &

One-shot: refuses to run if gates.json["predlab_oflow"]["verdicts"] exists.
Writes data/predlab/oflow/p0_result.json, one ledger row per cell, and the
verdict string back into the gates entry.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from predlab_xfam_lib import (  # noqa: E402
    DEV, MAIN_WT, bh_fdr, clip_dev, ledger_append, load_daily_panels,
)
from tradingagents.predlab import registry  # noqa: E402
from tradingagents.predlab.opt import monthly_universe  # noqa: E402
from tradingagents.predlab.xsec import daily_ic, ic_summary  # noqa: E402

OUT = ROOT / "data" / "predlab" / "oflow"
CACHE = OUT / "cache_1h"
KEY = "predlab_oflow"
CELLS = ["TS_1h_BTC", "TS_1h_ETH", "TS_24h_BTC", "TS_24h_ETH", "TS_5m1h_BTC", "TS_5m1h_ETH", "XS_24h_IC", "XS_7d_IC"]
FLOOR = {"ts_p": 0.01, "ts_years": 3, "xs_abs_ic": 0.02, "xs_nw_t": 3.0, "xs_subperiods": 2}
MIN_BREADTH = 25
SUBS = [("2021-2022", "2021-01-01", "2022-12-31"), ("2023-2024", "2023-01-01", "2024-12-31"), ("2025Q1", "2025-01-01", "2025-03-31")]
DEV_LO, DEV_HI = pd.Timestamp(DEV[0], tz="UTC"), pd.Timestamp(DEV[1], tz="UTC") + pd.Timedelta(hours=23)


def load_1h() -> dict[str, pd.DataFrame]:
    CACHE.mkdir(parents=True, exist_ok=True)
    names = ["close", "qv", "tb"]
    if all((CACHE / f"{n}.parquet").exists() for n in names):
        return {n: pd.read_parquet(CACHE / f"{n}.parquet") for n in names}
    cols = {n: {} for n in names}
    for p in sorted((MAIN_WT / "data" / "xsect" / "klines_1h").glob("*.parquet")):
        df = pd.read_parquet(p)
        df = df.loc[df.index <= DEV_HI]           # dev cap
        cols["close"][p.stem] = df["close"]
        cols["qv"][p.stem] = df["quote_volume"]
        cols["tb"][p.stem] = df["taker_buy_quote_volume"]
    panels = {n: pd.DataFrame(v) for n, v in cols.items()}
    for n, p in panels.items():
        p.to_parquet(CACHE / f"{n}.parquet")
    return panels


def imbalance(tb: pd.Series | pd.DataFrame, qv: pd.Series | pd.DataFrame):
    with np.errstate(invalid="ignore", divide="ignore"):
        imb = (2 * tb - qv) / qv
    return imb.where(qv > 0)


def zscore(x, window: int):
    mu = x.rolling(window, min_periods=window // 2).mean()
    sd = x.rolling(window, min_periods=window // 2).std(ddof=1)
    return (x - mu) / sd.replace(0.0, np.nan)


def hac_predictive(x: pd.Series, y_next: pd.Series, lag: int) -> dict:
    """OLS y_next ~ x (both already aligned so that y_next is the NEXT bar's return), HAC lag."""
    import statsmodels.api as sm
    df = pd.concat({"y": y_next, "x": x}, axis=1).dropna()
    df = df[(df.index >= DEV_LO) & (df.index <= DEV_HI)]
    X = sm.add_constant(df["x"])
    res = sm.OLS(df["y"], X).fit(cov_type="HAC", cov_kwds={"maxlags": lag})
    slope, t, p = float(res.params["x"]), float(res.tvalues["x"]), float(res.pvalues["x"])
    yearly = {}
    for yr in (2021, 2022, 2023, 2024):
        sub = df[df.index.year == yr]
        if len(sub) > 50:
            yearly[str(yr)] = float(np.polyfit(sub["x"], sub["y"], 1)[0])
    agree = sum(1 for v in yearly.values() if np.sign(v) == np.sign(slope))
    e_abs_z = float(df["x"].abs().mean())
    return {"slope": slope, "t": t, "p": p, "n": int(len(df)), "yearly_slopes": yearly, "n_year_agree": agree,
            "mean_abs_z": e_abs_z, "implied_effect_bp_per_bar": abs(slope) * e_abs_z * 1e4,
            "window": [str(df.index.min()), str(df.index.max())]}


def ts_cells(p1h: dict) -> dict:
    out = {}
    for sym in ("BTCUSDT", "ETHUSDT"):
        c, q, tb = p1h["close"][sym], p1h["qv"][sym], p1h["tb"][sym]
        r = c.pct_change(fill_method=None)
        # 1h: z_t from bars <= t predicts r_{t+1}
        z = zscore(imbalance(tb, q), 720)
        out[f"TS_1h_{sym[:3]}"] = hac_predictive(z, r.shift(-1), lag=24)
        # 24h: daily imbalance from 1h sums; next-day return of the daily close (23:00 bar close)
        day = c.index.tz_convert("UTC").normalize()
        tb_d, q_d = tb.groupby(day).sum(), q.groupby(day).sum()
        imb_d = imbalance(tb_d, q_d)
        c_d = c.groupby(day).last()
        r_d = c_d.pct_change(fill_method=None)
        z_d = zscore(imb_d, 30)
        out[f"TS_24h_{sym[:3]}"] = hac_predictive(z_d, r_d.shift(-1), lag=5)
        # 5m -> 1h: last 5-minute bar of hour t
        k5 = pd.read_parquet(ROOT / "data" / "predlab" / "klines_5m" / f"{sym}.parquet")
        k5 = k5.loc[k5.index <= DEV_HI]
        imb5 = imbalance(k5["taker_buy_quote_volume"], k5["quote_volume"])
        z5 = zscore(imb5, 8640)
        last5 = z5[z5.index.minute == 55]
        last5.index = last5.index.floor("h")            # stamp = hour t (bar [t+55, t+60) is inside hour t)
        out[f"TS_5m1h_{sym[:3]}"] = hac_predictive(last5.reindex(r.index), r.shift(-1), lag=24)
    return out


def xs_cells(p1h: dict) -> dict:
    daily = load_daily_panels()
    close_d, qv_d = clip_dev(daily["close"]), clip_dev(daily["qv"])
    uni = monthly_universe(qv_d, 200)
    c, q, tb = p1h["close"], p1h["qv"], p1h["tb"]
    day = c.index.tz_convert("UTC").normalize()
    imb_d = imbalance(tb.groupby(day).sum(), q.groupby(day).sum())
    z_d = zscore(imb_d, 30)                              # row d uses days <= d
    common = uni.columns.intersection(z_d.columns)
    idx = uni.index.intersection(z_d.index)
    sig = z_d.reindex(index=idx, columns=common).where(uni.reindex(index=idx, columns=common))
    ret = close_d.reindex(index=idx, columns=common).pct_change(fill_method=None)
    y24 = ret.shift(-1)                                  # next-day return, aligned to signal row d
    y7 = ret.rolling(7).sum().shift(-7)                  # next 7 days' return sum
    out = {}
    for name, y, lag in (("XS_24h_IC", y24, 5), ("XS_7d_IC", y7, 10)):
        ics = daily_ic(sig, y, min_breadth=MIN_BREADTH)
        ics = ics[(ics.index >= DEV_LO) & (ics.index <= DEV_HI)]
        if name == "XS_7d_IC":
            ics = ics[ics.index <= DEV_HI - pd.Timedelta(days=7)]
        s = ic_summary(ics, nw_lag=lag)
        subs = {}
        for label, lo, hi in SUBS:
            sub = ics[(ics.index >= lo) & (ics.index <= hi)].dropna()
            subs[label] = float(sub.mean()) if len(sub) > 20 else float("nan")
        right = sum(1 for v in subs.values() if not np.isnan(v) and np.sign(v) == np.sign(s["mean_ic"]))
        breadth = (sig.notna() & y.notna()).sum(axis=1)
        from scipy.stats import norm
        p_two = float(2 * (1 - norm.cdf(abs(s["nw_t"])))) if np.isfinite(s["nw_t"]) else float("nan")
        out[name] = {**s, "p": p_two, "subperiods": subs, "n_sub_right_sign": right,
                     "first_day_breadth_ge_25": str(breadth[breadth >= MIN_BREADTH].index.min()),
                     "median_breadth": float(breadth[breadth > 0].median())}
    return out


def main() -> None:
    gates = registry.load_gates()
    if gates[KEY].get("verdicts"):
        raise SystemExit("REFUSED: predlab_oflow verdicts already recorded (one-shot)")
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    p1h = load_1h()
    print(f"1h panels {p1h['close'].shape} ({time.time()-t0:.0f}s)", flush=True)
    res = {}
    res.update(ts_cells(p1h))
    print(f"TS cells done ({time.time()-t0:.0f}s)", flush=True)
    res.update(xs_cells(p1h))
    print(f"XS cells done ({time.time()-t0:.0f}s)", flush=True)
    assert set(res) == set(CELLS), set(res) ^ set(CELLS)
    pvals = {k: res[k]["p"] for k in CELLS}
    fdr = bh_fdr({k: v for k, v in pvals.items() if np.isfinite(v)}, q=0.10)
    survivors = []
    for k in CELLS:
        r = res[k]
        if k.startswith("TS"):
            floor_ok = r["p"] < FLOOR["ts_p"] and r["n_year_agree"] >= FLOOR["ts_years"]
        else:
            floor_ok = abs(r["mean_ic"]) >= FLOOR["xs_abs_ic"] and r["nw_t"] >= FLOOR["xs_nw_t"] and r["n_sub_right_sign"] >= FLOOR["xs_subperiods"]
        r["floor_pass"] = bool(floor_ok)
        r["fdr_reject"] = k in fdr
        r["survive"] = bool(floor_ok and k in fdr)
        if r["survive"]:
            survivors.append(k)
        ledger_append(KEY, k, "linear_P0", {"cell": k, "floor": FLOOR, "signal": "imb z30d"},
                      {kk: v for kk, v in r.items() if isinstance(v, (int, float, bool))})
        print(f"{k:12s} " + (f"slope {r['slope']:+.5f} t {r['t']:+.2f} p {r['p']:.4f} yrs {r['n_year_agree']}/4 eff {r['implied_effect_bp_per_bar']:.2f} bp"
                              if k.startswith("TS") else f"IC {r['mean_ic']:+.4f} NW-t {r['nw_t']:+.2f} p {r['p']:.4f} subs {r['n_sub_right_sign']}/3 breadth {r['median_breadth']:.0f} first {r['first_day_breadth_ge_25'][:10]}")
              + f" | floor {r['floor_pass']} fdr {r['fdr_reject']} -> {'SURVIVE' if r['survive'] else 'fail'}", flush=True)
    verdict = (f"P0 {len(survivors)}/8 survive BH-FDR q<0.10 + floors: {survivors}" if survivors
               else f"FAIL at P0 — 0/8 cells survive (min raw p {min(v for v in pvals.values() if np.isfinite(v)):.4f}); family CLOSED")
    payload = {"ts_utc": pd.Timestamp.utcnow().isoformat(), "cells": res, "pvals": pvals, "fdr_rejected": sorted(fdr),
               "survivors": survivors, "verdict": verdict, "runtime_sec": time.time() - t0}
    (OUT / "p0_result.json").write_text(json.dumps(payload, indent=1, default=str))
    gates = registry.load_gates()
    gates[KEY]["verdicts"] = {"P0": verdict}
    registry.gates_path().write_text(json.dumps(gates, indent=1))
    print(verdict, flush=True)


if __name__ == "__main__":
    main()

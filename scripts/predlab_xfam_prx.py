"""xfam_prx — pairs / cointegration MR (charter 2026-08-25).

Universe: top-50 by prior-90d median qv, monthly PIT. Formation: EG on 90d log
closes, keep ADF p<0.05 + half-life 2-20d, cap 20 by ADF p. P0 persistence
kill-test: next-month spread (formation beta frozen) ADF p<0.10 rate for
selected vs 20 random same-universe pairs; gate selected >= 1.5x random AND
Wilcoxon p<0.05. Sub-cell ETHBTC: yearly half-life in [2,40]d for >=3/4 years.
P1 (only if P0 passes): z-MR backtest, one grid point (z 2/0.5/4, 20d timeout,
1/20 capital) + ETHBTC.

ADF settings pinned pre-run: maxlag=5, autolag=None (speed; charter left
unpinned, frozen here before first execution).
"""

from __future__ import annotations

import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
from statsmodels.tsa.stattools import adfuller

sys.path.insert(0, str(Path(__file__).resolve().parent))
from predlab_xfam_lib import (  # noqa: E402
    DEV,
    ann_sr,
    ar1_half_life,
    clip_dev,
    ledger_append,
    load_daily_panels,
    pair_zmr_backtest,
    write_result,
)

DEV_LO = pd.Timestamp(DEV[0], tz="UTC")
DEV_HI = pd.Timestamp(DEV[1], tz="UTC")


def adf_p_fast(x: np.ndarray) -> float:
    x = x[~np.isnan(x)]
    if len(x) < 25 or np.std(x) == 0:
        return np.nan
    try:
        return float(adfuller(x, maxlag=5, autolag=None)[1])
    except Exception:
        return np.nan


def eg_beta_resid(la: pd.Series, lb: pd.Series):
    df = pd.concat({"a": la, "b": lb}, axis=1).dropna()
    if len(df) < 60:
        return np.nan, None
    beta = float(np.polyfit(df["b"].to_numpy(), df["a"].to_numpy(), 1)[0])
    return beta, df["a"] - beta * df["b"]


def month_starts(index: pd.DatetimeIndex, lo: str, hi: str):
    ms = pd.date_range(lo, hi, freq="MS", tz="UTC")
    return [m for m in ms if m >= index.min() + pd.Timedelta(days=95)]


def main():
    rng = np.random.default_rng(42)
    panels = load_daily_panels()
    close = clip_dev(panels["close"])
    qv = panels["qv"].loc[close.index]
    logc = np.log(close)

    months = month_starts(close.index, "2021-01-01", "2025-02-01")
    per_month = []
    for m in months:
        form_lo, form_hi = m - pd.Timedelta(days=90), m - pd.Timedelta(days=1)
        trade_hi = min(m + pd.offsets.MonthBegin(1) - pd.Timedelta(days=1), DEV_HI)
        med = qv[(qv.index >= form_lo) & (qv.index <= form_hi)].median()
        top = med.dropna().nlargest(50).index.tolist()
        lw = logc.loc[(logc.index >= form_lo) & (logc.index <= form_hi), top]
        tw = logc.loc[(logc.index >= m) & (logc.index <= trade_hi), top]
        if len(tw) < 20:
            continue
        selected = []
        for a, b in combinations(top, 2):
            beta, resid = eg_beta_resid(lw[a], lw[b])
            if resid is None:
                continue
            p = adf_p_fast(resid.to_numpy())
            if np.isnan(p) or p >= 0.05:
                continue
            hl = ar1_half_life(resid)
            if not (2.0 <= hl <= 20.0):
                continue
            selected.append((p, a, b, beta))
        selected.sort()
        selected = selected[:20]
        # OOS persistence of selected pairs
        sel_flags = []
        for _, a, b, beta in selected:
            sp = (tw[a] - beta * tw[b]).to_numpy()
            p_oos = adf_p_fast(sp)
            if not np.isnan(p_oos):
                sel_flags.append(p_oos < 0.10)
        # random-pair baseline (formation-fitted beta, same test)
        rnd_flags = []
        tries = 0
        while len(rnd_flags) < 20 and tries < 200:
            tries += 1
            a, b = rng.choice(top, size=2, replace=False)
            beta, resid = eg_beta_resid(lw[a], lw[b])
            if resid is None:
                continue
            p_oos = adf_p_fast((tw[a] - beta * tw[b]).to_numpy())
            if not np.isnan(p_oos):
                rnd_flags.append(p_oos < 0.10)
        if sel_flags and rnd_flags:
            per_month.append({
                "month": str(m.date()), "n_selected": len(sel_flags),
                "sel_rate": float(np.mean(sel_flags)),
                "rnd_rate": float(np.mean(rnd_flags)),
                "pairs": [(a, b, beta) for _, a, b, beta in selected],
            })

    sel = np.array([r["sel_rate"] for r in per_month])
    rnd = np.array([r["rnd_rate"] for r in per_month])
    ratio = sel.mean() / max(rnd.mean(), 1e-9)
    try:
        w_p = float(wilcoxon(sel, rnd, alternative="greater").pvalue)
    except Exception:
        w_p = np.nan
    p0_pass = bool(ratio >= 1.5 and w_p < 0.05)

    # ETHBTC sub-cell: yearly half-life
    ethbtc = {}
    for y in (2021, 2022, 2023, 2024):
        yr = logc[(logc.index.year == y)]
        beta, resid = eg_beta_resid(yr["ETHUSDT"], yr["BTCUSDT"])
        hl = ar1_half_life(resid) if resid is not None else np.nan
        ethbtc[str(y)] = float(hl) if np.isfinite(hl) else None
    eb_ok = sum(1 for v in ethbtc.values() if v is not None and 2 <= v <= 40)
    eb_pass = eb_ok >= 3

    payload = {"family": "xfam_prx",
               "P0": {"n_months": len(per_month),
                      "mean_sel_rate": float(sel.mean()),
                      "mean_rnd_rate": float(rnd.mean()),
                      "ratio": float(ratio), "wilcoxon_p": w_p,
                      "pass": p0_pass, "per_month": per_month},
               "P0_ethbtc": {"yearly_half_life": ethbtc, "n_in_band": eb_ok,
                             "pass": bool(eb_pass)}}
    ledger_append("predlab_xfam_prx", "top50|90d_form", "persistence_p0",
                  {"adf": "maxlag5_noauto", "cap": 20},
                  {"ratio": float(ratio), "wilcoxon_p": w_p,
                   "sel_rate": float(sel.mean()), "rnd_rate": float(rnd.mean())})
    print(f"P0 persistence: sel={sel.mean():.3f} rnd={rnd.mean():.3f} "
          f"ratio={ratio:.2f} wilcoxon p={w_p:.4g} -> {'PASS' if p0_pass else 'FAIL'}")
    print(f"P0 ETHBTC half-lives: {ethbtc} in-band {eb_ok}/4 -> "
          f"{'PASS' if eb_pass else 'FAIL'}")

    # P1 portfolio backtest only if main P0 passes
    if p0_pass:
        ret = close.pct_change(fill_method=None)
        daily = {}
        for r in per_month:
            m = pd.Timestamp(r["month"], tz="UTC")
            trade_hi = min(m + pd.offsets.MonthBegin(1) - pd.Timedelta(days=1), DEV_HI)
            tidx = close.index[(close.index >= m) & (close.index <= trade_hi)]
            for a, b, beta in r["pairs"]:
                hist_lo = m - pd.Timedelta(days=120)
                la = logc.loc[logc.index >= hist_lo, a]
                lb = logc.loc[logc.index >= hist_lo, b]
                df = pair_zmr_backtest(la, lb, ret[a], ret[b], beta, tidx)
                for d, row in df.iterrows():
                    daily[d] = daily.get(d, 0.0) + row["net"] / 20.0
        pnl = pd.Series(daily).sort_index()
        payload["P1"] = {"sr_net": ann_sr(pnl.to_numpy()), "n_days": int(len(pnl))}
        print(f"P1 net SR={payload['P1']['sr_net']:+.2f}")

    if eb_pass:
        ret = close.pct_change(fill_method=None)
        beta, _ = eg_beta_resid(clip_dev(logc)["ETHUSDT"], clip_dev(logc)["BTCUSDT"])
        tidx = close.index[(close.index >= DEV_LO) & (close.index <= DEV_HI)]
        df = pair_zmr_backtest(logc["ETHUSDT"], logc["BTCUSDT"], ret["ETHUSDT"],
                               ret["BTCUSDT"], beta, tidx)
        payload["P1_ethbtc"] = {"sr_net": ann_sr(df["net"].to_numpy()),
                                "n_days": int(len(df)),
                                "time_in_pos": float((df["gross"] != 0).mean())}
        ledger_append("predlab_xfam_prx", "ETHBTC", "zmr_single",
                      {"z": "2/0.5/4", "hold": 20}, payload["P1_ethbtc"])
        print(f"P1 ETHBTC: net SR={payload['P1_ethbtc']['sr_net']:+.2f} "
              f"in-pos={payload['P1_ethbtc']['time_in_pos']:.2f}")

    path = write_result("prx", payload)
    print(f"-> {path}")


if __name__ == "__main__":
    main()

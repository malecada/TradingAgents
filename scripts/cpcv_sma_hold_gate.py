"""CPCV + Deflated Sharpe gate for the sma×hold winner (sma20/hold14) vs the
deployed config (sma30/hold7), both at tv0.07/tm2.0, 8-coin. Cumulative trial
count = 36 (20 trend×vol + 16 sma×hold) so DSR pays for ALL tuning done."""
from __future__ import annotations
import itertools
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
import scripts.baseline_v5_mix as bm  # noqa: E402
from tradingagents.strategies.v2_sizing import (  # noqa: E402
    apply_trend_filter, build_positions_with_hold, compute_realized_vol,
    generate_term_structure_signals, vol_regime_mask)

START, END = "2021-11-07", "2026-04-14"
ANN = bm.ANN
TV, TM = 0.07, 2.0
_SMA, _HOLD = 30, 7
NG, KT, EMB = 10, 2, 14
N_TRIALS = 36  # 20 trend×vol + 16 sma×hold
ALL_SRS = None  # filled from both sweep jsons


def _patched(merged, kelly_fraction=0.5, early_exit_loss=bm.EARLY_EXIT_DEFAULT):
    sig, conf = generate_term_structure_signals(
        merged, [7, 14], bm.V5_CONFIDENCE_REF, asymmetric=bm.V5_ASYMMETRIC)
    px = merged["Close"].astype(float).values
    rv = compute_realized_vol(px, lookback=20)
    mask = vol_regime_mask(rv, percentile_cap=0.95)
    pos = build_positions_with_hold(
        signals=sig, vol_ok=mask, confidence=conf, realized_vol=rv, prices=px,
        target_vol=TV, kelly_fraction=kelly_fraction, max_leverage=3.0,
        min_hold=_HOLD, early_exit_loss=early_exit_loss)
    return apply_trend_filter(pos, px, sma_period=_SMA, multiplier=TM)


bm._v2_positions = _patched


def port(sma, hold):
    global _SMA, _HOLD
    _SMA, _HOLD = sma, hold
    cr = {c: bm.run_coin(c, REPO / p, START, END, kelly_fraction=0.5,
                         costs_override=bm.costs_for_coin(c))
          for c, p in bm.DEFAULT_ROUTING.items()}
    df = pd.DataFrame(cr).dropna().sort_index()
    return bm.portfolio_return(df, bm.PORTFOLIO_WEIGHTS).values


def sr(r):
    r = np.asarray(r); sd = r.std()
    return float(r.mean() / sd * ANN) if sd > 0 and len(r) > 2 else 0.0


def cpcv_srs(ret):
    n = len(ret); edges = np.linspace(0, n, NG + 1, dtype=int)
    groups = [np.arange(edges[i], edges[i + 1]) for i in range(NG)]
    out = []
    for combo in itertools.combinations(range(NG), KT):
        idx = np.sort(np.concatenate([groups[g] for g in combo]))
        keep = []; run = idx[0]; prev = -10**9
        for i in idx:
            if i != prev + 1:
                run = i
            if i - run >= EMB:
                keep.append(i)
            prev = i
        if len(keep) > 2:
            out.append(sr(ret[np.array(keep)]))
    return np.array(out)


def dsr(sr_obs, returns, n_trials, sr_var):
    T = len(returns); r = np.asarray(returns)
    sk = float(stats.skew(r)); ku = float(stats.kurtosis(r, fisher=False))
    sb = sr_obs / ANN
    s0s = np.sqrt(sr_var) / ANN
    e = np.e; g = 0.5772156649
    z1 = stats.norm.ppf(1 - 1.0 / n_trials); z2 = stats.norm.ppf(1 - 1.0 / (n_trials * e))
    sr0 = s0s * ((1 - g) * z1 + g * z2)
    num = (sb - sr0) * np.sqrt(T - 1)
    den = np.sqrt(1 - sk * sb + (ku - 1) / 4.0 * sb ** 2)
    return float(stats.norm.cdf(num / den)), sr0 * ANN


def main():
    base = port(30, 7)
    cand = port(20, 14)
    bc, cc = cpcv_srs(base), cpcv_srs(cand)
    print(f"full-sample: base(sma30/hold7) {sr(base):.3f}  cand(sma20/hold14) {sr(cand):.3f}\n")
    for nm, s in [("base", bc), ("cand", cc)]:
        print(f"  {nm} CPCV: median {np.median(s):.3f}  q05 {np.percentile(s,5):.3f}  "
              f"q95 {np.percentile(s,95):.3f}  frac>2 {np.mean(s>2):.0%}")
    d = cc - bc
    print(f"\n  paired cand-base: median {np.median(d):+.3f}  frac>0 {np.mean(d>0):.0%}  "
          f"min {d.min():+.3f}  max {d.max():+.3f}")
    # trial SR variance from BOTH sweeps
    srs = []
    for f in ["trend_vol_sweep_authoritative.json", "sma_hold_sweep.json"]:
        p = REPO / "data" / f
        if p.exists():
            srs += [v["sharpe"] for v in json.loads(p.read_text()).values()]
    var = float(np.var(srs)); nt = max(N_TRIALS, len(srs))
    dc, sr0 = dsr(sr(cand), cand, nt, var)
    db, _ = dsr(sr(base), base, nt, var)
    print(f"\n  DSR (n_trials={nt}, SR0={sr0:.3f}):")
    print(f"    base sma30/hold7  DSR {db:.4f}")
    print(f"    cand sma20/hold14 DSR {dc:.4f}  ({'PASS' if dc>0.95 else 'WEAK' if dc>0.9 else 'FAIL'} @0.95)")


if __name__ == "__main__":
    main()

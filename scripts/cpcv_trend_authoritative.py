"""CPCV + Deflated Sharpe gate for Lead #3 (trend-multiplier).

Portfolio-level CPCV on the 4-coin V5-MIX daily-return series:
  - n_groups=10, k_test=2 -> C(10,2)=45 test combos, 14-bar embargo per segment.
  - Compare baseline (tv0.10/tm1.5) vs candidate (tv0.07/tm2.0) PAIRED per fold.
Reuses the authoritative run_coin + portfolio_return (monkeypatched _v2_positions).

Deflated Sharpe (Lopez de Prado 2014) on the FULL-sample candidate SR, using the
20 swept cells (trend_vol_sweep_authoritative.json) as the trial set -> SR0
(expected max SR under 20 trials). Candidate must survive (DSR high) to ship.
"""
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

CORE = {
    "bitcoin": "data/multi_2coins_walkforward",
    "ethereum": "data/multi_2coins_pit_wf",
    "binancecoin": "data/multi_3coins_bnb_wf",
    "solana": "data/multi_3coins_sol_pit_wf",
}
START, END = "2021-11-07", "2026-04-14"
ANN = bm.ANN
_TV, _TM = 0.10, 1.5
NG, KT, EMB = 10, 2, 14


def _patched(merged, kelly_fraction=0.5, early_exit_loss=bm.EARLY_EXIT_DEFAULT):
    sig, conf = generate_term_structure_signals(
        merged, [7, 14], bm.V5_CONFIDENCE_REF, asymmetric=bm.V5_ASYMMETRIC)
    px = merged["Close"].astype(float).values
    rv = compute_realized_vol(px, lookback=20)
    mask = vol_regime_mask(rv, percentile_cap=0.95)
    pos = build_positions_with_hold(
        signals=sig, vol_ok=mask, confidence=conf, realized_vol=rv, prices=px,
        target_vol=_TV, kelly_fraction=kelly_fraction, max_leverage=3.0,
        min_hold=7, early_exit_loss=early_exit_loss)
    return apply_trend_filter(pos, px, sma_period=30, multiplier=_TM)


bm._v2_positions = _patched


def port_returns(tv, tm):
    global _TV, _TM
    _TV, _TM = tv, tm
    cr = {c: bm.run_coin(c, REPO / p, START, END, kelly_fraction=0.5,
                         costs_override=bm.costs_for_coin(c)) for c, p in CORE.items()}
    df = pd.DataFrame(cr).dropna().sort_index()
    return bm.portfolio_return(df, bm.PORTFOLIO_WEIGHTS).values


def sr(r):
    r = np.asarray(r); sd = r.std()
    return float(r.mean() / sd * ANN) if sd > 0 and len(r) > 2 else 0.0


def cpcv_srs(ret):
    n = len(ret)
    edges = np.linspace(0, n, NG + 1, dtype=int)
    groups = [np.arange(edges[i], edges[i + 1]) for i in range(NG)]
    out = []
    for combo in itertools.combinations(range(NG), KT):
        idx = np.sort(np.concatenate([groups[g] for g in combo]))
        # embargo: drop first EMB bars of each contiguous segment
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


def deflated_sharpe(sr_obs, returns, n_trials, sr_var_trials):
    """DSR per Lopez de Prado 2014. sr_obs in per-sqrt-bar units internally."""
    T = len(returns)
    r = np.asarray(returns)
    sk = float(stats.skew(r)); ku = float(stats.kurtosis(r, fisher=False))
    sr_bar = sr_obs / ANN  # de-annualize to per-bar
    # expected max SR under n_trials independent trials (per-bar units)
    sr0_std = np.sqrt(sr_var_trials) / ANN
    e = np.e; g = 0.5772156649
    z1 = stats.norm.ppf(1 - 1.0 / n_trials)
    z2 = stats.norm.ppf(1 - 1.0 / (n_trials * e))
    sr0 = sr0_std * ((1 - g) * z1 + g * z2)
    num = (sr_bar - sr0) * np.sqrt(T - 1)
    den = np.sqrt(1 - sk * sr_bar + (ku - 1) / 4.0 * sr_bar ** 2)
    return float(stats.norm.cdf(num / den)), sr0 * ANN


def main():
    print("=== CPCV gate: V5-MIX 4-coin, baseline(0.10/1.5) vs candidate(0.07/2.0) ===\n")
    base = port_returns(0.10, 1.5)
    cand = port_returns(0.07, 2.0)
    bc, cc = cpcv_srs(base), cpcv_srs(cand)
    print(f"full-sample SR: baseline {sr(base):.3f}  candidate {sr(cand):.3f}\n")
    for name, s in [("baseline", bc), ("candidate", cc)]:
        print(f"{name:9s} CPCV ({len(s)} folds): median {np.median(s):.3f}  "
              f"q05 {np.percentile(s,5):.3f}  q95 {np.percentile(s,95):.3f}  "
              f"frac>2 {np.mean(s>2):.0%}  frac>0 {np.mean(s>0):.0%}")
    # paired per-fold (combos in same order)
    delta = cc - bc
    print(f"\npaired per-fold (candidate - baseline): median {np.median(delta):+.3f}  "
          f"frac>0 {np.mean(delta>0):.0%}  min {delta.min():+.3f}  max {delta.max():+.3f}")

    # DSR using 20 swept cells as trial set
    j = REPO / "data" / "trend_vol_sweep_authoritative.json"
    srs_trials = [v["sharpe"] for v in json.loads(j.read_text()).values()]
    n_trials = len(srs_trials); var_trials = float(np.var(srs_trials))
    dsr_c, sr0 = deflated_sharpe(sr(cand), cand, n_trials, var_trials)
    dsr_b, _ = deflated_sharpe(sr(base), base, n_trials, var_trials)
    print(f"\nDSR (n_trials={n_trials}, SR0={sr0:.3f} annualized expected-max):")
    print(f"  baseline  DSR {dsr_b:.4f}")
    print(f"  candidate DSR {dsr_c:.4f}   ({'PASS' if dsr_c>0.95 else 'WEAK' if dsr_c>0.90 else 'FAIL'} @0.95)")
    json.dump({"base_sr": sr(base), "cand_sr": sr(cand),
               "cpcv_base_median": float(np.median(bc)), "cpcv_cand_median": float(np.median(cc)),
               "paired_frac_cand_gt_base": float(np.mean(delta > 0)),
               "dsr_candidate": dsr_c, "dsr_baseline": dsr_b, "sr0": sr0},
              open(REPO / "data" / "cpcv_trend_gate.json", "w"), indent=2)


if __name__ == "__main__":
    main()

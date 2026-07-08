"""8-coin V5-MIX: published baseline (tv0.10/tm1.5) vs V5.1 tuned (tv0.07/tm2.0).
Live universe is 8 coins; #3 was validated on 4-coin. Measure the lift on the
full live universe + per-year robustness. Authoritative monkeypatch of
_v2_positions, real run_coin + portfolio_return (core/satellite weights)."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
import scripts.baseline_v5_mix as bm  # noqa: E402
from tradingagents.strategies.v2_sizing import (  # noqa: E402
    apply_trend_filter, build_positions_with_hold, compute_realized_vol,
    generate_term_structure_signals, vol_regime_mask)

START, END = "2021-11-07", "2026-04-14"
ANN = bm.ANN
_TV, _TM = 0.10, 1.5


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


def port(tv, tm):
    global _TV, _TM
    _TV, _TM = tv, tm
    cr = {}
    for coin, pdir in bm.DEFAULT_ROUTING.items():  # all 8
        cr[coin] = bm.run_coin(coin, REPO / pdir, START, END, kelly_fraction=0.5,
                               costs_override=bm.costs_for_coin(coin))
    df = pd.DataFrame(cr).dropna().sort_index()
    s = bm.portfolio_return(df, bm.PORTFOLIO_WEIGHTS)
    s.index = pd.to_datetime(s.index)
    return s


def sr(r):
    sd = r.std()
    return float(r.mean() / sd * ANN) if sd > 0 else 0.0


def mdd(r):
    eq = (1 + r).cumprod()
    return float((eq / eq.cummax() - 1).min())


def main():
    print("=== 8-coin V5-MIX: baseline(0.10/1.5) vs tuned(0.07/2.0) ===\n")
    b = port(0.10, 1.5)
    c = port(0.07, 2.0)
    for nm, s in [("baseline", b), ("tuned", c)]:
        print(f"  {nm:8s} SR {sr(s):+.3f}  ret {(np.prod(1+s)-1)*100:+9.1f}%  "
              f"DD {mdd(s)*100:5.1f}%  vol {s.std()*ANN*100:.1f}%")
    print(f"\n  dSR (tuned-baseline): {sr(c)-sr(b):+.3f}")
    years = sorted({d.year for d in b.index})
    print("\n  per-year SR:")
    print("  year   baseline   tuned   delta")
    wins = 0
    for y in years:
        by = sr(b[b.index.year == y]); cy = sr(c[c.index.year == y])
        wins += cy > by
        print(f"  {y}   {by:7.2f}  {cy:7.2f}  {cy-by:+.2f}")
    print(f"  tuned-wins: {wins}/{len(years)} years")


if __name__ == "__main__":
    main()

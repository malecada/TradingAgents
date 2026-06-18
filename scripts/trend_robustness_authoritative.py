"""Per-year / per-half robustness of the trend-multiplier lead, AUTHORITATIVE
pipeline (monkeypatched real run_coin + portfolio_return). Compares
tm in {1.5 baseline, 1.7, 2.0} at production tv=0.10, and the dominating
low-vol cell tv=0.07/tm=2.0 vs baseline. A lead that only wins full-sample
but loses in individual years is overfit."""
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

CORE = {
    "bitcoin": "data/multi_2coins_walkforward",
    "ethereum": "data/multi_2coins_pit_wf",
    "binancecoin": "data/multi_3coins_bnb_wf",
    "solana": "data/multi_3coins_sol_pit_wf",
}
START, END = "2021-11-07", "2026-04-14"
_TV, _TM = 0.10, 1.5
ANN = bm.ANN


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


def series(tv, tm):
    global _TV, _TM
    _TV, _TM = tv, tm
    cr = {c: bm.run_coin(c, REPO / p, START, END, kelly_fraction=0.5,
                         costs_override=bm.costs_for_coin(c))
          for c, p in CORE.items()}
    df = pd.DataFrame(cr).dropna().sort_index()
    s = bm.portfolio_return(df, bm.PORTFOLIO_WEIGHTS)
    s.index = pd.to_datetime(s.index)
    return s


def sr(r):
    sd = r.std()
    return float(r.mean() / sd * ANN) if sd > 0 else 0.0


def main():
    cells = {
        "tv0.10_tm1.5 (base)": (0.10, 1.5),
        "tv0.10_tm1.7": (0.10, 1.7),
        "tv0.10_tm2.0": (0.10, 2.0),
        "tv0.07_tm2.0 (best)": (0.07, 2.0),
    }
    ports = {name: series(tv, tm) for name, (tv, tm) in cells.items()}
    names = list(cells)
    years = sorted({d.year for d in ports[names[0]].index})

    print("Per-year portfolio SR\n")
    print("period   " + "".join(f"{n[:14]:>16}" for n in names))
    for y in years:
        row = f"{y}     "
        for n in names:
            yr = ports[n][ports[n].index.year == y]
            row += f"{sr(yr):>16.2f}"
        print(row)
    print("-" * (9 + 16 * len(names)))
    mid = ports[names[0]].index[len(ports[names[0]]) // 2]
    for lbl, msk in [("H1", lambda i: i < mid), ("H2", lambda i: i >= mid)]:
        row = f"{lbl}       "
        for n in names:
            seg = ports[n][[msk(d) for d in ports[n].index]]
            row += f"{sr(seg):>16.2f}"
        print(row)
    print("-" * (9 + 16 * len(names)))
    row = "FULL     "
    for n in names:
        row += f"{sr(ports[n]):>16.2f}"
    print(row)

    # win-count: does tm=2.0 beat tm=1.5 each year?
    print("\ntm=2.0 vs tm=1.5 (tv=0.10), per-year SR delta:")
    b, t = ports["tv0.10_tm1.5 (base)"], ports["tv0.10_tm2.0"]
    wins = 0
    for y in years:
        db = sr(b[b.index.year == y]); dt = sr(t[t.index.year == y])
        d = dt - db
        wins += d > 0
        print(f"  {y}: {d:+.3f}")
    print(f"  win years: {wins}/{len(years)}")


if __name__ == "__main__":
    main()

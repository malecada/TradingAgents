"""trend_sma x min_hold joint sweep at the DEPLOYED tuned config (tv0.07/tm2.0),
8-coin live universe. Baseline cell = sma30/hold7 (must reproduce ~4.28).
Authoritative monkeypatch. Reports SR grid + per-year wins for the best cell.
The CPCV+DSR gate (cumulative trial count) runs separately on the winner."""
from __future__ import annotations
import json
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
_SMA, _HOLD = 30, 7
TV, TM = 0.07, 2.0  # deployed tuned config, held fixed


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
    smas = [20, 30, 40, 50]
    holds = [5, 7, 10, 14]
    out = {}
    print(f"SR grid (8-coin, tv={TV}/tm={TM} fixed)\n")
    print(f"{'sma\\hold':>9}" + "".join(f"{h:>8}" for h in holds))
    series = {}
    for sma in smas:
        row = []
        for hold in holds:
            s = port(sma, hold)
            series[(sma, hold)] = s
            m = {"sharpe": sr(s), "ret": float(np.prod(1 + s) - 1), "mdd": mdd(s)}
            out[f"sma{sma}_hold{hold}"] = m
            row.append(m["sharpe"])
        print(f"{sma:>9}" + "".join(f"{x:>8.3f}" for x in row))
    base = out["sma30_hold7"]
    print(f"\nCHECK base sma30/hold7: SR {base['sharpe']:.3f} (deployed tuned ~4.28)")
    best_k = max(out, key=lambda k: out[k]["sharpe"])
    bm_ = out[best_k]
    print(f"\nbest cell: {best_k}  SR {bm_['sharpe']:.3f}  ret {bm_['ret']*100:+.1f}%  DD {bm_['mdd']*100:.1f}%")
    print(f"  delta vs base sma30/hold7: {bm_['sharpe']-base['sharpe']:+.3f}")
    # per-year: best vs base
    b = series[(30, 7)]
    bk = tuple(int(x) for x in best_k.replace("sma", "").replace("hold", "").split("_"))
    c = series[bk]
    yrs = sorted({d.year for d in b.index})
    wins = sum(sr(c[c.index.year == y]) > sr(b[b.index.year == y]) for y in yrs)
    print(f"  best beats base in {wins}/{len(yrs)} years")
    json.dump(out, open(REPO / "data" / "sma_hold_sweep.json", "w"), indent=2)


if __name__ == "__main__":
    main()

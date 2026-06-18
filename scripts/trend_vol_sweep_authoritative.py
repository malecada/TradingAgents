"""Trend-mult x vol-target sweep using the AUTHORITATIVE V5-MIX pipeline.

Instead of re-implementing sizing (which drifts), we monkeypatch the two
constants inside baseline_v5_mix._v2_positions and call the real run_coin +
portfolio_return. Cell (0.10, 1.5) MUST reproduce SR 3.178 — that's the
correctness check. 4-coin core, kelly=0.5, full 4.5-yr window.
"""
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

CORE = {
    "bitcoin": "data/multi_2coins_walkforward",
    "ethereum": "data/multi_2coins_pit_wf",
    "binancecoin": "data/multi_3coins_bnb_wf",
    "solana": "data/multi_3coins_sol_pit_wf",
}
START, END = "2021-11-07", "2026-04-14"

# module-level knobs the patched _v2_positions reads
_TV = 0.10
_TM = 1.5


def _patched_v2_positions(merged, kelly_fraction=0.5,
                          early_exit_loss=bm.EARLY_EXIT_DEFAULT):
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


bm._v2_positions = _patched_v2_positions  # install patch


def cell(tv, tm):
    global _TV, _TM
    _TV, _TM = tv, tm
    coin_rets = {}
    for coin, pdir in CORE.items():
        coin_rets[coin] = bm.run_coin(
            coin, REPO / pdir, START, END, kelly_fraction=0.5,
            costs_override=bm.costs_for_coin(coin))
    df = pd.DataFrame(coin_rets).dropna().sort_index()
    port = bm.portfolio_return(df, bm.PORTFOLIO_WEIGHTS)
    return bm._metrics(port)


def main():
    out = {}
    vols = [0.07, 0.10, 0.13, 0.16]
    trends = [1.0, 1.3, 1.5, 1.7, 2.0]
    print("SR grid (4-coin core, kelly=0.5)\n")
    print(f"{'tv\\tm':>7}" + "".join(f"{t:>8}" for t in trends))
    for tv in vols:
        row = []
        for tm in trends:
            m = cell(tv, tm)
            out[f"tv{tv}_tm{tm}"] = m
            row.append(m["sharpe"])
        print(f"{tv:>7}" + "".join(f"{s:>8.3f}" for s in row))
    base = out["tv0.1_tm1.5"]
    print(f"\nCHECK baseline (0.10/1.5): SR {base['sharpe']:.3f} "
          f"(must=3.178)  ret {base['total_return']*100:+.1f}%  DD {base['max_drawdown']*100:.1f}%")
    print("\ntop cells by SR (full metrics):")
    top = sorted(out.items(), key=lambda kv: -kv[1]["sharpe"])[:6]
    for k, m in top:
        print(f"  {k:<14} SR {m['sharpe']:.3f}  ret {m['total_return']*100:+8.1f}%  "
              f"DD {m['max_drawdown']*100:5.1f}%  vol {m['ann_vol']*100:.1f}%")
    (REPO / "data" / "trend_vol_sweep_authoritative.json").write_text(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()

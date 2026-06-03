#!/usr/bin/env python
"""Stop-loss axis analysis for the intraday triple-barrier engine (THESIS §31.5b).

Isolates the pure stop-loss decision (TP=0, trailing=0, EE off) on the intrabar
1h engine and asks: is any SL level robustly better than the a-priori 3%?

Unlike the §29 daily engine — where SL ∈ {3..10}% clustered within <0.001 SR —
intrabar fills reveal a clear gradient: TIGHT stops bleed from intraday
wick-outs the close-only engine never saw. Outputs the SL marginal landscape,
a paired bootstrap of 7% vs 3% (full window + 4 OOS splits), and a per-coin
attribution. Writes data/intraday_sltp_sweep/sl_axis.json.

Usage:
    python scripts/intraday_sl_axis.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.baseline_v5_mix import CORE_COINS  # noqa: E402
from scripts.bootstrap_hybrid import diff_sharpe_ci  # noqa: E402
from scripts.intraday_sltp_stats import _preload, _portfolio_return_series  # noqa: E402

SL_LEVELS = [0.0, 0.01, 0.02, 0.03, 0.05, 0.07, 0.10]
SPLITS = ["2024-07-15", "2024-10-15", "2025-01-15", "2025-04-15"]
COMPARE = (0.07, 0.03)  # (looser candidate, a-priori baseline)


def _ann_sr(r) -> float:
    r = np.asarray(r, dtype=float)
    sd = np.std(r, ddof=1) if len(r) > 1 else 0.0
    return float(np.mean(r) / sd * np.sqrt(252)) if sd > 0 else 0.0


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--start", default="2021-11-07")
    p.add_argument("--end", default="2026-04-15")
    p.add_argument("--n-iter", type=int, default=5000)
    p.add_argument("--block-size", type=int, default=21)
    p.add_argument("--output", default="data/intraday_sltp_sweep/sl_axis.json")
    args = p.parse_args()

    data = _preload(args.start, args.end)

    # 1. SL marginal landscape (portfolio, TP=0, trail=0).
    landscape = []
    series_cache = {}
    for sl in SL_LEVELS:
        s = _portfolio_return_series(data, sl, 0.0, 0.0)
        series_cache[sl] = s
        landscape.append(dict(sl=sl, sharpe=_ann_sr(s.values)))

    cand, base = COMPARE
    s_cand, s_base = series_cache[cand], series_cache[base]

    # 2. Paired bootstrap cand-vs-base, full + each OOS split.
    def _pair(a, b) -> dict:
        r = diff_sharpe_ci(np.asarray(a), np.asarray(b),
                           n_iter=args.n_iter, block_size=args.block_size)
        return dict(sr_cand=_ann_sr(a), sr_base=_ann_sr(b),
                    delta_sr=r["delta_sr_point"], delta_sr_ci=r["delta_sr_ci"],
                    p_cand_gt_base=1.0 - r["p_delta_le_0"])

    windows = {"full": _pair(s_cand.values, s_base.values)}
    for sp in SPLITS:
        spt = pd.Timestamp(sp)
        windows[f"oos>={sp}"] = _pair(s_cand[s_cand.index >= spt].values,
                                      s_base[s_base.index >= spt].values)

    # 3. Per-coin attribution of cand-vs-base.
    per_coin = {}
    for c in CORE_COINS:
        one = {c: data[c]}
        a = _portfolio_return_series(one, cand, 0.0, 0.0)
        b = _portfolio_return_series(one, base, 0.0, 0.0)
        r = diff_sharpe_ci(a.values, b.values, n_iter=args.n_iter, block_size=args.block_size)
        per_coin[c] = dict(sr_cand=_ann_sr(a), sr_base=_ann_sr(b),
                           delta_sr=r["delta_sr_point"], p_cand_gt_base=1.0 - r["p_delta_le_0"])

    out = dict(
        window=[args.start, args.end], compare=dict(candidate_sl=cand, baseline_sl=base),
        sl_marginal_portfolio=landscape, paired_by_window=windows, per_coin=per_coin,
    )
    Path(PROJECT_ROOT / args.output).write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()

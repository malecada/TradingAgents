"""PP-03: strategy-holdout one-shot for the dev survivor (S1, config eq_h1).

Window 2025-04-01 -> 2026-07-01, ONE evaluation, spend rule enforced in
code (verdicts file blocks re-runs). Registered criteria (predlab_pp):
net SR >= 0.5 x dev net SR AND same sign AND placebo p < 0.10 on holdout
(both families). S2/S3 failed dev gates -> no holdout spend for them.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from tradingagents.predlab import pp, registry  # noqa: E402

DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))
HOLDOUT = ("2025-04-01", "2026-07-01")
OUT = DATA_ROOT / "predlab" / "pp_holdout_verdicts.json"
CONFIG = {"weighting": "eq", "smooth": 1}  # frozen at PP-02


def inputs():
    from predlab_t7 import build_panels, monthly_universe

    panels = build_panels()
    close, qv, park = panels["close"], panels["qv"], panels["park"]
    hi = pd.Timestamp(HOLDOUT[1], tz="UTC")
    close = close[close.index <= hi]
    qv, park = qv.loc[close.index], park.loc[close.index]
    # engine_correction_2026-08-24: simple returns — position PnL, never log
    ret = close.pct_change(fill_method=None)
    uni = monthly_universe(qv, top_n=200)
    sig = park.rolling(5).mean().shift(1)
    used = sorted(uni.columns[uni.any(axis=0)])
    fund = pp.build_funding_daily(used, DATA_ROOT / "xsect" / "funding", ret.index)
    return sig, ret, uni, fund


def main() -> None:
    if OUT.exists():
        print(f"STRATEGY HOLDOUT ALREADY SPENT — refusing ({OUT})")
        sys.exit(1)
    dev = json.loads((DATA_ROOT / "predlab" / "pp_dev_results.json").read_text())
    dev_sr = dev["S1"][dev["S1_best"]]["sr_net"]
    need = 0.5 * dev_sr

    sig, ret, uni, fund = inputs()
    r = pp.run_s1(sig, ret, uni, fund, CONFIG["weighting"], CONFIG["smooth"],
                  *HOLDOUT)
    print(f"S1 holdout: net SR {r['sr_net']:+.3f} (gross {r['sr_gross']:+.3f}) "
          f"need >={need:.3f}; dd {r['maxdd']:.1%} turn {r['avg_turnover']:.2f} "
          f"n={r['n_days']}", flush=True)

    def sr_of(s):
        return pp.run_s1(s, ret, uni, fund, CONFIG["weighting"],
                         CONFIG["smooth"], *HOLDOUT)["sr_net"]

    rng = np.random.default_rng(11)
    n = len(sig)
    fam_a = [sr_of(pd.DataFrame(np.roll(sig.to_numpy(),
                                        int(rng.integers(30, n - 30)), axis=0),
                                index=sig.index, columns=sig.columns))
             for _ in range(200)]
    fam_b = []
    for d in range(200):
        rngb = np.random.default_rng(2000 + d)
        vals = sig.to_numpy().copy()
        for i in range(vals.shape[0]):
            row = vals[i]
            ok = ~np.isnan(row)
            row[ok] = rngb.permutation(row[ok])
        fam_b.append(sr_of(pd.DataFrame(vals, index=sig.index, columns=sig.columns)))
    p_a = pp.placebo_pvalue(r["sr_net"], fam_a)
    p_b = pp.placebo_pvalue(r["sr_net"], fam_b)
    print(f"placebos: shift p={p_a:.4f}, xshuffle p={p_b:.4f}", flush=True)

    monthly = r["rets"]["net"].groupby(pd.PeriodIndex(r["rets"].index, freq="Q")).mean()
    passed = (r["sr_net"] >= need and r["sr_net"] > 0
              and p_a < 0.10 and p_b < 0.10)
    verdict = {
        "candidate": "S1_t7_lowvol_ls", "config": CONFIG,
        "dev_sr_net": dev_sr, "need": need,
        "holdout_sr_net": r["sr_net"], "holdout_sr_gross": r["sr_gross"],
        "maxdd": r["maxdd"], "avg_turnover": r["avg_turnover"],
        "n_days": r["n_days"], "p_shift": p_a, "p_xshuffle": p_b,
        "quarters": {str(k): float(v) for k, v in monthly.items()},
        "S2": "no spend (failed dev do-no-harm guard)",
        "S3": "no spend (exploratory, negative at dev)",
        "verdict": "PASS" if passed else "FAIL",
    }
    registry.log_trial("predlab_pp", "S1_t7_lowvol_ls", "holdout_oneshot",
                       {"config": CONFIG, "phase": "strategy_holdout"},
                       HOLDOUT, {k: v for k, v in verdict.items()
                                 if isinstance(v, (int, float, str))})
    OUT.write_text(json.dumps(verdict, indent=1, default=float))
    print(f"\nSTRATEGY HOLDOUT SPENT: {verdict['verdict']} -> {OUT}", flush=True)


if __name__ == "__main__":
    main()

"""predlab_opt2 stages R1 (LS) + R2 (long-only) — corrected-engine sweep.

Grids frozen in gates.json predlab_opt2.stages BEFORE this ran. One ledger
row per config. Dev gates (per registration):
  R1 (LS):  net SR on D >= 1.0
  R2 (LO):  net SR on D >= BTC B&H SR on D + 0.10, and same on V
  both:     V >= 0.5 x D and same sign
Placebo/DSR/subperiod/concentration gates apply only to dev-PASS configs
(none are run here if nothing passes). Output:
data/predlab/opt2_r1r2_results.json + one row per config in the ledger.
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

from tradingagents.predlab import opt, registry  # noqa: E402
from tradingagents.predlab.pp import ann_sr, max_drawdown  # noqa: E402

DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))
OUT = DATA_ROOT / "predlab" / "opt2_r1r2_results.json"

D = ("2021-01-01", "2025-03-31")
V = ("2025-04-01", "2026-07-01")
SIGNALS = ["park_3", "park_5", "park_10", "park_20", "cc_5", "cc_10", "cc_20",
           "vov_10", "vov_20", "ewma_5", "ewma_10", "ewma_20"]
TAKER_ENTRY = 5.0 / 1e4  # one-time entry cost for the B&H benchmark


def lo_tilt(d, w):
    return w.clip(lower=0.0)


def win(x: pd.Series, lo: str, hi: str) -> pd.Series:
    return x[(x.index >= pd.Timestamp(lo, tz="UTC"))
             & (x.index <= pd.Timestamp(hi, tz="UTC"))].dropna()


def main() -> None:
    if OUT.exists():
        print(f"refusing: {OUT} exists")
        sys.exit(1)
    from predlab_opt_o1 import inputs  # corrected ret inside
    close, park, ret, uni, fund = inputs()
    cfg = opt.OptConfig()

    # BTC buy-and-hold benchmark (net of one 5bp entry, amortized day 1)
    btc = ret["BTCUSDT"]
    bench = {}
    for wname, (lo, hi) in (("D", D), ("V", V)):
        b = win(btc, lo, hi).copy()
        if len(b):
            b.iloc[0] -= TAKER_ENTRY
        bench[wname] = {"sr": round(ann_sr(b.to_numpy()), 4),
                        "maxdd": round(max_drawdown(b.to_numpy()), 4),
                        "n_days": int(len(b))}
    print(f"BTC B&H: D SR {bench['D']['sr']:+.3f} | V SR {bench['V']['sr']:+.3f}",
          flush=True)

    results = {"benchmark_btc_bh": bench, "R1": {}, "R2": {}}
    full = (D[0], V[1])
    for stage, tilt in (("R1", None), ("R2", lo_tilt)):
        for s in SIGNALS:
            sig = opt.build_signal(park, close, s)
            r = opt.run_ls(sig, ret, uni, fund, cfg, *full, tilt=tilt)
            net = r["rets"]["net"]
            srD = ann_sr(win(net, *D).to_numpy())
            srV = ann_sr(win(net, *V).to_numpy())
            if stage == "R1":
                dev_pass = srD >= 1.0 and srV >= 0.5 * srD and srV > 0
            else:
                dev_pass = (srD >= bench["D"]["sr"] + 0.10
                            and srV >= bench["V"]["sr"] + 0.10
                            and srV >= 0.5 * srD and srV > 0)
            row = {"sr_net_D": round(float(srD), 4),
                   "sr_net_V": round(float(srV), 4),
                   "sr_net_full": round(float(r["sr_net"]), 4),
                   "sr_gross_full": round(float(r["sr_gross"]), 4),
                   "maxdd": round(float(r["maxdd"]), 4),
                   "avg_turnover": round(float(r["avg_turnover"]), 4),
                   "dev_pass": bool(dev_pass)}
            results[stage][s] = row
            registry.log_trial("predlab_opt2", stage, f"{stage}_{s}",
                               {"signal": s, "book": "ls" if stage == "R1"
                                else "long_only", "engine": "corrected"},
                               full,
                               {"sr_net": r["sr_net"], "sr_net_D": float(srD),
                                "sr_net_V": float(srV),
                                "maxdd": r["maxdd"]})
            print(f"{stage} {s}: D {srD:+.3f} V {srV:+.3f} "
                  f"full {r['sr_net']:+.3f} dd {r['maxdd']:.1%} "
                  f"{'DEV-PASS' if dev_pass else 'fail'}", flush=True)

    n1 = sum(v["dev_pass"] for v in results["R1"].values())
    n2 = sum(v["dev_pass"] for v in results["R2"].values())
    results["verdict"] = {
        "R1_dev_pass": n1, "R2_dev_pass": n2,
        "note": ("stage(s) with zero dev-PASS close negative per stop_rule; "
                 "placebo/DSR/forensics run only on dev-PASS configs"),
    }
    OUT.write_text(json.dumps(results, indent=1, default=float))
    print(f"R1 dev-PASS {n1}/12, R2 dev-PASS {n2}/12 -> {OUT}")


if __name__ == "__main__":
    main()

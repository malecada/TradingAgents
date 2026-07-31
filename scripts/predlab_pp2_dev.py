"""PP2 dev: vol-target overlay on the S1 eq_h1 book (dev window only).

Overlay: s_t = clip(target / realized_ann_vol_20d(book, shifted 1d), 0, 2).
Net_t = s_t * gross_t + s_t * carry_t - 5bp*(s_t * turn_t + |ds_t| * 2).
Gates (frozen predlab_pp2): MaxDD reduction >=25% vs raw AND net SR >=
0.9 x raw. ONE config frozen for the forward confirmation.
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
DEV = ("2021-01-01", "2025-03-31")
OUT = DATA_ROOT / "predlab" / "pp2_dev_results.json"


def overlay(base: pd.DataFrame, target: float, cap: float = 2.0) -> dict:
    """base: run_s1 rets frame (gross, net, turnover, carry)."""
    raw_pre_cost = base["gross"] + base["carry"]  # unit-book P&L before fees
    vol = raw_pre_cost.rolling(20).std().shift(1) * np.sqrt(pp.ANN_DAYS)
    s = (target / vol).clip(upper=cap).fillna(0.0)
    ds = s.diff().abs().fillna(s.iloc[0] if len(s) else 0.0)
    cost = pp.TAKER_BP / 1e4 * (s * base["turnover"] + ds * 2.0)
    net = s * raw_pre_cost - cost
    return {"rets": net, "sr_net": pp.ann_sr(net.to_numpy()),
            "maxdd": pp.max_drawdown(net.dropna().to_numpy()),
            "avg_scale": float(s.mean())}


def main() -> None:
    if OUT.exists():
        print(f"pp2 dev results exist ({OUT}) — refusing (stop rule)")
        sys.exit(1)
    from predlab_pp_dev import s1_inputs

    sig, ret, uni, fund = s1_inputs()
    base = pp.run_s1(sig, ret, uni, fund, "eq", 1, *DEV)
    raw_sr, raw_dd = base["sr_net"], base["maxdd"]
    print(f"raw eq_h1 dev: SR {raw_sr:+.2f} dd {raw_dd:.1%}", flush=True)
    res = {"raw": {"sr_net": raw_sr, "maxdd": raw_dd}}
    verdicts = {}
    for target in (0.10, 0.15, 0.20):
        key = f"vt{int(target*100)}"
        r = overlay(base["rets"], target)
        gate = (r["maxdd"] <= 0.75 * raw_dd and r["sr_net"] >= 0.9 * raw_sr)
        verdicts[key] = "PASS" if gate else "FAIL"
        res[key] = {"sr_net": r["sr_net"], "maxdd": r["maxdd"],
                    "avg_scale": r["avg_scale"], "gate": verdicts[key]}
        registry.log_trial("predlab_pp2", "S1_overlay", key,
                           {"target": target, "cap": 2.0}, DEV,
                           {"sr_net": r["sr_net"], "maxdd": r["maxdd"]})
        print(f"{key}: SR {r['sr_net']:+.2f} (>= {0.9*raw_sr:.2f}?) "
              f"dd {r['maxdd']:.1%} (<= {0.75*raw_dd:.1%}?) "
              f"scale {r['avg_scale']:.2f} -> {verdicts[key]}", flush=True)
    passing = [k for k, v in verdicts.items() if v == "PASS"]
    frozen = max(passing, key=lambda k: res[k]["sr_net"]) if passing else None
    res["frozen_for_confirmation"] = frozen
    OUT.write_text(json.dumps(res, indent=1, default=float))
    print(f"\nfrozen: {frozen} -> {OUT}", flush=True)


if __name__ == "__main__":
    main()

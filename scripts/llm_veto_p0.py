"""llm_c2_veto_ovl P0 — oracle ceiling (zero LLM cost).

Perfect-foresight veto: m=0 on the k=10 worst overlaid-book days per
calendar year inside dev D (2021-01-01 -> 2025-03-31), transition costs
charged. STOP if relative MaxDD reduction < 20% or dSR < -0.05.

Parity pin: the reproduced un-vetoed book must match the frozen
champion_backtest.json ovl metrics before anything else runs.

Refuses to overwrite existing results (stop rule).
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from llm_veto_engine import (  # noqa: E402
    DEV_D, FULL, VETO_BUDGET_PER_YEAR, apply_budget, book_metrics, load_book,
    o4_scale, oracle_m, overlay_net, seg,
)
from tradingagents.predlab.pp import ann_sr, max_drawdown  # noqa: E402

OUTDIR = Path("data/predlab/llm_veto")
OUT = OUTDIR / "p0_oracle.json"
LEDGER = Path("data/predlab/trial_ledger.jsonl")


def main() -> int:
    if OUT.exists():
        print(f"results exist ({OUT}) — refusing to overwrite (stop rule)")
        return 1
    OUTDIR.mkdir(parents=True, exist_ok=True)

    book = load_book()
    base, breadth = book["base"], book["breadth"]
    s = o4_scale(base, breadth)
    ovl = overlay_net(base, s)

    # ---- parity pin vs frozen champion_backtest.json (full window)
    pin = json.loads(Path("data/predlab/champion_backtest.json").read_text())
    want = pin["systems"]["new"]["ovl"]
    got_full = seg(ovl, *FULL)
    got = {"sr": ann_sr(got_full.to_numpy()),
           "maxdd": max_drawdown(got_full.to_numpy())}
    if abs(got["sr"] - want["sr"]) > 1e-9 or abs(got["maxdd"] - want["maxdd"]) > 1e-9:
        print(f"PARITY FAIL: reproduced ovl {got} != frozen {want}")
        return 1
    print(f"parity pin OK: ovl SR {got['sr']:+.4f} dd {got['maxdd']:.2%} (full)")

    # ---- oracle on dev D
    m = oracle_m(ovl, *DEV_D, k=VETO_BUDGET_PER_YEAR)
    m = apply_budget(m, budget=VETO_BUDGET_PER_YEAR)  # no-op by construction; belt+braces
    vet = overlay_net(base, s * m)

    b0 = book_metrics(ovl, *DEV_D)
    b1 = book_metrics(vet, *DEV_D)
    rel_dd = (b0["maxdd"] - b1["maxdd"]) / b0["maxdd"]
    d_sr = b1["sr"] - b0["sr"]
    rel_cvar = (b1["cvar5"] - b0["cvar5"]) / abs(b0["cvar5"])

    veto_days = m[(m < 1.0) & (m.index >= DEV_D[0]) & (m.index <= DEV_D[1])]
    per_year = veto_days.groupby(veto_days.index.year).size().to_dict()

    verdict = "PASS" if (rel_dd >= 0.20 and d_sr >= -0.05) else "STOP"
    res = {
        "experiment": "llm_c2_veto_ovl", "probe": "P0_oracle",
        "window_D": list(DEV_D), "budget_per_year": VETO_BUDGET_PER_YEAR,
        "book": b0, "oracle_vetoed": b1,
        "rel_maxdd_reduction": rel_dd, "d_sr": d_sr,
        "rel_cvar5_improvement": rel_cvar,
        "veto_days_per_year": {str(k): int(v) for k, v in per_year.items()},
        "veto_days": [str(d.date()) for d in veto_days.index],
        "criteria": {"rel_maxdd_reduction_min": 0.20, "d_sr_min": -0.05},
        "verdict": verdict,
    }
    OUT.write_text(json.dumps(res, indent=1, default=float))

    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    row = {"ts_utc": datetime.now(timezone.utc).isoformat(),
           "experiment": "llm_c2_veto_ovl", "cell": "P0_oracle",
           "model": "oracle_foresight",
           "config": {"k_per_year": VETO_BUDGET_PER_YEAR, "m_veto": 0.0,
                      "book": "ewma_20 eq_h1 top200 + vt15_naive20_b100"},
           "config_hash": "p0-oracle-k10-m0", "git_commit": commit,
           "window": list(DEV_D),
           "metrics": {"sr_book": b0["sr"], "sr_veto": b1["sr"],
                       "maxdd_book": b0["maxdd"], "maxdd_veto": b1["maxdd"],
                       "rel_maxdd_reduction": rel_dd, "d_sr": d_sr,
                       "rel_cvar5_improvement": rel_cvar}}
    with LEDGER.open("a") as f:
        f.write(json.dumps(row, default=float) + "\n")

    print(f"D book:   SR {b0['sr']:+.3f}  MaxDD {b0['maxdd']:.2%}  CVaR5 {b0['cvar5']:.4f}")
    print(f"D oracle: SR {b1['sr']:+.3f}  MaxDD {b1['maxdd']:.2%}  CVaR5 {b1['cvar5']:.4f}")
    print(f"rel MaxDD reduction {rel_dd:.1%} | dSR {d_sr:+.3f} | rel CVaR5 {rel_cvar:+.1%}")
    print(f"P0 verdict: {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

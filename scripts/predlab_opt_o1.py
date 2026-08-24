"""O-02 / stage O1 — signal-construction sweep (registered: predlab_opt.stages.O1).

Two subcommands:
  register  — freeze the O1 grid into gates.json (refuses if already frozen)
  run       — execute the frozen grid; one ledger row per config; results JSON

All configs use the incumbent portfolio parameters (eq weighting, quintiles,
smooth 1, cadence 1, no buffer, top-200 universe, 5bp + funding). Full-window
runs 2021-01-01 -> 2026-07-01 with D/V split metrics per the predlab_opt
adoption rule. The incumbent park_5 is re-run on the same full window as a
REFERENCE row (config already ledgered in predlab_pp; not a new trial).
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

from tradingagents.predlab import opt, pp, registry  # noqa: E402

DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))
GATES = DATA_ROOT / "predlab" / "gates.json"
OUT = DATA_ROOT / "predlab" / "opt_o1_results.json"
FUND_CACHE = DATA_ROOT / "predlab" / "opt_funding_daily.parquet"
FULL = ("2021-01-01", "2026-07-01")

GRID = ["park_3", "park_10", "park_20",
        "cc_5", "cc_10", "cc_20",
        "vov_10", "vov_20",
        "ewma_5", "ewma_10", "ewma_20"]
REFERENCE = "park_5"


def register() -> None:
    gates = json.loads(GATES.read_text())
    stages = gates["predlab_opt"]["stages"]
    if "O1" in stages:
        print("stage O1 already frozen — refusing")
        sys.exit(1)
    stages["O1"] = {
        "frozen_utc": "2026-07-31",
        "axis": "signal construction",
        "grid": GRID,
        "n_configs": len(GRID),
        "reference": REFERENCE + " (incumbent, not a new trial)",
        "portfolio_params": "incumbent eq_h1 defaults (eq, quintile, smooth 1, cadence 1, no buffer, top-200, 5bp+funding)",
        "window": list(FULL),
    }
    GATES.write_text(json.dumps(gates, indent=1))
    print(f"frozen stage O1: {len(GRID)} configs")


def inputs():
    from predlab_t7 import build_panels

    panels = build_panels()
    close, qv, park = panels["close"], panels["qv"], panels["park"]
    hi = pd.Timestamp(FULL[1], tz="UTC")
    close = close[close.index <= hi]
    qv, park = qv.loc[close.index], park.loc[close.index]
    # engine_correction_2026-08-24: simple returns — position PnL, never log
    ret = close.pct_change(fill_method=None)
    uni = opt.monthly_universe(qv, top_n=200)
    if FUND_CACHE.exists():
        fund = pd.read_parquet(FUND_CACHE).reindex(ret.index)
    else:
        used = sorted(uni.columns[uni.any(axis=0)])
        fund = pp.build_funding_daily(used, DATA_ROOT / "xsect" / "funding", ret.index)
        fund.to_parquet(FUND_CACHE)
    return close, park, ret, uni, fund


def run() -> None:
    gates = json.loads(GATES.read_text())
    stage = gates["predlab_opt"]["stages"].get("O1")
    if stage is None:
        print("stage O1 not frozen — run `register` first")
        sys.exit(1)
    if OUT.exists():
        print(f"results exist ({OUT}) — refusing to overwrite (stop rule)")
        sys.exit(1)
    close, park, ret, uni, fund = inputs()
    cfg = opt.OptConfig()
    res = {"stage": "O1", "window": list(FULL), "configs": {}}

    def one(kind: str, is_ref: bool) -> dict:
        sig = opt.build_signal(park, close, kind)
        r = opt.run_ls(sig, ret, uni, fund, cfg, *FULL)
        ev = opt.evaluate(r, opt.DESIGN_D, opt.VALIDATION_V, opt.SUBPERIODS_O)
        row = {"sr_net_full": ev["full"]["sr_net"], "sr_net_D": ev["D"]["sr_net"],
               "sr_net_V": ev["V"]["sr_net"], "maxdd": ev["full"]["maxdd"],
               "avg_turnover": ev["full"]["avg_turnover"],
               "n_days": ev["full"]["n_days"],
               "subperiods": ev["subperiods"],
               "max_name_share": ev["max_name_share"], "max_name": ev["max_name"],
               "sr_net_2x_costs": ev["sr_net_2x_costs"]}
        tag = "REF " if is_ref else ""
        registry.log_trial("predlab_opt", "O1_signal", ("ref_" if is_ref else "") + kind,
                           {"signal": kind, "portfolio": "eq_h1 defaults",
                            "reference": is_ref}, FULL,
                           {k: row[k] for k in ("sr_net_full", "sr_net_D", "sr_net_V",
                                                "maxdd", "avg_turnover")})
        print(f"{tag}{kind}: full {row['sr_net_full']:+.3f} "
              f"D {row['sr_net_D']:+.3f} V {row['sr_net_V']:+.3f} "
              f"dd {row['maxdd']:.1%} turn {row['avg_turnover']:.2f} "
              f"conc {row['max_name_share']:.2%} ({row['max_name']})", flush=True)
        return row

    res["reference"] = {REFERENCE: one(REFERENCE, True)}
    for kind in stage["grid"]:
        res["configs"][kind] = one(kind, False)

    ref_sr = res["reference"][REFERENCE]["sr_net_full"]
    assessment = {}
    for kind, row in res["configs"].items():
        clears_sr = row["sr_net_full"] >= ref_sr + 0.10
        consistent = row["sr_net_V"] >= 0.5 * row["sr_net_D"]
        conc_ok = row["max_name_share"] <= 0.50
        assessment[kind] = {"clears_sr": bool(clears_sr),
                            "consistent": bool(consistent),
                            "conc_ok": bool(conc_ok),
                            "candidate": bool(clears_sr and consistent and conc_ok)}
    res["incumbent_sr_full"] = ref_sr
    res["assessment"] = assessment
    cands = [k for k, a in assessment.items() if a["candidate"]]
    res["adoption_candidates"] = cands
    print(f"\nincumbent full SR {ref_sr:+.3f}; adoption candidates: {cands or 'NONE'}")
    OUT.write_text(json.dumps(res, indent=1, default=float))
    print(f"written {OUT}")


if __name__ == "__main__":
    {"register": register, "run": run}[sys.argv[1]]()

"""O-03 / stage O2 — portfolio-construction sweep (predlab_opt.stages.O2).

Signal fixed at the chain-seq-1 champion (ewma_20). 12 configs frozen
pre-run: quantile width, weighting, turnover buffer bands, rebalance
cadence, + 2 pre-declared interaction configs. Same full-window protocol
and adoption rule as O1; incumbent = ewma_20 eq_h1 defaults (full +1.928).

Subcommands: register | run
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from tradingagents.predlab import opt, registry  # noqa: E402

DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))
GATES = DATA_ROOT / "predlab" / "gates.json"
OUT = DATA_ROOT / "predlab" / "opt_o2_results.json"
FULL = ("2021-01-01", "2026-07-01")
SIGNAL = "ewma_20"

GRID: "dict[str, dict]" = {
    "decile": {"q_frac": 0.1},
    "tercile": {"q_frac": 1 / 3},
    "rank": {"weighting": "rank"},
    "ivol": {"weighting": "ivol"},
    "buf25": {"buffer": 0.25},
    "buf50": {"buffer": 0.5},
    "buf100": {"buffer": 1.0},
    "cad2": {"cadence": 2},
    "cad3": {"cadence": 3},
    "cad5": {"cadence": 5},
    "decile_ivol": {"q_frac": 0.1, "weighting": "ivol"},
    "buf50_cad2": {"buffer": 0.5, "cadence": 2},
}


def register() -> None:
    gates = json.loads(GATES.read_text())
    stages = gates["predlab_opt"]["stages"]
    if "O2" in stages:
        print("stage O2 already frozen — refusing")
        sys.exit(1)
    stages["O2"] = {
        "frozen_utc": "2026-08-03",
        "axis": "portfolio construction",
        "signal": SIGNAL + " (chain seq 1 champion)",
        "grid": GRID,
        "n_configs": len(GRID),
        "reference": "ewma_20 eq_h1 defaults (incumbent, not a new trial)",
        "window": list(FULL),
    }
    GATES.write_text(json.dumps(gates, indent=1))
    print(f"frozen stage O2: {len(GRID)} configs")


def run() -> None:
    gates = json.loads(GATES.read_text())
    stage = gates["predlab_opt"]["stages"].get("O2")
    if stage is None:
        print("stage O2 not frozen — run `register` first")
        sys.exit(1)
    if OUT.exists():
        print(f"results exist ({OUT}) — refusing to overwrite (stop rule)")
        sys.exit(1)
    from predlab_opt_o1 import inputs

    close, park, ret, uni, fund = inputs()
    sig = opt.build_signal(park, close, SIGNAL)
    res = {"stage": "O2", "signal": SIGNAL, "window": list(FULL), "configs": {}}

    def one(name: str, overrides: dict, is_ref: bool) -> dict:
        cfg = opt.OptConfig(signal=SIGNAL, **overrides)
        r = opt.run_ls(sig, ret, uni, fund, cfg, *FULL)
        ev = opt.evaluate(r, opt.DESIGN_D, opt.VALIDATION_V, opt.SUBPERIODS_O)
        row = {"sr_net_full": ev["full"]["sr_net"], "sr_net_D": ev["D"]["sr_net"],
               "sr_net_V": ev["V"]["sr_net"], "maxdd": ev["full"]["maxdd"],
               "avg_turnover": ev["full"]["avg_turnover"],
               "n_days": ev["full"]["n_days"], "subperiods": ev["subperiods"],
               "max_name_share": ev["max_name_share"], "max_name": ev["max_name"],
               "sr_net_2x_costs": ev["sr_net_2x_costs"]}
        registry.log_trial("predlab_opt", "O2_portfolio",
                           ("ref_" if is_ref else "") + name,
                           {"signal": SIGNAL, "overrides": overrides,
                            "reference": is_ref}, FULL,
                           {k: row[k] for k in ("sr_net_full", "sr_net_D", "sr_net_V",
                                                "maxdd", "avg_turnover")})
        subs_pos = sum(1 for x in row["subperiods"].values() if x > 0)
        print(f"{'REF ' if is_ref else ''}{name}: full {row['sr_net_full']:+.3f} "
              f"D {row['sr_net_D']:+.3f} V {row['sr_net_V']:+.3f} "
              f"dd {row['maxdd']:.1%} turn {row['avg_turnover']:.2f} "
              f"2x {row['sr_net_2x_costs']:+.3f} subs {subs_pos}/4 "
              f"conc {row['max_name_share']:.2%}", flush=True)
        return row

    res["reference"] = {"eq_h1": one("eq_h1", {}, True)}
    for name, ov in GRID.items():
        res["configs"][name] = one(name, ov, False)

    ref = res["reference"]["eq_h1"]
    assessment = {}
    for name, row in res["configs"].items():
        subs_pos = sum(1 for x in row["subperiods"].values() if x > 0)
        assessment[name] = {
            "clears_sr": bool(row["sr_net_full"] >= ref["sr_net_full"] + 0.10),
            "consistent": bool(row["sr_net_V"] >= 0.5 * row["sr_net_D"]),
            "subs_ok": bool(subs_pos >= 3),
            "dd_ok": bool(row["maxdd"] <= 1.25 * ref["maxdd"]),
            "conc_ok": bool(row["max_name_share"] <= 0.50)}
        assessment[name]["candidate"] = all(assessment[name].values())
    res["incumbent_sr_full"] = ref["sr_net_full"]
    res["assessment"] = assessment
    cands = [k for k, a in assessment.items() if a["candidate"]]
    res["adoption_candidates"] = cands
    print(f"\nincumbent full SR {ref['sr_net_full']:+.3f}; candidates: {cands or 'NONE'}")
    OUT.write_text(json.dumps(res, indent=1, default=float))
    print(f"written {OUT}")


if __name__ == "__main__":
    {"register": register, "run": run}[sys.argv[1]]()

"""O-04 / stage O3 — universe sweep (predlab_opt.stages.O3).

Signal = ewma_20 champion, portfolio = incumbent eq-quintile-daily.
Varies the monthly PIT universe: top-N by prior-month median quote volume
{100,150,300} and ADV floors {1M,5M,20M USD} (PIT, prior-month median),
plus pre-declared combos. 9 configs frozen pre-run. Single-name PnL share
> 50% = config FAIL (registered, §50 lesson).

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
OUT = DATA_ROOT / "predlab" / "opt_o3_results.json"
FULL = ("2021-01-01", "2026-07-01")
SIGNAL = "ewma_20"

GRID: "dict[str, dict]" = {
    "topn100": {"top_n": 100},
    "topn150": {"top_n": 150},
    "topn300": {"top_n": 300},
    "adv1m": {"top_n": 200, "adv_floor": 1e6},
    "adv5m": {"top_n": 200, "adv_floor": 5e6},
    "adv20m": {"top_n": 200, "adv_floor": 2e7},
    "topn150_adv5m": {"top_n": 150, "adv_floor": 5e6},
    "topn300_adv5m": {"top_n": 300, "adv_floor": 5e6},
    "topn300_adv20m": {"top_n": 300, "adv_floor": 2e7},
}


def register() -> None:
    gates = json.loads(GATES.read_text())
    stages = gates["predlab_opt"]["stages"]
    if "O3" in stages:
        print("stage O3 already frozen — refusing")
        sys.exit(1)
    stages["O3"] = {
        "frozen_utc": "2026-08-03",
        "axis": "universe",
        "signal": SIGNAL + " (chain seq 1 champion)",
        "portfolio": "eq-quintile-daily incumbent",
        "grid": GRID,
        "n_configs": len(GRID),
        "reference": "top-200 no floor (incumbent, not a new trial)",
        "window": list(FULL),
    }
    GATES.write_text(json.dumps(gates, indent=1))
    print(f"frozen stage O3: {len(GRID)} configs")


def run() -> None:
    gates = json.loads(GATES.read_text())
    if gates["predlab_opt"]["stages"].get("O3") is None:
        print("stage O3 not frozen — run `register` first")
        sys.exit(1)
    if OUT.exists():
        print(f"results exist ({OUT}) — refusing to overwrite (stop rule)")
        sys.exit(1)
    from predlab_opt_o1 import inputs

    close, park, ret, uni200, fund = inputs()
    import pandas as pd
    qv = pd.read_parquet(DATA_ROOT / "predlab" / "t7_panels" / "qv.parquet")
    qv = qv.loc[qv.index <= pd.Timestamp(FULL[1], tz="UTC")]
    sig = opt.build_signal(park, close, SIGNAL)
    cfg = opt.OptConfig(signal=SIGNAL)
    res = {"stage": "O3", "signal": SIGNAL, "window": list(FULL), "configs": {}}

    def one(name: str, spec: dict, is_ref: bool) -> dict:
        u = uni200 if is_ref else opt.monthly_universe(qv, top_n=spec["top_n"])
        if not is_ref and spec.get("adv_floor", 0) > 0:
            u = opt.apply_adv_floor(u, qv, spec["adv_floor"])
        r = opt.run_ls(sig, ret, u, fund, cfg, *FULL)
        ev = opt.evaluate(r, opt.DESIGN_D, opt.VALIDATION_V, opt.SUBPERIODS_O)
        row = {"sr_net_full": ev["full"]["sr_net"], "sr_net_D": ev["D"]["sr_net"],
               "sr_net_V": ev["V"]["sr_net"], "maxdd": ev["full"]["maxdd"],
               "avg_turnover": ev["full"]["avg_turnover"],
               "n_days": ev["full"]["n_days"], "subperiods": ev["subperiods"],
               "max_name_share": ev["max_name_share"], "max_name": ev["max_name"],
               "sr_net_2x_costs": ev["sr_net_2x_costs"]}
        registry.log_trial("predlab_opt", "O3_universe",
                           ("ref_" if is_ref else "") + name,
                           {"signal": SIGNAL, "universe": spec,
                            "reference": is_ref}, FULL,
                           {k: row[k] for k in ("sr_net_full", "sr_net_D", "sr_net_V",
                                                "maxdd", "avg_turnover")})
        subs_pos = sum(1 for x in row["subperiods"].values() if x > 0)
        print(f"{'REF ' if is_ref else ''}{name}: full {row['sr_net_full']:+.3f} "
              f"D {row['sr_net_D']:+.3f} V {row['sr_net_V']:+.3f} "
              f"dd {row['maxdd']:.1%} turn {row['avg_turnover']:.2f} "
              f"2x {row['sr_net_2x_costs']:+.3f} subs {subs_pos}/4 "
              f"conc {row['max_name_share']:.2%} ({row['max_name']})", flush=True)
        return row

    res["reference"] = {"top200": one("top200", {"top_n": 200}, True)}
    for name, spec in GRID.items():
        res["configs"][name] = one(name, spec, False)

    ref = res["reference"]["top200"]
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

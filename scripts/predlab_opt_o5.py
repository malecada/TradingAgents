"""O-06 / stage O5 — funding-carry tilt inside the book (predlab_opt.stages.O5).

Prior disclosed: standalone XS carry NEGATIVE (§46). Different mechanism
here: weights only REDISTRIBUTE within the already-selected low-vol legs
(engine renorms legs to +/-1), so the alpha book is unchanged in
membership and the tilt can only re-weight carry-friendly names.

Tilt: per leg, rank names by trailing-mean funding (shifted 1d); linear
multiplier 1+lam (carry-best) .. 1-lam (carry-worst); missing funding ->
1. Long leg prefers LOW funding (pay less / get paid), short leg prefers
HIGH funding (collect). `rev` configs flip the direction — mechanism
check: if carry tilt helps for carry reasons, reverse must hurt.

Grid: lam {0.25,0.5,1.0} x window {7,30} = 6 + rev lam 0.5 x {7,30} = 8.
Judged on the RAW book vs incumbent raw (+1.928) under the standard
adoption rule (overlay reapplied only on adoption).

Subcommands: register | run
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

DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))
GATES = DATA_ROOT / "predlab" / "gates.json"
OUT = DATA_ROOT / "predlab" / "opt_o5_results.json"
FULL = ("2021-01-01", "2026-07-01")

GRID: "dict[str, dict]" = {}
for lam in (0.25, 0.5, 1.0):
    for win in (7, 30):
        GRID[f"carry_l{int(lam*100)}_w{win}"] = {"lam": lam, "win": win, "rev": False}
GRID["rev_l50_w7"] = {"lam": 0.5, "win": 7, "rev": True}
GRID["rev_l50_w30"] = {"lam": 0.5, "win": 30, "rev": True}


def register() -> None:
    gates = json.loads(GATES.read_text())
    stages = gates["predlab_opt"]["stages"]
    if "O5" in stages:
        print("stage O5 already frozen — refusing")
        sys.exit(1)
    stages["O5"] = {
        "frozen_utc": "2026-08-03",
        "axis": "funding-carry tilt inside book (prior: standalone carry NEGATIVE §46)",
        "base_book": "ewma_20 eq-quintile-daily top-200 (chain seq 1)",
        "grid": GRID,
        "n_configs": len(GRID),
        "mechanism_check": "rev_* must not outperform its carry twin, else effect is not carry",
        "window": list(FULL),
    }
    GATES.write_text(json.dumps(gates, indent=1))
    print(f"frozen stage O5: {len(GRID)} configs")


def make_tilt(fund_ma: pd.DataFrame, lam: float, rev: bool):
    def tilt(d, w):
        if d not in fund_ma.index:
            return w
        f = fund_ma.loc[d].reindex(w.index)
        out = w.copy()
        for leg_mask, prefer_low in ((w > 0, True), (w < 0, False)):
            names = w.index[leg_mask]
            if len(names) < 2:
                continue
            fv = f[names]
            ranked = fv.rank(ascending=prefer_low, na_option="keep")  # 1 = best carry
            n_ok = int(ranked.notna().sum())
            if n_ok < 2:
                continue
            mult = pd.Series(1.0, index=names)
            direction = -1.0 if rev else 1.0
            mult[ranked.notna()] = 1.0 + direction * lam * (
                1.0 - 2.0 * (ranked[ranked.notna()] - 1) / (n_ok - 1))
            mult = mult.clip(lower=0.0)
            out[names] = w[names] * mult
        return out
    return tilt


def run() -> None:
    gates = json.loads(GATES.read_text())
    if gates["predlab_opt"]["stages"].get("O5") is None:
        print("stage O5 not frozen — run `register` first")
        sys.exit(1)
    if OUT.exists():
        print(f"results exist ({OUT}) — refusing to overwrite (stop rule)")
        sys.exit(1)
    from predlab_opt_o1 import inputs

    close, park, ret, uni, fund = inputs()
    sig = opt.build_signal(park, close, "ewma_20")
    cfg = opt.OptConfig()
    ref = opt.run_ls(sig, ret, uni, fund, cfg, *FULL)
    res = {"stage": "O5", "raw_ref": {"sr_net": ref["sr_net"], "maxdd": ref["maxdd"]},
           "configs": {}}
    print(f"REF raw book: SR {ref['sr_net']:+.3f} carry_sum "
          f"{ref['rets']['carry'].sum():+.4f}", flush=True)

    for name, spec in GRID.items():
        fund_ma = fund.rolling(spec["win"]).mean().shift(1)
        r = opt.run_ls(sig, ret, uni, fund, cfg, *FULL,
                       tilt=make_tilt(fund_ma, spec["lam"], spec["rev"]))
        ev = opt.evaluate(r, opt.DESIGN_D, opt.VALIDATION_V, opt.SUBPERIODS_O)
        row = {"sr_net_full": ev["full"]["sr_net"], "sr_net_D": ev["D"]["sr_net"],
               "sr_net_V": ev["V"]["sr_net"], "maxdd": ev["full"]["maxdd"],
               "avg_turnover": ev["full"]["avg_turnover"],
               "carry_sum": float(r["rets"]["carry"].sum()),
               "subperiods": ev["subperiods"],
               "max_name_share": ev["max_name_share"],
               "sr_net_2x_costs": ev["sr_net_2x_costs"]}
        res["configs"][name] = row
        registry.log_trial("predlab_opt", "O5_funding_tilt", name, spec, FULL,
                           {k: row[k] for k in ("sr_net_full", "sr_net_D", "sr_net_V",
                                                "maxdd", "carry_sum")})
        subs_pos = sum(1 for x in row["subperiods"].values() if x > 0)
        print(f"{name}: full {row['sr_net_full']:+.3f} D {row['sr_net_D']:+.3f} "
              f"V {row['sr_net_V']:+.3f} dd {row['maxdd']:.1%} "
              f"carry {row['carry_sum']:+.4f} turn {row['avg_turnover']:.2f} "
              f"subs {subs_pos}/4", flush=True)

    ref_sr = ref["sr_net"]
    assessment = {}
    for name, row in res["configs"].items():
        subs_pos = sum(1 for x in row["subperiods"].values() if x > 0)
        assessment[name] = {
            "clears_sr": bool(row["sr_net_full"] >= ref_sr + 0.10),
            "consistent": bool(row["sr_net_V"] >= 0.5 * row["sr_net_D"]),
            "subs_ok": bool(subs_pos >= 3),
            "dd_ok": bool(row["maxdd"] <= 1.25 * ref["maxdd"]),
            "conc_ok": bool(row["max_name_share"] <= 0.50)}
        assessment[name]["candidate"] = all(assessment[name].values()) \
            and not name.startswith("rev_")
    res["assessment"] = assessment
    cands = [k for k, a in assessment.items() if a["candidate"]]
    res["adoption_candidates"] = cands
    print(f"\nincumbent raw SR {ref_sr:+.3f}; candidates: {cands or 'NONE'}")
    OUT.write_text(json.dumps(res, indent=1, default=float))
    print(f"written {OUT}")


if __name__ == "__main__":
    {"register": register, "run": run}[sys.argv[1]]()

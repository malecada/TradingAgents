"""O-08 / stage O7 — momentum/trend tilt inside the book
(predlab_opt.stages.O7).

Disclosed priors: standalone XS momentum NEGATIVE (§43), wide-universe
trend NEGATIVE (§45); O2/O5/O6 showed within-leg tilts consistently hurt
this equal-weight book. Registered axis nonetheless — tested honestly.

Family A (tilt): within-leg multiplier 1 + lam*z, z = cross-sectional
z-score of skip-5 momentum (r over `win` days ending t-5, shift 1),
clipped to [-2,2]; lam=0.5; both directions (toward winners / losers).
Family B (gate): drop names fighting their own SMA trend (long leg needs
close > SMA_k, short leg close < SMA_k, shift 1); legs renorm.

Subcommands: register | run
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from tradingagents.predlab import opt, registry  # noqa: E402

DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))
GATES = DATA_ROOT / "predlab" / "gates.json"
OUT = DATA_ROOT / "predlab" / "opt_o7_results.json"
FULL = ("2021-01-01", "2026-07-01")

GRID: "dict[str, dict]" = {
    "mom30_win": {"family": "tilt", "win": 30, "lam": 0.5},
    "mom90_win": {"family": "tilt", "win": 90, "lam": 0.5},
    "mom180_win": {"family": "tilt", "win": 180, "lam": 0.5},
    "mom30_lose": {"family": "tilt", "win": 30, "lam": -0.5},
    "mom90_lose": {"family": "tilt", "win": 90, "lam": -0.5},
    "mom180_lose": {"family": "tilt", "win": 180, "lam": -0.5},
    "gate_sma100": {"family": "gate", "sma": 100},
    "gate_sma200": {"family": "gate", "sma": 200},
}


def register() -> None:
    gates = json.loads(GATES.read_text())
    stages = gates["predlab_opt"]["stages"]
    if "O7" in stages:
        print("stage O7 already frozen — refusing")
        sys.exit(1)
    stages["O7"] = {
        "frozen_utc": "2026-08-04",
        "axis": "momentum/trend tilt inside book (priors: §43/§45 standalone NEGATIVE, disclosed)",
        "base_book": "ewma_20 eq-quintile-daily top-200 (chain seq 1)",
        "grid": GRID,
        "n_configs": len(GRID),
        "window": list(FULL),
    }
    GATES.write_text(json.dumps(gates, indent=1))
    print(f"frozen stage O7: {len(GRID)} configs")


def run() -> None:
    gates = json.loads(GATES.read_text())
    if gates["predlab_opt"]["stages"].get("O7") is None:
        print("stage O7 not frozen — run `register` first")
        sys.exit(1)
    if OUT.exists():
        print(f"results exist ({OUT}) — refusing to overwrite (stop rule)")
        sys.exit(1)
    from predlab_opt_o1 import inputs

    close, park, ret, uni, fund = inputs()
    sig = opt.build_signal(park, close, "ewma_20")
    cfg = opt.OptConfig()
    ref = opt.run_ls(sig, ret, uni, fund, cfg, *FULL)
    res = {"stage": "O7", "raw_ref": {"sr_net": ref["sr_net"], "maxdd": ref["maxdd"]},
           "configs": {}}
    print(f"REF raw book: SR {ref['sr_net']:+.3f} dd {ref['maxdd']:.1%}", flush=True)

    def tilt_factory(spec):
        if spec["family"] == "tilt":
            mom = close.pct_change(spec["win"]).shift(5 + 1)
            lam = spec["lam"]

            def tilt(d, w):
                if d not in mom.index:
                    return w
                m = mom.loc[d].reindex(w.index)
                out = w.copy()
                for leg_mask in (w > 0, w < 0):
                    names = w.index[leg_mask]
                    if len(names) < 3:
                        continue
                    z = (m[names] - m[names].mean())
                    sd = z.std()
                    if not sd or pd.isna(sd):
                        continue
                    z = (z / sd).clip(-2, 2).fillna(0.0)
                    out[names] = w[names] * (1.0 + lam * z).clip(lower=0.05)
                return out
            return tilt
        sma = close.rolling(spec["sma"]).mean()
        above = (close > sma).shift(1)

        def gate(d, w):
            if d not in above.index:
                return w
            a = above.loc[d].reindex(w.index)
            out = w.copy()
            out[(w > 0) & (a == False)] = 0.0  # noqa: E712
            out[(w < 0) & (a == True)] = 0.0  # noqa: E712
            return out
        return gate

    for name, spec in GRID.items():
        r = opt.run_ls(sig, ret, uni, fund, cfg, *FULL, tilt=tilt_factory(spec))
        ev = opt.evaluate(r, opt.DESIGN_D, opt.VALIDATION_V, opt.SUBPERIODS_O)
        row = {"sr_net_full": ev["full"]["sr_net"], "sr_net_D": ev["D"]["sr_net"],
               "sr_net_V": ev["V"]["sr_net"], "maxdd": ev["full"]["maxdd"],
               "avg_turnover": ev["full"]["avg_turnover"],
               "subperiods": ev["subperiods"],
               "max_name_share": ev["max_name_share"],
               "sr_net_2x_costs": ev["sr_net_2x_costs"]}
        res["configs"][name] = row
        registry.log_trial("predlab_opt", "O7_momentum_tilt", name, spec, FULL,
                           {k: row[k] for k in ("sr_net_full", "sr_net_D",
                                                "sr_net_V", "maxdd")})
        subs_pos = sum(1 for x in row["subperiods"].values() if x > 0)
        print(f"{name}: full {row['sr_net_full']:+.3f} D {row['sr_net_D']:+.3f} "
              f"V {row['sr_net_V']:+.3f} dd {row['maxdd']:.1%} "
              f"turn {row['avg_turnover']:.2f} subs {subs_pos}/4", flush=True)

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
        assessment[name]["candidate"] = all(assessment[name].values())
    res["assessment"] = assessment
    cands = [k for k, a in assessment.items() if a["candidate"]]
    res["adoption_candidates"] = cands
    print(f"\nincumbent raw SR {ref_sr:+.3f}; candidates: {cands or 'NONE'}")
    OUT.write_text(json.dumps(res, indent=1, default=float))
    print(f"written {OUT}")


if __name__ == "__main__":
    {"register": register, "run": run}[sys.argv[1]]()

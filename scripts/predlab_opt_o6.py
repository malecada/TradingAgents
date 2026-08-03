"""O-07 / stage O6 — volume/liquidity weighting inside the book
(predlab_opt.stages.O6).

The P5-usable LGB volume champions cover BTC/ETH only — they cannot weight
a 200-name cross-section directly. Dominance design instead: weight legs by
(a) PIT trailing quote-volume (what a deployable liquidity weighting can
use), and (b) ORACLE future volume (perfect-foresight upper bound on ANY
volume forecast, incl. per-alt LGB generalization — DIAGNOSTIC ONLY, never
adoptable). If the oracle itself cannot clear the adoption floor, the whole
forecast-based-weighting axis is closed without building per-alt models
(predlab_p6 alt-generalization claim untouched).

Weightings via the leg-preserving tilt hook (multiplier within leg, legs
renormed to +/-1): qv ∝ trailing median qv, qv_sqrt ∝ sqrt(same),
qv_inv ∝ 1/same (small-name tilt), oracle ∝ realized NEXT-k-day mean qv.

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
OUT = DATA_ROOT / "predlab" / "opt_o6_results.json"
FULL = ("2021-01-01", "2026-07-01")

GRID: "dict[str, dict]" = {
    "qv_w7": {"kind": "qv", "win": 7},
    "qv_w30": {"kind": "qv", "win": 30},
    "qv_sqrt_w7": {"kind": "qv_sqrt", "win": 7},
    "qv_sqrt_w30": {"kind": "qv_sqrt", "win": 30},
    "qv_inv_w7": {"kind": "qv_inv", "win": 7},
    "qv_inv_w30": {"kind": "qv_inv", "win": 30},
    "oracle_next1": {"kind": "oracle", "win": 1, "diagnostic": True},
    "oracle_next7": {"kind": "oracle", "win": 7, "diagnostic": True},
}


def register() -> None:
    gates = json.loads(GATES.read_text())
    stages = gates["predlab_opt"]["stages"]
    if "O6" in stages:
        print("stage O6 already frozen — refusing")
        sys.exit(1)
    stages["O6"] = {
        "frozen_utc": "2026-08-03",
        "axis": "volume/liquidity weighting (dominance design; LGB champions are BTC/ETH-only)",
        "base_book": "ewma_20 eq-quintile-daily top-200 (chain seq 1)",
        "grid": GRID,
        "n_configs": len(GRID),
        "diagnostic_rule": ("oracle_* use FUTURE volume: upper bound on any volume "
                            "forecast; NEVER adoptable; if oracle < adoption floor, "
                            "forecast-weighting axis closes without per-alt models"),
        "window": list(FULL),
    }
    GATES.write_text(json.dumps(gates, indent=1))
    print(f"frozen stage O6: {len(GRID)} configs")


def make_tilt(measure: pd.DataFrame):
    """Multiplier proportional to `measure` within each leg (NaN -> leg mean)."""
    def tilt(d, w):
        if d not in measure.index:
            return w
        m = measure.loc[d].reindex(w.index)
        out = w.copy()
        for leg_mask in (w > 0, w < 0):
            names = w.index[leg_mask]
            if len(names) < 2:
                continue
            mv = m[names]
            if mv.notna().sum() < 2:
                continue
            mv = mv.fillna(mv.mean())
            lo = mv[mv > 0].min() if (mv > 0).any() else 1.0
            mv = mv.clip(lower=lo * 1e-3)
            out[names] = w[names] * mv
        return out
    return tilt


def run() -> None:
    gates = json.loads(GATES.read_text())
    if gates["predlab_opt"]["stages"].get("O6") is None:
        print("stage O6 not frozen — run `register` first")
        sys.exit(1)
    if OUT.exists():
        print(f"results exist ({OUT}) — refusing to overwrite (stop rule)")
        sys.exit(1)
    from predlab_opt_o1 import inputs

    close, park, ret, uni, fund = inputs()
    qv = pd.read_parquet(DATA_ROOT / "predlab" / "t7_panels" / "qv.parquet")
    qv = qv.loc[qv.index <= pd.Timestamp(FULL[1], tz="UTC")]
    sig = opt.build_signal(park, close, "ewma_20")
    cfg = opt.OptConfig()
    ref = opt.run_ls(sig, ret, uni, fund, cfg, *FULL)
    res = {"stage": "O6", "raw_ref": {"sr_net": ref["sr_net"], "maxdd": ref["maxdd"]},
           "configs": {}}
    print(f"REF raw book: SR {ref['sr_net']:+.3f}", flush=True)

    for name, spec in GRID.items():
        k, win = spec["kind"], spec["win"]
        if k == "oracle":
            measure = qv.rolling(win).mean().shift(-win)  # FUTURE volume (diagnostic)
        else:
            base = qv.rolling(win).median().shift(1)
            measure = {"qv": base, "qv_sqrt": np.sqrt(base),
                       "qv_inv": 1.0 / base}[k]
        r = opt.run_ls(sig, ret, uni, fund, cfg, *FULL, tilt=make_tilt(measure))
        ev = opt.evaluate(r, opt.DESIGN_D, opt.VALIDATION_V, opt.SUBPERIODS_O)
        row = {"sr_net_full": ev["full"]["sr_net"], "sr_net_D": ev["D"]["sr_net"],
               "sr_net_V": ev["V"]["sr_net"], "maxdd": ev["full"]["maxdd"],
               "avg_turnover": ev["full"]["avg_turnover"],
               "subperiods": ev["subperiods"],
               "max_name_share": ev["max_name_share"],
               "sr_net_2x_costs": ev["sr_net_2x_costs"],
               "diagnostic": bool(spec.get("diagnostic", False))}
        res["configs"][name] = row
        registry.log_trial("predlab_opt", "O6_volume_weighting", name, spec, FULL,
                           {k2: row[k2] for k2 in ("sr_net_full", "sr_net_D",
                                                   "sr_net_V", "maxdd")})
        subs_pos = sum(1 for x in row["subperiods"].values() if x > 0)
        print(f"{'DIAG ' if row['diagnostic'] else ''}{name}: "
              f"full {row['sr_net_full']:+.3f} D {row['sr_net_D']:+.3f} "
              f"V {row['sr_net_V']:+.3f} dd {row['maxdd']:.1%} "
              f"turn {row['avg_turnover']:.2f} subs {subs_pos}/4 "
              f"conc {row['max_name_share']:.2%}", flush=True)

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
            and not row["diagnostic"]
    res["assessment"] = assessment
    cands = [k for k, a in assessment.items() if a["candidate"]]
    res["adoption_candidates"] = cands
    oracle_best = max(res["configs"][k]["sr_net_full"]
                      for k in ("oracle_next1", "oracle_next7"))
    res["oracle_best_sr"] = oracle_best
    res["axis_dominance_closed"] = bool(oracle_best < ref_sr + 0.10)
    print(f"\nincumbent raw SR {ref_sr:+.3f}; candidates: {cands or 'NONE'}; "
          f"oracle best {oracle_best:+.3f} -> forecast axis "
          f"{'CLOSED by dominance' if res['axis_dominance_closed'] else 'still open'}")
    OUT.write_text(json.dumps(res, indent=1, default=float))
    print(f"written {OUT}")


if __name__ == "__main__":
    {"register": register, "run": run}[sys.argv[1]]()

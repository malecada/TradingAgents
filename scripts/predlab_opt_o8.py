"""O-09 / stage O8 — final composition + champion freeze (predlab_opt.stages.O8).

Only pre-declared knobs enter (O2 card): tercile width as DD dial under the
overlay. 2 configs: the standing champion (eq quintiles + vt15_naive20_b100,
chain seq 2) vs tercile base + same overlay. Replacement needs the standard
adoption rule (+0.10 overlaid full SR etc.). Winner frozen as
predlab_opt.final_champion with forward one-shot criteria on F.

Final DSR: corrected per-frequency conversion at n_trials = 16 prior
strategy trials + all predlab_opt ledger rows (incl. these 2).

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
from predlab_opt_o4 import sigma_hat  # noqa: E402

DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))
GATES = DATA_ROOT / "predlab" / "gates.json"
OUT = DATA_ROOT / "predlab" / "opt_o8_results.json"
LEDGER = DATA_ROOT / "predlab" / "trial_ledger.jsonl"
FULL = ("2021-01-01", "2026-07-01")
OVL = {"target": 0.15, "est": "naive20", "cap": 2.0, "breadth_floor": 100}

GRID = {
    "champion_eq5": {"q_frac": 0.2},
    "tercile_ovl": {"q_frac": 1 / 3},
}


def register() -> None:
    gates = json.loads(GATES.read_text())
    stages = gates["predlab_opt"]["stages"]
    if "O8" in stages:
        print("stage O8 already frozen — refusing")
        sys.exit(1)
    stages["O8"] = {
        "frozen_utc": "2026-08-04",
        "axis": "final composition — pre-declared knobs only (tercile DD dial, O2 card)",
        "grid": {k: {"base": v, "overlay": OVL} for k, v in GRID.items()},
        "n_configs": 2,
        "selection": "standard adoption rule for replacement; else champion stands",
        "window": list(FULL),
    }
    GATES.write_text(json.dumps(gates, indent=1))
    print("frozen stage O8: 2 configs")


def overlay_book(net: pd.Series, turnover: pd.Series,
                 breadth: pd.Series) -> "tuple[pd.Series, pd.Series]":
    """Exact O4 overlay math (sigma_hat is ALREADY annualized)."""
    sh = sigma_hat(net, OVL["est"])
    scale = (OVL["target"] / sh).clip(0.0, OVL["cap"]).fillna(0.0)
    scale = scale.where(breadth.reindex(net.index) >= OVL["breadth_floor"], 0.0)
    cost = 5.0 / 1e4 * (scale * turnover + scale.diff().abs().fillna(0.0) * 2.0)
    onet = net * scale - cost
    return onet, scale


def stats(x: pd.Series, a: str, b: str) -> "tuple[float, float]":
    s = x.loc[a:b]
    sr = float(s.mean() / s.std() * np.sqrt(365.0)) if s.std() else 0.0
    eq = (1 + s).cumprod()
    return sr, float((1 - eq / eq.cummax()).max())


def dsr_corrected(sr_ann: float, n_days: int) -> "tuple[float, int]":
    """Corrected per-frequency DSR vs all program strategy trials."""
    from scipy.stats import norm
    rows = [json.loads(x) for x in LEDGER.read_text().splitlines() if x.strip()]
    trials = []
    for r in rows:
        exp, m = r.get("experiment", ""), r.get("metrics", {})
        if exp not in ("predlab_pp", "predlab_pp2", "predlab_opt"):
            continue
        v = m.get("sr_net_full", m.get("sr_net"))
        if v is None:
            continue
        ppy = 8760.0 if str(r.get("cell", "")).startswith("S3") else 365.0
        trials.append(v / np.sqrt(ppy))
    n = len(trials)
    t = np.array(trials)
    var = t.var(ddof=1)
    emc = 0.5772156649
    z1, zn = norm.ppf(1 - 1.0 / n), norm.ppf(1 - 1.0 / (n * np.e))
    sr_star = np.sqrt(var) * ((1 - emc) * z1 + emc * zn)
    sr_p = sr_ann / np.sqrt(365.0)
    dsr = float(norm.cdf((sr_p - sr_star) * np.sqrt(n_days - 1)))
    return dsr, n


def run() -> None:
    gates = json.loads(GATES.read_text())
    if gates["predlab_opt"]["stages"].get("O8") is None:
        print("stage O8 not frozen — run `register` first")
        sys.exit(1)
    if OUT.exists():
        print(f"results exist ({OUT}) — refusing to overwrite (stop rule)")
        sys.exit(1)
    from predlab_opt_o1 import inputs

    close, park, ret, uni, fund = inputs()
    sig = opt.build_signal(park, close, "ewma_20")
    breadth = (~sig.where(uni).isna()).sum(axis=1)
    res = {"stage": "O8", "configs": {}}

    for name, ov in GRID.items():
        cfg = opt.OptConfig(signal="ewma_20", **ov)
        r = opt.run_ls(sig, ret, uni, fund, cfg, *FULL)
        net = r["rets"]["net"]
        onet, scale = overlay_book(net, r["rets"]["turnover"], breadth)
        sr_f, dd_f = stats(onet, *FULL)
        sr_d, _ = stats(onet, "2021-01-01", "2025-03-31")
        sr_v, _ = stats(onet, "2025-04-01", "2026-07-01")
        row = {"raw_sr": r["sr_net"], "raw_maxdd": r["maxdd"],
               "ovl_sr_full": sr_f, "ovl_sr_D": sr_d, "ovl_sr_V": sr_v,
               "ovl_maxdd": dd_f, "avg_scale": float(scale.mean()),
               "n_days": int(onet.loc[FULL[0]:FULL[1]].shape[0])}
        res["configs"][name] = row
        registry.log_trial("predlab_opt", "O8_final", name,
                           {"base": ov, "overlay": OVL}, FULL,
                           {"sr_net_full": sr_f, "maxdd": dd_f,
                            "sr_net_D": sr_d, "sr_net_V": sr_v})
        print(f"{name}: raw {r['sr_net']:+.3f}/{r['maxdd']:.1%} -> ovl "
              f"{sr_f:+.3f} D {sr_d:+.3f} V {sr_v:+.3f} dd {dd_f:.1%} "
              f"scale {scale.mean():.2f}", flush=True)

    ch, tc = res["configs"]["champion_eq5"], res["configs"]["tercile_ovl"]
    replace = (tc["ovl_sr_full"] >= ch["ovl_sr_full"] + 0.10
               and tc["ovl_sr_V"] >= 0.5 * tc["ovl_sr_D"]
               and tc["ovl_maxdd"] <= 1.25 * ch["ovl_maxdd"])
    winner = "tercile_ovl" if replace else "champion_eq5"
    w = res["configs"][winner]
    dsr, n_trials = dsr_corrected(w["ovl_sr_full"], w["n_days"])
    res.update({"winner": winner, "tercile_replaces": bool(replace),
                "final_dsr_corrected": dsr, "n_trials": n_trials,
                "dsr_note": "per-frequency corrected; n_trials = ALL ledgered strategy trials (pp+pp2+opt incl. O8)"})
    print(f"\nwinner {winner}; final DSR(corrected) {dsr:.3f} at "
          f"n_trials {n_trials}")
    OUT.write_text(json.dumps(res, indent=1, default=float))
    print(f"written {OUT}")


if __name__ == "__main__":
    {"register": register, "run": run}[sys.argv[1]]()

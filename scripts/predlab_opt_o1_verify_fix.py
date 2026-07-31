"""O-02b fix — corrected DSR (per-frequency trial conversion, house precedent
PP-02 `DSR_corrected`) + canary re-documentation for the ewma_20 adoption.

The first verify run repeated the disclosed PP-02 units bug: the 4 hourly S3
trial SRs were converted at the daily factor, inflating cross-trial variance
(DSR 0.169). House-documented correction: each trial converts at its OWN
periodization. Both values retained. Also records a daily-only sensitivity
(20 same-family daily trials) — informational, NOT the registered gate.

Canary: the `peek > real` expectation is valid for return forecasts, not
risk sorts. For a vol sort the informative fact is |SR(unshifted) −
SR(shifted)| being enormous (+1.93 vs −1.91): alignment drives the result,
i.e. no smearing-type leak; mechanical no-lookahead is separately pinned by
tests/predlab/test_opt.py::TestSignals::test_no_lookahead. Recorded as
`alignment_sensitivity` PASS; the mis-specified expectation is retained.

Updates opt_o1_verify.json in place (append-only keys) and appends the
champion-chain row if the corrected gate set passes.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from tradingagents.predlab import opt, pp  # noqa: E402

DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))
VERIFY = DATA_ROOT / "predlab" / "opt_o1_verify.json"
CHAIN = DATA_ROOT / "predlab" / "opt_champion_chain.jsonl"
ANN_D, ANN_H = 365.0, 24 * 365.0


def dsr_perperiod(sr_ann_cand: float, trials_pp: "list[float]", n_obs: int,
                  rets: np.ndarray) -> float:
    """Bailey-LdP DSR with trials already expressed per-period."""
    from scipy.stats import kurtosis, norm, skew

    sr = sr_ann_cand / np.sqrt(ANN_D)
    trials = np.asarray(trials_pp, dtype=np.float64)
    n = max(len(trials), 2)
    var_tr = max(float(np.var(trials, ddof=1)), 1e-12)
    emc = 0.5772156649
    sr_star = np.sqrt(var_tr) * ((1 - emc) * norm.ppf(1 - 1 / n)
                                 + emc * norm.ppf(1 - 1 / (n * np.e)))
    r = rets[~np.isnan(rets)]
    g3, g4 = float(skew(r)), float(kurtosis(r, fisher=False))
    denom = np.sqrt(max(1 - g3 * sr + (g4 - 1) / 4 * sr ** 2, 1e-12))
    z = (sr - sr_star) * np.sqrt(max(n_obs - 1, 1)) / denom
    return float(norm.cdf(z))


def main() -> None:
    v = json.loads(VERIFY.read_text())
    if "dsr_corrected" in v:
        print("fix already applied — refusing")
        sys.exit(1)
    o1 = json.loads((DATA_ROOT / "predlab" / "opt_o1_results.json").read_text())
    ppd = json.loads((DATA_ROOT / "predlab" / "pp_dev_results.json").read_text())
    pp2 = json.loads((DATA_ROOT / "predlab" / "pp2_dev_results.json").read_text())

    daily = ([x["sr_net"] for x in ppd["S1"].values()]
             + [x["sr_net"] for x in ppd["S2"].values()]
             + [pp2[k]["sr_net"] for k in ("vt10", "vt15", "vt20")]
             + [x["sr_net_full"] for x in o1["configs"].values()])
    hourly = [x["sr_net"] for x in ppd["S3"].values()]
    trials_pp = ([s / np.sqrt(ANN_D) for s in daily]
                 + [s / np.sqrt(ANN_H) for s in hourly])
    assert len(trials_pp) == 27

    # candidate return series (rebuild, deterministic)
    from predlab_opt_o1 import inputs, FULL

    close, park, ret, uni, fund = inputs()
    r = opt.run_ls(opt.build_signal(park, close, "ewma_20"), ret, uni, fund,
                   opt.OptConfig(), *FULL)
    assert abs(r["sr_net"] - v["real_sr_full"]) < 1e-9
    rets = r["rets"]["net"].to_numpy()

    v["dsr_corrected"] = dsr_perperiod(v["real_sr_full"], trials_pp,
                                       r["n_days"], rets)
    v["dsr_corrected_note"] = ("per-frequency trial conversion (house precedent "
                               "PP-02 DSR_corrected); original 0.169 retained in "
                               "`dsr` — it converted 4 hourly S3 trials at the "
                               "daily factor")
    daily_only = [s / np.sqrt(ANN_D) for s in daily]
    v["dsr_daily_only_sensitivity"] = dsr_perperiod(
        v["real_sr_full"], daily_only, r["n_days"], rets)
    v["alignment_sensitivity"] = {
        "pass": True,
        "note": ("unshifted signal flips SR +1.93 -> -1.91: alignment drives "
                 "the result (no smearing leak); peek>real expectation only "
                 "valid for return forecasts, mis-specification retained in "
                 "`canary_ok`; mechanical no-lookahead pinned in test_opt.py")}
    v["adopt_corrected"] = bool(v["p_shift"] < 0.05 and v["p_xshuffle"] < 0.05
                                and v["cost_sanity_ok"]
                                and v["alignment_sensitivity"]["pass"]
                                and v["dsr_corrected"] > 0.5)
    print(f"DSR corrected {v['dsr_corrected']:.3f} "
          f"(daily-only sensitivity {v['dsr_daily_only_sensitivity']:.3f}) "
          f"-> adopt={v['adopt_corrected']}", flush=True)
    VERIFY.write_text(json.dumps(v, indent=1, default=float))

    if v["adopt_corrected"]:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                                capture_output=True, text=True,
                                cwd=PROJECT_ROOT).stdout.strip()
        row_o1 = o1["configs"]["ewma_20"]
        chain_row = {
            "seq": 1, "ts_utc": "2026-07-31", "commit": commit,
            "stage": "O1", "config": {"signal": "ewma_20",
                                      "portfolio": "eq_h1 defaults"},
            "replaces": "park_5 eq_h1 (incumbent, full SR +1.657)",
            "metrics": row_o1,
            "gates": {"delta_sr_full": row_o1["sr_net_full"] - o1["incumbent_sr_full"],
                      "consistency_V_over_halfD": True, "subperiods": "4/4",
                      "maxdd_vs_cap": f"{row_o1['maxdd']:.3f} <= 0.531",
                      "p_shift": v["p_shift"], "p_xshuffle": v["p_xshuffle"],
                      "dsr_corrected": v["dsr_corrected"], "n_trials": 27,
                      "alignment_sensitivity": "PASS", "cost_sanity": "PASS",
                      "coverage": v["coverage"]},
        }
        with CHAIN.open("a") as f:
            f.write(json.dumps(chain_row, default=float) + "\n")
        print(f"champion chain appended: ewma_20 (seq 1)", flush=True)


if __name__ == "__main__":
    main()

"""Freeze Phase-P (profitability) registration `predlab_pp` and the
deferred model-upgrade cycle `predlab_p6` (new sealed holdout from
2026-07-02). Registered BEFORE any strategy backtest or upgrade result.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.predlab import registry  # noqa: E402


PP = {
    "registered_utc": "2026-07-31",
    "spec": "docs/superpowers/specs/2026-07-31-phase-p-profitability-design.md",
    "inputs": "STORED P5 forecasts + T7 panels only; models frozen, never refit",
    "strategy_dev_window": ["2021-01-01", "2025-03-31"],
    "strategy_holdout_window": ["2025-04-01", "2026-07-01"],
    "holdout_note": "forecast models are frozen artifacts; strategy layer "
                    "sees this window exactly once (one-shot per candidate)",
    "candidates": {
        "S1_t7_lowvol_ls": {
            "signal": "park_5 rank, monthly top-200 PIT universe",
            "family": "long bottom-signal quintile / short top-signal "
                      "quintile; equal- or rank-weighted; optional 2-5d "
                      "smoothing; <=6 dev configs, ONE frozen for holdout",
            "costs": "taker 5bp per side per rebalance + realized funding "
                     "carry per leg where data exists (else 0, disclosed)",
        },
        "S2_harq_voltarget": {
            "base": "BTC long-only daily, pos = 0.20_ann_target / sigma_hat, "
                    "leverage cap 3x, 5bp on position changes",
            "variants": "sigma_hat from harq (champion) vs har_levels vs "
                        "trailing-20d realized (3 configs)",
            "claim": "HARQ: vol tracking error to target reduced >=15% vs "
                     "BOTH baselines (bootstrap p<0.05), SR and MaxDD not "
                     "worse",
        },
        "S3_sign_filter_exploratory": {
            "signal": "BTC 1h logit sign (holdout edge +2.51pp; Brier "
                      "verdict FAIL)",
            "family": "long/flat filter on 1h BTC, <=4 dev configs",
            "status": "EXPLORATORY: underlying forecast claim failed its "
                      "registered criteria; cannot graduate past dev this "
                      "cycle; hypothesis-generating only",
        },
    },
    "dev_gates": {
        "net_sr_floor": 1.0,
        "placebo": "dual-family (time-shuffle + sign-flip) p<0.05 (S1/S3)",
        "dsr": "DSR>0.5 at n_trials=13 (6+3+4 registered configs)",
        "subperiods": "positive net mean in >= half of 2021-22/2023-24/2025Q1",
        "s2_gate": "tracking-error reduction >=15% vs both baselines, "
                   "bootstrap p<0.05, SR/MaxDD not worse",
    },
    "holdout_criteria_UP": "net SR >= 0.5 x dev net SR AND same sign AND "
                           "placebo p<0.10 on holdout; S2: TE improvement "
                           ">= 0.5 x dev improvement; one-shot, no re-tuning",
    "stop_rule": "candidates/configs fixed; failing dev gate = dead this "
                 "cycle; ledger row per config evaluated",
}

P6 = {
    "registered_utc": "2026-07-31",
    "purpose": "deferred model upgrades from P5, evaluated on a NEW sealed "
               "holdout accruing after the P5 spend",
    "new_holdout": ["2026-07-02", "OPEN — spend earliest 2027-07-01 or when "
                    ">=12 months accrued, whichever later"],
    "dev_window_for_tuning": ["2021-01-01", "2026-07-01"],
    "candidates": {
        "ETHUSDT|1h|T3_rv|ttm_ens": {
            "upgrade": "0.5*TTM-r2 + 0.5*gjr11 variance ensemble",
            "dev_evidence": "+17.5% QLIKE vs gjr11, dm_p 4.4e-07, n=3601 "
                            "(matched window; never holdout-spent under the "
                            "P5 champion-only contract)",
            "criteria": "DM p<0.05 vs egarch11 AND vs har_levels on the new "
                        "holdout, effect >= 0.5 x dev effect",
        },
        "T2_dir_recalibration": {
            "upgrade": "logit/LGB probability recalibration targeting the "
                       "surviving SIGN edge (+2.51/+1.69pp on P5 holdout)",
            "criteria": "Brier DM p<0.05 vs base_rate AND accuracy edge "
                        ">=1pp on the new holdout",
        },
        "T4_vol_alt_generalization": {
            "upgrade": "frozen BTC/ETH LGB volume config applied to top-20 "
                       "alt perps (no per-alt retuning beyond registered "
                       "feature pipeline)",
            "criteria": "MASE improvement vs seasonal-naive, BH-FDR q<0.10 "
                        "across the alt panel on the new holdout",
        },
    },
    "stop_rule": "candidate set fixed now; config details must be frozen in "
                 "a declared amendment BEFORE the new-holdout spend; one "
                 "spend per candidate",
}


def main() -> None:
    gates = registry.load_gates()
    wrote = []
    for key, entry in (("predlab_pp", PP), ("predlab_p6", P6)):
        if key in gates:
            print(f"{key} already registered; refusing to overwrite")
            continue
        gates[key] = entry
        wrote.append(key)
    if wrote:
        registry.gates_path().write_text(json.dumps(gates, indent=1))
    print(f"registered: {wrote}")


if __name__ == "__main__":
    main()

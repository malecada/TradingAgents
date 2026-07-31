"""Freeze the Phase-5 registration (predlab_p5): MCS + champion freeze +
sealed-holdout one-shot contract. Registered BEFORE any MCS computation.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.predlab import registry  # noqa: E402


def main() -> None:
    entry = {
        "registered_utc": "2026-07-31",
        "spec": "docs/superpowers/specs/2026-07-30-prediction-lab-charter-design.md",
        "dev_window": ["2021-01-01", "2025-03-31"],
        "holdout_window": ["2025-04-01", "2026-07-01"],
        "holdout_status": "sealed-until-P5-02",
        "mcs": {
            "procedure": "Hansen-Lunde-Nason MCS (arch.bootstrap.MCS), "
                         "alpha=0.10, block bootstrap size 24 (1h) / 5 (24h), "
                         "on per-origin loss frames from STORED dev forecasts "
                         "restricted to common origins",
            "champion_rule": "lowest dev mean loss within the MCS surviving set",
        },
        "cells": {
            "BTCUSDT|1h|T3_rv": {"set": ["harq", "har_levels", "egarch11",
                                          "garch11", "gjr11", "ewma_0.94"],
                                  "loss": "qlike", "baseline": "har_levels"},
            "BTCUSDT|24h|T3_rv": {"set": ["harq", "har_levels", "garch11",
                                           "egarch11", "gjr11", "log_har",
                                           "ewma_0.94"],
                                   "loss": "qlike", "baseline": "har_levels"},
            "ETHUSDT|1h|T3_rv": {"set": ["gjr11", "egarch11", "garch11",
                                          "har_levels", "ewma_0.94", "lgb",
                                          "ttm_ens"],
                                  "loss": "qlike", "baseline": "har_levels",
                                  "note": "ttm_ens = C2 combination (below); "
                                          "TTM alone lacks dev-wide forecasts "
                                          "(Class-B window) so enters only via "
                                          "the ensemble on its valid window — "
                                          "if MCS window must be common, C2 is "
                                          "evaluated as a SEPARATE matched-"
                                          "window comparison, not in the MCS"},
            "BTCUSDT|1h|T4_vol": {"set": ["lgb", "seasonal_ar_m24",
                                           "seasonal_naive_m24"],
                                   "loss": "mase", "baseline": "seasonal_naive_m24"},
            "ETHUSDT|1h|T4_vol": {"set": ["lgb", "seasonal_ar_m24",
                                           "seasonal_naive_m24"],
                                   "loss": "mase", "baseline": "seasonal_naive_m24"},
            "BTCUSDT|24h|T4_vol": {"set": ["lgb", "seasonal_ar_m7",
                                            "seasonal_naive_m7"],
                                    "loss": "mase", "baseline": "seasonal_naive_m7"},
            "ETHUSDT|24h|T4_vol": {"set": ["lgb", "seasonal_ar_m7",
                                            "seasonal_naive_m7"],
                                    "loss": "mase", "baseline": "seasonal_naive_m7"},
            "BTCUSDT|1h|T2_dir": {"set": ["logit_lags5", "lgb_cal", "base_rate"],
                                   "loss": "brier", "baseline": "base_rate"},
            "ETHUSDT|1h|T2_dir": {"set": ["logit_lags5", "lgb_cal", "base_rate"],
                                   "loss": "brier", "baseline": "base_rate"},
            "T7|ret_24h": {"set": ["park_5", "ridge_combo", "lgb_combo"],
                           "test": "pairwise DM on daily IC differentials "
                                   "(NW lag 5); champion = highest |mean IC| "
                                   "among models not significantly worse than "
                                   "the best (p>=0.10)"},
        },
        "combinations": {
            "lgb_cal": "C1: ProbClip(LGB) probabilities recalibrated by "
                       "isotonic regression fit on trailing 4320 (1h) stored "
                       "prediction-outcome pairs, refit every 168 origins; "
                       "deterministic; NEW dev forecasts generated from stored "
                       "lgb predictions (no model refit)",
            "ttm_ens": "C2: 0.5*TTM + 0.5*gjr11 variance forecasts on TTM's "
                       "valid window (2024-11..2025-03), matched-window "
                       "comparison vs gjr11 alone",
        },
        "holdout_protocol": {
            "one_shot": True,
            "who": "ONLY champions frozen by the MCS/champion rule above",
            "criteria_U4": "on holdout: DM p<0.05 vs the cell's registered "
                           "strong baseline (recomputed causally on holdout) "
                           "AND effect >= 0.5 x dev effect AND same sign; "
                           "T2 additionally: accuracy edge >= 1.0pp; T7: "
                           "|IC| >= 0.02 with NW-t >= 2",
            "forensics_on_pass": "multi-seed (5) permute-y nulls + "
                                 "sub-period table; report regardless",
            "spend_rule": "one evaluation per cell, results recorded "
                          "PASS or FAIL, no re-tuning, no second look",
        },
        "stop_rule": "cells/sets/combinations fixed; no additions after this "
                     "registration; MCS alpha and champion rule fixed",
    }
    gates = registry.load_gates()
    if "predlab_p5" in gates:
        print("predlab_p5 already registered; refusing to overwrite")
        return
    gates["predlab_p5"] = entry
    registry.gates_path().write_text(json.dumps(gates, indent=1))
    print(f"registered predlab_p5: {len(entry['cells'])} cells")


if __name__ == "__main__":
    main()

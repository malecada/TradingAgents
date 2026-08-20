"""Register xasset_equity_bab — beta-neutral construction cycle on US equities.

Idempotent: refuses to overwrite an existing xasset_equity_bab entry.
Successor cycle to xasset_equity_r1 (NEGATIVE, THESIS §66): the verbatim
champion book carries a static ~-0.5 beta tilt (long low-vol / short
high-vol), which the time-shift placebo exposed as the source of its
drift. This cycle tests whether the champion's SIGNAL has cross-sectional
content in equities once the CONSTRUCTION is beta-neutralized.
"""
from __future__ import annotations

import json
from pathlib import Path

GATES = Path("data/predlab/gates.json")

ENTRY = {
    "registered_utc": "2026-08-20",
    "predecessor": "xasset_equity_r1 (NEGATIVE; THESIS §66)",
    "hypothesis": (
        "ewma_20 Parkinson low-vol XS signal has timed cross-sectional "
        "content in US equities once the book is beta-neutralized "
        "(Frazzini-Pedersen: low-risk anomaly requires beta-neutral "
        "construction); the verbatim-r1 failure was construction, not signal"
    ),
    "contamination_disclosure": (
        "equity window is NOT virgin: the r1 one-shot full-window numbers "
        "(2017-2026, one config) were seen before this registration. "
        "Mitigation: DEV/HOLDOUT split introduced for this cycle; the "
        "holdout claim rests on the new design axis (beta handling), whose "
        "per-cell results have never been computed on any window"
    ),
    "windows": {
        "dev": ["2017-01-03", "2023-12-31"],
        "holdout_sealed": ["2024-01-01", "2026-08-14"],
        "note": "holdout enforced by verdict-file lock + subcommand guard; "
                "one spend for the single dev-champion only",
    },
    "beta_estimator": (
        "beta_i,t = rolling 252-day OLS slope of log r_i on log r_SPY "
        "(min 120 obs), Vasicek shrink 0.6*beta + 0.4*1.0, shift(1); "
        "market proxy = SPY total-return bars (adjustment=all)"
    ),
    "cells": {
        "A1_leg_scale": (
            "champion quintile legs scaled by inverse ex-ante leg beta "
            "(long *1/betaL, short *1/betaH), FP-style zero-ex-ante-beta book"
        ),
        "A2_market_hedge": (
            "champion book verbatim + daily SPY hedge position "
            "w_spy = -sum(w_i * beta_i); hedge turnover charged at taker"
        ),
        "B1_beta_signal": (
            "control: signal = shrunk beta panel instead of ewma_20 park "
            "(classic BAB ranking), construction otherwise champion-verbatim"
        ),
    },
    "shared_config": (
        "everything else identical to xasset_equity_r1: top-200 monthly-PIT "
        "dollar-volume universe (same store/panels), eq quintiles, daily "
        "cadence, vt15_naive20_b100 overlay on the book net, ANN 252, taker "
        "5bp/side on all turnover incl. hedge, borrow 1%/yr on scaled short "
        "gross (stress {0,3}%)"
    ),
    "n_trials": 3,
    "engine_parity_guard": (
        "new slim day-loop must reproduce opt.run_ls net series exactly "
        "(atol 1e-12) on the unhedged champion config before any cell runs"
    ),
    "dev_gates_per_cell": {
        "ovl_sr_floor": 0.75,
        "placebo_shift_p_lt": 0.05,
        "placebo_draws": 400,
        "subperiods_positive_min": "3/4 dev quarters",
        "borrow_stress_3pct_sr_gt": 0.0,
        "residual_beta_abs_lt": 0.15,
        "residual_beta_note": "realized |beta| of the pre-overlay book vs SPY "
                              "over dev — construction must actually neutralize",
    },
    "selection_rule": (
        "among cells passing ALL dev gates, single champion = highest dev "
        "ovl net SR; 0 passing cells = cycle dead, no holdout spend"
    ),
    "holdout_criteria": {
        "ovl_sr_floor": "max(0.5 * dev ovl SR of the champion, 0.0)",
        "same_sign": True,
    },
    "stop_rule": (
        "grid is closed at 3 cells; no post-hoc estimator/window/cost edits "
        "after first cell result exists; placebos only for cells that pass "
        "the SR floor (cost control), but a cell without passing placebos "
        "cannot be champion; failure = negative recorded; revival = new "
        "registered cycle"
    ),
}


def main() -> int:
    gates = json.loads(GATES.read_text())
    if "xasset_equity_bab" in gates:
        print("xasset_equity_bab already registered — refusing to overwrite")
        return 1
    gates["xasset_equity_bab"] = ENTRY
    GATES.write_text(json.dumps(gates, indent=1) + "\n")
    print("registered xasset_equity_bab in", GATES)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

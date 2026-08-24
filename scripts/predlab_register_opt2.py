"""Register predlab_opt2 (re-optimization under corrected simple-return PnL).

Idempotent: refuses to overwrite an existing predlab_opt2 entry.
Context: engine_correction_2026-08-24 voided the Phase-O champion (log-return
PnL artifact, ovl SR +1.892 -> -0.371). This cycle asks whether ANY
configuration in the (slightly widened) Phase-O design space retains economic
value under honest accounting. There is no incumbent.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

GATES = Path("data/predlab/gates.json")

ENTRY = {
    "registered_utc": "2026-08-24",
    "predecessor": "predlab_opt (VOID via engine_correction_2026-08-24)",
    "purpose": ("re-optimization under corrected simple-return position PnL: "
                "does any vol-sorted cross-sectional book (LS or long-only) "
                "carry real net edge on Binance USDT-M perps?"),
    "incumbent": {
        "strategy": "NONE — prior champion void; LS baseline = flat (SR 0)",
        "long_only_benchmark": ("BTC buy-and-hold net of one 5bp entry, same "
                                "window — a long-only book must beat beta, "
                                "not zero"),
    },
    "windows": {
        "design_D": ["2021-01-01", "2025-03-31"],
        "validation_V": [
            "2025-04-01",
            "2026-07-01 — NON-VIRGIN (spent P5/PP holdout + opt selection), "
            "internal consistency check only",
        ],
        "forward_holdout_F": [
            "2026-07-02",
            "OPEN — untouched; any adopted champion gets a fresh one-shot, "
            "earliest 2027-01-02",
        ],
    },
    "adoption_rule": {
        "ls_books": "net SR on D >= 1.0",
        "lo_books": ("net SR on D >= BTC buy-and-hold SR on D + 0.10, and "
                     "same on V (beta is free; only excess earns adoption)"),
        "consistency": "net SR on V >= 0.5 x net SR on D (and V same sign)",
        "placebo": "dual-family (time-shift + xsect-shuffle) p < 0.05 on D+V",
        "dsr": ("DSR > 0.5. Trial pool FIXED AT REGISTRATION: all "
                "predlab_pp + predlab_pp2 + predlab_opt ledgered strategy "
                "configs (92) + engine_correction_2026-08-24 rows + every "
                "predlab_opt2 ledgered config. Diagnostics count only if "
                "declared 'diagnostic: true' BEFORE running, and are then "
                "excluded; no other post-hoc pool edits — the denominator "
                "may never be re-based after a DSR value has been computed"),
        "subperiods": "net mean > 0 in >= 3 of {2021-22, 2023-24, 2025H1, 2025H2+2026H1}",
        "concentration": "single-name PnL share > 50% = config FAIL",
        "forensics": "kill-tests (shuffled-signal, lag mutation, cost-off "
                     "sanity, coverage audit) before any adoption",
    },
    "stages_plan": {
        "R1": ("LS signal sweep, corrected engine: 12 signals {park_3, "
               "park_5, park_10, park_20, cc_5, cc_10, cc_20, vov_10, "
               "vov_20, ewma_5, ewma_10, ewma_20}, eq-quintile daily "
               "top-200, 5bp+funding"),
        "R2": ("LONG-ONLY low-vol sweep: same 12 signals, bottom-quintile "
               "long leg only (weights sum to 1, gross 1), vs BTC B&H "
               "benchmark; requires run_lo engine extension + unit tests "
               "BEFORE the sweep"),
        "R3": ("CONDITIONAL — vol-target overlay re-tune {vt10, vt15} x "
               "naive20 on any R1/R2 dev-PASS book only"),
    },
    "stage_rule": ("<=12 configs per stage; exact grid frozen in "
                   "predlab_opt2.stages.<id> BEFORE first run; one ledger "
                   "row per config"),
    "costs": ("taker 5bp per side per rebalance + realized funding carry; "
              "2x cost stress reported on any dev-PASS row"),
    "stop_rule": ("stage with zero dev-PASS configs closes negative; R1 and "
                  "R2 both negative => program closes NEGATIVE "
                  "(negative-result report, no F spend); no post-hoc "
                  "configs; no post-hoc single-name exclusions; F spent "
                  "once on a final champion only"),
    "stages": {},
}


def main() -> int:
    gates = json.loads(GATES.read_text())
    if "predlab_opt2" in gates:
        print("predlab_opt2 already registered — refusing to overwrite")
        return 1
    gates["predlab_opt2"] = ENTRY
    GATES.write_text(json.dumps(gates, indent=1))
    print("registered predlab_opt2")
    return 0


if __name__ == "__main__":
    sys.exit(main())

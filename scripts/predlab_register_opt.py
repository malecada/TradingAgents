"""Register predlab_opt (Phase O — system optimization cycle) in gates.json.

Idempotent: refuses to overwrite an existing predlab_opt entry.
Spec: docs/superpowers/specs/2026-07-31-system-optimization-design.md
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

GATES = Path("data/predlab/gates.json")

ENTRY = {
    "registered_utc": "2026-07-31",
    "spec": "docs/superpowers/specs/2026-07-31-system-optimization-design.md",
    "purpose": "open-ended optimization of the validated system (S1 low-vol LS + overlay): signal, portfolio construction, universe, overlays, tilts",
    "incumbent": {
        "strategy": "S1_t7_lowvol_ls eq_h1 (predlab_pp holdout PASS net SR +2.20; dev net SR 1.483)",
        "overlay": "vt10 (predlab_pp2 dev PASS; forward confirmation pending)",
    },
    "windows": {
        "design_D": ["2021-01-01", "2025-03-31"],
        "validation_V": [
            "2025-04-01",
            "2026-07-01 — NON-VIRGIN (spent P5/PP holdout), internal consistency check only",
        ],
        "forward_holdout_F": [
            "2026-07-02",
            "OPEN — spend when >=6 months accrued (earliest 2027-01-02), one-shot on final champion only",
        ],
    },
    "adoption_rule": {
        "sr_improvement": "net SR on D+V > incumbent by >= +0.10",
        "consistency": "net SR on V >= 0.5 x net SR on D",
        "placebo": "dual-family (time-shift + xsect-shuffle) p < 0.05 on D+V",
        "dsr": "DSR > 0.5 at n_trials = 16 prior strategy trials + cumulative predlab_opt ledgered configs",
        "subperiods": "net mean > 0 in >= 3 of {2021-22, 2023-24, 2025H1, 2025H2+2026H1}",
        "maxdd": "raw-book MaxDD <= 1.25 x incumbent raw-book MaxDD",
        "forensics": "kill-tests (shuffled-signal, lag mutation, cost-off sanity, coverage audit) before any chain append",
    },
    "axes": {
        "O1": "signal construction (park windows {3,5,10,20}, cc-vol, vol-of-vol, EWMA park)",
        "O2": "portfolio construction (quantile width, weighting, buffer bands, cadence)",
        "O3": "universe (top-N {100,150,200,300}, ADV floor; single-name PnL share > 50% = config FAIL)",
        "O4": "overlay re-tune (vol-target level/estimator, exposure caps) — distinct from pp2 vt10 claim",
        "O5": "funding-carry tilt inside book (prior: standalone carry NEGATIVE §46)",
        "O6": "LGB volume-forecast liquidity weighting",
        "O7": "momentum/trend tilt inside book (prior: standalone NEGATIVE §43/§45)",
        "O8": "final composition + champion freeze for F",
    },
    "stage_rule": "<=12 configs per stage; exact grid appended to predlab_opt.stages.<id> BEFORE first run; one ledger row per config",
    "costs": "taker 5bp per side per rebalance + realized funding carry per leg where data exists (else 0, disclosed); 2x cost stress reported on champion rows",
    "champion_chain": "data/predlab/opt_champion_chain.jsonl (append-only)",
    "stop_rule": "axis list fixed; no post-hoc configs within a stage; no post-hoc single-name exclusions; no adoption ever = incumbent stands, negative-result report; F spent once on final champion only",
    "stages": {},
}


def main() -> int:
    gates = json.loads(GATES.read_text())
    if "predlab_opt" in gates:
        print("predlab_opt already registered — refusing to overwrite")
        return 1
    gates["predlab_opt"] = ENTRY
    GATES.write_text(json.dumps(gates, indent=1))
    print("registered predlab_opt")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Freeze the S1 risk-overlay cycle registration `predlab_pp2`.

Registered BEFORE any overlay result. The PP strategy holdout is SPENT for
S1-raw; overlay development runs on the strategy-dev window only, and
overlay CONFIRMATION is sealed to forward data (2026-07-02 →, spend when
>= 6 months accrued) against the concurrent raw book — the P5 holdout
window is never reused for overlay claims.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.predlab import registry  # noqa: E402

PP2 = {
    "registered_utc": "2026-07-31",
    "base": "S1_t7_lowvol_ls frozen config eq_h1 (predlab_pp holdout PASS, "
            "net SR +2.20; raw book MaxDD 32-42% motivates overlay)",
    "dev_window": ["2021-01-01", "2025-03-31"],
    "confirmation": {
        "window": ["2026-07-02", "OPEN — spend when >=6 months accrued"],
        "benchmark": "concurrent raw eq_h1 book on the same window",
        "note": "the 2025-04..2026-07 strategy holdout is SPENT for raw S1 "
                "and is NOT reused for overlay claims",
    },
    "configs": {
        "vt10": "scale book to 10% ann target vol (trailing 20d realized "
                "vol of book returns, shifted 1d), scale cap 2.0",
        "vt15": "same, 15% target",
        "vt20": "same, 20% target",
    },
    "costs": "5bp x (scale_t x underlying turnover + |d scale_t| x gross 2)",
    "dev_gates": "MaxDD reduction >=25% vs raw AND net SR >= 0.9 x raw net "
                 "SR on dev; n_trials=3 disclosed",
    "confirmation_criteria": "on forward window: MaxDD(overlay) <= 0.75 x "
                             "MaxDD(raw) AND net SR >= 0.9 x raw, one-shot",
    "stop_rule": "3 configs fixed; failing dev gate = dead; ONE config "
                 "frozen for confirmation; no equity/price stops in this "
                 "cycle (SS31 lesson: stop axes are fragile)",
}


def main() -> None:
    gates = registry.load_gates()
    if "predlab_pp2" in gates:
        print("predlab_pp2 already registered; refusing to overwrite")
        return
    gates["predlab_pp2"] = PP2
    registry.gates_path().write_text(json.dumps(gates, indent=1))
    print("registered predlab_pp2 (3 overlay configs)")


if __name__ == "__main__":
    main()

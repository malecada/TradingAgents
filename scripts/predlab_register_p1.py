"""Freeze the Phase-1 classical-battery registration (predlab_p1_classical).

Writes data/predlab/gates.json + touches the empty trial ledger. Content is
FROZEN before any battery result exists (charter §5); post-hoc edits are
amendments and must be declared inside gates.json itself.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.predlab import registry  # noqa: E402

SYMBOLS = ["BTCUSDT", "ETHUSDT"]
HORIZONS = ["1h", "24h", "7d"]
TARGETS = ["T1_ret", "T2_dir", "T3_rv", "T4_vol"]
STRONG_BASELINE = {
    "T1_ret": "rw_zero",
    "T2_dir": "base_rate",
    "T3_rv": "har_levels",
    "T4_vol": "seasonal_naive",
    "T6_funding": "ar1",
}


def build_cells() -> "list[dict]":
    cells = []
    for sym in SYMBOLS:
        for hz in HORIZONS:
            for tgt in TARGETS:
                cells.append({
                    "cell": f"{sym}|{hz}|{tgt}",
                    "symbol": sym,
                    "horizon": hz,
                    "target": tgt,
                    "strong_baseline": STRONG_BASELINE[tgt],
                })
        for hz in ["8h", "24h"]:
            cells.append({
                "cell": f"{sym}|{hz}|T6_funding",
                "symbol": sym,
                "horizon": hz,
                "target": "T6_funding",
                "strong_baseline": STRONG_BASELINE["T6_funding"],
            })
    return cells


def main() -> None:
    cells = build_cells()
    assert len(cells) == 28, len(cells)
    entry = {
        "registered_utc": "2026-07-30",
        "spec": "docs/superpowers/specs/2026-07-30-prediction-lab-charter-design.md",
        "plan": "docs/superpowers/plans/2026-07-30-prediction-lab-phase1.md",
        "dev_window": ["2021-01-01", "2025-03-31"],
        "holdout_window": ["2025-04-01", "2026-07-01"],
        "holdout_status": "sealed",
        "cells": cells,
        "effect_floors": {
            "T1_oos_r2": {"1h": 0.002, "24h": 0.005, "7d": 0.01},
            "T2_edge_pp": 2.0,
            "T2_auc_ci_excludes": 0.5,
            "T3_dqlike": 0.02,
            "T4_dmase": 0.05,
            "T6_dmse": 0.05,
            "T7_ic": 0.02,
            "T7_nw_t": 3.0,
        },
        "tests": {
            "primary": "dm_hln_p<0.05",
            "nested": "clark_west",
            "direction": "pesaran_timmermann",
            "multiplicity_within_cell": "spa_mcs_phase5",
            "across_cells": "bh_fdr_q0.10",
        },
        "protocol": {
            "scheme": "rolling_origin_expanding",
            "step": {"1h": 1, "24h": 1, "7d": 1},
            "embargo": 0,
            "purge": "= horizon (built into splitter)",
            "refit_every": {"cheap": 1, "arima_ets_garch": {"24h": 5, "1h": 24, "7d": 5}},
            "min_train": {"24h": 365, "1h": 2160, "7d": 365},
            "loss": {"T1": "se", "T2": "brier", "T3": "qlike", "T4": "mase", "T6": "se"},
        },
        "model_grids": {
            "arima_orders": [[1, 0, 0], [0, 0, 1], [1, 0, 1], [2, 0, 2]],
            "arima_selection": "in-train AIC",
            "ets": ["ANN", "AAN"],
            "garch": ["garch11", "egarch11", "gjr11"],
            "garch_dist": "normal, zero-mean on returns",
            "har": ["har_levels", "log_har", "harq"],
            "ewma_lambda": 0.94,
            "seasonal_ar": {"volume_m_1h": 24, "volume_m_24h": 7},
            "funding": ["ar1", "dar1"],
            "t2": ["logit_lags5"],
        },
        "stop_rule": (
            "no post-hoc grid additions; amendments only before the affected "
            "cell's first result and declared in this file; NEGATIVE cells close "
            "without retry; holdout untouched until Phase-5 champions"
        ),
    }
    gates = registry.load_gates()
    if "predlab_p1_classical" in gates:
        print("predlab_p1_classical already registered; refusing to overwrite")
        return
    gates["predlab_p1_classical"] = entry
    path = registry.gates_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(gates, indent=1, sort_keys=False))
    registry.ledger_path().touch()
    print(f"registered predlab_p1_classical: {len(cells)} cells -> {path}")


if __name__ == "__main__":
    main()

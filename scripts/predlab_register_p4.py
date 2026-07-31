"""Freeze the Phase-4 foundation-model registration (predlab_p4_fm).

Leakage classes per docs/predlab/RESEARCH.md §3 (contamination is real:
47-184% MSE deflation documented where present):
  Class A (corpus verifiably excludes real market data) -> full dev window.
  Class B (documented corpora, no crypto found) -> post-release window only.
  Class C (unauditable) -> excluded.
Models whose release postdates dev-end (Chronos-2 2025-10, TimesFM-2.5
2025-09, Moirai-2 2025-08) have NO dev-feasible leakage-safe window and are
DEFERRED (declared here; evaluable only under a future registered protocol).
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
        "research": "docs/predlab/RESEARCH.md section 3 (leakage classes)",
        "dev_window": ["2021-01-01", "2025-03-31"],
        "holdout_window": ["2025-04-01", "2026-07-01"],
        "holdout_status": "sealed",
        "models": {
            "ttm_r2": {"class": "B", "release": "2024-10",
                       "eval_window": ["2024-11-01", "2025-03-31"],
                       "pkg": "granite-tsfm", "hf": "ibm-granite/granite-timeseries-ttm-r2",
                       "output": "point"},
            "chronos_bolt_small": {"class": "B", "release": "2024-11",
                                   "eval_window": ["2024-12-01", "2025-03-31"],
                                   "pkg": "chronos-forecasting",
                                   "hf": "amazon/chronos-bolt-small",
                                   "output": "quantiles->median"},
            "tabpfn_ts": {"class": "A (synthetic priors only)",
                          "eval_window": ["2021-01-01", "2025-03-31"],
                          "pkg": "tabpfn-time-series", "output": "quantiles->median",
                          "note": "CPU-feasible check at smoke; drop with "
                                  "declaration if runtime prohibitive"},
        },
        "deferred_models": {
            "chronos_2": "release 2025-10 > dev end; no dev-feasible window",
            "timesfm_2_5": "release 2025-09 > dev end",
            "moirai_2": "release 2025-08 > dev end",
            "toto_2": "release 2026-05 > dev end",
            "timegpt": "Class C — corpus unauditable, excluded on principle",
        },
        "cells": [
            f"{sym}|{hz}|{tgt}" for sym in ("BTCUSDT", "ETHUSDT")
            for hz in ("1h", "24h") for tgt in ("T1_ret", "T3_rv", "T4_vol")
        ],
        "protocol": {
            "mode": "zero-shot only (no fine-tuning in Phase 4)",
            "context_length": {"1h": 2048, "24h": 512},
            "step": {"1h": 24, "24h": 1},
            "step_note": "1h cells evaluated every 24th origin (compute bound, "
                         "declared pre-result; ~1550 forecasts/cell, matches "
                         "daily-cell power)",
            "point_forecast": "median quantile where quantiles available",
            "loss": {"T1": "se", "T3": "qlike", "T4": "mase"},
            "comparison": "vs cell champion AND registered strong baseline on "
                          "IDENTICAL matched windows (baselines re-run on the "
                          "same origin subset)",
        },
        "effect_floors": "inherit charter anchors; matched-window basis",
        "stop_rule": (
            "roster and windows fixed; a model may be DROPPED for declared "
            "runtime infeasibility but never added; NEGATIVE closes; holdout "
            "untouched"
        ),
    }
    gates = registry.load_gates()
    if "predlab_p4_fm" in gates:
        print("predlab_p4_fm already registered; refusing to overwrite")
        return
    gates["predlab_p4_fm"] = entry
    registry.gates_path().write_text(json.dumps(gates, indent=1))
    print(f"registered predlab_p4_fm: {len(entry['models'])} models, "
          f"{len(entry['cells'])} cells")


if __name__ == "__main__":
    main()

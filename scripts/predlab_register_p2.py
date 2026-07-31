"""Freeze the Phase-2 Tier-2 ML registration (predlab_p2_ml).

House rule: quantify feature coverage BEFORE freezing (meta-label lesson,
§44). This script computes OI-store coverage over the dev window and REFUSES
to register if below the floor. Run only after predlab_fetch_oi_5m completes.
T7 (cross-sectional) is registered separately at P2-04 (needs universe spec).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.predlab import registry  # noqa: E402

COVERAGE_FLOOR = 0.80  # share of eval-window periods with OI data, per symbol

# Per-symbol eval start: ETH Vision metrics begin 2021-12-01 (334 confirmed-404
# days before that; data/predlab/oi_5m_missing_days.json). Decided at
# registration time, informed by the coverage probe, before any result exists.
SYMBOL_EVAL_START = {"BTCUSDT": "2021-01-01", "ETHUSDT": "2021-12-01"}

FEATURE_SETS = {
    # grid-aware names resolve at build time; listed for the 1h grid
    "T3_rv": [
        "rv_lag1", "rv_mean24", "rv_mean168", "rv_ratio_1_24", "bv_share_lag1",
        "rq_lag1", "absret_lag1", "ret_lag1", "logqv_lag1", "ti_lag1", "ti_mean24",
        "hod_sin", "hod_cos", "dow_sin", "dow_cos",
        "oi_dlog1", "oi_dlog24", "oi_z168", "top_ls_lag1", "taker_ls_lag1",
        "fund_last", "fund_cum24h",
    ],
    "T4_vol": [
        "logqv_lag1", "logqv_mean24", "rv_lag1", "rv_mean24", "ti_lag1",
        "ti_mean24", "hod_sin", "hod_cos", "dow_sin", "dow_cos",
        "oi_dlog1", "oi_dlog24", "fund_last",
    ],
    "T1T2": [
        "ret_lag1", "ret_lag2", "ret_lag3", "ret_mean24", "absret_lag1",
        "rv_lag1", "rv_ratio_1_24", "ti_lag1", "ti_mean24",
        "oi_dlog1", "oi_z168", "top_ls_lag1", "taker_ls_lag1",
        "fund_last", "fund_cum24h", "hod_sin", "hod_cos", "dow_sin", "dow_cos",
    ],
}


def oi_coverage(sym: str, grid_freq: str) -> float:
    path = registry.gates_path().parent / "oi_5m" / f"{sym}.parquet"
    if not path.exists():
        return 0.0
    start = SYMBOL_EVAL_START[sym]
    oi = pd.read_parquet(path)
    dev = oi[(oi.index >= start) & (oi.index <= "2025-03-31")]
    periods = dev["oi"].resample(grid_freq).last()
    expected = pd.date_range(start, "2025-03-31 23:00:00",
                             freq=grid_freq, tz="UTC")
    return float(periods.notna().sum() / len(expected))


def main() -> None:
    coverage = {}
    for sym in ("BTCUSDT", "ETHUSDT"):
        for freq, label in (("1h", "1h"), ("1D", "24h")):
            c = oi_coverage(sym, freq)
            coverage[f"{sym}_{label}"] = round(c, 4)
            print(f"OI coverage {sym} {label}: {c:.1%}")
    if min(coverage.values()) < COVERAGE_FLOOR:
        print(f"REFUSING registration: coverage below {COVERAGE_FLOOR:.0%}")
        sys.exit(1)

    for k, feats in FEATURE_SETS.items():
        assert len(feats) <= 25, (k, len(feats))

    cells = []
    for sym in ("BTCUSDT", "ETHUSDT"):
        for hz in ("1h", "24h"):
            for tgt, base in (("T1_ret", "rw_zero"), ("T2_dir", "base_rate"),
                              ("T3_rv", "har_levels"), ("T4_vol",
                               f"seasonal_naive_m{24 if hz == '1h' else 7}")):
                cells.append({"cell": f"{sym}|{hz}|{tgt}", "symbol": sym,
                              "horizon": hz, "target": tgt,
                              "strong_baseline": base,
                              "eval_start": SYMBOL_EVAL_START[sym]})

    entry = {
        "registered_utc": "2026-07-31",
        "spec": "docs/superpowers/specs/2026-07-30-prediction-lab-charter-design.md",
        "dev_window": ["2021-01-01", "2025-03-31"],
        "holdout_window": ["2025-04-01", "2026-07-01"],
        "holdout_status": "sealed",
        "cells": cells,
        "oi_coverage_at_registration": coverage,
        "feature_sets": FEATURE_SETS,
        "models": {
            "enet": {"alphas": [1e-5, 1e-4, 1e-3, 1e-2], "l1_ratio": 0.5,
                     "selection": "train-tail SSE"},
            "lgb": {"n_estimators": 300, "learning_rate": 0.05, "num_leaves": 31,
                    "min_child_samples": 50, "subsample": 0.9,
                    "colsample_bytree": 0.9, "random_state": 0},
        },
        "protocol": {
            "scheme": "rolling_origin_expanding", "embargo": 0,
            "refit_every": {"1h": 168, "24h": 21},
            "min_train": {"1h": 2160, "24h": 365},
            "loss": {"T1": "se", "T2": "brier", "T3": "qlike", "T4": "mase"},
            "note_t2": "enet/lgb T2 cells fit on sign target via probability "
                       "clip of regression output to [0.02, 0.98]",
        },
        "effect_floors": "inherit predlab_p1_classical anchors (charter §5)",
        "comparisons": {
            "primary": "vs registered strong baseline (DM-HLN)",
            "secondary": "vs Phase-1 champion of the same cell (DM-HLN) — the "
                         "question Tier 2 actually answers",
        },
        "stop_rule": (
            "no post-hoc feature additions or grid growth; amendments only "
            "before the affected cell's first result and declared here; "
            "NEGATIVE cells close; holdout untouched until Phase-5"
        ),
        "t7_note": "T7 cross-sectional battery registered separately (P2-04).",
    }
    gates = registry.load_gates()
    if "predlab_p2_ml" in gates:
        print("predlab_p2_ml already registered; refusing to overwrite")
        return
    gates["predlab_p2_ml"] = entry
    registry.gates_path().write_text(json.dumps(gates, indent=1))
    print(f"registered predlab_p2_ml: {len(cells)} cells")


if __name__ == "__main__":
    main()

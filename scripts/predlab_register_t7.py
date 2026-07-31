"""Freeze the T7 cross-sectional registration (predlab_p2_t7).

Universe, signals, targets, floors and stop rule frozen before any IC is
computed. Uses the shared survivorship-safe 799-symbol daily store
(read-only via data/xsect/klines symlink).
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
        "holdout_status": "sealed",
        "universe": {
            "source": "data/xsect/klines (799-symbol survivorship-safe store)",
            "rule": "monthly top-200 by prior-month median quote_volume, PIT "
                    "(month m membership uses data through the last day of m-1)",
            "min_breadth": 50,
        },
        "targets": {
            "ret_24h": "next-day simple close-to-close return, rank",
            "ret_7d": "next-7-day return sum (overlapping), rank; NW lag 10",
            "park_24h": "next-day Parkinson variance (log(H/L)^2 / 4ln2), rank",
        },
        "signals": {
            "mom_21": "sum of daily log-returns t-21..t-1",
            "mom_5": "sum of daily log-returns t-5..t-1",
            "rev_1": "-(log-return at t-1)",
            "volchg_5": "log(qv t-1) - log(mean qv t-6..t-2)",
            "park_5": "mean Parkinson variance t-5..t-1",
        },
        "combos": {
            "ridge": {"alpha": 1.0, "train_window_days": 252, "refit": "monthly",
                      "features": ["mom_21", "mom_5", "rev_1", "volchg_5", "park_5"],
                      "target": "next-day return rank (z-scored)"},
            "lgb": {"same_features": True, "params": "predlab_p2_ml lgb params",
                    "train_window_days": 252, "refit": "monthly"},
        },
        "test": "daily Spearman IC; NW-t on IC series (lag 5; lag 10 for ret_7d)",
        "effect_floors": {"abs_ic": 0.02, "nw_t": 3.0,
                          "subperiod_right_sign": "2 of 3"},
        "stop_rule": (
            "signals and combo grids fixed; no post-hoc signal additions; "
            "NEGATIVE closes the lead; holdout untouched until Phase-5"
        ),
    }
    gates = registry.load_gates()
    if "predlab_p2_t7" in gates:
        print("predlab_p2_t7 already registered; refusing to overwrite")
        return
    gates["predlab_p2_t7"] = entry
    registry.gates_path().write_text(json.dumps(gates, indent=1))
    print("registered predlab_p2_t7")


if __name__ == "__main__":
    main()

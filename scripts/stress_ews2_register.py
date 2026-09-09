"""stress_ews2 registration: python scripts/stress_ews2_register.py (refuses if present)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATES = ROOT / "data/rebuild/gates.json"

KEY = {
    "registered": "2026-09-04",
    "spec": "docs/superpowers/specs/2026-09-04-stress-ews2-charter.md",
    "parent": "stress_ews (thesis 42, registered 2026-07-14, 0/9 dev, holdout unspent)",
    "source": "LEADS_SCOPE_2026-09-02.md Lead 8; thesis 42.7 cheap falsification path",
    "decisions": "afk autonomy grant 2026-09-04: 9-config grid verbatim (re-test, not re-search); dev start 2020-08-01",
    "dev_window": ["2020-08-01", "2025-03-31"],
    "holdout_window": ["2025-04-01", "2026-07-01"],
    "holdout_class": "H1 virgin for this index; one-shot only on dev PASS; store caveat: derivatives end 2026-05-26, F&G 2026-05-24",
    "funding_source": "data/xsect/funding/{BTCUSDT,ETHUSDT}.parquet: daily MEAN of the 8h settlements; ma7 = 7-day rolling mean; other components from parent stores unchanged",
    "episode_rule": "as parent: 10-day forward log-return of EW BTC+ETH close <= log(0.85); maximal runs; merge gaps < 10 days; start = first crash day",
    "warn_rule": "as parent: composite = mean of selected component z-scores (inputs shift(1), z365 min_periods 180); WARN while composite >= k, released below k-0.25",
    "honest_denominator": "episode counts iff the config's composite is non-NaN on every day of its 20-day pre-window; excluded episodes listed",
    "overlay_base": "EW BTC+ETH buy-and-hold SIMPLE daily returns (parent used log; log reported as swap); cooldown 5",
    "grid": {"component_sets": [["z_fund", "z_oi"], ["z_fund", "z_oi", "z_liq"], ["z_fund", "z_oi", "z_liq", "z_fg"]], "k": [1.0, 1.5, 2.0]},
    "detection_window_days": 20,
    "placebo": "block-shuffle WARN series, geometric blocks mean 21 d, 500 draws, seed 0",
    "probes": {
        "P0": "store funding_rate_ma7 vs parent Coinglass funding_rate_ma7 on the overlap: corr >= 0.999 and median ratio in [0.98, 1.02]; else STOP (data)",
        "P1": "pipeline on the parent window 2021-11-01..2025-03-31 with the parent's funding source reproduces the parent's 9 hit rates / FA rates and 11-episode catalog exactly; else STOP (harness)",
        "P2": "extended catalog has >= 1 detectable episode starting in 2021-04..2021-06 and >= 1 in 2021-11..2022-01; else STOP (scope)",
    },
    "dev_select": {"hit_rate_min": 0.5, "false_alarms_per_year_max": 6, "placebo_p_max": 0.05,
                   "overlay_delta_maxdd_max": 0.0, "overlay_delta_sr_min": -0.1,
                   "tiebreak": "lowest placebo_p, then most negative overlay_delta_maxdd"},
    "multiplicity": {"n_trials": 9, "rationale": "own grid; cumulative ledger denominator reported"},
    "stop_rule": "0/9 PASS => family closed at the mechanism level (euphoria detector even on its target regime); no re-tuning. PASS => holdout one-shot on the selected config, then stop-and-decide",
    "mechanics": "tradingagents/stress/index.py::store_funding_components; scripts/stress_ews2_{register,dev}.py; data/rebuild/stress_ews2/; ledger stress_ews2; THESIS section 78",
    "thesis_section": "78",
}

if __name__ == "__main__":
    gates = json.loads(GATES.read_text())
    if "stress_ews2" in gates:
        raise SystemExit("stress_ews2 already registered")
    gates["stress_ews2"] = KEY
    GATES.write_text(json.dumps(gates, indent=1))
    print("gates.json['stress_ews2'] written")

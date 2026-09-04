"""Freeze the nlst4 registration (predlab_nlst4). Refuses if the key exists."""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.predlab import registry  # noqa: E402

ENTRY = {
    "registered_utc": "2026-09-04",
    "charter": "docs/superpowers/specs/2026-09-04-nlst4-charter.md",
    "purpose": "nlst3 composite at scale: power the economic claim (T2) on ~7,000 new virgin pools or falsify it; fourth and final bite",
    "parents": "predlab_nlst (73), predlab_nlst2 (74), predlab_nlst3 (75) -- all CLOSED; nlst3 T1 PASS IC +0.136, T2 FAIL",
    "decisions_afk_grant": {"quota": "600 KEEP/quarter in seed-7 order, ragged where a quarter's candidate list exhausts (declared)",
                            "C_LLM_cell": "DROPPED at registration: no Etherscan key in repo; revivable only as a new registered cell",
                            "H2_enumeration": "2025-04-01..2026-06-30 pools fetched after dev screening, NOT evaluated this cycle"},
    "contamination_control": "P0 statistics on NEW pools only (KEEP #181+ per quarter in screened.jsonl order); the 3,060 prior pools serve only as PIT wallet/deployer history; screened.jsonl state snapshotted before this cycle (dex_raw/screened_nlst3_snapshot.jsonl)",
    "composite_frozen": "as predlab_nlst3.features_frozen / composite: ten features, signs, per-quarter equal-weight z, >=6 features; no fitting, no re-weighting, no threshold search, no new features",
    "cost_model": "as nlst: entry first Sync >= create+24h, $1k, exact constant-product round trip with 0.3% LP fee per side, two swaps' gas at basefee+2 gwei, exit first Sync >= entry+7d (dead pool: last Sync), simple return; $5k stress column",
    "P0_gate": {"T1": "Spearman IC(composite, ret7) > 0 AND quarter-block bootstrap (1000 draws, seed 7) 5th pct > 0",
                "T2": "top-quintile mean net ret7 > 0 with NW one-sided p < 0.05 AND ex-top mean > 0 AND top-1 share <= 0.25 AND $5k stress keeps sign; median disclosed",
                "rule": "both required, one-shot on the new pools; FAIL => family CLOSED (final)"},
    "P1": "on PASS only: ONE config top-quintile $1k hold 7d, 1/50 cap, house gates (net SR >= 1, shift placebo p < 0.10, 2x cost-stress, concentration <= 25%, convention swap); then STOP-AND-DECIDE",
    "holdout": "H2: pools created 2025-04-01..2026-06-30 (virgin for every DEX signal); enumeration fetched later, never evaluated without a user decision",
    "mechanics": "scripts/predlab_nlst4_{screen,features,p0}.py reuse predlab_nlst_dex_fetch phase_a/b/c (quota override, closed script unedited), predlab_nlst2_features, predlab_nlst3_features; logs data/predlab/nlst/nlst4_*.log; ledger predlab_nlst4; THESIS section 79",
    "stop_rule": "no re-tuning of quota, features, signs or thresholds after any pool outcome is seen; P0 script refuses to run twice",
}


def main() -> None:
    gates = registry.load_gates()
    if "predlab_nlst4" in gates:
        raise SystemExit("predlab_nlst4 already registered")
    gates["predlab_nlst4"] = ENTRY
    registry.gates_path().write_text(json.dumps(gates, indent=1))
    print("gates.json['predlab_nlst4'] written")


if __name__ == "__main__":
    main()

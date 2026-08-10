"""Register llm_c2_veto_ovl (LLM asymmetric risk veto on champion book).

Idempotent: refuses to overwrite an existing llm_c2_veto_ovl entry.
Charter: docs/superpowers/specs/2026-08-10-llm-c2-veto-charter.md
Parent proposal: master_thesis/LLM_INTEGRATION_PROPOSAL_2026-08.md §6.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

GATES = Path("data/predlab/gates.json")

ENTRY = {
    "registered_utc": "2026-08-10",
    "spec": "docs/superpowers/specs/2026-08-10-llm-c2-veto-charter.md",
    "proposal": "master_thesis/LLM_INTEGRATION_PROPOSAL_2026-08.md §6 (charter C2)",
    "purpose": "reduce-only LLM news veto on Phase-O champion book: DD/CVaR reduction at SR non-inferiority",
    "book": "ewma_20 eq_h1 top-200 + vt15_naive20_b100 (O4 formula), frozen; report-only reproduction",
    "windows": {
        "dev_D": ["2021-01-01", "2025-03-31"],
        "V": ["2025-04-01", "2026-07-01 — NON-VIRGIN, disclosure-only, no gate reads it"],
        "forward_F": ["2026-07-02", "OPEN — sealed; veto forward one-shot only alongside champion F spend (earliest 2027-01-02)"],
    },
    "mechanism": {
        "multiplier_map": {"severity_2": 0.0, "severity_1": 0.5, "severity_0": 1.0},
        "budget": "<=10 veto-days (m<1) per calendar year, deterministic calendar-order enforcement",
        "actuation": "s_veto_t = s_t * m_t; O4 cost formula on s_veto (transition costs charged)",
        "causality": "m_t may use news ingest <= end of day t-1 UTC (oracle P0 exempt: ceiling only)",
    },
    "probes": {
        "P0_oracle": "perfect-foresight m=0 on k=10 worst overlaid-book days per calendar year in D; STOP if rel MaxDD reduction < 0.20 or dSR < -0.05",
        "P1_news_recall": "admissible corpus (Alpaca PIT store + declared backfill of missing D months + GDELT backfill; frozen before P2) contains >=1 crisis-class headline <=24h before each oracle veto day; STOP if coverage < 0.60",
        "P2_classifier": "gpt-5.4-mini temp 0, one frozen prompt (charter appendix A), 48h digest max 60 headlines thru t-1; LOEO over 7 frozen episodes; recall >=0.5 of oracle days; anonymization kill-probe: anon recall >= 0.7 x named recall else STOP",
        "P3_overlay": "G1 rel MaxDD reduction >=0.10; G2 rel CVaR5 improvement >=0.05; G3 dSR >= -0.10 AND stationary-bootstrap(20d, 2000) P(dSR<=-0.30)<0.05; G4 random-veto placebo 400 budget-matched draws, real > p95; G5 veto hits >=2 distinct frozen episodes",
    },
    "episodes_loeo": [
        "2021-05 crash", "2022-05 Terra/LUNA", "2022-06/07 3AC/Celsius",
        "2022-11 FTX", "2023-03 USDC/SVB", "2024-08 carry unwind",
        "2025-02/03 drawdown",
    ],
    "multiplicity": "<=6 ledgered configs into predlab DSR pool (oracle 1, classifier named+anon 2, overlay real+placebo 2, reserve 1)",
    "llm_spend_cap_usd": 50,
    "stop_rule": "any probe STOP = charter dead this cycle; no post-hoc episode exclusions, budget changes, or prompt iteration after eval output exists; V/F never read by gates; amendments only pre-result, declared in-file",
}


def main() -> int:
    gates = json.loads(GATES.read_text())
    if "llm_c2_veto_ovl" in gates:
        print("llm_c2_veto_ovl already registered — refusing to overwrite")
        return 1
    gates["llm_c2_veto_ovl"] = ENTRY
    GATES.write_text(json.dumps(gates, indent=1))
    print("registered llm_c2_veto_ovl")
    return 0


if __name__ == "__main__":
    sys.exit(main())

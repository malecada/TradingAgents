"""Register the S1 live-execution measurement run (observational, no claim).

Idempotent: refuses to overwrite an existing predlab_s1_live entry.
Spec: docs/superpowers/specs/2026-08-21-s1-live-executor-design.md
Precedent: predlab_xasset_register.py (direct gates.json read-modify-write).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.predlab import registry  # noqa: E402

GATES = PROJECT_ROOT / "data" / "predlab" / "gates.json"

ENTRY = {
    "type": "observational",
    "registered_utc": None,  # stamped below
    "description": (
        "S1 champion live execution measurement: journal-follower trading "
        "the Phase-O champion book (journal_champion.jsonl) with ~$3,000 "
        "real capital on Binance USDT-M perps. Purpose: measure real taker "
        "fills, per-leg slippage vs paper mark_px, and implementation "
        "shortfall. NOT a registered gate; no pass/fail claim attached; "
        "the sealed paper forward test (final_champion, one-shot >= 2027-01) "
        "is unaffected and remains authoritative. A testnet rehearsal phase "
        "(s1_testnet/, plumbing only) precedes live trading; its fills feed "
        "no conclusions."),
    "capital_usdt": 3000,
    "rollout": (
        "dry-run -> testnet rehearsal (s1_testnet/, plumbing only) -> user "
        "go/no-go -> live $3,000"),
    "risk_rails": {
        "gross_cap_x_equity": 2.2, "per_symbol_cap_of_gross": 0.05,
        "daily_loss_halt": 0.05, "leverage": 2, "order_type": "MARKET"},
    "artifacts": "data/predlab/s1_live/",
    "spec": "docs/superpowers/specs/2026-08-21-s1-live-executor-design.md",
}


def main() -> int:
    gates = json.loads(GATES.read_text())
    if "predlab_s1_live" in gates:
        print("predlab_s1_live already registered — skip")
        return 0
    ENTRY["registered_utc"] = datetime.now(timezone.utc).isoformat()
    gates["predlab_s1_live"] = ENTRY
    GATES.write_text(json.dumps(gates, indent=1) + "\n")
    registry.log_trial(
        "predlab_s1_live", "registration", "journal_follower",
        {"capital_usdt": 3000, "rollout": ENTRY["rollout"]},
        [ENTRY["registered_utc"], ENTRY["registered_utc"]],
        {"note": "observational measurement run registered, no claim"})
    print("registered predlab_s1_live (observational) in", GATES)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Phase-1 predictability map roll-up (P1-08).

Reads all cards for predlab_p1_classical, picks the champion per cell (latest
tier), applies BH-FDR (q=0.10) across cells on champion-vs-baseline DM p, and
writes docs/predlab/reports/phase1_map.md. Verdict downgrades are ONLY via the
explicit OVERRIDES map below, each with a documented reason (charter A1 /
strongest-baseline principle) — never silent.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.predlab import registry, rollup  # noqa: E402

GATES_KEY = "predlab_p1_classical"

# Documented verdict overrides (charter A1: strongest-baseline principle).
OVERRIDES = {
    "ETHUSDT|24h|T3_rv": (
        "PREDICTABLE-VS-WEAK-ONLY",
        "battery p 4.8e-12 vs har_levels reflects baseline fragility; no "
        "significant edge vs log_har (p 0.43) or EWMA (p 0.21) — forensics v2 K3",
    ),
    "ETHUSDT|1h|T3_rv": (
        "SKILL-CANDIDATE (family)",
        "gjr11 = egarch11 (pairwise p 0.50); GARCH family beats har_levels "
        "(p 8.7e-58) and EWMA (p 0.003); single champion deferred to Phase-5 MCS",
    ),
}

# Effect floors per target (registration, anchors); improvement_pct is vs the
# registered strong baseline as computed by rollup.champion.
FLOORS = {"T1": None, "T2": None, "T3": 2.0, "T4": 5.0, "T6": 5.0}

# T2 floor evidence is accuracy-edge, computed from stored forecasts
# (scripts run 2026-07-31): cell -> (edge_pp, floor_pp, pass)
T2_EDGE = {
    "BTCUSDT|1h|T2_dir": (2.86, 2.0, True),
    "ETHUSDT|1h|T2_dir": (2.59, 2.0, True),
    "BTCUSDT|24h|T2_dir": (None, 2.0, False),
    "ETHUSDT|24h|T2_dir": (None, 2.0, False),
    "BTCUSDT|7d|T2_dir": (None, 2.0, False),
    "ETHUSDT|7d|T2_dir": (None, 2.0, False),
}


def main() -> None:
    cards_dir = registry.gates_path().parent / "cards" / GATES_KEY
    rows = []
    for path in sorted(cards_dir.glob("*.json")):
        card = json.loads(path.read_text())
        tier = "t1" if "t1" in card else "t0"
        payload = card[tier]
        cell = payload["cell"]
        ch = rollup.champion(payload)
        target = cell.split("|")[-1].split("_")[0]
        floor = FLOORS.get(target)
        floor_pass = None
        if target == "T2":
            edge = T2_EDGE.get(cell)
            floor_pass = bool(edge and edge[2])
        elif floor is not None and ch["improvement_pct"] is not None:
            floor_pass = ch["improvement_pct"] >= floor
        rows.append({
            "cell": cell, "tier": tier, **ch, "floor_pass": floor_pass,
        })

    fdr = rollup.bh_fdr(
        {r["cell"]: r["dm_p"] for r in rows if r["dm_p"] == r["dm_p"]}, q=0.10
    )
    lines = [
        "# Phase-1 Predictability Map (P1-08 roll-up, 2026-07-31)",
        "",
        f"Cells: {len(rows)} | BH-FDR q=0.10 across cells | verdict downgrades",
        "only via documented overrides (strongest-baseline principle).",
        "",
        "| Cell | Champion | Impr% vs base | DM p | FDR | Floor | Stable | Verdict |",
        "|---|---|---:|---:|---|---|---|---|",
    ]
    n_cand = 0
    for r in rows:
        cell = r["cell"]
        fdr_pass = fdr.get(cell, False)
        if cell in OVERRIDES:
            verdict, reason = OVERRIDES[cell]
        else:
            verdict = rollup.verdict(
                fdr_pass=fdr_pass, floor_pass=bool(r["floor_pass"]),
                stable=bool(r["subperiod_stable"]),
                baseline_wins=r["baseline_wins"], override=None,
            )
            reason = ""
        if verdict.startswith("SKILL-CANDIDATE"):
            n_cand += 1
        imp = "" if r["improvement_pct"] is None else f"{r['improvement_pct']:.1f}"
        dmp = "" if r["dm_p"] != r["dm_p"] else f"{r['dm_p']:.2g}"
        lines.append(
            f"| {cell} | {r['model']} | {imp} | {dmp} | "
            f"{'Y' if fdr_pass else 'n'} | "
            f"{'Y' if r['floor_pass'] else ('n' if r['floor_pass'] is not None else '—')} | "
            f"{'Y' if r['subperiod_stable'] else 'n'} | **{verdict}**"
            + (f" — {reason}" if reason else "") + " |"
        )
    lines += [
        "",
        f"**{n_cand} SKILL-CANDIDATE cells.** Ledger trials: "
        f"{registry.trial_count()} unique configs.",
    ]
    out = PROJECT_ROOT / "docs" / "predlab" / "reports" / "phase1_map.md"
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()

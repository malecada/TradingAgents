"""Unregistered diagnostic for Charter 0: gate outcomes under the two extreme resolutions of
the blind review (every dispute against the model; every dispute for the model), plus the
mechanism split. Reads committed E1 outputs only; computes no lifecycle receipt.

Rationale (recorded 2026-11-08): the reviewer was unavailable; if both bounds agree, the
registered verdict is determined without the review and the review becomes a refinement of
point estimates, not of the decision. This script never replaces E2.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from llm_event_xs_truth import check_reproduction, class_counts, dir_reader, load_rounds  # noqa: E402
from llm_jev_review import apply_review, class_set  # noqa: E402
from llm_jev_score import evaluate  # noqa: E402
from llm_v2c0_p0 import E1, PROGRAM_DIR  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def best_case_filled(rows, key):
    filled = {}
    for row in rows:
        info = key[str(row["row"])]
        same = {p["class"]: True for p in row["same"]}
        if row["kind"] == "entity":
            filled[row["row"]] = {"verdict": None, "labels": None, "same": {row["entity_class"]: True}}
        elif row["kind"] == "class":
            filled[row["row"]] = {"verdict": "A" if info["A"] == "jev" else "B", "labels": None, "same": same}
        else:
            filled[row["row"]] = {"verdict": "BOTH", "labels": None, "same": same}
    return filled


def _agg(truth, pred, idxs):
    c = class_counts({i: truth[i] for i in idxs}, {i: pred[i] for i in idxs})
    tp = sum(v["tp"] for v in c.values()); fp = sum(v["fp"] for v in c.values()); fn = sum(v["fn"] for v in c.values())
    return {"rows": len(idxs), "tp": tp, "fp": fp, "fn": fn,
            "precision": tp / max(1, tp + fp), "recall": tp / max(1, tp + fn)}


def main() -> int:
    rounds = load_rounds(dir_reader(ROOT))
    check_reproduction(rounds)
    out = ROOT / "research_runs" / E1 / "outputs"
    named = json.loads((out / "ds_labels.json").read_text())
    anon = json.loads((out / "ds_labels_anon.json").read_text())
    repeat = json.loads((out / "ds_labels_repeat.json").read_text())
    rows = json.loads((out / "review_sheet.json").read_text())["rows"]
    key = json.loads((out / "review_key.json").read_text())
    pred = {int(k): v["events"] for k, v in named.items()}
    stored = {int(i): list(e) for d in rounds.values() for i, e in d.truth.items()}
    worst = evaluate(stored, pred, {}, named, anon)
    truth_b, same, stats = apply_review(rounds, named, rows, key, best_case_filled(rows, key))
    best = evaluate(truth_b, pred, same, named, anon, jev_adopted=frozenset(stats["jev_adopted_rows"]))
    audited = {int(i) for d in rounds.values() for i in d.audited}
    amb_empty = [i for i in stored if named[str(i)]["ambiguous"] and not named[str(i)]["events"]]
    disputes = {}
    for row in rows:
        if row["kind"] == "class":
            info = key[str(row["row"])]
            ds, st = (row["A"], row["B"]) if info["A"] == "jev" else (row["B"], row["A"])
            disputes[f"{st} -> {ds}"] = disputes.get(f"{st} -> {ds}", 0) + 1
    result = {
        "note": "Unregistered diagnostic; not a lifecycle receipt. E2 requires the filled sheet.",
        "e1": E1,
        "worst_case": {"primary": worst["primary"]["verdict"], "secondary": worst["secondary"]["verdict"],
                       "gate_rows": worst["gate_rows"], "asset_link": worst["gates"]["asset_link"],
                       "anon_agreement": worst["gates"]["anon_agreement"]},
        "best_case": {"primary": best["primary"]["verdict"], "secondary": best["secondary"]["verdict"],
                      "gate_rows": best["gate_rows"], "asset_link": best["gates"]["asset_link"],
                      "anon_agreement": best["gates"]["anon_agreement"]},
        "mechanism": {
            "stored_truth_all": _agg(stored, pred, sorted(stored)),
            "human_adjudicated_rows": _agg(stored, pred, sorted(audited)),
            "unaudited_rows": _agg(stored, pred, sorted(set(stored) - audited)),
            "raw_events": sum(l["raw_events"] for l in named.values()),
            "kept_events": sum(len(l["events"]) for l in named.values()),
            "spans_dropped": sum(l["spans_dropped"] for l in named.values()),
            "ambiguous_rate": sum(l["ambiguous"] for l in named.values()) / len(named),
            "ambiguous_empty_rows": len(amb_empty),
            "ambiguous_empty_rows_with_truth_events": sum(1 for i in amb_empty if stored[i]),
            "truth_events_in_ambiguous_empty_rows": sum(len(stored[i]) for i in amb_empty),
            "repeat_class_set_flips": sum(class_set(named[k]["events"]) != class_set(v["events"])
                                          for k, v in repeat.items()),
            "repeat_n": len(repeat),
            "class_dispute_pattern": disputes,
        },
    }
    target = ROOT / PROGRAM_DIR / "p0_bounds.json"
    target.write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps({k: result[k] for k in ("worst_case", "best_case")}, indent=1)[:1500])
    print(target)
    return 0


if __name__ == "__main__":
    sys.exit(main())

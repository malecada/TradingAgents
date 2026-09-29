"""Blind review sheet for Jev disputes (charter §3.2): build, render, parse, apply.

Class disputes offer A, B, NO EVENTS or NEITHER (BOTH is not offered because
the class sets differ). Agreement spot-checks offer BOTH, NO EVENTS or
NEITHER. Entity questions ask whether two names denote the same entity. A Jev
asset of ``none`` is never sent for entity review; it counts as a mismatch.
"""
from __future__ import annotations

import random
import re

from llm_event_xs_p0_score import norm_asset
from llm_event_xs_truth import match_events, parse_labels
from llm_jev_questions import CLASS_DEFINITIONS, CLASSES, GENERAL_RULES, V2_RULES, build_state

SEED = 20260929
N_CHECKS = 20
CLASS_VERDICTS = frozenset({"A", "B", "NO EVENTS"})
CHECK_VERDICTS = frozenset({"BOTH", "NO EVENTS"})


def header() -> str:
    """Reviewer header rendered from the frozen question wording (charter §3.2/§4)."""
    lines = [
        "# Jev P0 blind review — llm-jev-p0-label-20260929",
        "",
        "Judge only from the article text shown.",
        "",
        "Do not consult, until the filled sheet is committed: anything under "
        "`research_runs/llm-jev-p0-label-20260929/outputs/`, anything under "
        "`data/llm_event_xs/` (C1 labels and sheets), or any git/GitHub view of those files.",
        "",
        GENERAL_RULES,
    ]
    for cls in CLASSES:
        bullet = f"- {cls}: {CLASS_DEFINITIONS[cls]}"
        if cls in V2_RULES:
            bullet += f" Additional rule: {V2_RULES[cls]}"
        lines.append(bullet)
    lines.append("The additional rules apply to every row.")
    lines.append("")
    lines.append("- `class` rows: A and B list event classes only. Write `A` or `B` only if "
                 "that class set is exactly right; `NO EVENTS` if the article reports no "
                 "qualifying event; otherwise `NEITHER: class/asset; class/asset` with the "
                 "correct events.")
    lines.append("- `check` rows: `BOTH` if the shown class set is right, `NO EVENTS`, or "
                 "`NEITHER: class/asset; ...`.")
    lines.append("- `ENTITY (class)` lines appear for classes present on both sides whose "
                 "affected-entity names differ; answer the following `SAME (class)` line with "
                 "`Y` if both names denote the same affected entity, else `N`.")
    lines.append("- `entity` rows: A and B are two names for the affected entity of the stated "
                 "class; answer `SAME` with `Y` or `N`.")
    return "\n".join(lines) + "\n"


def _tokens(name: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", norm_asset(name))


def auto_asset_match(a, b) -> bool:
    """Equal after C1 normalization/aliases, or one is a contiguous token run of the other."""
    if not a or not b:
        return False
    x, y = _tokens(a), _tokens(b)
    if not x or not y:
        return False
    short, long_ = (x, y) if len(x) <= len(y) else (y, x)
    return any(long_[i:i + len(short)] == short for i in range(len(long_) - len(short) + 1))


def class_set(events: list[dict]) -> tuple[str, ...]:
    return tuple(sorted({e["class"] for e in events}))


def label_string(events: list[dict]) -> str:
    if not events:
        return "NO EVENTS"
    return "; ".join(class_set(events))


def _entity_pairs(truth_events: list[dict], jev_events: list[dict]):
    """Same-class pairs whose names fail the automatic rule; one per class.

    Jev emits at most one event per class (llm_jev_labels.aggregate), so one
    pair per class covers every Jev prediction.
    """
    pairs, _, _ = match_events(truth_events, jev_events)
    out, seen = [], set()
    for p, t in pairs:
        if (p.get("asset") and t.get("asset") and p["class"] not in seen
                and not auto_asset_match(p["asset"], t["asset"])):
            seen.add(p["class"])
            out.append((p["class"], p["asset"], t["asset"]))
    return out


def build_review(rounds: dict, jev: dict, seed: int = SEED, n_checks: int = N_CHECKS):
    """Return (rows, key). ``jev`` maps str(sample_idx) -> label dict with ``events``."""
    rng = random.Random(seed)
    items, agree = [], []
    for data in rounds.values():
        for idx in data.sample.index:
            idx = int(idx)
            stored, mine = data.truth[idx], jev[str(idx)]["events"]
            if idx not in data.audited and class_set(stored) != class_set(mine):
                items.append(("class", data, idx, None, None, None))
                continue
            if idx not in data.audited:
                agree.append((data, idx))
            for cls, j_name, t_name in _entity_pairs(stored, mine):
                items.append(("entity", data, idx, cls, j_name, t_name))
    for data, idx in rng.sample(agree, min(n_checks, len(agree))):
        items.append(("check", data, idx, None, None, None))
    rng.shuffle(items)
    rows, key = [], {}
    for number, (kind, data, idx, cls, j_name, t_name) in enumerate(items, 1):
        jev_side = "A" if rng.random() < 0.5 else "B"
        other = "B" if jev_side == "A" else "A"
        stored, mine = data.truth[idx], jev[str(idx)]["events"]
        record = data.sample.loc[idx]
        row = {"row": number, "kind": kind, "sample_idx": idx, "store": str(record["store"]),
               "date": str(record["event_ts"])[:10], "text": build_state(record.to_dict()),
               "entity_class": cls, "same": []}
        if kind == "entity":
            row[jev_side], row[other] = j_name, t_name
            row["same"] = [{"class": cls, jev_side: j_name, other: t_name}]
        else:
            row[jev_side], row[other] = label_string(mine), label_string(stored)
            if kind == "class":
                same = []
                for c, j, t in _entity_pairs(stored, mine):
                    first_jev = rng.random() < 0.5
                    names = (j, t) if first_jev else (t, j)
                    same.append({"class": c, "X": names[0], "Y": names[1]})
                row["same"] = same
        rows.append(row)
        key[str(number)] = {"kind": kind, "sample_idx": idx, "entity_class": cls,
                            jev_side: "jev", other: "stored"}
    return rows, key


def _flat(value) -> str:
    return " ".join(str(value).split())


def render_markdown(rows: list[dict]) -> str:
    out = [header()]
    for row in rows:
        out.append(f"### row {row['row']} ({row['store']}, {row['date']}, {row['kind']})\n")
        text = row["text"]
        headline = _flat(text.get('headline', ''))
        out.append(f"**{headline}**\n")
        for name in ("summary", "content"):
            if text.get(name):
                out.append("> " + _flat(text[name]) + "\n")
        if row["kind"] == "entity":
            out.append(f"- Event class: {row['entity_class']}")
        out.append(f"- A: {_flat(row['A'])}")
        out.append(f"- B: {_flat(row['B'])}")
        if row["kind"] != "entity":
            out.append("- VERDICT: ")
        for pair in row["same"]:
            if "X" in pair:
                out.append(f"- ENTITY ({pair['class']}): X = {_flat(pair['X'])} | "
                          f"Y = {_flat(pair['Y'])}")
            else:
                out.append(f"- ENTITY ({pair['class']}): A = {_flat(pair['A'])} | "
                          f"B = {_flat(pair['B'])}")
            out.append(f"- SAME ({pair['class']}): ")
        out.append("")
    return "\n".join(out) + "\n"


def parse_filled(text: str, rows: list[dict]) -> dict[int, dict]:
    blocks = {}
    for block in re.split(r"(?m)^(?=### row )", text):
        head = re.match(r"### row (\d+)", block)
        if head:
            blocks[int(head.group(1))] = block
    problems, parsed = [], {}
    for row in rows:
        number = row["row"]
        block = blocks.get(number)
        if block is None:
            problems.append(f"row {number}: missing from sheet")
            continue
        entry = {"verdict": None, "labels": None, "same": {}}
        if row["kind"] != "entity":
            match = re.search(r"(?m)^- VERDICT:[ \t]*(.*)$", block)
            raw = (match.group(1) if match else "").strip()
            upper = raw.upper()
            allowed = CLASS_VERDICTS if row["kind"] == "class" else CHECK_VERDICTS
            if upper in allowed:
                entry["verdict"] = upper
            elif upper.startswith("NEITHER") and ":" in raw:
                try:
                    labels = parse_labels(raw.split(":", 1)[1])
                except ValueError as exc:
                    problems.append(f"row {number}: bad NEITHER labels ({exc})")
                else:
                    entry["verdict"], entry["labels"] = "NEITHER", labels
                    if not labels:
                        problems.append(f"row {number}: NEITHER needs at least one label; "
                                        f"use NO EVENTS")
                    for label in labels:
                        if label["class"] not in CLASSES:
                            problems.append(f"row {number}: NEITHER class "
                                            f"{label['class']!r} not recognized")
                        if not label.get("asset", "").strip():
                            problems.append(f"row {number}: NEITHER asset is empty")
            else:
                problems.append(f"row {number}: verdict {raw!r} not in {sorted(allowed)} "
                                f"or 'NEITHER: labels'")
        for pair in row["same"]:
            match = re.search(rf"(?m)^- SAME \({re.escape(pair['class'])}\):[ \t]*(.*)$", block)
            answer = (match.group(1) if match else "").strip().upper()
            if answer in ("Y", "YES"):
                entry["same"][pair["class"]] = True
            elif answer in ("N", "NO"):
                entry["same"][pair["class"]] = False
            else:
                problems.append(f"row {number}: SAME ({pair['class']}) must be Y or N")
        parsed[number] = entry
    if problems:
        raise ValueError("review sheet incomplete:\n" + "\n".join(problems))
    return parsed


def apply_review(rounds: dict, jev: dict, rows: list[dict], key: dict, filled: dict):
    truth = {int(i): list(e) for data in rounds.values() for i, e in data.truth.items()}
    stored = dict(truth)
    same, jev_adopted, checks, check_errors = {}, set(), 0, 0
    for row in rows:
        info, entry = key[str(row["row"])], filled[row["row"]]
        idx = info["sample_idx"]
        if row["kind"] == "entity":
            for cls, answer in entry["same"].items():
                same[f"{idx}|{cls}"] = answer
            continue
        verdict = entry["verdict"]
        if verdict != "NEITHER":
            for cls, answer in entry["same"].items():
                same[f"{idx}|{cls}"] = answer
        if verdict in ("A", "B"):
            adopted_jev = info[verdict] == "jev"
            truth[idx] = list(jev[str(idx)]["events"]) if adopted_jev else stored[idx]
            if row["kind"] == "class" and adopted_jev:
                jev_adopted.add(idx)
        elif verdict == "NO EVENTS":
            truth[idx] = []
        elif verdict == "NEITHER":
            truth[idx] = entry["labels"]
        if row["kind"] == "check":
            checks += 1
            check_errors += verdict != "BOTH" and truth[idx] != stored[idx]
    stats = {"rows": len(rows), "class_rows": sum(r["kind"] == "class" for r in rows),
             "check_rows": checks, "entity_rows": sum(r["kind"] == "entity" for r in rows),
             "check_error_rate": check_errors / checks if checks else None,
             "jev_adopted_rows": sorted(jev_adopted)}
    return truth, same, stats

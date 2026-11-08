"""Blind review sheet for Charter 0 disputes; construction and parsing reuse the Jev protocol."""
from __future__ import annotations

from llm_jev_questions import CLASS_DEFINITIONS, CLASSES, GENERAL_RULES, V2_RULES
from llm_jev_review import _flat, apply_review, build_review, parse_filled  # noqa: F401

SEED = 20261109
N_CHECKS = 20
E1 = "llm-v2c0-p0-label-20261109"


def header() -> str:
    lines = [
        f"# DeepSeek V4-Pro P0 blind review — {E1}",
        "",
        "Judge only from the article text shown.",
        "",
        "Do not consult, until the filled sheet is committed: anything under "
        f"`research_runs/{E1}/outputs/`, anything under `data/llm_event_xs/` (C1 labels and "
        "sheets), or any git/GitHub view of those files.",
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


def build(rounds: dict, labels: dict):
    return build_review(rounds, labels, seed=SEED, n_checks=N_CHECKS)


def render_markdown(rows: list[dict]) -> str:
    out = [header()]
    for row in rows:
        out.append(f"### row {row['row']} ({row['store']}, {row['date']}, {row['kind']})\n")
        text = row["text"]
        out.append(f"**{_flat(text.get('headline', ''))}**\n")
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

"""Check the thesis table of the v2 attempts (``tables/T_8_1_v2_attempts.tex``) against the run receipts.

Only the cells that carry evidence are compared: test sample, gate statistics, verdict and cost. The descriptive
column (agent role and target) is prose and stays with the thesis. Read-only; nothing is generated into the thesis.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from tradingagents.mav2 import registry

DEFAULT_TABLE = registry.ROOT.parent / "thesis-latex" / "tables" / "T_8_1_v2_attempts.tex"
LABELS = ("V1", "V1b", "V2", "V3", "V4", "V5")
_T = re.compile(r"\$t\s*=\s*(-?\d+(?:\.\d+)?)\$")
_ROW = re.compile(r"^\s*(V1b|V[1-5])\s*&")


@dataclass(frozen=True)
class Expected:
    label: str
    sample: str
    t_values: tuple[str, ...]      # every $t=...$ in the gate cell, in order, two decimals
    verdict: str
    cost: str                      # as typeset, e.g. \$5.75 or \$0


def _t(x: float) -> str:
    s = f"{x:.2f}"
    return "0.00" if s == "-0.00" else s


def _cost(usd: float | None) -> str:
    if usd is None:
        return "?"
    return r"\$0" if usd == 0 else rf"\${usd:.2f}"


def expected(root: Path = registry.ROOT) -> list[Expected]:
    rows = {r["label"]: r for r in registry.status(root, verify=False)}
    out = []
    for label in LABELS:
        r = rows[label]
        if label == "V1":
            out.append(Expected(label, "none", (), "interrupted", _cost(r["cost_usd"])))
            continue
        ts = [_t(r["value"])]
        if label == "V1b":
            verdict = registry._json(registry.get(label).outputs(root) / "verdict.json")
            ts.append(_t(verdict["forecast_gates"]["hybrid_ic_nw_t"]["value"]))
        out.append(Expected(label, r["sample"], tuple(ts), r["verdict"], _cost(r["cost_usd"])))
    return out


def parse_rows(tex: str) -> dict[str, list[str]]:
    """Body rows of the table, keyed by attempt label; cells split on ``&`` with the row end removed."""
    rows = {}
    for line in tex.splitlines():
        m = _ROW.match(line)
        if m:
            body = line.split(r"\\")[0]
            rows[m.group(1)] = [c.strip() for c in body.split("&")]
    return rows


def check_table(tex: str, exp: list[Expected]) -> list[str]:
    """Differences between the typeset table and the receipts; empty when they agree."""
    rows = parse_rows(tex)
    problems = [f"{label}: row only in the table" for label in rows if label not in {e.label for e in exp}]
    for e in exp:
        cells = rows.get(e.label)
        if cells is None:
            problems.append(f"{e.label}: row missing from the table")
            continue
        if len(cells) != 6:
            problems.append(f"{e.label}: expected 6 cells, found {len(cells)}")
            continue
        _, _, sample, gate, verdict, cost = cells
        found_t = tuple(_t(float(v)) for v in _T.findall(gate))
        for name, typeset, want in (("sample", sample, e.sample), ("verdict", verdict, e.verdict),
                                    ("cost", cost, e.cost)):
            if typeset != want:
                problems.append(f"{e.label}: {name} typeset {typeset!r}, receipts give {want!r}")
        if e.t_values and found_t != e.t_values:
            problems.append(f"{e.label}: gate t typeset {found_t}, receipts give {e.t_values}")
        if not e.t_values and gate != "not reached":
            problems.append(f"{e.label}: gate typeset {gate!r}, receipts give 'not reached'")
    return problems


def check_file(path: Path = DEFAULT_TABLE, root: Path = registry.ROOT) -> list[str]:
    return check_table(Path(path).read_text(), expected(root))

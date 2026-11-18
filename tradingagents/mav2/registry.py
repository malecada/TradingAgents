"""Registry of the registered runs of the family ``llm-multiagent-v2``.

Only identities and paths are written here. Every number (verdict, gate statistic, test sample, cost) is read from
the run receipts and stored outputs, so the status table cannot drift from the evidence. Attempt labels follow the
thesis (chapter "Second Multi-Agent Framework"): V1, V1b, V2-V5 for Charters 1, 1b, 2-5.
"""
from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FAMILY = "llm-multiagent-v2"


@dataclass(frozen=True)
class Run:
    label: str                 # thesis label
    run_id: str                # directory under research_runs/
    runner: str | None         # scripts/<module>.py that executed the run
    question: str              # one line, what the run asked
    attempt: bool = True       # counts against the attempt budget of the family

    def run_dir(self, root: Path = ROOT) -> Path:
        return Path(root) / "research_runs" / self.run_id

    def outputs(self, root: Path = ROOT) -> Path:
        return self.run_dir(root) / "outputs"

    def claim(self, root: Path = ROOT) -> dict:
        return json.loads((self.run_dir(root) / "claim.json").read_text())

    def charter(self, root: Path = ROOT) -> str:
        """Path of the frozen charter text, as pinned in the claim."""
        return self.claim(root)["experiment"]["charter"]["path"]

    def registration(self, root: Path = ROOT) -> str:
        return self.claim(root)["registration"]


RUNS: tuple[Run, ...] = (
    Run("C0", "llm-v2c0-p0-label-20261109", None,
        "Extraction-quality probe of the reader model (family llm-news-event-extraction, not an attempt of this "
        "family)", attempt=False),
    Run("V1", "llm-v2c1-dev-run-20261111", "llm_v2c1_run",
        "Agents forecast the weekly relative return from anonymised dossiers; debate and judge"),
    Run("V1b", "llm-v2c1b-dev-run-20261112", "llm_v2c1b_run",
        "V1 with the evaluation code corrected; cached V1 calls reused, older weeks run under the remaining cap"),
    Run("V2", "llm-v2c2-reader-dev-run-20261112", "reader_charter2_run",
        "Readers extract facts from news; a fitted ridge model forecasts the weekly return"),
    Run("V3", "llm-v2c3-volatility-dev-run-20261113", "reader_charter3_run",
        "Same reader records; target changed to next-week volatility rank"),
    Run("V4", "llm-v2c4-fresh-news-dev-run-20261114", "reader_charter4_run",
        "Reader tone at a daily 00:00 UTC decision; next-day relative return"),
    Run("V5", "llm-v2c5-direct-comparison-dev-run-20261117", "cmp_charter5_run",
        "Pairwise comparison of anonymised text dossiers, public news archive added"),
)


def get(label_or_id: str) -> Run:
    for run in RUNS:
        if label_or_id in (run.label, run.run_id):
            return run
    raise KeyError(f"unknown run {label_or_id!r}; known: {', '.join(r.label for r in RUNS)}")


def _json(path: Path) -> dict | None:
    return json.loads(path.read_text()) if path.is_file() else None


# --- headline gate, read from verdict.json ------------------------------------------------------------------------

def _h_v1b(v: dict) -> tuple[str, float]:
    return "encompassing_llm_nw_t", v["forecast_gates"]["encompassing_llm_nw_t"]["value"]


def _h_v2(v: dict) -> tuple[str, float]:
    return "text_encompassing.nw_t", v["gates"]["text_encompassing"]["value"]["nw_t"]


def _h_v3(v: dict) -> tuple[str, float]:
    return "reader_partial_ic.nw_t", v["gates"]["reader_partial_ic"]["value"]["nw_t"]


def _h_v4(v: dict) -> tuple[str, float]:
    return "reader_partial.nw_t", v["gates"]["reader_partial"]["value"]["nw_t"]


def _h_v5(v: dict) -> tuple[str, float]:
    return "G1_coefficient_t", v["gates"]["G1_coefficient_t"]["t"]


HEADLINE: dict[str, Callable[[dict], tuple[str, float]]] = {"V1b": _h_v1b, "V2": _h_v2, "V3": _h_v3, "V4": _h_v4, "V5": _h_v5}


def sample(run: Run, root: Path = ROOT) -> str | None:
    """Test sample as recorded by the run (weeks or days)."""
    out = run.outputs(root)
    if run.label == "V1b":
        cost = _json(out / "cost.json")
        return f"{cost['weeks_completed']} weeks" if cost else None
    verdict = _json(out / "verdict.json")
    if not verdict:
        return None
    if "test_days" in verdict:
        return f"{verdict['test_days']} days"
    return f"{verdict['test_weeks']} weeks" if "test_weeks" in verdict else None


# --- cost of model calls ------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Cost:
    usd: float | None
    source: str


def _cache_cost(path: Path) -> float | None:
    """Sum of ``value.meta.cost`` over a JSONL call cache; None if the cache is absent (data is not versioned)."""
    if not path.is_file():
        return None
    total = 0.0
    with path.open() as fh:
        for line in fh:
            if line.strip():
                meta = (json.loads(line).get("value") or {}).get("meta") or {}
                total += float(meta.get("cost") or 0.0)
    return total


V5_COST_CACHES = ("data/compare/calls.jsonl", "data/compare/duel_calls.jsonl", "data/compare/probe_calls.jsonl")


def cost(run: Run, root: Path = ROOT) -> Cost:
    """New model spend attributable to the run, with the place it was read from."""
    root = Path(root)
    c1b = _json(get("V1b").outputs(root) / "cost.json")
    if run.label == "C0":
        meta = _json(run.outputs(root) / "run_meta.json")
        return Cost(meta["spent_usd"] if meta else None, "run_meta.json spent_usd")
    if run.label == "V1":
        return Cost(c1b["attempt1"]["recorded_spend_usd"] if c1b else None, "V1b cost.json attempt1.recorded_spend_usd")
    if run.label == "V1b":
        return Cost(c1b["spent_usd"] if c1b else None, "V1b cost.json spent_usd")
    if run.label == "V2":
        reader = _json(run.outputs(root) / "reader.json")
        return Cost(reader["extraction"]["cache"]["paid_usd"] if reader else None, "reader.json extraction.cache.paid_usd")
    if run.label in ("V3", "V4"):
        return Cost(0.0, "no new call: reuses the V2 reader records")
    if run.label == "V5":
        parts = [_cache_cost(root / p) for p in V5_COST_CACHES]
        if any(p is None for p in parts):
            return Cost(None, "call caches absent on this machine")
        return Cost(sum(parts), "meta.cost in the archive, comparison and probe caches; the typing cache records no "
                                "cost (the account balance fell by $7.61, research/multiagent-v2/STATE.md)")
    raise KeyError(run.label)


# --- status ---------------------------------------------------------------------------------------------------------

def status(root: Path = ROOT) -> list[dict]:
    """One row per run: receipt state, verdict, headline gate, test sample, cost. Read-only."""
    from tradingagents.research.verify import verify_run

    rows = []
    for run in RUNS:
        receipt = verify_run(run.run_dir(root))["status"] if run.run_dir(root).is_dir() else "missing"
        verdict = _json(run.outputs(root) / "verdict.json")
        gate, value = HEADLINE[run.label](verdict) if verdict and run.label in HEADLINE else (None, None)
        c = cost(run, root)
        rows.append({"label": run.label, "run_id": run.run_id, "receipt": receipt,
                     "verdict": verdict["verdict"] if verdict else ("interrupted" if run.label == "V1" else None),
                     "gate": gate, "value": value, "sample": sample(run, root), "cost_usd": c.usd, "cost_source": c.source})
    return rows

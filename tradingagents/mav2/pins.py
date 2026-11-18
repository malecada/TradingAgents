"""Check that every file pinned by a run receipt still has its pinned bytes.

Each claim records ``experiment.source_files`` (code and charter texts, sha256) plus the registration and charter
hashes. A file that changed after a run means the checkout no longer holds the code that produced that verdict.
The interrupted first attempt (V1) is the one known exception: its evaluation code was corrected afterwards, and
that correction is the reason Charter 1b exists. The exception is listed explicitly so that any other change fails.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from tradingagents.mav2.registry import ROOT, RUNS, Run

# run label -> files whose change after the run is documented and expected
EXPECTED_DRIFT: dict[str, dict[str, str]] = {
    "V1": {
        "tradingagents/agents_v2/evaluate.py": "evaluation defect of the interrupted V1 run corrected for Charter 1b",
        "tradingagents/agents_v2/portfolio_eval.py": "evaluation defect of the interrupted V1 run corrected for Charter 1b",
    },
}


def sha256_file(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


@dataclass
class PinReport:
    label: str
    pinned: int = 0
    drifted: list[str] = field(default_factory=list)      # changed or missing, not expected
    expected: list[str] = field(default_factory=list)     # changed, documented in EXPECTED_DRIFT

    @property
    def ok(self) -> bool:
        return not self.drifted


def pinned_files(run: Run, root: Path = ROOT) -> dict[str, str]:
    """Every path -> sha256 that the claim of ``run`` pins: source files, the charter and the registration."""
    claim = run.claim(root)
    pins = dict(claim["experiment"].get("source_files") or {})
    charter = claim["experiment"].get("charter")
    if isinstance(charter, dict) and charter.get("sha256"):
        pins[charter["path"]] = charter["sha256"]
    if claim.get("registration_sha256"):
        pins[claim["registration"]] = claim["registration_sha256"]
    return pins


def check_run(run: Run, root: Path = ROOT) -> PinReport:
    root = Path(root)
    report = PinReport(run.label)
    allowed = EXPECTED_DRIFT.get(run.label, {})
    for path, digest in sorted(pinned_files(run, root).items()):
        report.pinned += 1
        if sha256_file(root / path) != digest:
            (report.expected if path in allowed else report.drifted).append(path)
    return report


def check_all(root: Path = ROOT) -> list[PinReport]:
    return [check_run(run, root) for run in RUNS if run.run_dir(root).is_dir()]


def all_pinned_paths(root: Path = ROOT) -> set[str]:
    """Union of the paths pinned by any run: the files that must not be edited."""
    return {p for run in RUNS if run.run_dir(root).is_dir() for p in pinned_files(run, root)}

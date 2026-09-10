"""Reviewed engineering/checker suite; never starts a saved financial experiment.

This explicit inventory is deliberately narrower than the legacy test tree.
Review collection/import behavior and fixtures before adding another module.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OFFLINE_FILES = frozenset({
    "tests/test_offline_workflow.py",
    "tests/test_research_artifact_catalog.py",
    "tests/test_accounting_audit.py",
    "tests/test_event_accounting.py",
    "tests/test_factor_correction.py",
    "tests/test_factor_risk_diagnostics.py",
    "tests/test_factor_risk_policy.py",
    "tests/test_factor_risk_policy_evaluation.py",
    "tests/test_factor_v2_trace.py",
    "tests/test_carry_feasibility_math_2026_09_10.py",
    "tests/test_capture_dated_carry_2026_09_10.py",
    "tests/predlab/test_registry.py",
    "tests/predlab/test_audit_evidence.py",
    "tests/predlab/test_audit_forecast_availability.py",
    "tests/predlab/test_audit_causal_dex.py",
    "tests/predlab/test_audit_nested_inference.py",
    "tests/predlab/test_audit_reeval_common.py",
    "tests/predlab/test_lifecycle_replay_guards.py",
    "tests/predlab/test_lifecycle_exposure_audit.py",
    "tests/predlab/test_funding_snapshot.py",
    "tests/predlab/test_funding_capture.py",
    "tests/predlab/test_funding_paper_admission.py",
    "tests/predlab/test_losses.py",
    "tests/predlab/test_splits.py",
    "tests/predlab/test_meanstats.py",
    "tests/predlab/test_execution_repair.py",
    "tests/dataflows/test_audit_vintages.py",
    "docs/diagnostics-2026-09-10/verification/test_verify_preservation.py",
    "docs/risk-policy-2026-09-10/verification/test_verify_preservation.py",
    "docs/risk-policy-2026-09-10/verification/test_registered_inputs.py",
    "docs/risk-policy-2026-09-10/verification/test_check_results.py",
    "docs/carry-feasibility-2026-09-10/verification/test_check_saved.py",
})
# New preparation modules are synthetic contracts, reviewed by their named owner.
OFFLINE_DIRECTORIES = ("tests/research",)
EXTERNAL_FILES = {
    "tests/regression/test_v2_unchanged.py": frozenset({"empirical"}),
    "tests/execution/test_exchange_smoke.py": frozenset({"network", "account"}),
}


def offline_paths(root=ROOT):
    """Missing admitted files are errors, not silently lost coverage."""
    paths = sorted(OFFLINE_FILES)
    missing = [name for name in paths if not (root / name).is_file()]
    if missing:
        raise ValueError("missing admitted offline test files: " + ", ".join(missing))
    for directory in OFFLINE_DIRECTORIES:
        if (root / directory).is_dir():
            paths.extend(str(p.relative_to(root)) for p in sorted((root / directory).rglob("test_*.py")))
    return paths


def requirements(relative):
    """None means unreviewed; an empty set means reviewed offline engineering."""
    if relative in OFFLINE_FILES or any(relative.startswith(d + "/") for d in OFFLINE_DIRECTORIES):
        return frozenset()
    return EXTERNAL_FILES.get(relative)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collect-only", action="store_true")
    args = parser.parse_args()
    paths = offline_paths()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=str(ROOT),
               PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", RUN_ONLINE_TESTS="0")
    env.pop("PYTEST_ADDOPTS", None)
    command = [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider",
               "--import-mode=importlib", *(["--collect-only"] if args.collect_only else []), *paths]
    print(f"Reviewed offline profile: {len(paths)} modules; legacy/unreviewed modules excluded.", flush=True)
    return subprocess.run(command, cwd=ROOT, env=env).returncode


if __name__ == "__main__":
    raise SystemExit(main())

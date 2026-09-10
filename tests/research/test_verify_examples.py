"""Integrity checking is independent of the admission/lifecycle implementation."""
import json
import subprocess
import sys

import pytest

from .test_lifecycle import api, registered, start, complete


def verifier():
    import importlib.util
    assert importlib.util.find_spec("tradingagents.research.verify"), "independent verifier is missing"
    from tradingagents.research.verify import verify_run
    return verify_run


def test_verify_complete_reads_no_empirical_inputs(registered):
    run = start(registered)
    complete(run)
    (registered[0] / "sample.json").unlink()
    report = verifier()(run.directory)
    assert report["status"] == "complete"
    assert report["cell_count"] == 2


def test_verify_rejects_changed_output(registered):
    run = start(registered)
    complete(run)
    (run.directory / "outputs/summary.json").write_text("changed")
    with pytest.raises(ValueError, match="output hash"):
        verifier()(run.directory)


def test_verify_partial_failure_is_not_success(registered):
    run = start(registered)
    run.fail("synthetic failure")
    assert verifier()(run.directory)["status"] == "failed"


def test_two_synthetic_examples_run_only_in_temporary_repositories():
    result = subprocess.run([sys.executable, "-B", "-m", "tradingagents.research", "examples"],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["synthetic_only"] is True
    assert [r["status"] for r in payload["runs"]] == ["complete", "complete"]

"""Synthetic Git fixtures only; no real registration, market data or ledger access."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
import os
import subprocess

import pytest


def api():
    # A clear assertion records the missing feature before implementation exists.
    import importlib.util
    assert importlib.util.find_spec("tradingagents.research"), "new research lifecycle is missing"
    from tradingagents.research import ResearchRun, admit, runtime_hashes
    return ResearchRun, admit, runtime_hashes


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def commit(root, spec):
    (root / "registration.json").write_text(json.dumps(spec))
    git(root, "add", "registration.json", "engine.py", "selection.txt", "charter.md")
    git(root, "-c", "user.name=Synthetic", "-c", "user.email=synthetic@example.invalid",
        "commit", "-qm", "synthetic registration")
    return git(root, "rev-parse", "HEAD")


@pytest.fixture
def registered(tmp_path):
    Run, admit, runtime_hashes = api()
    git(tmp_path, "init", "-q")
    (tmp_path / "engine.py").write_text("# synthetic runner\n")
    (tmp_path / "selection.txt").write_text("fixed synthetic rule\n")
    (tmp_path / "charter.md").write_text("Synthetic sum and count, fixed cells; no market experiment.\n")
    (tmp_path / "sample.json").write_text('[2, 3]')
    digest = lambda p: hashlib.sha256((tmp_path / p).read_bytes()).hexdigest()
    spec = {
        "schema_version": 1, "program_id": "synthetic-program",
        "families": {"family-a": {"mechanism_id": "synthetic-mechanism", "attempt_budget": 3,
            "prior_attempts": 0, "history_reference": "synthetic; no prior market research"}},
        "datasets": {"sample": {"identity": "synthetic-sample-v1", "history_reference": "synthetic",
            "exposures": [{"start": "2000-01-01T00:00:00Z", "end": "2001-01-01T00:00:00Z", "state": "spent"}]}},
        "experiments": {"example-a": {"family": "family-a", "parent": None,
            "charter": {"path": "charter.md", "sha256": digest("charter.md")},
            "question": "synthetic sum", "stage": "development", "reuse": "exploratory",
            "windows": [{"dataset": "sample", "start": "2000-01-01T00:00:00Z", "end": "2001-01-01T00:00:00Z", "availability": "existing"}],
            "inputs": {"sample": {"path": "sample.json", "sha256": digest("sample.json"), "dataset": "sample"}},
            "source_files": {"engine.py": digest("engine.py")}, "runtime_hashes": runtime_hashes(),
            "selection": None, "cells": ["sum", "count"], "outputs": ["summary.json"]}},
    }
    source = commit(tmp_path, spec)
    return tmp_path, spec, source


def start(fixture, experiment="example-a"):
    root, _, source = fixture
    Run, _, _ = api()
    return Run.start(root=root, registration="registration.json", experiment=experiment, source=source)


def complete(run):
    run.write_json("summary.json", {"sum": 5})
    return run.finish([{"id": "sum", "status": "complete", "value": 5},
                       {"id": "count", "status": "complete", "value": 2}])


def test_feature_contract_is_available():
    assert api()


def test_development_reuses_spent_data_without_claiming_confirmation(registered):
    root, _, source = registered
    _, admit, _ = api()
    admitted = admit(root=root, registration="registration.json", experiment="example-a", source=source)
    assert admitted.experiment["stage"] == "development"
    assert not (root / "research_runs").exists()  # metadata admission has no writes
    with start(registered) as run:
        assert json.loads(run.read_input("sample")) == [2, 3]
        receipt = complete(run)
    assert receipt["status"] == "complete"
    assert receipt["cell_count"] == 2
    assert (run.directory / "complete.json").is_file()


@pytest.mark.parametrize("mutation, match", [
    (lambda s: s["experiments"]["example-a"].update(stage="confirmation"), "selection"),
    (lambda s: s["experiments"]["example-a"].update(reuse="fresh"), "exploratory"),
    (lambda s: s["experiments"]["example-a"].update(parent="example-a"), "ancestry"),
    (lambda s: s["families"]["family-a"].update(attempt_budget=0), "budget"),
    (lambda s: s["experiments"]["example-a"].update(outputs=["../escape.json"]), "output"),
])
def test_invalid_admission_metadata_is_rejected(registered, mutation, match):
    root, spec, _ = registered
    mutation(spec)
    source = commit(root, spec)
    _, admit, _ = api()
    with pytest.raises(ValueError, match=match):
        admit(root=root, registration="registration.json", experiment="example-a", source=source)
    assert not (root / "research_runs").exists()


def test_spent_window_cannot_be_renamed_fresh_confirmation(registered):
    root, spec, _ = registered
    experiment = spec["experiments"]["example-a"]
    experiment.update(stage="confirmation", reuse="fresh",
        selection={"path": "selection.txt", "sha256": hashlib.sha256((root / "selection.txt").read_bytes()).hexdigest()})
    source = commit(root, spec)
    _, admit, _ = api()
    with pytest.raises(ValueError, match="expos"):
        admit(root=root, registration="registration.json", experiment="example-a", source=source)


def test_registered_prospective_confirmation_waits_for_window_end(registered):
    root, spec, _ = registered
    experiment = spec["experiments"]["example-a"]
    experiment.update(stage="confirmation", reuse="fresh",
        selection={"path": "selection.txt", "sha256": hashlib.sha256((root / "selection.txt").read_bytes()).hexdigest()})
    experiment["windows"][0].update(start="2099-01-01T00:00:00Z", end="2099-02-01T00:00:00Z", availability="prospective")
    source = commit(root, spec)
    _, admit, _ = api()
    admitted = admit(root=root, registration="registration.json", experiment="example-a", source=source)
    assert admitted.ready is False
    with pytest.raises(ValueError, match="window.*complete"):
        start((root, spec, source))


def test_source_mismatch_rejected_before_input_access(registered):
    root, spec, source = registered
    (root / "engine.py").write_text("changed source")
    (root / "sample.json").unlink()
    with pytest.raises(ValueError, match="source"):
        start(registered)
    assert not (root / "research_runs").exists()


def test_registration_must_be_committed(registered):
    root, spec, _ = registered
    spec["experiments"]["example-a"]["question"] = "uncommitted change"
    (root / "registration.json").write_text(json.dumps(spec))
    with pytest.raises(ValueError, match="committed"):
        start(registered)


def test_charter_must_be_committed_and_pinned(registered):
    root, _, _ = registered
    (root / "charter.md").write_text("different outcomes/thresholds")
    with pytest.raises(ValueError, match="committed"):
        start(registered)


def test_confirmation_selection_cannot_change_after_design(prospective_bound):
    root, spec, source, design, binding = prospective_bound
    (root / "selection.txt").write_text("a post-result rule")
    git(root, "add", "selection.txt")
    git(root, "-c", "user.name=Synthetic", "-c", "user.email=synthetic@example.invalid", "commit", "-qm", "invalid synthetic selection")
    _, admit, _ = api()
    with pytest.raises(ValueError, match="source hash"):
        admit(root=root, registration="registration.json", experiment="example-a", source=git(root, "rev-parse", "HEAD"),
              design_source=design, bindings="bindings.json")


def test_input_hash_mismatch_leaves_failed_claim_and_never_returns_data(registered):
    root, _, _ = registered
    (root / "sample.json").write_text("corrupted")
    with pytest.raises(ValueError, match="input hash"):
        start(registered)
    folder = root / "research_runs" / "example-a"
    assert json.loads((folder / "failed.json").read_text())["status"] == "failed"
    with pytest.raises(ValueError, match="repeat"):
        start(registered)


def test_duplicate_and_concurrent_starts_have_one_owner(registered):
    def attempt():
        try:
            return start(registered)
        except ValueError as exc:
            return str(exc)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: attempt(), range(2)))
    assert sum(not isinstance(value, str) for value in results) == 1
    assert any("repeat" in value for value in results if isinstance(value, str))


def test_concurrent_completion_has_one_immutable_record(registered):
    run = start(registered)
    run.write_json("summary.json", {"sum": 5})
    cells = [{"id": x, "status": "complete"} for x in ("sum", "count")]
    def attempt():
        try:
            return run.finish(cells)
        except ValueError as exc:
            return str(exc)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: attempt(), range(2)))
    assert sum(isinstance(value, dict) for value in results) == 1
    assert not (run.directory / "failed.json").exists()
    assert json.loads((run.directory / "complete.json").read_text())["cell_count"] == 2


@pytest.mark.parametrize("cells", [[], [{"id": "sum", "status": "complete"}],
    [{"id": "sum", "status": "complete"}, {"id": "sum", "status": "complete"}],
    [{"id": "sum", "status": "complete"}, {"id": "count", "status": "missing"}]])
def test_denominator_or_status_loss_records_failure(registered, cells):
    run = start(registered)
    run.write_json("summary.json", {})
    with pytest.raises(ValueError, match="cells|status"):
        run.finish(cells)
    assert (run.directory / "failed.json").exists()
    assert not (run.directory / "complete.json").exists()


def test_unavailable_cases_count_and_unregistered_outputs_rejected(registered):
    run = start(registered)
    with pytest.raises(ValueError, match="unregistered output"):
        run.write_json("extra.json", {})
    run.write_json("summary.json", {})
    result = run.finish([{"id": "sum", "status": "complete"},
                         {"id": "count", "status": "unavailable", "reason": "synthetic gap"}])
    assert result["unavailable_count"] == 1
    with pytest.raises(ValueError, match="terminal"):
        run.write_json("summary.json", {})


def test_partial_exception_retains_output_and_failure_receipt(registered):
    with pytest.raises(RuntimeError, match="interrupted"):
        with start(registered) as run:
            run.write_json("summary.json", {"partial": True})
            raise RuntimeError("interrupted")
    assert json.loads((run.directory / "outputs/summary.json").read_text()) == {"partial": True}
    assert (run.directory / "failed.json").exists()
    with pytest.raises(ValueError, match="repeat"):
        start(registered)


def test_context_without_completion_is_failed(registered):
    with start(registered) as run:
        pass
    assert (run.directory / "failed.json").exists()


def test_changed_inputs_before_finish_cannot_produce_success(registered):
    root, _, _ = registered
    run = start(registered)
    run.write_json("summary.json", {})
    (root / "sample.json").write_text('[8]')
    with pytest.raises(ValueError, match="input hash"):
        run.finish([{"id": x, "status": "complete"} for x in ("sum", "count")])
    assert (run.directory / "failed.json").exists()


def add_child(root, spec, *, family="family-a", budget=None, experiment="example-b"):
    child = deepcopy(spec["experiments"]["example-a"])
    child.update(family=family, parent="example-a", question="follow-up synthetic")
    spec["experiments"][experiment] = child
    if budget is not None:
        spec["families"][family]["attempt_budget"] = budget
    return commit(root, spec)


def test_child_cannot_start_before_parent_terminal(registered):
    root, spec, _ = registered
    source = add_child(root, spec)
    with pytest.raises(ValueError, match="parent"):
        start((root, spec, source), "example-b")


def test_family_budget_cumulative_and_cannot_reset(registered):
    root, spec, _ = registered
    spec["families"]["family-a"]["attempt_budget"] = 1
    source = commit(root, spec)
    complete(start((root, spec, source)))
    source = add_child(root, spec)
    with pytest.raises(ValueError, match="budget"):
        start((root, spec, source), "example-b")
    spec["families"]["family-a"]["attempt_budget"] = 5
    source = commit(root, spec)
    with pytest.raises(ValueError, match="budget.*changed"):
        start((root, spec, source), "example-b")


def test_child_cannot_rewrite_parent_history(registered):
    root, spec, _ = registered
    complete(start(registered))
    source = add_child(root, spec)
    spec["experiments"]["example-a"]["question"] = "rewrite old outcome interpretation"
    source = commit(root, spec)
    with pytest.raises(ValueError, match="parent.*changed"):
        start((root, spec, source), "example-b")


def test_confirmation_cannot_reuse_prior_claim_via_dataset_alias(registered):
    root, spec, _ = registered
    complete(start(registered))
    source = add_child(root, spec)
    child = spec["experiments"]["example-b"]
    spec["datasets"]["alias"] = {"identity": "synthetic-sample-v1", "history_reference": "alias", "exposures": []}
    child["windows"][0]["dataset"] = "alias"
    child["inputs"]["sample"]["dataset"] = "alias"
    child.update(stage="confirmation", reuse="fresh", selection={"path": "selection.txt",
        "sha256": hashlib.sha256((root / "selection.txt").read_bytes()).hexdigest()})
    source = commit(root, spec)
    with pytest.raises(ValueError, match="expos"):
        start((root, spec, source), "example-b")


def test_successful_second_synthetic_example_uses_new_unseen_window(registered):
    root, spec, _ = registered
    complete(start(registered))
    source = add_child(root, spec)
    child = spec["experiments"]["example-b"]
    child.update(stage="confirmation", reuse="fresh", selection={"path": "selection.txt",
        "sha256": hashlib.sha256((root / "selection.txt").read_bytes()).hexdigest()})
    child["windows"][0].update(start="2002-01-01T00:00:00Z", end="2003-01-01T00:00:00Z")
    source = commit(root, spec)
    complete(start((root, spec, source), "example-b"))
    assert len(list((root / "research_runs").glob("*/complete.json"))) == 2


@pytest.fixture
def prospective_bound(registered):
    root, spec, _ = registered
    Run, admit, _ = api()
    exp = spec["experiments"]["example-a"]
    exp.update(stage="confirmation", reuse="fresh", selection={"path": "selection.txt",
        "sha256": hashlib.sha256((root / "selection.txt").read_bytes()).hexdigest()})
    exp["inputs"]["sample"]["sha256"] = None
    exp["windows"][0].update(start="2002-01-01T00:00:00Z", end="2003-01-01T00:00:00Z", availability="prospective")
    design = commit(root, spec)
    # Synthetic Git timestamps exercise design-before-window without waiting or
    # replacing the runtime clock. These are invented records, not evidence.
    subprocess.check_call(["git", "-c", "user.name=Synthetic", "-c", "user.email=synthetic@example.invalid",
        "commit", "--amend", "--no-edit", "--date=2001-01-01T00:00:00Z", "-q"], cwd=root,
        env={**os.environ, "GIT_COMMITTER_DATE": "2001-01-01T00:00:00Z"})
    design = git(root, "rev-parse", "HEAD")
    assert not admit(root=root, registration="registration.json", experiment="example-a", source=design).ready
    (root / "capture.json").write_text('{"synthetic":true}')
    binding = {"schema_version": 1, "design_commit": design, "experiment": "example-a",
        "registration_sha256": hashlib.sha256((root / "registration.json").read_bytes()).hexdigest(),
        "inputs": {"sample": {"sha256": hashlib.sha256((root / "sample.json").read_bytes()).hexdigest(),
            "capture_manifest": {"path": "capture.json", "sha256": hashlib.sha256((root / "capture.json").read_bytes()).hexdigest()}}}}
    (root / "bindings.json").write_text(json.dumps(binding))
    git(root, "add", "bindings.json", "capture.json")
    git(root, "-c", "user.name=Synthetic", "-c", "user.email=synthetic@example.invalid", "commit", "-qm", "synthetic binding")
    source = git(root, "rev-parse", "HEAD")
    return root, spec, source, design, binding


def test_prospective_design_can_bind_only_later_inputs(prospective_bound):
    root, spec, source, design, binding = prospective_bound
    Run, _, _ = api()
    with Run.start(root=root, registration="registration.json", experiment="example-a", source=source,
                  design_source=design, bindings="bindings.json") as run:
        complete(run)
    assert (run.directory / "complete.json").exists()


@pytest.mark.parametrize("change", ["threshold", "path", "extra_input"])
def test_binding_cannot_change_selection_paths_or_denominator(prospective_bound, change):
    root, spec, source, design, binding = prospective_bound
    if change == "threshold":
        binding["threshold"] = 0.2
    elif change == "path":
        binding["inputs"]["sample"]["path"] = "alternate.json"
    else:
        binding["inputs"]["other"] = deepcopy(binding["inputs"]["sample"])
    (root / "bindings.json").write_text(json.dumps(binding))
    git(root, "add", "bindings.json")
    git(root, "-c", "user.name=Synthetic", "-c", "user.email=synthetic@example.invalid", "commit", "-qm", "invalid synthetic binding")
    _, admit, _ = api()
    with pytest.raises(ValueError, match="bindings"):
        admit(root=root, registration="registration.json", experiment="example-a", source=git(root, "rev-parse", "HEAD"),
              design_source=design, bindings="bindings.json")


def test_prospective_freeze_cannot_be_replaced_at_execution(prospective_bound):
    root, spec, source, design, binding = prospective_bound
    spec["experiments"]["example-a"]["question"] = "selected after outcomes"
    source = commit(root, spec)
    _, admit, _ = api()
    with pytest.raises(ValueError, match="design registration changed"):
        admit(root=root, registration="registration.json", experiment="example-a", source=source,
              design_source=design, bindings="bindings.json")


def test_exhausted_unrelated_family_does_not_block_valid_family(registered):
    root, spec, _ = registered
    spec["families"]["other"] = {"mechanism_id": "other", "attempt_budget": 5,
        "prior_attempts": 5, "history_reference": "synthetic closed family"}
    source = commit(root, spec)
    assert start((root, spec, source))


def test_mutating_admitted_contract_cannot_add_output(registered):
    run = start(registered)
    run.admission.experiment["outputs"].append("sneaked.json")
    with pytest.raises(ValueError, match="contract changed"):
        run.write_json("sneaked.json", {})


def test_modifying_published_output_cannot_be_blessed_at_finish(registered):
    run = start(registered)
    run.write_json("summary.json", {"original": 1})
    (run.directory / "outputs" / "summary.json").write_text('{"different":2}')
    with pytest.raises(ValueError, match="output.*changed"):
        run.finish([{"id": x, "status": "complete"} for x in ("sum", "count")])

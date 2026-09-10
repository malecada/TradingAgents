"""Two disposable synthetic runs demonstrating plumbing, never a strategy test."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from .admission import runtime_hashes
from .lifecycle import ResearchRun
from .verify import verify_run


def examples():
    reports = []
    with TemporaryDirectory(prefix="research-synthetic-") as temporary:
        root = Path(temporary)
        def git(*args):
            return subprocess.check_output(["git", *args], cwd=root, stderr=subprocess.PIPE, text=True).strip()
        def sha(name):
            return hashlib.sha256((root / name).read_bytes()).hexdigest()
        git("init", "-q")
        (root / "runner.py").write_text("# Frozen synthetic sum/count example; no market data.\n")
        (root / "selection.txt").write_text("Fixed toy threshold: sum greater than zero; no investment claim.\n")
        (root / "charter.md").write_text("Synthetic sum/count with fixed cells and no financial interpretation.\n")
        (root / "sample.json").write_text("[2, 3]")
        spec = {"schema_version": 1, "program_id": "synthetic-only",
            "families": {"toy": {"mechanism_id": "invented-toy-arithmetic", "attempt_budget": 2,
                "prior_attempts": 0, "history_reference": "Invented example; no market history."}},
            "datasets": {"toy": {"identity": "invented-toy-sample", "history_reference": "Invented clocks, not real data.",
                "exposures": [{"start": "2000-01-01T00:00:00Z", "end": "2001-01-01T00:00:00Z", "state": "spent"}]}},
            "experiments": {"toy-development": {"family": "toy", "parent": None, "question": "Sum two invented scalars",
                "charter": {"path": "charter.md", "sha256": sha("charter.md")},
                "stage": "development", "reuse": "exploratory", "selection": None,
                "source_files": {"runner.py": sha("runner.py")}, "runtime_hashes": runtime_hashes(),
                "windows": [{"dataset": "toy", "start": "2000-01-01T00:00:00Z", "end": "2001-01-01T00:00:00Z", "availability": "existing"}],
                "inputs": {"sample": {"path": "sample.json", "sha256": sha("sample.json"), "dataset": "toy"}},
                "cells": ["sum", "count"], "outputs": ["summary.json"]}}}
        child = deepcopy(spec["experiments"]["toy-development"])
        child.update(parent="toy-development", stage="confirmation", reuse="fresh",
                     selection={"path": "selection.txt", "sha256": sha("selection.txt")})
        child["windows"][0].update(start="2002-01-01T00:00:00Z", end="2003-01-01T00:00:00Z")
        spec["experiments"]["toy-confirmation"] = child
        (root / "gates.json").write_text(json.dumps(spec, indent=2))
        git("add", "gates.json", "runner.py", "selection.txt", "charter.md")
        git("-c", "user.name=Synthetic", "-c", "user.email=synthetic@example.invalid", "commit", "-qm", "synthetic-only registration")
        source = git("rev-parse", "HEAD")
        for name in ("toy-development", "toy-confirmation"):
            with ResearchRun.start(root=root, registration="gates.json", experiment=name, source=source) as run:
                values = json.loads(run.read_input("sample"))
                result = {"sum": sum(values), "count": len(values)}
                run.write_json("summary.json", {"synthetic_only": True, **result})
                run.finish([{"id": key, "status": "complete", "value": value} for key, value in result.items()])
            reports.append(verify_run(run.directory))
    return {"synthetic_only": True, "temporary_repositories_removed": True, "runs": reports}

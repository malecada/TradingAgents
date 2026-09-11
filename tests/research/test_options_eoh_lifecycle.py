"""Invented EOH lexical objects in disposable guarded ResearchRun repositories."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys

import pytest

DIRECTORY = Path(__file__).resolve().parents[2] / "research/strategy-search-2026-09-11"
FROZEN_DEPENDENCIES = {
    "options_metadata.py": "d95c6a68edf987db3112d01e6aa74883488f02077970681fa2c7a1154e02c48f",
    "carry_capture.py": "323ea01ac0d8137288e6f72f697101db1884595e876622402c321f38367d6b12",
}


DRIVER = r'''
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile
import options_eoh_schema as collector
from tradingagents.research import ResearchRun, runtime_hashes

root = Path(__file__).resolve().parent
mode = sys.argv[1]
assert len(os.sched_getaffinity(0)) <= 2
spec = json.loads((root / "options-eoh-request-spec.json").read_text())
def git(*args):
    return subprocess.check_output(["git", "-c", "core.hooksPath=/dev/null", *args], cwd=root, text=True).strip()
def sha(name):
    return hashlib.sha256((root / name).read_bytes()).hexdigest()
git("init", "-q")
(root / "charter.md").write_text("Synthetic lexical resource fixture only; no market observations or field meaning.")
ids = [request["id"] for request in spec["requests"]]
source_names = ("driver.py", "options_eoh_schema.py", "options_metadata.py", "carry_capture.py")
registration = {
 "schema_version":1, "program_id":"synthetic-eoh-resource",
 "families":{"synthetic":{"mechanism_id":"synthetic-eoh-lexical-only","attempt_budget":1,"prior_attempts":0,"history_reference":"invented test"}},
 "datasets":{"synthetic":{"identity":"invented-eoh-inputs","history_reference":"invented test","exposures":[{"start":"2000-01-01T00:00:00Z","end":"2001-01-01T00:00:00Z","state":"spent"}]}},
 "experiments":{"synthetic-eoh":{"family":"synthetic","parent":None,"charter":{"path":"charter.md","sha256":sha("charter.md")},
  "question":"Synthetic lexical source lifecycle and resource admission", "stage":"development","reuse":"exploratory",
  "windows":[{"dataset":"synthetic","start":"2000-01-01T00:00:00Z","end":"2001-01-01T00:00:00Z","availability":"existing"}],
  "inputs":{"request_spec":{"path":"options-eoh-request-spec.json","sha256":sha("options-eoh-request-spec.json"),"dataset":"synthetic"}},
  "source_files":{name:sha(name) for name in source_names},"runtime_hashes":runtime_hashes(),"selection":None,"cells":ids,"outputs":spec["outputs"]}}}
(root / "registration.json").write_text(json.dumps(registration))
git("add", *source_names, "charter.md", "registration.json", "options-eoh-request-spec.json")
git("-c", "user.name=Synthetic", "-c", "user.email=synthetic@example.invalid", "commit", "-qm", "synthetic EOH lifecycle")
source = git("rev-parse", "HEAD")

if mode == "valid_large_header":
    # A field exactly at the fixed lexical limit; no semantic labels or values.
    field_size = spec["max_csv_field_characters"]
    content = b"H" * field_size + b"\n" + b"V" * field_size + b"\n"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as zipped:
        zipped.writestr(spec["expected_member"], content)
    zip_bytes = buffer.getvalue()
    checksum = (hashlib.sha256(zip_bytes).hexdigest() + "  " + spec["requests"][0]["filename"] + "\n").encode()
    bodies = [zip_bytes, checksum]
else:
    assert mode == "invalid_max_raw"
    # Two complete maximum-size bodies; checksum/schema unavailability is kept.
    bodies = [b"x" * spec["max_response_bytes"], b"y" * spec["max_response_bytes"]]
calls = []
def fake(url):
    raw = bodies[len(calls)]
    calls.append(url)
    return {"body":raw,"http_status":200,"headers":{},"body_complete":True,"error":None}

with ResearchRun.start(root=root, registration="registration.json", experiment="synthetic-eoh", source=source) as run:
    raw, schema, cells = collector.capture(json.loads(run.read_input("request_spec")), fake, run.write_json)
    run.write_json("eoh-capture.json", raw)
    run.write_json("eoh-schema.json", schema)
    run.finish(cells)
output_dir = root / "research_runs/synthetic-eoh/outputs"
actual_bytes = sum((output_dir / name).stat().st_size for name in spec["outputs"])
assert len(calls) == len(cells) == 2
assert len(spec["outputs"]) == 4
assert actual_bytes <= 64 * 1024**2
assert len(list(output_dir.iterdir())) == 4
if mode == "valid_large_header":
    assert all(cell["status"] == "complete" for cell in cells)
    lexical = schema["lexical_schema"]
    assert len(lexical["candidate_header"]) == 1
    assert len(lexical["candidate_header"][0]) == field_size
    assert lexical["total_records_including_first"] == 2
    assert lexical["field_semantics"].startswith("unavailable")
    assert schema["paired_integrity"]["status"] == "complete"
else:
    assert all(cell["status"] == "unavailable" for cell in cells)
    assert raw["total_body_bytes"] == 10 * 1024**2
    assert schema["lexical_schema"]["status"] == "unavailable"
(root / "synthetic-result.json").write_text(json.dumps({
    "mode":mode,"actual_four_output_bytes":actual_bytes,"raw_body_bytes":raw["total_body_bytes"],
    "cells":len(cells),"statuses":[cell["status"] for cell in cells],"cpu_count":len(os.sched_getaffinity(0)),
    "source_sha256":{name:sha(name) for name in source_names}}))
'''


@pytest.mark.parametrize("mode", ["valid_large_header", "invalid_max_raw"])
def test_full_eoh_lexical_lifecycle_under_resource_guard(tmp_path, mode):
    guard_spec = importlib.util.spec_from_file_location("eoh_lifecycle_guard", DIRECTORY / "resource_guard_v2.py")
    guard = importlib.util.module_from_spec(guard_spec)
    guard_spec.loader.exec_module(guard)
    for name, digest in FROZEN_DEPENDENCIES.items():
        assert hashlib.sha256((DIRECTORY / name).read_bytes()).hexdigest() == digest
    for name in ("options_eoh_schema.py", "options_metadata.py", "carry_capture.py", "options-eoh-request-spec.json"):
        shutil.copyfile(DIRECTORY / name, tmp_path / name)
    (tmp_path / "driver.py").write_text(DRIVER)
    report = guard.run_guard([sys.executable, "-B", str(tmp_path / "driver.py"), mode])
    (tmp_path / "guard-report.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    assert report["child_exit_code"] == 0 and report["limit_reason"] is None, report
    assert report["rss_limit_bytes"] == 512 * 1024**2 and report["wall_limit_seconds"] == 120
    saved = json.loads((tmp_path / "synthetic-result.json").read_text())
    assert saved["actual_four_output_bytes"] <= 64 * 1024**2
    assert saved["cells"] == 2 and saved["cpu_count"] <= 2
    assert report["peak_sampled_tree_rss_bytes"] <= 512 * 1024**2

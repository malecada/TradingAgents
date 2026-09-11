"""Disposable synthetic Git/run subprocesses under the actual options guard."""
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import types

import pytest

DIRECTORY = Path(__file__).resolve().parents[2] / "research/strategy-search-2026-09-11"
spec = importlib.util.spec_from_file_location("options_resource_launcher", DIRECTORY / "options_resource_launcher.py")
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


def test_report_is_exclusive_and_guard_limits_are_exact(monkeypatch, tmp_path):
    calls = []
    def guarded(command, **kwargs):
        calls.append((command, kwargs))
        return {"child_exit_code": 0, "limit_reason": None}
    monkeypatch.setitem(sys.modules, "resource_guard_v2", types.SimpleNamespace(run_guard=guarded))
    report = tmp_path / "report.json"
    launcher.launch(["synthetic"], report)
    assert calls == [(["synthetic"], {"rss_limit_bytes": 256 * 1024**2, "wall_seconds": 120})]
    with pytest.raises(FileExistsError):
        launcher.launch(["synthetic"], report)
    assert len(calls) == 1


def test_guard_failure_has_structured_exclusive_report(monkeypatch, tmp_path):
    def fail(*args, **kwargs):
        raise RuntimeError("invented guard failure")
    monkeypatch.setitem(sys.modules, "resource_guard_v2", types.SimpleNamespace(run_guard=fail))
    result = launcher.launch(["synthetic"], tmp_path / "report.json")
    assert result["child_exit_code"] is None
    assert "invented guard failure" in result["limit_reason"]
    assert result["retry"] is False


DRIVER = r'''
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import options_metadata as collector
from tradingagents.research import ResearchRun, runtime_hashes

root = Path(__file__).resolve().parent
collector.enforce_one_cpu()
assert len(os.sched_getaffinity(0)) == 1
spec = json.loads((root / "options-request-spec.json").read_text())
def git(*args):
    return subprocess.check_output(["git", "-c", "core.hooksPath=/dev/null", *args], cwd=root, text=True).strip()
def sha(name):
    return hashlib.sha256((root / name).read_bytes()).hexdigest()
git("init", "-q")
(root / "charter.md").write_text("Synthetic metadata resource test; invented responses only. No market observation.\n")
ids = [request["id"] for request in spec["requests"]]
outputs = [name + "-receipt.json" for name in ids] + ["metadata-capture.json", "metadata-admission.json"]
registration = {"schema_version":1,"program_id":"synthetic-options-resource",
 "families":{"synthetic":{"mechanism_id":"synthetic-options-resource-only","attempt_budget":1,"prior_attempts":0,"history_reference":"invented test"}},
 "datasets":{"synthetic":{"identity":"invented-options-inputs","history_reference":"invented test","exposures":[{"start":"2000-01-01T00:00:00Z","end":"2001-01-01T00:00:00Z","state":"spent"}]}},
 "experiments":{"synthetic-options-resource":{"family":"synthetic","parent":None,"charter":{"path":"charter.md","sha256":sha("charter.md")},
  "question":"Synthetic response retention under fixed resources", "stage":"development","reuse":"exploratory",
  "windows":[{"dataset":"synthetic","start":"2000-01-01T00:00:00Z","end":"2001-01-01T00:00:00Z","availability":"existing"}],
  "inputs":{"request_spec":{"path":"options-request-spec.json","sha256":sha("options-request-spec.json"),"dataset":"synthetic"}},
  "source_files":{name:sha(name) for name in ("driver.py","options_metadata.py","carry_capture.py")},
  "runtime_hashes":runtime_hashes(),"selection":None,"cells":ids,"outputs":outputs}}}
(root / "registration.json").write_text(json.dumps(registration))
git("add", "driver.py", "options_metadata.py", "carry_capture.py", "options-request-spec.json", "charter.md", "registration.json")
git("-c","user.name=Synthetic","-c","user.email=synthetic@example.invalid","commit","-qm","synthetic resource fixture")
source = git("rev-parse","HEAD")
calls = []
def fake(url):
    request = spec["requests"][len(calls)]
    calls.append(url)
    if request["kind"] == "exchange-info":
        rows = [{"symbol":"INVENTED"+str(i),"underlying":"BTCUSDT","unit":"1","minQty":"0.01","maxQty":"10",
                 "filters":[{"filterType":"LOT_SIZE","minQty":"0.01","maxQty":"10","stepSize":"0.01"}]} for i in range(10000)]
        raw = json.dumps({"optionSymbols":rows}).encode()
    elif request["kind"] == "server-time":
        raw = b'{"serverTime":1800000000000}'
    else:
        raw = ('<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><Prefix>data/option/daily/</Prefix><MaxKeys>'+str(request["max_keys"])+
               '</MaxKeys>'+('<Delimiter>/</Delimiter>' if "delimiter" in request else '')+'<IsTruncated>false</IsTruncated></ListBucketResult>').encode()
    assert len(raw) < spec["max_response_bytes"]
    raw += b' ' * (spec["max_response_bytes"] - len(raw))
    return {"body":raw,"http_status":200,"headers":{},"body_complete":True,"error":None}

with ResearchRun.start(root=root, registration="registration.json", experiment="synthetic-options-resource", source=source) as run:
    raw, admission, cells = collector.capture(json.loads(run.read_input("request_spec")),fake,run.write_json)
    run.write_json("metadata-capture.json",raw)
    run.write_json("metadata-admission.json",admission)
    run.finish(cells)
directory = root / "research_runs/synthetic-options-resource/outputs"
actual = sum((directory / name).stat().st_size for name in outputs)
assert len(calls) == len(cells) == 4
assert raw["total_body_bytes"] == 20 * 1024**2
assert actual <= 80 * 1024**2
assert cells[0]["status"] == "unavailable" and "resource allowance" in cells[0]["reason"]
assert all(cell["status"] == "complete" for cell in cells[1:])
(root / "synthetic-result.json").write_text(json.dumps({"actual_six_output_bytes":actual,"raw_body_bytes":raw["total_body_bytes"],"cells":len(cells),"cpu_count":len(os.sched_getaffinity(0))}))
'''


def test_full_padded_synthetic_lifecycle_under_exact_guard(monkeypatch, tmp_path):
    guard_spec = importlib.util.spec_from_file_location("resource_guard_v2", DIRECTORY / "resource_guard_v2.py")
    guard = importlib.util.module_from_spec(guard_spec)
    guard_spec.loader.exec_module(guard)
    monkeypatch.setitem(sys.modules, "resource_guard_v2", guard)
    for name in ("options_metadata.py", "carry_capture.py", "options-request-spec.json"):
        shutil.copyfile(DIRECTORY / name, tmp_path / name)
    (tmp_path / "driver.py").write_text(DRIVER)
    result = launcher.launch([sys.executable, "-B", str(tmp_path / "driver.py")], tmp_path / "guard-report.json")
    assert result["child_exit_code"] == 0, result
    assert result["limit_reason"] is None, result
    saved = json.loads((tmp_path / "synthetic-result.json").read_text())
    assert saved["actual_six_output_bytes"] <= 80 * 1024**2
    assert saved["raw_body_bytes"] == 20 * 1024**2
    assert saved["cells"] == 4 and saved["cpu_count"] == 1
    assert result["peak_sampled_tree_rss_bytes"] <= 256 * 1024**2

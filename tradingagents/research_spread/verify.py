"""Independent structural receipt verification; no admission/numerical imports.

This proves retained-byte/count consistency only. It does not verify data
chronology, economic correctness, statistical claims or completeness of history.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess


def _blob(root, commit, path):
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("saved provenance requires a full SHA-1 commit identity")
    raw = Path(path)
    if (raw.is_absolute() or ".." in raw.parts
            or any(part in {"keys", "apis", ".env", "hf_token.txt"} or part.startswith(".env.") for part in raw.parts)):
        raise ValueError("untrusted or secret committed path")
    try:
        return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=root, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as exc:
        raise ValueError("saved committed provenance cannot be verified") from exc


def verify_claim(directory) -> dict:
    """Bind claim fields to committed design without admission or input reads."""
    directory = Path(directory).resolve()
    raw = (directory / "claim.json").read_bytes()
    claim = json.loads(raw)
    if claim["experiment_id"] != directory.name or directory.parent.name != "research_runs":
        raise ValueError("claim directory identity mismatch")
    root = directory.parent.parent
    registration = _blob(root, claim["source"], claim["registration"])
    if hashlib.sha256(registration).hexdigest() != claim["registration_sha256"]:
        raise ValueError("registration hash differs from committed source")
    registered = json.loads(registration)
    if claim["program_id"] != registered["program_id"]:
        raise ValueError("claim program differs from committed registration")
    if _blob(root, claim["design_source"], claim["registration"]) != registration:
        raise ValueError("claim design registration differs from execution registration")
    exp = registered["experiments"][claim["experiment_id"]]
    if exp != claim["experiment"] or registered["families"][exp["family"]] != claim["family"]:
        raise ValueError("claim contract differs from committed registration")
    windows = [{**w, "identity": registered["datasets"][w["dataset"]]["identity"],
                "state": "spent" if exp["stage"] == "confirmation" else "exposed"} for w in exp["windows"]]
    exposures = [{**item, "identity": info["identity"]} for info in registered["datasets"].values()
                 for item in info["exposures"]]
    if claim["windows"] != windows or claim["prior_exposures"] != exposures:
        raise ValueError("claim exposure windows differ from committed registration")
    pinned = dict(exp["source_files"])
    for key in ("charter", "selection"):
        if exp.get(key):
            pinned[exp[key]["path"]] = exp[key]["sha256"]
    for path, expected in pinned.items():
        for commit in {claim["source"], claim["design_source"]}:
            if hashlib.sha256(_blob(root, commit, path)).hexdigest() != expected:
                raise ValueError("registered source/charter/selection hash mismatch")
    inputs = {name: dict(item) for name, item in exp["inputs"].items()}
    pending = {name for name, item in inputs.items() if item["sha256"] is None}
    if claim["bindings"] is not None:
        raw_binding = _blob(root, claim["source"], claim["bindings"])
        if hashlib.sha256(raw_binding).hexdigest() != claim["bindings_sha256"]:
            raise ValueError("binding hash mismatch")
        binding = json.loads(raw_binding)
        if (set(binding) != {"schema_version", "design_commit", "experiment", "registration_sha256", "inputs"}
                or binding["schema_version"] != 1 or binding["design_commit"] != claim["design_source"]
                or binding["experiment"] != claim["experiment_id"]
                or binding["registration_sha256"] != claim["registration_sha256"]
                or set(binding["inputs"]) != pending):
            raise ValueError("binding identity/denominator mismatch")
        for name, bound in binding["inputs"].items():
            if set(bound) != {"sha256", "capture_manifest"}:
                raise ValueError("binding has extra selection/configuration fields")
            capture = bound["capture_manifest"]
            if set(capture) != {"path", "sha256"}:
                raise ValueError("capture manifest binding differs")
            if hashlib.sha256(_blob(root, claim["source"], capture["path"])).hexdigest() != capture["sha256"]:
                raise ValueError("capture manifest hash mismatch")
            inputs[name]["sha256"] = bound["sha256"]
    elif pending or claim["bindings_sha256"] is not None:
        raise ValueError("claim has unbound input hashes")
    if claim["inputs"] != inputs:
        raise ValueError("claim input identities/hashes differ from committed bindings")
    from tradingagents.research_extended.verify_v1_snapshot import check as check_v1
    from .verify_v2_snapshot import check as check_v2
    from .verify_grant import check
    check_v1(directory, claim, registered, _blob)
    check_v2(directory, claim, registered, _blob)
    check(directory, claim, registered, _blob)
    return claim


def verify_run(directory) -> dict:
    directory = Path(directory).resolve()
    claim = verify_claim(directory)
    exp = claim["experiment"]
    raw = (directory / "claim.json").read_bytes()
    terminal = [p for p in (directory / "complete.json", directory / "failed.json") if p.exists()]
    if len(terminal) != 1:
        raise ValueError("run has no unique terminal receipt; partial claim is not a completion")
    receipt = json.loads(terminal[0].read_text())
    status = "complete" if terminal[0].name == "complete.json" else "failed"
    if receipt["status"] != status or receipt["experiment_id"] != claim["experiment_id"]:
        raise ValueError("terminal identity/status mismatch")
    if receipt["claim_sha256"] != hashlib.sha256(raw).hexdigest():
        raise ValueError("claim hash mismatch")
    outputs = list((directory / "outputs").iterdir())
    if any(not p.is_file() or p.is_symlink() for p in outputs):
        raise ValueError("unexpected output type")
    expected_outputs = receipt["output_sha256"]
    if {p.name for p in outputs} != set(expected_outputs):
        raise ValueError("output denominator mismatch")
    for path in outputs:
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected_outputs[path.name]:
            raise ValueError("output hash mismatch: " + path.name)
    count, unavailable = 0, 0
    if status == "complete":
        if receipt["source"] != claim["source"] or receipt["registration_sha256"] != claim["registration_sha256"]:
            raise ValueError("completion provenance mismatch")
        if set(expected_outputs) != set(exp["outputs"]):
            raise ValueError("registered output denominator mismatch")
        ids = [cell["id"] for cell in receipt["cells"]]
        if len(ids) != len(set(ids)) or set(ids) != set(exp["cells"]):
            raise ValueError("registered cell denominator mismatch")
        for cell in receipt["cells"]:
            if cell["status"] not in {"complete", "unavailable"}:
                raise ValueError("invalid cell status")
            if cell["status"] == "unavailable":
                unavailable += 1
                if not cell.get("reason"):
                    raise ValueError("missing unavailable reason")
        count = len(ids)
        if count != receipt["cell_count"] or unavailable != receipt["unavailable_count"]:
            raise ValueError("saved counts differ from retained cells")
    return {"experiment": claim["experiment_id"], "status": status, "cell_count": count,
            "unavailable_count": unavailable, "output_count": len(outputs),
            "verification": "structural hashes and denominators; v1/v2 certificates at their closed inventories, book grant against complete live inventory; no scientific validation"}

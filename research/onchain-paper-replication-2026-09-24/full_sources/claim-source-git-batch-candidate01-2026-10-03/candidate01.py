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


# Fresh per-claim source transport. No admission or numerical dependency.
_GIT_PARTS = 128
_GIT_BODY = 8 * 1024**2
_GIT_REQUEST = 65536
_GIT_SECONDS = 10

class _GitCleanupFailure(BaseException):
    """Git ownership could not be conclusively released; stop verification."""

def _git_fatal(error):
    return (isinstance(error, MemoryError) or not isinstance(error, Exception)) and not isinstance(error, _GitCleanupFailure)

def _git_cleanup(actions, primary):
    # First true fatal wins; all acquired resources get exactly one close call.
    selected = primary
    uncertain = False
    for action in actions:
        try:
            action()
        except BaseException as error:
            fatal = _git_fatal(error)
            already = selected is not None and _git_fatal(selected)
            if fatal and not already:
                selected = error
            uncertain = True
    if selected is not None and _git_fatal(selected):
        if selected is not primary:
            raise selected
        return
    if uncertain:
        raise _GitCleanupFailure('Git cleanup uncertain')


def _git_transport(root, requests, expression=None):
    """Finite fresh child, bounded stdout/stderr; no shell, no network fetch."""
    import os
    import selectors
    import sys
    import time
    if type(requests) is not bytes or len(requests) > _GIT_REQUEST:
        raise ValueError('Git request ceiling exceeded')
    if expression is not None and len(os.fsencode(expression)) > 131072:
        raise ValueError('Git argv expression ceiling exceeded')
    command = ['git', 'cat-file', '--batch'] if expression is None else ['git', 'cat-file', 'blob', expression]
    process = selector = None
    stdin_closed = False
    output = bytearray()
    errors = bytearray()
    sent = 0
    deadline = time.monotonic() + _GIT_SECONDS
    def stop():
        if process is not None and process.poll() is None:
            process.kill()
    def reap():
        if process is not None:
            process.wait(timeout=5)
    def close_input():
        nonlocal stdin_closed
        if process is not None and not stdin_closed:
            stdin_closed = True
            process.stdin.close()
    try:
        process = subprocess.Popen(command, cwd=root, env={**os.environ, 'GIT_NO_LAZY_FETCH':'1'},
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
        selector = selectors.DefaultSelector()
        for stream, label, event in ((process.stdin,'input',selectors.EVENT_WRITE),
                (process.stdout,'output',selectors.EVENT_READ),(process.stderr,'error',selectors.EVENT_READ)):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream,event,label)
        while selector.get_map():
            left = deadline - time.monotonic()
            if left <= 0:
                raise subprocess.TimeoutExpired(command, _GIT_SECONDS)
            for key, _ in selector.select(min(left, .25)):
                stream = key.fileobj
                if key.data == 'input':
                    if sent < len(requests):
                        try:
                            n = os.write(stream.fileno(),requests[sent:sent+4096])
                        except BlockingIOError:
                            continue
                        if n <= 0:
                            raise ValueError('Git input closed')
                        sent += n
                    if sent == len(requests):
                        selector.unregister(stream)
                        close_input()
                else:
                    try:
                        part = os.read(stream.fileno(),65536)
                    except BlockingIOError:
                        continue
                    if not part:
                        selector.unregister(stream)
                        continue
                    target = output if key.data == 'output' else errors
                    limit = _GIT_BODY + 128 * _GIT_PARTS if key.data == 'output' else 65536
                    if len(target) + len(part) > limit:
                        raise ValueError('Git aggregate output ceiling exceeded')
                    target.extend(part)
        left = deadline - time.monotonic()
        if left <= 0:
            raise subprocess.TimeoutExpired(command, _GIT_SECONDS)
        if process.wait(timeout=left) != 0 or sent != len(requests):
            raise ValueError('saved committed provenance cannot be verified')
        return bytes(output)
    finally:
        _git_cleanup((stop, reap, close_input,
            lambda: process.stdout.close() if process is not None else None,
            lambda: process.stderr.close() if process is not None else None,
            lambda: selector.close() if selector is not None else None), sys.exception())


def _verify_batch(raw, rows):
    offset = 0
    for path, commit, expected in rows:
        end = raw.find(b'\n', offset, offset+128)
        if end < 0:
            raise ValueError('Git batch header missing or oversized')
        fields = raw[offset:end].split(b' ')
        if (len(fields) != 3 or re.fullmatch(rb'[0-9a-f]{40}',fields[0]) is None
                or fields[1] != b'blob' or re.fullmatch(rb'0|[1-9][0-9]*',fields[2]) is None):
            raise ValueError('Git batch object missing, malformed or non-blob')
        size = int(fields[2])
        if size > _GIT_BODY:
            raise ValueError('Git blob body ceiling exceeded')
        offset = end+1
        if offset+size >= len(raw) or raw[offset+size:offset+size+1] != b'\n':
            raise ValueError('Git batch short body or terminator')
        if hashlib.sha256(memoryview(raw)[offset:offset+size]).hexdigest() != expected:
            raise ValueError('registered source/charter/selection hash mismatch')
        offset += size+1
    if offset != len(raw):
        raise ValueError('Git batch trailing response')


def _source_request(commit, path):
    # Identical original _blob validation; path text is not normalized.
    import os
    if not isinstance(commit, str) or not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('saved provenance requires a full SHA-1 commit identity')
    raw = Path(path)
    if (raw.is_absolute() or '..' in raw.parts
            or any(part in {'keys', 'apis', '.env', 'hf_token.txt'} or part.startswith('.env.') for part in raw.parts)):
        raise ValueError('untrusted or secret committed path')
    expression = f'{commit}:{path}'
    encoded = os.fsencode(expression)
    if b'\0' in encoded:
        raise ValueError('embedded null byte')
    # Git 2.34 has no NUL batch framing. Valid LF/CR/non-UTF8 names
    # use argv and an independently bounded blob child, never line splitting.
    if b'\n' in encoded or b'\r' in encoded or len(encoded)+1 > _GIT_REQUEST:
        return expression, None
    return expression, encoded+b'\n'


def _verify_sources(root, pinned, commits):
    rows = []
    requests = bytearray()
    def flush():
        if rows:
            _verify_batch(_git_transport(root,bytes(requests)), rows)
            rows.clear()
            requests.clear()
    for path, expected in pinned.items():
        for commit in commits:
            try:
                expression, request = _source_request(commit,path)
            except BaseException:
                # Preserve comparison order: earlier hash errors still precede
                # this path's ordinary validation failure. Fatal is not delayed.
                import sys
                error = sys.exception()
                if isinstance(error, Exception) and not isinstance(error, MemoryError):
                    flush()
                raise
            if request is None:
                flush()
                raw = _git_transport(root,b'',expression)
                if len(raw)>_GIT_BODY:
                    raise ValueError('Git blob body ceiling exceeded')
                if hashlib.sha256(raw).hexdigest()!=expected:
                    raise ValueError('registered source/charter/selection hash mismatch')
            else:
                if len(rows)==_GIT_PARTS or len(requests)+len(request)>_GIT_REQUEST:
                    flush()
                rows.append((path,commit,expected))
                requests.extend(request)
    flush()


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
    # Independently check the saved ceiling, without importing admission logic.
    ceiling = claim["family"]["attempt_budget"]
    if exp.get("cumulative_budget_extension") is not None:
        reference = exp["cumulative_budget_extension"]
        bodies = {}
        for kind in ("extension", "review"):
            ref = reference[kind]
            body = _blob(root, claim["source"], ref["path"])
            if (hashlib.sha256(body).hexdigest() != ref["sha256"]
                    or exp["source_files"].get(ref["path"]) != ref["sha256"]):
                raise ValueError("saved budget extension metadata differs")
            bodies[kind] = json.loads(body)
        extension, review = bodies["extension"], bodies["review"]
        if (extension["base_family"] != claim["family"] or extension["program_id"] != claim["program_id"]
                or type(extension["cumulative_ceiling"]) is not int or extension["cumulative_ceiling"] <= ceiling
                or review["decision"] != "accepted" or review["extension_sha256"] != reference["extension"]["sha256"]):
            raise ValueError("saved budget extension/review ceiling differs")
        allocation = extension["allocation"]
        if exp["source_files"].get(allocation["path"]) != allocation["sha256"]:
            raise ValueError("saved budget allocation is not pinned")
        ceiling = extension["cumulative_ceiling"]
    if type(claim.get("effective_attempt_budget", ceiling)) is not int or claim.get("effective_attempt_budget", claim["family"]["attempt_budget"]) != ceiling:
        raise ValueError("saved effective budget ceiling differs")
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
    _verify_sources(root, pinned, {claim["source"], claim["design_source"]})
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
            "verification": "structural hashes and denominators only; no scientific validation"}

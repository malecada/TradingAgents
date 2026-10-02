"""Admission metadata for new programs; historical registries remain untouched.

The declared sample identities/history require independent review. This helper
cannot detect a covertly renamed mechanism or data inspected outside its API.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def runtime_hashes() -> dict[str, str]:
    """Pin this additive helper independently of the experiment runner."""
    return {p.name: digest(p.read_bytes()) for p in sorted(Path(__file__).parent.glob("*.py"))}


def utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError("explicit UTC timestamp required")
    return parsed


def identity(value, label):
    if not isinstance(value, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}", value):
        raise ValueError(f"invalid {label} identity")
    return value


def local_path(root: Path, value: str) -> Path:
    path = root / value
    forbidden = {"keys", "apis", ".env", "hf_token.txt"}
    if any(part in forbidden or part.startswith(".env.") for part in Path(value).parts):
        raise ValueError("secret paths cannot be registered inputs or source")
    if Path(value).is_absolute() or not path.resolve().is_relative_to(root) or ".." in Path(value).parts:
        raise ValueError("registered path must stay inside the checkout")
    if any(part in forbidden or part.startswith(".env.") for part in path.resolve().relative_to(root).parts):
        raise ValueError("registered symlink resolves to a secret path")
    return path


def _git(root, *args) -> bytes:
    try:
        return subprocess.check_output(["git", *args], cwd=root, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as exc:
        raise ValueError("committed source/registration cannot be verified") from exc


def _committed(root, source, name, expected=None):
    path = local_path(root, name)
    recorded = _git(root, "show", f"{source}:{Path(name).as_posix()}")
    if path.read_bytes() != recorded:
        raise ValueError(f"committed source differs: {name}")
    if expected is not None and digest(recorded) != expected:
        raise ValueError(f"registered source hash differs: {name}")
    return recorded


_SOURCE_BATCH_FILES = 128
_SOURCE_BATCH_BYTES = 8 * 1024 * 1024


def _source_git_batch(root, requests, *, bodies=False):
    """One finite, reaped process; no state survives an admission call."""
    try:
        return subprocess.run(
            ["git", "cat-file", "--batch" if bodies else "--batch-check"],
            cwd=root, input=b"\n".join(requests) + b"\n",
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError("committed source/registration cannot be verified") from exc


def _source_batch_parse(raw, count, *, extents=None):
    """Parse headers separately from binary extents, rejecting extra responses."""
    result = []
    offset = 0
    for index in range(count):
        end = raw.find(b"\n", offset)
        header = raw[offset:end] if end >= 0 else b""
        match = re.fullmatch(rb"([0-9a-f]{40}|[0-9a-f]{64}) blob (0|[1-9][0-9]*)", header)
        if match is None:
            raise ValueError("committed source/registration cannot be verified")
        oid, size = match[1], int(match[2])
        offset = end + 1
        if extents is None:
            result.append((oid, size))
        else:
            if (oid, size) != extents[index] or raw[offset + size:offset + size + 1] != b"\n":
                raise ValueError("committed source/registration cannot be verified")
            result.append(raw[offset:offset + size])
            offset += size + 1
    if offset != len(raw):
        raise ValueError("committed source/registration cannot be verified")
    return result


def _source_files(root, source, design_source, files):
    """Fresh bounded Git reads for the source_files loop alone.

    Size queries bound body batches. Unrepresentable line-protocol requests and
    oversized pairs retain the original argv-based per-file checks.
    """
    def single(name, expected):
        _committed(root, source, name, expected)
        if digest(_git(root, "show", f"{design_source}:{name}")) != expected:
            raise ValueError("source differs from design freeze")

    def bodies(entries, extents):
        raw = _source_git_batch(root, [oid for oid, _ in extents], bodies=True)
        recorded = _source_batch_parse(raw, len(extents), extents=extents)
        for index, (name, expected, _) in enumerate(entries):
            current, frozen = recorded[2 * index:2 * index + 2]
            if local_path(root, name).read_bytes() != current:
                raise ValueError(f"committed source differs: {name}")
            if digest(current) != expected:
                raise ValueError(f"registered source hash differs: {name}")
            if digest(frozen) != expected:
                raise ValueError("source differs from design freeze")

    def batch(entries):
        requests = [request for _, _, pair in entries for request in pair]
        extents = _source_batch_parse(_source_git_batch(root, requests), len(requests))
        pending, sizes, total = [], [], 0
        for index, (name, expected, pair) in enumerate(entries):
            current, frozen = extents[2 * index:2 * index + 2]
            if len(local_path(root, name).read_bytes()) != current[1]:
                raise ValueError(f"committed source differs: {name}")
            size = current[1] + frozen[1]
            if pending and total + size > _SOURCE_BATCH_BYTES:
                bodies(pending, sizes)
                pending, sizes, total = [], [], 0
            if size > _SOURCE_BATCH_BYTES:
                single(name, expected)
            else:
                pending.append((name, expected, pair))
                sizes.extend((current, frozen))
                total += size
        if pending:
            bodies(pending, sizes)

    pending = []
    for name, expected in files.items():
        local_path(root, name)
        requests = (f"{source}:{Path(name).as_posix()}", f"{design_source}:{name}")
        if any("\x00" in request for request in requests):
            raise ValueError("committed source/registration cannot be verified")
        try:
            pair = tuple(request.encode("utf-8") for request in requests)
        except UnicodeEncodeError:
            pair = None
        if pair is None or any(b"\n" in request or b"\r" in request for request in pair):
            if pending:
                batch(pending)
                pending = []
            single(name, expected)
        else:
            pending.append((name, expected, pair))
            if len(pending) == _SOURCE_BATCH_FILES:
                batch(pending)
                pending = []
    if pending:
        batch(pending)


def _window(window):
    start, end = utc(window["start"]), utc(window["end"])
    if start >= end:
        raise ValueError("window start must precede exclusive end")
    return start, end


def _overlaps(left, right):
    a, b = _window(left)
    c, d = _window(right)
    return a < d and c < b


def claims(root: Path) -> list[dict]:
    """Every start spends one attempt and exposes its windows, including failures."""
    folder = root / "research_runs"
    if not folder.exists():
        return []
    result = []
    for child in sorted(folder.iterdir()):
        if child.name.startswith("."):
            continue
        if not child.is_dir() or not (child / "claim.json").is_file():
            raise ValueError("partial run claim requires manual recovery; automatic reuse prohibited")
        from .verify import verify_claim
        claim = verify_claim(child)
        if claim["experiment_id"] != child.name:
            raise ValueError("run claim identity differs from its directory")
        if (child / "complete.json").exists() and (child / "failed.json").exists():
            raise ValueError("contradictory terminal receipts require review")
        result.append(claim)
    return result


@dataclass(frozen=True)
class Admission:
    root: Path
    registration: str
    experiment_id: str
    source: str
    registration_sha256: str
    spec: dict
    experiment: dict
    family: dict
    windows: list[dict]
    ready: bool
    design_source: str
    bindings: str | None
    bindings_sha256: str | None
    inputs: dict
    effective_attempt_budget: int


def admit(*, root, registration, experiment, source, design_source=None, bindings=None,
          _own_claim=None) -> Admission:
    """Read only registration, source and prior receipts; no empirical input bytes.

    `ready=False` admits a prospective design while refusing its execution until
    all declared sample windows have ended. Input hashing occurs in start().
    """
    root = Path(root).resolve()
    if _git(root, "rev-parse", "HEAD").decode().strip() != source:
        raise ValueError("source must equal the full current HEAD")
    raw = _committed(root, source, registration)
    design_source = design_source or source
    _git(root, "merge-base", "--is-ancestor", design_source, source)
    frozen = _git(root, "show", f"{design_source}:{Path(registration).as_posix()}")
    if raw != frozen:
        raise ValueError("design registration changed between freeze and execution")
    spec = json.loads(raw)
    if spec.get("schema_version") != 1:
        raise ValueError("unsupported registration schema")
    identity(spec["program_id"], "program")
    identity(experiment, "experiment")
    experiments = spec["experiments"]
    exp = experiments[experiment]
    charter = exp["charter"]
    _committed(root, source, charter["path"], charter["sha256"])
    if digest(_git(root, "show", f"{design_source}:{charter['path']}")) != charter["sha256"]:
        raise ValueError("charter differs from design freeze")
    family = spec["families"][exp["family"]]
    mechanisms = []
    for name, info in spec["families"].items():
        identity(name, "family")
        mechanisms.append(identity(info["mechanism_id"], "mechanism"))
        for field in ("attempt_budget", "prior_attempts"):
            if type(info[field]) is not int or info[field] < 0:
                raise ValueError("family budget and prior attempts must be nonnegative integers")
        if name == exp["family"] and info["attempt_budget"] <= info["prior_attempts"]:
            raise ValueError("family budget has no remaining attempts")
        if not info.get("history_reference"):
            raise ValueError("family history reference is required")
    if len(mechanisms) != len(set(mechanisms)):
        raise ValueError("same mechanism cannot reset budget under another family")
    seen = set()
    parent = experiment
    while parent is not None:
        if parent in seen or parent not in experiments:
            raise ValueError("invalid parent ancestry")
        seen.add(parent)
        ancestor = experiments[parent]
        if ancestor["family"] != exp["family"]:
            raise ValueError("parent ancestry cannot move into another family budget")
        parent = ancestor["parent"]
    if not exp.get("question"):
        raise ValueError("experiment question is required")
    if exp["stage"] not in {"discovery", "development", "confirmation"}:
        raise ValueError("unrecognized research stage")
    if exp["reuse"] not in {"exploratory", "fresh"}:
        raise ValueError("reuse must be exploratory or fresh")
    if exp["stage"] == "confirmation":
        if not exp.get("selection"):
            raise ValueError("confirmation requires a committed selection freeze")
        selection = exp["selection"]
        _committed(root, source, selection["path"], selection["sha256"])
        if digest(_git(root, "show", f"{design_source}:{selection['path']}")) != selection["sha256"]:
            raise ValueError("selection differs from design freeze")
    if not exp["source_files"] or exp["runtime_hashes"] != runtime_hashes():
        raise ValueError("source files/runtime hashes are missing or changed")
    _source_files(root, source, design_source, exp["source_files"])
    for key in ("cells", "outputs"):
        names = exp[key]
        if not names or len(names) != len(set(names)):
            raise ValueError(f"registered {key} must be nonempty and unique")
        for name in names:
            identity(name, "output" if key == "outputs" else "cell")
    if any(not name.endswith(".json") for name in exp["outputs"]):
        raise ValueError("this narrow helper accepts JSON outputs only")
    if not exp["windows"] or not exp["inputs"]:
        raise ValueError("registered sample windows and inputs required")
    datasets = spec["datasets"]
    history = []
    for info in datasets.values():
        identity(info["identity"], "dataset")
        if not info.get("history_reference"):
            raise ValueError("dataset exposure history reference is required")
        for exposure in info["exposures"]:
            _window(exposure)
            if exposure["state"] not in {"exposed", "spent"}:
                raise ValueError("invalid prior exposure state")
            history.append({**exposure, "identity": info["identity"]})
    prior = claims(root)
    if any(c["experiment_id"] == experiment for c in prior if c["experiment_id"] != _own_claim):
        raise ValueError("repeat run prohibited; use a separately justified registration")
    relevant = [c for c in prior if c["family"]["mechanism_id"] == family["mechanism_id"]]
    for claim in relevant:
        if claim["family"] != family:
            raise ValueError("family budget/history changed; explicit extension process required")
    def extension_metadata(reference):
        if (not isinstance(reference, dict) or set(reference) != {"path", "sha256"}
                or not isinstance(reference["path"], str)
                or not isinstance(reference["sha256"], str)
                or not re.fullmatch(r"[0-9a-f]{64}", reference["sha256"])
                or exp["source_files"].get(reference["path"]) != reference["sha256"]):
            raise ValueError("budget extension metadata must be source-pinned")
        value = _committed(root, source, reference["path"], reference["sha256"])
        if _git(root, "show", f"{design_source}:{reference['path']}") != value:
            raise ValueError("budget extension metadata differs from design freeze")
        return value
    from .budget_extensions import effective_budget
    ceiling = effective_budget(root, spec["program_id"], experiment, exp, family, relevant, extension_metadata)
    used = len([c for c in relevant if c["experiment_id"] != _own_claim]) + family["prior_attempts"]
    if used >= ceiling:
        raise ValueError("cumulative family attempt budget exhausted")
    if exp["parent"] is not None:
        parent_dir = root / "research_runs" / exp["parent"]
        if not any((parent_dir / p).exists() for p in ("complete.json", "failed.json")):
            raise ValueError("parent must have a terminal decision receipt before follow-up")
        parent_claim = next((c for c in prior if c["experiment_id"] == exp["parent"]), None)
        if parent_claim is None or parent_claim["family"]["mechanism_id"] != family["mechanism_id"]:
            raise ValueError("parent claim ancestry differs")
        if parent_claim["experiment"] != experiments[exp["parent"]]:
            raise ValueError("parent registration changed after its recorded run")
    for claim in prior:
        history.extend(claim["prior_exposures"])
        if claim["experiment_id"] != _own_claim:
            history.extend(claim["windows"])
    now = datetime.now(timezone.utc)
    committed_at = datetime.fromisoformat(
        _git(root, "show", "-s", "--format=%cI", design_source).decode().strip()).astimezone(timezone.utc)
    windows = []
    ready = True
    for window in exp["windows"]:
        start, end = _window(window)
        info = datasets[window["dataset"]]
        if window["availability"] not in {"existing", "prospective"}:
            raise ValueError("unrecognized sample availability")
        if window["availability"] == "prospective" and committed_at >= start:
            raise ValueError("prospective sample must start after committed source/selection freeze")
        ready = ready and end <= now
        exposed = any(h["identity"] == info["identity"] and _overlaps(window, h) for h in history)
        if exposed and exp["stage"] == "confirmation":
            raise ValueError("confirmation overlaps exposed or spent sample")
        if exposed and exp["reuse"] != "exploratory":
            raise ValueError("exposed sample requires explicitly exploratory reuse")
        windows.append({**window, "identity": info["identity"],
                        "state": "spent" if exp["stage"] == "confirmation" else "exposed"})
    declared_datasets = {w["dataset"] for w in exp["windows"]}
    if {i["dataset"] for i in exp["inputs"].values()} != declared_datasets:
        raise ValueError("every input must map to a registered sample window")
    for name, item in exp["inputs"].items():
        identity(name, "input")
        local_path(root, item["path"])
        if item["sha256"] is None:
            related = [w for w in exp["windows"] if w["dataset"] == item["dataset"]]
            if any(w["availability"] != "prospective" for w in related):
                raise ValueError("only prospective inputs may defer their content hash")
        elif not isinstance(item["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]):
            raise ValueError("input requires SHA-256")
    resolved_inputs = {name: dict(item) for name, item in exp["inputs"].items()}
    bindings_sha256 = None
    pending = {name for name, item in resolved_inputs.items() if item["sha256"] is None}
    if bindings is not None:
        bound_raw = _committed(root, source, bindings)
        bound = json.loads(bound_raw)
        if set(bound) != {"schema_version", "design_commit", "experiment", "registration_sha256", "inputs"}:
            raise ValueError("bindings contain unregistered fields")
        if (bound["schema_version"] != 1 or bound["design_commit"] != design_source
                or bound["experiment"] != experiment or bound["registration_sha256"] != digest(raw)):
            raise ValueError("bindings differ from frozen design identity")
        if set(bound["inputs"]) != pending:
            raise ValueError("bindings must cover exactly the pending prospective inputs")
        for name, item in bound["inputs"].items():
            if set(item) != {"sha256", "capture_manifest"}:
                raise ValueError("bindings may supply only hashes and capture provenance")
            if not isinstance(item["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]):
                raise ValueError("binding input requires SHA-256")
            capture = item["capture_manifest"]
            if set(capture) != {"path", "sha256"}:
                raise ValueError("invalid capture manifest binding")
            _committed(root, source, capture["path"], capture["sha256"])
            resolved_inputs[name]["sha256"] = item["sha256"]
        bindings_sha256 = digest(bound_raw)
    ready = ready and all(item["sha256"] is not None for item in resolved_inputs.values())
    return Admission(root, registration, experiment, source, digest(raw), spec, exp, family, windows, ready,
                     design_source, bindings, bindings_sha256, resolved_inputs, ceiling)

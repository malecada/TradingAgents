"""Predlab pre-registration: gates, append-only trial ledger, dev-window guard.

Mirror of tradingagents/rebuild/ledger.py semantics in the predlab namespace
(data/predlab/): registration is frozen before results exist, every evaluated
config appends a ledger row, and multiplicity denominators are computed from
the ledger — never quoted.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

HOLDOUT_START = "2025-04-01"
MAX_LOAD_END = "2025-03-31"


def _data_root() -> Path:
    return Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))


def gates_path() -> Path:
    return _data_root() / "predlab" / "gates.json"


def ledger_path() -> Path:
    return _data_root() / "predlab" / "trial_ledger.jsonl"


def assert_dev_window(end_date: str, allow_holdout: bool = False) -> None:
    """Raise if an evaluation window reaches into the sealed holdout."""
    if allow_holdout:
        return
    if str(end_date) >= HOLDOUT_START:
        raise RuntimeError(
            f"evaluation end {end_date} reaches into sealed holdout "
            f"(>= {HOLDOUT_START}); pass allow_holdout=True only for a "
            "registered one-shot champion evaluation"
        )


def _config_hash(config: dict) -> str:
    canonical = json.dumps(config, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:12]


def trial_identity(row: dict) -> str:
    """One identity per evaluated experiment/cell/model/config/window, across writers."""
    identity = {k: row.get(k) for k in ("experiment", "cell", "model", "config", "window")}
    return hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def preflight(experiment: str, window: tuple[str, str]) -> dict:
    """Require a committed registration and clean executable inputs BEFORE a run.

    Legacy artifacts are immutable. A correction listed as requiring a new
    registration cannot be rerun under its old key. This checks local Git, not
    the credibility of a registration made before this control existed.
    """
    gate = get_experiment(experiment)
    path = gates_path().resolve()
    try:
        relative = path.relative_to(PROJECT_ROOT.resolve())
        committed = subprocess.run(["git", "show", f"HEAD:{relative.as_posix()}"], cwd=PROJECT_ROOT,
                                   capture_output=True, text=True, check=True).stdout
    except (ValueError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("gate must exist in the committed checkout") from exc
    if json.loads(committed).get(experiment) != gate:
        raise RuntimeError("gate differs from its committed registration")
    from tradingagents.predlab.evidence import resolve
    correction = resolve(experiment, PROJECT_ROOT / "docs/audit/corrections.jsonl")
    if correction and correction.get("rerun_requires_new_registration", False):
        raise RuntimeError(f"{experiment}: audited evidence requires a new correction registration")
    bounds = gate.get("development_window", gate.get("dev_window", gate.get("strategy_dev_window")))
    if bounds and (window[0] < bounds[0] or window[1] > bounds[1]):
        raise RuntimeError(f"window {window} is outside registered window {bounds}")
    assert_dev_window(window[1], allow_holdout=bool(gate.get("allow_holdout", False)))
    changes = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"],
                             cwd=PROJECT_ROOT, capture_output=True, text=True, check=True).stdout
    dirty = []
    for line in changes.splitlines():
        name = line[3:].strip('"')
        if Path(name).suffix in {".py", ".toml", ".lock", ".yaml", ".yml", ".sh"} or name.endswith("gates.json") or name == "docs/audit/corrections.jsonl":
            dirty.append(name)
    if dirty:
        raise RuntimeError("uncommitted executable/configuration inputs: " + ", ".join(dirty[:12]))
    policy = PROJECT_ROOT / "docs/audit/corrections.jsonl"
    return {"git_commit": _git_commit(), "correction_policy_sha256": hashlib.sha256(policy.read_bytes()).hexdigest() if policy.exists() else None,
            "gate_sha256": hashlib.sha256(
        json.dumps(gate, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "evidence_policy": "audit-v2", "registered_experiment": experiment}


def _git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
    except Exception:
        return "unknown"


def log_trial(
    experiment: str,
    cell: str,
    model: str,
    config: dict,
    window: "tuple[str, str]",
    metrics: dict,
) -> dict:
    """Append one ledger row; returns the row written."""
    provenance = preflight(experiment, window)
    row = {
        **provenance,
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "experiment": experiment,
        "cell": cell,
        "model": model,
        "config": config,
        "config_hash": _config_hash(config),
        "git_commit": _git_commit(),
        "window": list(window),
        "metrics": metrics,
    }
    row["trial_id"] = trial_identity(row)
    path = ledger_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")
    return row


def _iter_ledger() -> "list[dict]":
    path = ledger_path()
    if not path.exists():
        return []
    return [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]


def trial_count(experiment: "str | None" = None) -> int:
    """Distinct evaluated hypotheses; legacy rows are normalized without rewriting."""
    rows = _iter_ledger()
    if experiment is not None:
        rows = [r for r in rows if r.get("experiment") == experiment]
    return len({trial_identity(r) for r in rows})


def load_gates() -> dict:
    path = gates_path()
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def get_experiment(key: str) -> dict:
    gates = load_gates()
    if key not in gates:
        raise KeyError(f"experiment {key!r} not registered in {gates_path()}")
    return gates[key]


def resolved_evidence(key: str) -> dict:
    """Read original registration together with its latest dated qualification."""
    from tradingagents.predlab.evidence import resolve
    return {"registration": get_experiment(key), "correction": resolve(key)}

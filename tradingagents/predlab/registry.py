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


def _git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
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
    row = {
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
    """Unique config_hash count (multiplicity denominator source of truth)."""
    rows = _iter_ledger()
    if experiment is not None:
        rows = [r for r in rows if r.get("experiment") == experiment]
    return len({r["config_hash"] for r in rows})


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

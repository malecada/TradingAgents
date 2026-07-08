"""Trial ledger + holdout guard for the honest rebuild.

Every full-window config evaluation MUST be logged here before its result is
read. DSR trial counts are computed from this file, never quoted from memory
(audit 2026-07-07: 12 claimed vs >450 actual evaluations).

The holdout window (>= HOLDOUT_START) is locked until the Phase 3 one-shot;
log_trial and assert_dev_window enforce it mechanically.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_LEDGER = PROJECT_ROOT / "data" / "rebuild" / "trial_ledger.jsonl"
HOLDOUT_START = "2025-04-01"


def assert_dev_window(end_date: str, allow_holdout: bool = False) -> None:
    """Raise if end_date reaches into the locked holdout window."""
    if allow_holdout:
        return
    if str(end_date)[:10] >= HOLDOUT_START:
        raise ValueError(
            f"window end {end_date} reaches into the locked holdout "
            f"(>= {HOLDOUT_START}); pass allow_holdout=True only for the "
            f"Phase 3 one-shot"
        )


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
    config: dict,
    window: tuple[str, str],
    metrics: dict,
    ledger_path: Path = DEFAULT_LEDGER,
    allow_holdout: bool = False,
) -> dict:
    """Append one config evaluation to the ledger; returns the written row."""
    assert_dev_window(window[1], allow_holdout=allow_holdout)
    cfg_json = json.dumps(config, sort_keys=True, default=str)
    row = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(),
        "experiment": experiment,
        "config": config,
        "config_hash": hashlib.sha256(cfg_json.encode()).hexdigest()[:12],
        "window": list(window),
        "metrics": metrics,
    }
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with open(ledger_path, "a") as f:
        f.write(json.dumps(row, default=str) + "\n")
    return row


def trial_count(
    ledger_path: Path = DEFAULT_LEDGER, experiment: str | None = None
) -> int:
    """Number of logged trials (optionally for one experiment) — DSR input."""
    if not ledger_path.exists():
        return 0
    n = 0
    with open(ledger_path) as f:
        for line in f:
            if not line.strip():
                continue
            if experiment is None or json.loads(line)["experiment"] == experiment:
                n += 1
    return n

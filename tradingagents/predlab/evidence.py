"""Append-only claim corrections. Old gates, ledgers and results remain intact."""
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone
import fcntl

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "docs/audit/corrections.jsonl"


def read_corrections(path: Path = DEFAULT_PATH) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def append_correction(row: dict, path: Path = DEFAULT_PATH) -> dict:
    for required in ("id", "claim", "status", "reason"):
        if not row.get(required):
            raise ValueError(f"missing correction field {required}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        fh.seek(0)
        rows = [json.loads(line) for line in fh if line.strip()]
        if any(r["id"] == row["id"] for r in rows):
            raise ValueError("correction id already exists")
        previous = [r for r in rows if r["claim"] == row["claim"]]
        if previous and row.get("supersedes") != previous[-1]["id"]:
            raise ValueError("correction must explicitly supersede latest claim record")
        result = {"recorded_utc": datetime.now(timezone.utc).isoformat(), **row}
        fh.write(json.dumps(result, sort_keys=True) + "\n")
        fh.flush()
        return result


def resolve(claim: str, path: Path = DEFAULT_PATH) -> dict | None:
    """Latest correction for a claim; original numeric rows are never changed."""
    matches = [r for r in read_corrections(path) if r["claim"] == claim]
    return matches[-1] if matches else None

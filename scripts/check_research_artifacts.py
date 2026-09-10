"""Read-only integrity/retention check for the explicit research artifact catalogue.

Git recoverability is a local blob check, never a claim of a remote backup.
External workspace material is optional for a portable clone and required only
with --require-external. No market data are decoded or experiments executed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def _path(base: Path, relative: str) -> Path:
    raw = Path(relative)
    if raw.is_absolute() or ".." in raw.parts or not raw.parts:
        raise ValueError("catalogue paths must be relative and contained")
    if any(part in {"keys", "apis", ".env", "hf_token.txt"} for part in raw.parts):
        raise ValueError("secret paths are not catalogue inputs")
    resolved = (base / raw).resolve()
    if not resolved.is_relative_to(base.resolve()):
        raise ValueError("catalogue path escapes its declared root")
    if any(part in {"keys", "apis", ".env", "hf_token.txt"}
           for part in resolved.relative_to(base.resolve()).parts):
        raise ValueError("catalogue symlink resolves to a secret path")
    return resolved


def _sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def inspect_file(base: Path, entry: dict, *, git_root: Path | None = None) -> dict:
    expected = entry.get("sha256")
    if expected is not None and not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("invalid expected SHA256")
    path = _path(base, entry["path"])
    row = {"id": entry.get("id", entry["path"]), "path": entry["path"],
           "present": path.is_file(), "sha256_matches": None,
           "local_git_blob_matches": None, "remote_backup_verified": False}
    if path.is_file() and expected is not None:
        row["sha256_matches"] = _sha(path) == expected
    if git_root is not None and entry.get("git_tracked"):
        blob = subprocess.run(["git", "show", f"HEAD:{entry['path']}"], cwd=git_root,
                              stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
        row["local_git_blob_matches"] = blob.returncode == 0 and hashlib.sha256(blob.stdout).hexdigest() == expected
    return row


def check(root: Path, catalogue: Path, *, require_external: bool = False) -> dict:
    document = json.loads(catalogue.read_text())
    if document.get("schema_version") != 1:
        raise ValueError("unsupported catalogue schema")
    artifacts, members, external = [], [], []
    for entry in document["artifacts"]:
        row = inspect_file(root, entry, git_root=root)
        artifacts.append(row)
        field = entry.get("manifest_map")
        if field and row["sha256_matches"]:
            manifest = json.loads(_path(root, entry["path"]).read_text())
            mapping = manifest[field]
            if not isinstance(mapping, dict):
                raise ValueError("manifest_map must name a path-to-hash object")
            for name, digest in mapping.items():
                members.append(inspect_file(root, {"path": name, "sha256": digest}))
    for entry in document.get("external_inputs", []):
        external.append(inspect_file(root.parent, entry))
    failures = [row for row in artifacts + members if not row["present"] or row["sha256_matches"] is not True
                or row["local_git_blob_matches"] is False]
    external_problems = [row for row in external if not row["present"] or row["sha256_matches"] is not True]
    return {"schema_version": 1, "artifacts": artifacts, "manifest_members": members,
            "external_inputs": external, "failures": failures,
            "external_unverified": external_problems,
            "ok": not failures and (not require_external or not external_problems),
            "qualification": "Checks declared files and local Git blobs only. No remote backup or full workspace coverage is asserted."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue", type=Path)
    parser.add_argument("--require-external", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = check(root, args.catalogue or root / "docs/research/artifact_catalog.json",
                   require_external=args.require_external)
    print(json.dumps(result, indent=2))
    return int(not result["ok"])


if __name__ == "__main__":
    raise SystemExit(main())

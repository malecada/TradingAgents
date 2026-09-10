"""Emit a credential-free receipt for this checkout's locked research runtime."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import platform
import subprocess
import sys
import tomllib


def receipt(root: Path) -> dict:
    root = root.resolve()
    # Resolve as a user of the installed package, without fixing sys.path here.
    spec = importlib.util.find_spec("tradingagents")
    origin = Path(spec.origin).resolve() if spec and spec.origin else None
    lock = root / "uv.lock"
    lock_bytes = lock.read_bytes()
    locked = tomllib.loads(lock_bytes.decode())
    versions: dict[str, set[str]] = {}
    for package in locked["package"]:
        versions.setdefault(package["name"].lower().replace("_", "-"), set()).add(package["version"])
    installed = {d.metadata["Name"].lower().replace("_", "-"): d.version
                 for d in importlib.metadata.distributions() if d.metadata["Name"]}
    mismatches = {name: version for name, version in installed.items()
                  if version not in versions.get(name, set())}
    expected_python = (root / ".python-version").read_text().strip()
    problems = []
    if platform.python_version() != expected_python:
        problems.append("interpreter differs from .python-version")
    if Path(sys.prefix).resolve() != root / ".venv":
        problems.append("interpreter is not the checkout-local .venv")
    if origin != root / "tradingagents" / "__init__.py":
        problems.append("tradingagents resolves outside this checkout")
    if mismatches:
        problems.append("installed versions differ from the lockfile")
    try:
        sync = subprocess.run(["uv", "sync", "--locked", "--all-extras", "--check", "--offline",
                               "--python", expected_python], cwd=root, capture_output=True, check=False)
        sync_exit = sync.returncode
    except OSError:
        sync_exit = None
    if sync_exit != 0:
        problems.append("uv offline locked environment completeness check failed or uv unavailable")
    return {
        "schema_version": 1,
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "executable": sys.executable,
        "prefix": sys.prefix,
        "package_origin": str(origin) if origin else None,
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        "lock_sha256": hashlib.sha256(lock_bytes).hexdigest(),
        "installed_versions": dict(sorted(installed.items())),
        "version_mismatches": mismatches,
        "locked_sync_check_exit_code": sync_exit,
        "problems": problems,
        "ok": not problems,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Exit nonzero for a runtime/source mismatch")
    args = parser.parse_args()
    result = receipt(Path(__file__).resolve().parents[1])
    print(json.dumps(result, indent=2))
    return int(args.check and not result["ok"])


if __name__ == "__main__":
    raise SystemExit(main())

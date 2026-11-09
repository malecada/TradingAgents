"""Freeze the inputs of Charter 1: a manifest of dev-window dossier files (path -> sha256, builder version),
a digest of the kline store, and the agent config sha. Written to data/agents_v2/charter1/ and committed before
registration; the lifecycle runner verifies every dossier against it.
Usage: llm_v2c1_manifest.py --start 2022-01-07 --end 2024-12-30 [--dossiers data/dossier/dossiers_v26]
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tradingagents.agents_v2.graph import CONFIG_VERSION, config_sha  # noqa: E402
from tradingagents.dossier.builder import BUILDER_VERSION, OUT as DOSSIERS  # noqa: E402

TARGET = Path("data/agents_v2/charter1")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--dossiers", default=str(DOSSIERS), help="dossier directory (the dossier_build.py --out)")
    args = ap.parse_args()
    TARGET.mkdir(parents=True, exist_ok=True)
    files = {}
    versions = set()
    for day in sorted(p for p in Path(args.dossiers).iterdir() if p.is_dir() and args.start <= p.name <= args.end):
        for f in sorted(day.glob("*.json")):
            files[str(f)] = sha(f)
            versions.add(json.loads(f.read_text()).get("builder_version"))
    if len(versions) != 1:
        raise SystemExit(f"mixed builder versions in window: {versions}")
    manifest = {"builder_version": versions.pop(), "start": args.start, "end": args.end, "dossiers_dir": args.dossiers,
                "n_dossiers": len(files), "n_weeks": len({Path(p).parent.name for p in files}), "files": files}
    (TARGET / "dossier_manifest.json").write_text(json.dumps(manifest, indent=0, sort_keys=True) + "\n")
    klines = {str(p): sha(p) for p in sorted(Path("data/xsect/klines").glob("*.parquet"))}
    (TARGET / "klines_digest.json").write_text(json.dumps(klines, indent=0, sort_keys=True) + "\n")
    (TARGET / "agent_config.json").write_text(json.dumps({"config_version": CONFIG_VERSION, "config_sha": config_sha(),
                                                          "builder_version": BUILDER_VERSION}, indent=1) + "\n")
    print(json.dumps({k: manifest[k] for k in ("builder_version", "n_dossiers", "n_weeks")}), "klines", len(klines))
    return 0


if __name__ == "__main__":
    sys.exit(main())

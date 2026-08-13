"""llm_c1_event_xs — corpus freeze manifest.

Snapshots the admissible corpus (alpaca + gdelt stores): per-month row
counts, totals, remaining GDELT failed days (post-retry), and a content
hash per file. P0 sampling refuses to run without this manifest; the
manifest refuses to regenerate once written (freeze discipline).
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

STORES = {"alpaca": Path("data/sentiment/alpaca"),
          "gdelt": Path("data/sentiment/gdelt")}
OUT = Path("data/llm_event_xs/corpus_manifest.json")
FAILED_DAYS_LOG = Path("/tmp/claude-1000/-home-malecada-master-thesis/"
                       "f08d2b6d-f71e-4c57-a703-b74203ce521c/scratchpad/"
                       "gdelt_retry.log")


def file_hash(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def main() -> int:
    if OUT.exists():
        print(f"manifest exists ({OUT}) — corpus already frozen")
        return 1
    manifest = {"frozen_utc": datetime.now(timezone.utc).isoformat(),
                "stores": {}, "gdelt_failed_days_post_retry": []}
    for name, root in STORES.items():
        months = {}
        total = 0
        for f in sorted(root.rglob("*.parquet")):
            n = len(pd.read_parquet(f, columns=["id"]))
            months[f"{f.parent.name}-{f.stem}"] = {"rows": n,
                                                   "sha": file_hash(f)}
            total += n
        manifest["stores"][name] = {"months": months, "total_rows": total}
    if FAILED_DAYS_LOG.exists():
        failed = [ln.split(":")[0].replace("INFO", "").strip()
                  for ln in FAILED_DAYS_LOG.read_text().splitlines()
                  if ": 0 articles" in ln]
        # a day that still returned 0 in the retry pass is a permanent hole
        manifest["gdelt_failed_days_post_retry"] = sorted(set(
            d.split(" ")[-1] for d in failed))
    OUT.write_text(json.dumps(manifest, indent=1))
    a = manifest["stores"]["alpaca"]["total_rows"]
    g = manifest["stores"]["gdelt"]["total_rows"]
    print(f"corpus frozen: alpaca {a} rows, gdelt {g} rows, "
          f"{len(manifest['gdelt_failed_days_post_retry'])} permanent gdelt holes")
    return 0


if __name__ == "__main__":
    sys.exit(main())

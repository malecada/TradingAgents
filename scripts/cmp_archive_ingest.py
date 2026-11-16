"""Ingest the public news archive into its own text store root (Charter 5, no outcome, no model call).

Usage: python -I scripts/cmp_archive_ingest.py <repository root> <news.csv> <store root> [--manifest PATH]

The archive file is a download, so the interpreter runs isolated (``-I``) and the repository root is passed
as an argument. The store root must not be the root of the present store (``data/dossier/text``): registered
inputs of finished runs stay untouched.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


def main(argv: list[str]) -> int:
    if len(argv) < 4:
        print(__doc__)
        return 2
    repo, csv, root = Path(argv[1]).resolve(), Path(argv[2]), Path(argv[3])
    manifest = Path(argv[argv.index("--manifest") + 1]) if "--manifest" in argv else root / "ccnews_manifest.json"
    sys.path.insert(0, str(repo))
    import pandas as pd
    from tradingagents.compare import archive
    from tradingagents.dossier import store

    if root.resolve() == (repo / store.DEFAULT_ROOT).resolve():
        raise SystemExit("the archive must not be written into the present store root")
    if (root / archive.SOURCE).exists():
        raise SystemExit(f"{root / archive.SOURCE} exists; ingest into an empty root")
    raw = pd.read_csv(csv, usecols=archive.RAW_COLUMNS)
    rows, counts = archive.store_rows(raw)
    written = store.upsert(rows, root=root)
    digest = hashlib.sha256(csv.read_bytes()).hexdigest()
    by_year = rows.groupby(rows["event_ts"].dt.year).size().to_dict()
    out = {"archive": "maryamfakhari/crypto-news-coindesk-2020-2025", "licence": "CC-BY-NC-4.0", "csv_sha256": digest,
           "counts": counts, "written": int(written), "outlets": int(rows["outlet"].nunique()),
           "by_year": {str(k): int(v) for k, v in by_year.items()},
           "first": str(rows["event_ts"].min()), "last": str(rows["event_ts"].max())}
    manifest.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

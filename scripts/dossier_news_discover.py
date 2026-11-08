"""Discover canonical article URLs and first-capture times per outlet and month (Wayback CDX).

Writes data/dossier/captures/<outlet>/<YYYY-MM>.parquet; months already present are skipped.
Usage: dossier_news_discover.py --start 2022-01 --end 2026-10 [--outlets coindesk,cointelegraph,theblock]
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tradingagents.dossier.wayback import OUTLETS, discover  # noqa: E402

OUT = Path("data/dossier/captures")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--outlets", default=",".join(OUTLETS))
    args = ap.parse_args()
    months = pd.period_range(args.start, args.end, freq="M")
    for outlet in args.outlets.split(","):
        for p in months:
            target = OUT / outlet / f"{p.year:04d}-{p.month:02d}.parquet"
            if target.exists():
                continue
            df = discover(outlet, p.year, p.month)
            target.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(target, index=False)
            print(f"{outlet} {p}: {len(df)} articles", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

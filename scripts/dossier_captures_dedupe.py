"""Collapse monthly capture files per outlet to one row per canonical URL (earliest capture),
drop URLs already captured before 2022 (pre-existing articles recaptured later), and for
The Block keep only post ids plausibly published in the window. Writes
data/dossier/captures/<outlet>_dedup.parquet, which the fetch worker prefers.
Usage: dossier_captures_dedupe.py [--old-json /tmp/old_cointelegraph.json ...]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tradingagents.dossier.wayback import OUTLETS, canonical_url  # noqa: E402

CAPTURES = Path("data/dossier/captures")


def load_old(path: Path, outlet: str) -> set[str]:
    if not path or not Path(path).exists():
        return set()
    rows = json.loads(Path(path).read_text())
    pat = OUTLETS[outlet]["article"]
    return {canonical_url(r[0]) for r in rows[1:] if pat.match(canonical_url(r[0]))}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--old-json", nargs="*", default=[], help="<outlet>=<path> pairs")
    args = ap.parse_args()
    old_paths = dict(p.split("=", 1) for p in args.old_json)
    for outlet in OUTLETS:
        files = sorted((CAPTURES / outlet).glob("????-??.parquet"))
        if not files:
            continue
        df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
        df["first_ts"] = pd.to_datetime(df["first_ts"], utc=True)
        before = len(df)
        df = df.sort_values("first_ts").drop_duplicates("url", keep="first")
        old = load_old(Path(old_paths[outlet]), outlet) if outlet in old_paths else set()
        df = df[~df["url"].isin(old)]
        note = f"old-excluded {len(old)}"
        if outlet == "theblock":
            pid = df["url"].str.extract(r"/post/(\d+)/")[0].astype(float)
            df = df.assign(pid=pid)
            medians = df.assign(m=df["first_ts"].dt.to_period("M")).groupby("m")["pid"].median()
            floor = float(medians.iloc[0]) * 0.75
            df = df[df["pid"] >= floor].drop(columns="pid")
            note += f"; pid floor {floor:.0f}"
        target = CAPTURES / f"{outlet}_dedup.parquet"
        df.reset_index(drop=True).to_parquet(target, index=False)
        print(f"{outlet}: {before} rows -> {len(df)} unique urls ({note}); dev-window "
              f"{int(((df['first_ts'] >= '2022-01-01') & (df['first_ts'] < '2025-01-01')).sum())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

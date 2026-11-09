"""Fetch discovered captures from the Wayback Machine and append to the bitemporal store.

Idempotent: a ledger (data/dossier/captures/fetched.jsonl) records every attempted URL with
its outcome; URLs already in the ledger are skipped. Rows are upserted per 50 articles.
Usage: dossier_news_fetch.py [--outlets ...] [--start 2022-01 --end 2024-12] [--max N]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tradingagents.dossier import store  # noqa: E402
from tradingagents.dossier.wayback import FETCH_INTERVAL_S, OUTLETS, fetch_capture, to_store_row, _session  # noqa: E402

CAPTURES = Path("data/dossier/captures")
LEDGER = CAPTURES / "fetched.jsonl"


def load_ledger() -> set[str]:
    if not LEDGER.exists():
        return set()
    return {json.loads(line)["url"] for line in LEDGER.read_text().splitlines() if line.strip()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outlets", default=",".join(OUTLETS))
    ap.add_argument("--start", default="2022-01")
    ap.add_argument("--end", default="2026-12")
    ap.add_argument("--max", type=int, default=None)
    args = ap.parse_args()
    done = load_ledger()
    frames = []
    for outlet in args.outlets.split(","):
        dedup = CAPTURES / f"{outlet}_dedup.parquet"
        if dedup.exists():
            d = pd.read_parquet(dedup)
            ym = d["first_ts"].dt.strftime("%Y-%m")
            frames.append(d[(ym >= args.start) & (ym <= args.end)])
            continue
        for path in sorted((CAPTURES / outlet).glob("????-??.parquet")):
            if args.start <= path.stem <= args.end:
                frames.append(pd.read_parquet(path))
    todo = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    todo = todo[~todo["url"].isin(done)].sort_values("first_ts") if len(todo) else todo
    if args.max:
        todo = todo.head(args.max)
    print(f"to fetch: {len(todo)} (ledger {len(done)})", flush=True)
    session = _session()
    batch, n_ok, started = [], 0, time.monotonic()
    with LEDGER.open("a") as ledger:
        for i, row in enumerate(todo.itertuples(index=False), 1):
            t0 = time.monotonic()
            try:
                f = fetch_capture(row.url, row.first_ts, session=session)
                if f.status == 429 or f.status >= 500:
                    raise RuntimeError(f"HTTP{f.status}")  # transient: not ledgered, retried later
                rec = to_store_row(row.outlet, f)
                outcome = "ok" if rec else f"skip:{f.status}:{'notext' if f.status == 200 else ''}"
            except Exception as exc:  # network, rate limit or parse failure: retried on a later run
                rec, outcome = None, f"error:{type(exc).__name__}:{exc}"
                print(f"transient {row.url[-60:]}: {outcome}", flush=True)
                time.sleep(20)
            if rec:
                batch.append(rec)
                n_ok += 1
            if not outcome.startswith("error"):
                ledger.write(json.dumps({"url": row.url, "outcome": outcome,
                                         "ts": pd.Timestamp.now("UTC").isoformat()}) + "\n")
                ledger.flush()
            if len(batch) >= 50:
                store.upsert(pd.DataFrame(batch))
                batch = []
            if i % 100 == 0:
                rate = i / (time.monotonic() - started)
                print(f"{i}/{len(todo)} ok={n_ok} {rate*3600:.0f}/h", flush=True)
            time.sleep(max(0.0, FETCH_INTERVAL_S - (time.monotonic() - t0)))
    if batch:
        store.upsert(pd.DataFrame(batch))
    print(f"done: fetched {n_ok} of {len(todo)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

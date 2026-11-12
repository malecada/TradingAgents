"""Build the uncapped reading list (tradingagents/reader/items.py) from the text store and the typing cache.

Usage: reader_items_build.py --start 2021-12 --end 2024-12 [--workers 4] [--out data/reader]
No LLM call, no outcome. One part per (source, month); existing parts are skipped; the parts are then
concatenated into items.parquet and docs.parquet.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import sys
import time

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tradingagents.dossier import store  # noqa: E402
from tradingagents.dossier.entities import build_dictionary  # noqa: E402
from tradingagents.dossier.universe import base_symbol, load_cards  # noqa: E402
from tradingagents.reader.items import FastLinker, load_typing_cache, month_rows  # noqa: E402

_STATE: dict = {}


def _init():
    cards = load_cards()
    dictionary = build_dictionary(sorted({base_symbol(s) for s in cards["symbol"].unique()}))
    _STATE.update(dictionary=dictionary, linker=FastLinker(dictionary), cache=load_typing_cache())


def _job(args) -> tuple[str, int, int, float]:
    path, out = args
    started = time.monotonic()
    name = f"{path.parts[-3]}-{path.parent.name}-{path.stem}"
    items_path, docs_path = out / "parts" / f"items-{name}.parquet", out / "parts" / f"docs-{name}.parquet"
    if items_path.exists() and docs_path.exists():
        return name, -1, -1, 0.0
    rows = pd.read_parquet(path)
    items, docs = month_rows(rows, _STATE["dictionary"], _STATE["linker"], _STATE["cache"])
    docs.to_parquet(docs_path, index=False)
    items.to_parquet(items_path, index=False)
    return name, len(items), len(docs), time.monotonic() - started


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True, help="first month, YYYY-MM")
    ap.add_argument("--end", required=True, help="last month, YYYY-MM")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", default="data/reader")
    args = ap.parse_args()
    out = Path(args.out)
    (out / "parts").mkdir(parents=True, exist_ok=True)
    first, last = pd.Period(args.start, "M"), pd.Period(args.end, "M")
    paths = [p for p in sorted(Path(store.DEFAULT_ROOT).glob("*/*/*.parquet"))
             if first <= pd.Period(f"{p.parent.name}-{p.stem}", "M") <= last]
    paths.sort(key=lambda p: -p.stat().st_size)          # largest first keeps the pool busy to the end
    with ProcessPoolExecutor(max_workers=args.workers, initializer=_init) as pool:
        for name, n_items, n_docs, secs in pool.map(_job, [(p, out) for p in paths]):
            print(f"{name}: {'skipped' if n_items < 0 else f'{n_items} item rows, {n_docs} typed docs, {secs:.0f}s'}", flush=True)
    for kind, key in (("items", ["doc_id", "base"]), ("docs", ["doc_id"])):
        parts = [pd.read_parquet(p) for p in sorted((out / "parts").glob(f"{kind}-*.parquet"))]
        frame = pd.concat([p for p in parts if len(p)], ignore_index=True).drop_duplicates(subset=key)
        frame.to_parquet(out / f"{kind}.parquet", index=False)
        print(f"{kind}.parquet: {len(frame)} rows", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Link the archive store and join its typing (Charter 5): items and docs tables of the archive rows.

Usage: cmp_items_build.py [--root data/compare/text] [--cache data/compare/typing_cache.jsonl]
                          [--out data/compare] [--workers 4]
Same rule as ``scripts/reader_items_build.py`` (``tradingagents.reader.items.month_rows``) on the separate
store root and the separate typing cache of the archive. No LLM call, no outcome. Every run rebuilds the
tables, so a run after the typing picks the new typings up.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import sys
import time

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tradingagents.dossier.entities import build_dictionary  # noqa: E402
from tradingagents.dossier.universe import base_symbol, load_cards  # noqa: E402
from tradingagents.reader.items import FastLinker, load_typing_cache, month_rows  # noqa: E402

_STATE: dict = {}


def _init(cache, bases):
    """``cache``: path of a typing cache file (no file: no typing) or the cache itself as a dict; ``bases``: the
    asset symbols of the dictionary."""
    dictionary = build_dictionary(sorted(bases))
    if not isinstance(cache, dict):
        cache = load_typing_cache(Path(cache)) if Path(cache).exists() else {}
    _STATE.update(dictionary=dictionary, linker=FastLinker(dictionary), cache=cache)


def _job(path: Path):
    started = time.monotonic()
    items, docs = month_rows(pd.read_parquet(path), _STATE["dictionary"], _STATE["linker"], _STATE["cache"])
    return f"{path.parts[-3]}-{path.parent.name}-{path.stem}", items, docs, time.monotonic() - started


def store_files(root: Path) -> list[Path]:
    """Month files of the archive store, largest first (the order of the work, not of the result)."""
    return sorted(Path(root).glob("*/*/*.parquet"), key=lambda p: -p.stat().st_size)


def card_bases(cards: pd.DataFrame) -> list[str]:
    return sorted({base_symbol(s) for s in cards["symbol"].unique()})


def build_tables(paths, cache, bases, workers: int = 4, log=print) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(items, docs) of the given store files with the typings of ``cache`` (a cache file or a dict) and the
    dictionary of ``bases``, sorted and without duplicates."""
    items, docs = [], []
    with ProcessPoolExecutor(max_workers=workers, initializer=_init, initargs=(cache if isinstance(cache, dict) else str(cache), list(bases))) as pool:
        for name, part_items, part_docs, secs in pool.map(_job, paths):
            log(f"{name}: {len(part_items)} item rows, {len(part_docs)} typed docs, {secs:.0f}s")
            items.append(part_items)
            docs.append(part_docs)
    out = []
    for parts, key in ((items, ["doc_id", "base"]), (docs, ["doc_id"])):
        frame = pd.concat([p for p in parts if len(p)] or parts[:1], ignore_index=True).drop_duplicates(subset=key)
        out.append(frame.sort_values(key).reset_index(drop=True))
    return out[0], out[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="data/compare/text")
    ap.add_argument("--cache", default="data/compare/typing_cache.jsonl")
    ap.add_argument("--out", default="data/compare")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    items, docs = build_tables(store_files(Path(args.root)), args.cache, card_bases(load_cards()), args.workers,
                               log=lambda m: print(m, flush=True))
    for kind, frame in (("items", items), ("docs", docs)):
        frame.to_parquet(out / f"{kind}.parquet", index=False)
        print(f"{kind}.parquet: {len(frame)} rows", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

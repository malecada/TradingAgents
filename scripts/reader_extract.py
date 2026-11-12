"""Fact extraction of the reader configuration (Charter 2): two readers and an adjudicator on every unit of the
work list. Runs outside the registered run. No outcome is read.

Phase 1 fills the call cache over the network (thread pool, resumable, cumulative spend limit). Phase 2 rebuilds
every record from the cache alone, so the record table is a function of the cache and the code.
Usage: reader_extract.py --pilot 300 --cost-cap 0.25      pilot sample, report only (allowed before the freeze)
       reader_extract.py --cost-cap 9.50                   full extraction (frozen charter required)
       reader_extract.py --offline                         rebuild from the cache and compare, no call
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import threading
import time

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from tradingagents.dossier.or_client import PINS, SpendCapError, StructuredClient  # noqa: E402
from tradingagents.reader import consensus, schema  # noqa: E402
from tradingagents.reader.charter2 import PANEL_END, PANEL_START, UNIVERSE_N, reading, universe  # noqa: E402
from tradingagents.reader.extract import MAX_TOKENS, CallCache, CallFailed, Reader  # noqa: E402
from tradingagents.reader.reading import Unit, units  # noqa: E402

CHARTER = "docs/superpowers/specs/2026-11-12-llm-v2-charter2-reader-charter.md"
DRAFT_MARK = "DRAFT, NOT FROZEN"
PIN = "flash"
PILOT_SEED = 20261112
PILOT_GROUNDING, PILOT_DIRECTION = 0.95, 0.70      # stop rule of stage R1
MAX_CONSECUTIVE_FAILURES = 50
SOURCES = ("tradingagents/reader/schema.py", "tradingagents/reader/extract.py", "tradingagents/reader/consensus.py",
           "tradingagents/reader/reading.py", "tradingagents/reader/charter2.py", "tradingagents/dossier/or_client.py",
           "tradingagents/dossier/universe.py", "tradingagents/dossier/builder.py", "scripts/reader_extract.py")
INPUTS = {"items": "data/reader/items.parquet", "docs": "data/reader/docs.parquet", "cards": "data/llm_rank_xs/cards.parquet"}
CACHE = "data/reader/calls.jsonl"
RECORDS = "data/reader/records.parquet"
MANIFEST = "data/reader/extraction_manifest.json"
PILOT_RECORDS = "data/reader/pilot_records.parquet"
PILOT_REPORT = "data/reader/pilot_report.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_units(items: pd.DataFrame, docs: pd.DataFrame, cards: pd.DataFrame) -> tuple[pd.DataFrame, list[Unit]]:
    """The work list of the registered universe and its units (one per document, in ``doc_id`` order)."""
    _, work = reading(items, docs, universe(cards))
    return work, units(work, docs, items)


def pilot_sample(unit_list: list[Unit], n: int, seed: int = PILOT_SEED) -> list[Unit]:
    """A simple random sample of units, returned in ``doc_id`` order."""
    if n >= len(unit_list):
        return list(unit_list)
    picked = random.Random(seed).sample(range(len(unit_list)), n)
    return [unit_list[i] for i in sorted(picked)]


def fill(reader: Reader, unit_list: list[Unit], workers: int = 16, passes: int = 3, log=print, every: int = 500) -> dict:
    """Phase 1: answer every call of every unit into the cache. A unit whose call fails is tried again in a later
    pass. The spend limit or a run of consecutive failures stops the phase."""
    stop, lock = threading.Event(), threading.Lock()
    state = {"streak": 0, "reason": None}

    def one(unit: Unit) -> str:
        if stop.is_set():
            return "skipped"
        try:
            consensus.resolve(reader, unit)
        except SpendCapError:
            with lock:
                state["reason"] = state["reason"] or "spend_cap"
            stop.set()
            return "skipped"
        except CallFailed:
            with lock:
                state["streak"] += 1
                if state["streak"] >= MAX_CONSECUTIVE_FAILURES:
                    state["reason"] = state["reason"] or "consecutive_failures"
                    stop.set()
            return "failed"
        with lock:
            state["streak"] = 0
        return "ok"

    pending, started = list(unit_list), time.monotonic()
    for n_pass in range(1, passes + 1):
        left = []
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for i, (unit, outcome) in enumerate(zip(pending, pool.map(one, pending)), 1):
                if outcome != "ok":
                    left.append(unit)
                if i % every == 0:
                    log(json.dumps({"pass": n_pass, "done": i, "of": len(pending), "not_ok": len(left),
                                    "new_calls": reader.stats["calls"], "paid_usd": round(reader.cache.paid_usd, 4),
                                    "minutes": round((time.monotonic() - started) / 60, 1)}))
        pending = left
        if not pending or stop.is_set():
            break
    return {"unfinished_units": len(pending), "stopped": state["reason"], "new_calls": reader.stats["calls"],
            "new_cost_usd": reader.stats["cost"], "minutes": (time.monotonic() - started) / 60}


def grounding(stats: dict) -> dict:
    """Evidence grounding of first reads, by role and for the two readers together."""
    out = {r: (g["found"] / g["needed"] if g["needed"] else None) for r, g in stats["grounding"].items()}
    needed = sum(stats["grounding"][r]["needed"] for r in ("A", "B"))
    out["readers"] = sum(stats["grounding"][r]["found"] for r in ("A", "B")) / needed if needed else None
    return out


def call_summary(cache: CallCache, keys) -> dict:
    """Calls, cost, tokens and providers of the calls the records were built from."""
    by_role: dict[str, dict] = {}
    providers: dict[str, int] = {}
    latency = []
    for key in keys:
        value = cache.get(key)
        meta = value.get("meta") or {}
        role = by_role.setdefault(value.get("role", "?"), {"calls": 0, "cost": 0.0, "prompt_tokens": 0, "completion_tokens": 0})
        role["calls"] += 1
        role["cost"] += float(meta.get("cost") or 0.0)
        role["prompt_tokens"] += int(meta.get("prompt_tokens") or 0)
        role["completion_tokens"] += int(meta.get("completion_tokens") or 0)
        providers[str(meta.get("provider"))] = providers.get(str(meta.get("provider")), 0) + 1
        if meta.get("latency_s") is not None:
            latency.append(float(meta["latency_s"]))
    latency.sort()
    return {"calls": sum(r["calls"] for r in by_role.values()), "cost_usd": sum(r["cost"] for r in by_role.values()),
            "by_role": dict(sorted(by_role.items())), "providers": dict(sorted(providers.items())),
            "latency_s": {"median": latency[len(latency) // 2], "q90": latency[int(len(latency) * 0.9)]} if latency else None}


def describe(rows: list[dict], reader: Reader, failed: list[str], cache: CallCache) -> dict:
    stats = reader.stats
    return {"units": len({r["doc_id"] for r in rows}), "records": len(rows), "units_call_missing": failed,
            "quality": consensus.quality(rows),
            "readings": {"first_read": stats["first_read"], "reread": stats["reread"]},
            "evidence_grounding": grounding(stats), "calls": call_summary(cache, sorted(reader.used))}


def _head(root: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=1, ensure_ascii=False, allow_nan=False) + "\n")


def main(argv=None, root: Path | None = None, client=None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pilot", type=int, default=0, help="sample size of the pilot; 0 = the whole work list")
    ap.add_argument("--cost-cap", type=float, default=None, help="cumulative spend limit in USD over every call in the cache")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--passes", type=int, default=3)
    ap.add_argument("--offline", action="store_true", help="no call: rebuild the records from the cache")
    ap.add_argument("--accept-missing", type=int, default=0,
                    help="units with a call that keeps failing that may be written as unresolved (full extraction)")
    ap.add_argument("--charter", default=CHARTER)
    args = ap.parse_args(argv)
    root = Path(root or ROOT)
    pilot = args.pilot > 0
    charter = root / args.charter
    if not pilot and DRAFT_MARK in charter.read_text():
        raise SystemExit("the charter is a draft: only the pilot may run before the freeze")

    frames = {name: pd.read_parquet(root / path) for name, path in INPUTS.items()}
    work, unit_list = build_units(frames["items"], frames["docs"], frames["cards"])
    total_units = len(unit_list)
    if pilot:
        unit_list = pilot_sample(unit_list, args.pilot)
    model = client.model if client is not None else PINS[PIN][0]
    cache = CallCache(root / CACHE)
    print(json.dumps({"work_list_units": total_units, "work_list_records": len(work), "units_this_run": len(unit_list),
                      "cache_calls": len(cache), "cache_paid_usd": round(cache.paid_usd, 4), "prompt_sha256": schema.prompt_sha256()}))

    filled = None
    if not args.offline:
        if args.cost_cap is None:
            raise SystemExit("--cost-cap is required for a run that may call the model")
        remaining = args.cost_cap - cache.paid_usd
        if remaining <= 0:
            raise SystemExit(f"spend limit reached: {cache.paid_usd:.4f} of {args.cost_cap}")
        if client is None:
            import requests
            from llm_v2c0_client import load_api_key
            session = requests.Session()
            session.mount("https://", requests.adapters.HTTPAdapter(pool_connections=4, pool_maxsize=args.workers + 4))
            client = StructuredClient.pinned(PIN, load_api_key(), cost_cap_usd=remaining, reasoning_enabled=False,
                                             max_tokens=MAX_TOKENS, session=session)
        filled = fill(Reader(client, cache, model=model), unit_list, workers=args.workers, passes=args.passes)
        print(json.dumps({"phase_1": filled}))

    rows, reader, failed = consensus.rebuild(unit_list, cache, model)
    summary = describe(rows, reader, failed, cache)
    frame = consensus.record_frame(rows)

    if pilot:
        g, d = summary["evidence_grounding"]["readers"], summary["quality"]["agreement"]["direction"]
        per_unit = summary["calls"]["cost_usd"] / max(summary["units"], 1)
        report = {"stage": "R1 pilot", "seed": PILOT_SEED, "prompt_sha256": schema.prompt_sha256(), "model": model,
                  "phase_1": filled, **summary,
                  "stop_rule": {"evidence_grounding": g, "minimum_grounding": PILOT_GROUNDING, "direction_agreement": d,
                                "minimum_direction_agreement": PILOT_DIRECTION,
                                "passed": bool(g is not None and d is not None and g >= PILOT_GROUNDING and d >= PILOT_DIRECTION)},
                  "cost": {"per_unit_usd": per_unit, "work_list_units": total_units, "projected_full_usd": per_unit * total_units,
                           "cache_paid_usd": cache.paid_usd}}
        frame.to_parquet(root / PILOT_RECORDS, index=False)
        _write_json(root / PILOT_REPORT, report)
        print(json.dumps({"stop_rule": report["stop_rule"], "cost": report["cost"], "report": PILOT_REPORT}))
        return report

    records_path = root / RECORDS
    if args.offline and records_path.exists():
        same = consensus.same_records(pd.read_parquet(records_path), frame)
        print(json.dumps({"offline_rebuild_equals_stored_records": bool(same), "records": len(frame)}))
        if not same:
            raise SystemExit("the rebuild from the cache differs from the stored records")
        return {"equal": True, **summary}
    if (filled and filled["stopped"]) or len(failed) > args.accept_missing:
        print(json.dumps({"incomplete": filled, "units_call_missing": len(failed)}))
        raise SystemExit("extraction incomplete: no record table written; run again to resume")
    frame.to_parquet(records_path, index=False)
    manifest = {"charter": {"path": args.charter, "sha256": sha256_file(charter)}, "prompt_sha256": schema.prompt_sha256(),
                "model": {"id": model, "providers": list(PINS[PIN][1]), "quantization": PINS[PIN][2], "reasoning": "disabled",
                          "temperature": 0, "max_tokens": MAX_TOKENS},
                "universe": {"n": UNIVERSE_N, "start": PANEL_START, "end": PANEL_END}, **summary,
                "cache": {"path": CACHE, "sha256": sha256_file(root / CACHE), "calls": len(cache), "paid_usd": cache.paid_usd},
                "inputs": {name: {"path": path, "sha256": sha256_file(root / path)} for name, path in INPUTS.items()},
                "records_file": {"path": RECORDS, "sha256": sha256_file(records_path)},
                "source_files": {path: sha256_file(root / path) for path in SOURCES}, "head": _head(root)}
    _write_json(root / MANIFEST, manifest)
    print(json.dumps({"records": len(frame), "units": summary["units"], "units_call_missing": len(failed),
                      "cache_paid_usd": round(cache.paid_usd, 4), "manifest": MANIFEST}))
    return manifest


if __name__ == "__main__":
    main()

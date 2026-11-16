"""Pairwise comparison calls on the text dossiers (Charter 5). No outcome is read.

Usage: cmp_duels.py --pilot --cap 0.20       pilot weeks, quality report and stop rule (allowed before the freeze)
       cmp_duels.py --cap 4.00               every test week (frozen charter required)
       cmp_duels.py --offline                rebuild the results from the cache and compare, no call
Phase 1 fills the call cache (thread pool, resumable, cumulative spend limit); phase 2 rebuilds every result
from the cache alone, so the result table and the scores are a function of the cache, the dossiers and the code.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys
import threading
import time

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import cmp_common as common  # noqa: E402
from scripts.reader_extract import MAX_CONSECUTIVE_FAILURES, _write_json, call_summary  # noqa: E402
from tradingagents.compare import duel  # noqa: E402
from tradingagents.dossier.or_client import SpendCapError  # noqa: E402
from tradingagents.reader.extract import CallCache, CallFailed  # noqa: E402

CACHE = "data/compare/duel_calls.jsonl"
# stop rule of the pilot, fixed before the first call
PILOT_RULE = {"first_shown": (0.40, 0.60), "same_asset_min": 0.70, "decided_min": 0.30}


def fill(judge: duel.Judge, duels: list[dict], workers: int = 16, passes: int = 3, every: int = 500) -> dict:
    """Phase 1: answer every call of every comparison into the cache; failed comparisons are tried again."""
    stop, lock = threading.Event(), threading.Lock()
    state = {"streak": 0, "reason": None}

    def one(d: dict) -> str:
        if stop.is_set():
            return "skipped"
        try:
            duel.resolve(judge, d)
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

    pending, started = list(duels), time.monotonic()
    for n_pass in range(1, passes + 1):
        left = []
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for i, (d, outcome) in enumerate(zip(pending, pool.map(one, pending)), 1):
                if outcome != "ok":
                    left.append(d)
                if i % every == 0:
                    print(json.dumps({"pass": n_pass, "done": i, "of": len(pending), "not_ok": len(left),
                                      "new_calls": judge.stats["calls"], "paid_usd": round(judge.cache.paid_usd, 4)}), flush=True)
        pending = left
        if not pending or stop.is_set():
            break
    return {"unfinished": len(pending), "stopped": state["reason"], "new_calls": judge.stats["calls"],
            "new_cost_usd": judge.stats["cost"], "minutes": (time.monotonic() - started) / 60}


def all_duels(dossiers: pd.DataFrame) -> list[dict]:
    """The comparisons of every week of the dossier table."""
    return [d for friday, week in dossiers.groupby("friday") for d in duel.week_duels(friday, week)]


def stop_rule(quality: dict) -> dict:
    lo, hi = PILOT_RULE["first_shown"]
    first, same, decided = quality.get("first_shown"), quality.get("same_asset"), quality.get("decided")
    checks = {"first_shown_in_band": first is not None and lo <= first <= hi,
              "same_asset": same is not None and same >= PILOT_RULE["same_asset_min"],
              "decided": decided is not None and decided >= PILOT_RULE["decided_min"]}
    return {"rule": PILOT_RULE, "checks": checks, "passed": all(checks.values())}


def main(argv=None, root: Path | None = None, client=None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    common.add_week_args(ap)
    ap.add_argument("--cap", type=float, default=None, help="spend limit of the call cache in USD, all runs together")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--passes", type=int, default=3)
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args(argv)
    root = Path(root or common.ROOT)
    _, fridays, pilot = common.universe_weeks(args)
    if not pilot and not args.offline:
        common.require_frozen(root)
    prefix = "pilot_" if pilot else ""
    out = root / "data/compare"
    dossiers = pd.read_parquet(out / f"{prefix}dossiers.parquet")
    dossiers = dossiers[dossiers["friday"].isin(set(fridays))]
    duels = all_duels(dossiers)
    model = client.model if client is not None else common.MODEL
    cache = CallCache(root / CACHE)
    print(json.dumps({"weeks": dossiers["friday"].nunique(), "dossiers": len(dossiers), "comparisons": len(duels),
                      "cache_calls": len(cache), "cache_paid_usd": round(cache.paid_usd, 4),
                      "prompt_sha256": duel.prompt_sha256()}), flush=True)
    filled = None
    if not args.offline:
        if args.cap is None:
            raise SystemExit("--cap is required for a run that may call the model")
        remaining = args.cap - cache.paid_usd
        if remaining <= 0:
            raise SystemExit(f"spend limit reached: {cache.paid_usd:.4f} of {args.cap}")
        client = client or common.make_client(remaining, args.workers, duel.MAX_TOKENS)
        filled = fill(duel.Judge(client, cache, model=model), duels, workers=args.workers, passes=args.passes)
        print(json.dumps({"phase_1": filled}), flush=True)
    results, judge, missing = duel.rebuild(duels, cache, model)
    scores = duel.scores(results, dossiers)
    calls = call_summary(cache, sorted(judge.used))
    quality = duel.quality(results)
    report = {"pilot": pilot, "model": model, "prompt_sha256": duel.prompt_sha256(), "k_rounds": duel.K_ROUNDS,
              "phase_1": filled, "comparisons": len(duels), "comparisons_call_missing": missing, "quality": quality,
              "invalid_answers": judge.stats["invalid"], "calls": calls,
              "cost": {"per_comparison_usd": calls["cost_usd"] / max(len(results), 1), "cache_paid_usd": cache.paid_usd}}
    if pilot:
        report["stop_rule"] = stop_rule(quality)
    results_path = out / f"{prefix}duels.parquet"
    if args.offline and results_path.exists():
        stored = pd.read_parquet(results_path)
        same = stored.astype(object).where(stored.notna(), None).equals(results.astype(object).where(results.notna(), None))
        print(json.dumps({"offline_rebuild_equals_stored_results": bool(same), "comparisons": len(results)}))
        if not same:
            raise SystemExit("the rebuild from the cache differs from the stored results")
        return report
    if not pilot and ((filled and filled["stopped"]) or missing):
        print(json.dumps({"incomplete": filled, "comparisons_call_missing": missing}))
        raise SystemExit("comparison incomplete: no result table written; run again to resume")
    results.to_parquet(results_path, index=False)
    scores.to_parquet(out / f"{prefix}scores.parquet", index=False)
    _write_json(out / f"{prefix}duel_report.json", report)
    print(json.dumps({k: report[k] for k in ("comparisons", "comparisons_call_missing", "quality", "invalid_answers", "cost")
                      } | ({"stop_rule": report["stop_rule"]} if pilot else {})), flush=True)
    return report


if __name__ == "__main__":
    main()

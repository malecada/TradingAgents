"""Type the archive documents of the small scope (Charter 5).

Usage: cmp_type.py [--cap USD] [--workers 8] [--pilot | --weeks 2023-03-10,2024-01-05] [--dry-run]
                   [--root data/compare/text] [--items data/compare/items.parquet]
                   [--cache data/compare/typing_cache.jsonl] [--out data/compare/typing_report.json]
The typing call and its instruction are those of the dossier build (``tradingagents.dossier.llm_text``); the
answers go to a separate cache, so the cache of the registered runs stays as it is. ``--cap`` limits the
spend of this cache over all runs. No outcome is read. After a run, ``cmp_items_build.py`` joins the typings.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys
import time

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import cmp_common as common  # noqa: E402
from scripts.llm_v2c0_client import load_api_key  # noqa: E402
from tradingagents.compare import scope  # noqa: E402
from tradingagents.dossier.entities import build_dictionary  # noqa: E402
from tradingagents.dossier.llm_text import CreditError, TextLLM, TextLLMError  # noqa: E402
from tradingagents.dossier.universe import base_symbol, load_cards  # noqa: E402
from tradingagents.reader.items import typing_key  # noqa: E402


def cache_cost(path: Path) -> tuple[set[str], float]:
    """Keys and the spend of a typing cache file."""
    keys, cost = set(), 0.0
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip():
                rec = json.loads(line)
                keys.add(rec["key"])
                cost += float(rec.get("cost") or 0.0)
    return keys, cost


def scope_texts(root: Path, wanted: pd.DataFrame, dictionary) -> tuple[pd.DataFrame, int]:
    """(doc_id, masked) of the scope documents long enough to type, and the number too short."""
    ids = set(wanted["doc_id"])
    rows, short = [], 0
    for path in sorted(root.glob("*/*/*.parquet")):
        part = pd.read_parquet(path, columns=["doc_id", "event_ts", "title", "body"])
        for r in part[part["doc_id"].isin(ids)].itertuples(index=False):
            masked = scope.typing_text(r.title, r.body, r.event_ts, dictionary)
            if masked is None:
                short += 1
            else:
                rows.append((r.doc_id, masked))
    return pd.DataFrame(rows, columns=["doc_id", "masked"]).drop_duplicates("doc_id"), short


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", type=float, default=0.0, help="spend limit of the typing cache in USD, all runs together")
    ap.add_argument("--workers", type=int, default=8)
    common.add_week_args(ap)
    ap.add_argument("--dry-run", action="store_true", help="count the calls, call nothing")
    ap.add_argument("--root", default="data/compare/text")
    ap.add_argument("--items", default="data/compare/items.parquet")
    ap.add_argument("--cache", default="data/compare/typing_cache.jsonl")
    ap.add_argument("--out", default="data/compare/typing_report.json")
    args = ap.parse_args()

    top, fridays, pilot = common.universe_weeks(args)
    if not pilot and not args.dry_run:
        common.require_frozen()
    cards = load_cards()
    wanted = scope.typing_scope(pd.read_parquet(args.items), top, fridays)
    dictionary = build_dictionary(sorted({base_symbol(s) for s in cards["symbol"].unique()}))
    started = time.monotonic()
    texts, short = scope_texts(Path(args.root), wanted, dictionary)
    keys, paid = cache_cost(Path(args.cache))
    texts["key"] = texts["masked"].map(typing_key)
    todo = texts[~texts["key"].isin(keys)].drop_duplicates("key")
    report = {"weeks": len(fridays), "scope_documents": len(wanted), "too_short": short, "to_type": len(texts),
              "in_cache": int(texts["key"].isin(keys).sum()), "calls_needed": len(todo),
              "masked_chars_mean": float(texts["masked"].str.len().mean()) if len(texts) else 0.0,
              "cache_paid_usd_before": paid, "cap_usd": args.cap, "mask_seconds": round(time.monotonic() - started, 1)}
    print(json.dumps(report), flush=True)
    if args.dry_run or todo.empty:
        return 0
    if args.cap - paid <= 0:
        raise SystemExit(f"spend limit reached: paid {paid:.4f} of {args.cap:.4f}")
    llm = TextLLM(api_key=load_api_key(), cost_cap_usd=args.cap - paid, cache_path=Path(args.cache))
    state = {"failed": 0, "stopped": None}

    def classify(masked: str) -> bool:
        if state["stopped"]:
            return False
        try:
            llm.classify(masked)
            return True
        except CreditError as exc:
            state["stopped"] = f"credit: {exc}"
        except TextLLMError as exc:
            if "spend cap" in str(exc):
                state["stopped"] = str(exc)
            else:
                state["failed"] += 1
        return False

    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for ok in pool.map(classify, todo["masked"]):
            done += ok
            if done and done % 500 == 0 and ok:
                print(json.dumps({"typed": done, "spent_usd": round(llm.spent_usd, 4)}), flush=True)
    report.update(typed=done, failed=state["failed"], stopped=state["stopped"], spent_usd=llm.spent_usd,
                  usd_per_1000=1000 * llm.spent_usd / done if done else None,
                  seconds=round(time.monotonic() - started, 1))
    Path(args.out).write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps(report), flush=True)
    return 0 if not state["stopped"] else 2


if __name__ == "__main__":
    sys.exit(main())

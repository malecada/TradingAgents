"""Identification probe on the text dossiers (Charter 5): can the comparison model name the asset and the month?

Usage: cmp_probe.py --pilot --cap 0.05 | cmp_probe.py --cap 0.50 | cmp_probe.py --offline
One call per dossier with the comparison model, cached (``data/compare/probe_calls.jsonl``). Writes
``flags.parquet`` (friday, base, identified, month_within_6, guess, year_month) and ``probe_report.json``
(prefix ``pilot_`` for pilot weeks). The flag splits a descriptive panel; it changes no score. No outcome is read.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import cmp_common as common  # noqa: E402
from tradingagents.compare import charter5  # noqa: E402
from tradingagents.dossier.or_client import ORError, SpendCapError  # noqa: E402
from tradingagents.reader.extract import CallCache, call_key  # noqa: E402

CACHE = "data/compare/probe_calls.jsonl"
MAX_TOKENS = 100
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["asset", "year_month", "confidence"],
          "properties": {"asset": {"type": "string"}, "year_month": {"type": "string"}, "confidence": {"type": "number"}}}
SYSTEM = ("The reports below are about one crypto asset. Its name and all other entities are replaced by role tokens. "
          "Name the real asset (a ticker from the list) and the calendar month (YYYY-MM) in which the reports were "
          "written. Use any clue. Always give your best guess.")
FLAG_COLUMNS = ["friday", "base", "identified", "month_within_6", "guess", "year_month"]


def probe_prompt(alias: str, text: str, tickers: list[str]) -> str:
    return f"Candidate tickers: {', '.join(tickers)}\n\nAsset token: {alias}\nReports of the last seven days:\n{text}"


def prompt_sha256() -> str:
    return hashlib.sha256(json.dumps({"system": SYSTEM, "schema": SCHEMA, "max_tokens": MAX_TOKENS}, sort_keys=True).encode()).hexdigest()


def month_gap(year_month: str, friday) -> int | None:
    try:
        y, m = (int(v) for v in str(year_month).strip()[:7].split("-"))
    except ValueError:
        return None
    day = pd.Timestamp(friday)
    return abs((y - day.year) * 12 + (m - day.month))


def flags(dossiers: pd.DataFrame, cache: CallCache, model: str, tickers: list[str]) -> tuple[pd.DataFrame, int, list[str]]:
    """Flags from the cache alone: (rows, dossiers without a cached answer, the keys used)."""
    rows, missing, used = [], 0, []
    for r in dossiers.itertuples(index=False):
        key = call_key(model, SYSTEM, probe_prompt(r.alias, r.text, tickers))
        hit = cache.get(key)
        if hit is None:
            missing += 1
            continue
        used.append(key)
        parsed = hit["parsed"] if isinstance(hit["parsed"], dict) else {}
        guess = str(parsed.get("asset", "")).strip().upper()
        gap = month_gap(parsed.get("year_month", ""), r.friday)
        rows.append((r.friday, r.base, guess == r.base.upper(), gap is not None and gap <= 6, guess, str(parsed.get("year_month", ""))))
    return pd.DataFrame(rows, columns=FLAG_COLUMNS), missing, used


def main(argv=None, root: Path | None = None, client=None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    common.add_week_args(ap)
    ap.add_argument("--cap", type=float, default=None)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args(argv)
    root = Path(root or common.ROOT)
    top, fridays, pilot = common.universe_weeks(args)
    if not pilot and not args.offline:
        common.require_frozen(root)
    prefix = "pilot_" if pilot else ""
    out = root / "data/compare"
    dossiers = pd.read_parquet(out / f"{prefix}dossiers.parquet")
    dossiers = dossiers[dossiers["friday"].isin(set(fridays))]
    tickers = sorted(charter5.test_universe(top)["base"].unique())
    model = client.model if client is not None else common.MODEL
    cache = CallCache(root / CACHE)
    state = {"failed": 0, "stopped": None, "calls": 0}
    if not args.offline:
        if args.cap is None:
            raise SystemExit("--cap is required for a run that may call the model")
        remaining = args.cap - cache.paid_usd
        if remaining <= 0:
            raise SystemExit(f"spend limit reached: {cache.paid_usd:.4f} of {args.cap}")
        client = client or common.make_client(remaining, args.workers, MAX_TOKENS)

        def one(r) -> None:
            prompt = probe_prompt(r.alias, r.text, tickers)
            key = call_key(model, SYSTEM, prompt)
            if cache.get(key) is not None or state["stopped"]:
                return
            try:
                parsed, meta = client.call(prompt, SCHEMA, schema_name="identification", system=SYSTEM, max_tokens=MAX_TOKENS)
            except SpendCapError:
                state["stopped"] = "spend_cap"
                return
            except ORError:
                state["failed"] += 1
                return
            keep = {k: meta.get(k) for k in ("provider", "cost", "prompt_tokens", "completion_tokens", "latency_s")}
            cache.put(key, {"parsed": parsed, "meta": keep, "role": "probe"})
            state["calls"] += 1

        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            list(pool.map(one, list(dossiers.itertuples(index=False))))
    table, missing, used = flags(dossiers, cache, model, tickers)
    cost = sum(float((cache.get(k).get("meta") or {}).get("cost") or 0.0) for k in used)
    report = {"pilot": pilot, "model": model, "prompt_sha256": prompt_sha256(), "dossiers": len(dossiers), "answered": len(table),
              "without_answer": missing, "new_calls": state["calls"], "failed_calls": state["failed"], "stopped": state["stopped"],
              "candidate_tickers": len(tickers), "chance": 1 / len(tickers),
              "identified_share": float(table["identified"].mean()) if len(table) else None,
              "month_within_6_share": float(table["month_within_6"].mean()) if len(table) else None,
              "cost_usd": cost, "per_dossier_usd": cost / max(len(table), 1), "cache_paid_usd": cache.paid_usd}
    if not pilot and not args.offline and (missing or state["stopped"]):
        print(json.dumps(report))
        raise SystemExit("probe incomplete: no flag table written; run again to resume")
    table.to_parquet(out / f"{prefix}flags.parquet", index=False)
    (out / f"{prefix}probe_report.json").write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps(report), flush=True)
    return report


if __name__ == "__main__":
    main()

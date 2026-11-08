"""Re-identification probe (plan §5.4 probe 1): can a model name the asset and the month
from an anonymized dossier? Target: asset accuracy <= 2x chance on the universe, month
within +-6 months <= 25%. Unregistered diagnostic; writes data/dossier/reid_probe.json.

Usage: dossier_reid_probe.py --n 300 [--seed 20261109]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tradingagents.dossier.builder import OUT  # noqa: E402
from tradingagents.dossier.universe import base_symbol  # noqa: E402
from tradingagents.dossier.or_client import StructuredClient  # noqa: E402
from llm_v2c0_client import load_api_key  # noqa: E402

SCHEMA = {"type": "object", "properties": {"asset": {"type": "string"}, "year_month": {"type": "string"},
                                           "confidence": {"type": "number"}},
          "required": ["asset", "year_month", "confidence"], "additionalProperties": False}
PROMPT = """The following is an anonymized research dossier about one crypto asset. Identify the real asset (ticker from the list) and the calendar month (YYYY-MM) the dossier was written in. Use any clue: numbers, events, phrasing. Return JSON {{"asset": ticker, "year_month": "YYYY-MM", "confidence": 0-1}}.

Candidate tickers: {tickers}

Dossier:
{text}"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--seed", type=int, default=20261109)
    args = ap.parse_args()
    files = sorted(OUT.glob("*/*.json"))
    rng = random.Random(args.seed)
    sample = rng.sample(files, min(args.n, len(files)))
    tickers = sorted({base_symbol(p.stem) for p in files})
    client = StructuredClient.pinned("pro", load_api_key(), cost_cap_usd=5.0)
    from tradingagents.dossier.or_client import ORError
    partial = Path("data/dossier/reid_probe_rows.jsonl")
    done = {}
    if partial.exists():
        for line in partial.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                done[row["file"]] = row
    results, failures = [], 0
    with partial.open("a") as out:
        for p in sample:
            if str(p) in done:
                results.append(done[str(p)])
                continue
            d = json.loads(p.read_text())
            text = PROMPT.format(tickers=", ".join(tickers), text=d["text"][:12000])
            try:
                guess, _ = client.call(text, SCHEMA, "reid")
            except ORError as exc:
                failures += 1
                print(f"skip {p.name}: {exc}", flush=True)
                continue
            row = {"file": str(p), "true_asset": d["base"], "true_month": d["friday"][:7],
                   "asset": str(guess.get("asset", "")), "year_month": str(guess.get("year_month", "")),
                   "confidence": guess.get("confidence")}
            results.append(row)
            out.write(json.dumps(row) + "\n")
            out.flush()
    if not results:
        print("no results")
        return 1
    df = pd.DataFrame(results)
    df["asset_hit"] = df["asset"].str.upper() == df["true_asset"].str.upper()
    tm = pd.to_datetime(df["true_month"]); gm = pd.to_datetime(df["year_month"], errors="coerce")
    df["month_within_6"] = (gm - tm).abs() <= pd.Timedelta(days=183)
    summary = {"n": len(df), "asset_accuracy": float(df["asset_hit"].mean()), "chance": 1 / len(tickers),
               "month_within_6_rate": float(df["month_within_6"].fillna(False).mean()),
               "spent_usd": client.spent_usd, "failures": failures}
    Path("data/dossier/reid_probe.json").write_text(json.dumps({"summary": summary, "rows": results}, indent=1))
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

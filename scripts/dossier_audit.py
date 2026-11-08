"""Dossier quality summary (plan §6.3 noise audit and coverage proxies). Reads built dossiers.

Usage: dossier_audit.py [--start 2022-01-01 --end 2024-12-31]
Writes data/dossier/audit_summary.json and prints the headline numbers.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tradingagents.dossier.builder import OUT  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2000-01-01")
    ap.add_argument("--end", default="2100-01-01")
    args = ap.parse_args()
    rows = []
    for day in sorted(OUT.iterdir()):
        if not (args.start <= day.name <= args.end):
            continue
        for p in day.glob("*.json"):
            d = json.loads(p.read_text())
            c = d["counts"]
            retrieved = c.get("retrieved", 0)
            noise = c.get("price_recap", 0) + c.get("promotional", 0) + c.get("unrelated", 0)
            rows.append({"friday": day.name, "symbol": d["symbol"], "retrieved": retrieved, "shown": len(d["items"]),
                         "events": c.get("event", 0), "analysis": c.get("analysis_opinion", 0), "noise": noise,
                         "reddit_items": sum(i["source"] == "reddit" for i in d["items"]),
                         "leaks": len(d["leaks"]), "chars": len(d["text"])})
    if not rows:
        print("no dossiers")
        return 1
    df = pd.DataFrame(rows)
    with_text = df[df["retrieved"] > 0]
    summary = {
        "dossiers": int(len(df)), "weeks": int(df["friday"].nunique()),
        "share_with_any_text": float((df["retrieved"] > 0).mean()),
        "share_with_shown_items": float((df["shown"] > 0).mean()),
        "items_shown_median": float(df["shown"].median()),
        "retrieved_median": float(df["retrieved"].median()),
        "noise_share_of_retrieved": float(with_text["noise"].sum() / max(1, with_text["retrieved"].sum())),
        "event_share_of_retrieved": float(with_text["events"].sum() / max(1, with_text["retrieved"].sum())),
        "reddit_share_of_shown": float(df["reddit_items"].sum() / max(1, df["shown"].sum())),
        "dossiers_with_leaks": int((df["leaks"] > 0).sum()),
        "tokens_median_est": float((df["chars"] // 4).median()),
        "by_year_share_with_shown": {str(k): float(v) for k, v in
                                     df.assign(y=df["friday"].str[:4]).groupby("y")["shown"].apply(lambda s: (s > 0).mean()).items()},
    }
    Path("data/dossier/audit_summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

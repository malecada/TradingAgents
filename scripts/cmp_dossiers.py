"""Text dossiers of the test weeks from the present material and the archive together (Charter 5).

Usage: cmp_dossiers.py [--pilot | --weeks ...] [--out data/compare]
Reads the link tables, the typings and the reader records of both stores; writes ``lines.parquet``,
``dossiers.parquet`` and ``dossier_report.json`` (with the prefix ``pilot_`` for pilot weeks). A dossier whose
rendered text still carries a name is left out and its asset counts as an asset without a dossier.
No model call, no outcome.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import cmp_common as common  # noqa: E402
from tradingagents.compare import charter5, dossier  # noqa: E402
from tradingagents.dossier.entities import build_dictionary  # noqa: E402
from tradingagents.dossier.universe import base_symbol, load_cards  # noqa: E402

ARCHIVE_SOURCE = "ccnews"


def build(items: pd.DataFrame, docs: pd.DataFrame, records: pd.DataFrame, top: pd.DataFrame, fridays, dictionary):
    """(lines, dossiers, report) of the given weeks."""
    sets = dossier.weekly_sets(items, docs, top, fridays)
    cands, counts = dossier.candidates(sets, records, docs)
    lines = dossier.line_table(cands)
    dossiers = dossier.build(lines, docs, dictionary)
    leaking = dossiers[dossiers["leaks"] > 0][["friday", "base"]]
    if len(leaking):
        keep = lines.merge(leaking.assign(_drop=True), on=["friday", "base"], how="left")["_drop"].isna().to_numpy()
        lines, dossiers = lines[keep].reset_index(drop=True), dossiers[dossiers["leaks"] == 0].reset_index(drop=True)
    weeks = top[top["date"].isin(set(fridays))]
    per_week = dossiers.groupby("friday")["base"].nunique().reindex(sorted(set(fridays)), fill_value=0)
    chars = dossiers["text"].str.len()
    report = {"weeks": len(per_week), "universe_rows": len(weeks), **counts, "lines": len(lines), "dossiers": len(dossiers),
              "dossier_share": len(dossiers) / len(weeks), "dossiers_dropped_for_a_name": len(leaking),
              "dossiers_per_week": {"min": int(per_week.min()), "median": float(per_week.median()), "max": int(per_week.max())},
              "weeks_below_minimum": int((per_week < charter5.MIN_WEEK_DOSSIERS).sum()),
              "lines_per_dossier": {"mean": float(dossiers["n_lines"].mean()), "median": float(dossiers["n_lines"].median())},
              "lead_report_source": {k: int(v) for k, v in lines["source"].value_counts().items()},
              "dossiers_with_an_archive_line": int(lines[lines["source"] == ARCHIVE_SOURCE].groupby(["friday", "base"]).ngroups),
              "chars": {"median": float(chars.median()), "mean": float(chars.mean()), "max": int(chars.max())}}
    return lines, dossiers, report


def main() -> int:
    ap = argparse.ArgumentParser()
    common.add_week_args(ap)
    ap.add_argument("--out", default="data/compare")
    args = ap.parse_args()
    top, fridays, pilot = common.universe_weeks(args)
    prefix = "pilot_" if pilot else ""
    items, docs, records = common.joined_tables(records=f"data/compare/{prefix}records.parquet")
    cards = load_cards()
    dictionary = build_dictionary(sorted({base_symbol(s) for s in cards["symbol"].unique()}))
    lines, dossiers, report = build(items, docs, records, top, fridays, dictionary)
    out = Path(args.out)
    lines.to_parquet(out / f"{prefix}lines.parquet", index=False)
    dossiers.to_parquet(out / f"{prefix}dossiers.parquet", index=False)
    (out / f"{prefix}dossier_report.json").write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps(report), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

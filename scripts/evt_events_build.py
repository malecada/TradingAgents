"""Build the event table of the event-time study from the text stores and the reader records. No price is read.

Step 1 (``--pub``, once): publication times to the second for the page-archive documents, by URL from the
raw news feed dump (outside the repository, CC-BY-NC-4.0, never committed) -> data/eventtime/pub_times.parquet.
Step 2: data/eventtime/events.parquet (every news record with its event clock and the lead flags) and
data/eventtime/events_report.json (counts only).
Usage: evt_events_build.py [--pub /path/to/news.csv]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tradingagents.compare.archive import to_utc
from tradingagents.eventtime import study

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/eventtime"
PAGE_STORE = ROOT / "data/dossier/text/wayback"
INPUTS = {"page_items": "data/reader/items.parquet", "page_records": "data/reader/records.parquet",
          "feed_items": "data/compare/items.parquet", "feed_records": "data/compare/records.parquet",
          "pub_times": "data/eventtime/pub_times.parquet"}
KLINES = ROOT / "data/xsect/klines_1m"


def build_pub_times(raw_csv: Path) -> pd.DataFrame:
    raw = pd.read_csv(raw_csv, usecols=["published_on", "url"])
    feed = pd.DataFrame({"url": raw["url"], "event_ts": to_utc(raw["published_on"])}).dropna()
    docs = set(pd.read_parquet(ROOT / INPUTS["page_records"], columns=["doc_id"])["doc_id"])
    pages = pd.concat([pd.read_parquet(p, columns=["doc_id", "url", "event_ts", "as_of_ts"])
                       for p in sorted(PAGE_STORE.glob("*/*.parquet"))], ignore_index=True)
    pages = pages[pages["doc_id"].isin(docs)].sort_values("as_of_ts").drop_duplicates("doc_id")
    for col in ("event_ts", "as_of_ts"):
        pages[col] = pd.to_datetime(pages[col], utc=True)
    pub = study.publication_times(pages, feed)
    return pub.dt.floor("s").rename("pub_ts").reset_index()


def load_events() -> pd.DataFrame:
    frames = {k: pd.read_parquet(ROOT / v) for k, v in INPUTS.items()}
    pub = frames["pub_times"].set_index("doc_id")["pub_ts"]
    events = study.event_table(frames["page_items"], frames["page_records"], frames["feed_items"], frames["feed_records"], pub)
    return study.mark_leads(events)


def report(events: pd.DataFrame) -> dict:
    window = events[(events["t0"] >= study.TEST_START) & (events["t0"] < study.TEST_END)]
    signed = window[window["sign"] != 0]
    gate = study.gate_set(events)
    has_bars = gate["base"].map(lambda b: study.symbol_file(KLINES, b) is not None)
    lead = gate[has_bars]
    per_day = lead.groupby(lead["t0"].dt.floor("D")).size()
    return {
        "news_records": len(events), "records_in_test_window": len(window),
        "signed_in_test_window": len(signed),
        "signed_by_clock": {str(k): int(v) for k, v in signed["clock"].value_counts().items()},
        "signed_by_clock_and_source": {f"{c}/{s}": int(v) for (c, s), v in signed.groupby(["clock", "source"]).size().items()},
        "lead_events_gate_set": len(gate), "lead_events_with_minute_bars": len(lead),
        "lead_events_without_bars_by_asset": {str(k): int(v) for k, v in gate[~has_bars]["base"].value_counts().head(15).items()},
        "lead_by_year": {str(k): int(v) for k, v in lead["t0"].dt.year.value_counts().sort_index().items()},
        "lead_by_sign": {str(k): int(v) for k, v in lead["sign"].value_counts().items()},
        "lead_by_source": {str(k): int(v) for k, v in lead["source"].value_counts().items()},
        "lead_fresh": int(lead["fresh"].sum()), "lead_materiality": {str(k): int(v) for k, v in lead["materiality"].value_counts().sort_index().items()},
        "lead_assets": int(lead["base"].nunique()), "lead_top_assets": {str(k): int(v) for k, v in lead["base"].value_counts().head(10).items()},
        "lead_days": len(per_day), "lead_per_day_median": float(per_day.median()) if len(per_day) else None,
        "lead_with_following": int((lead["n_following"] > 0).sum()), "lead_with_opposed": int((lead["n_opposed"] > 0).sum()),
        "lead_hour_utc": {str(k): int(v) for k, v in lead["t0"].dt.hour.value_counts().sort_index().items()},
        "lead_event_class": {str(k): int(v) for k, v in lead["event_class"].value_counts().items()},
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pub", help="raw news feed dump (news.csv); builds pub_times.parquet when given")
    args = ap.parse_args(argv)
    OUT.mkdir(parents=True, exist_ok=True)
    if args.pub:
        target = ROOT / INPUTS["pub_times"]
        if target.exists():
            raise SystemExit(f"{target} exists; publication times are built once")
        pub = build_pub_times(Path(args.pub))
        pub.to_parquet(target, index=False)
        print(f"publication times: {len(pub)} page-archive documents")
    events = load_events()
    events.to_parquet(OUT / "events.parquet", index=False)
    rep = report(events)
    (OUT / "events_report.json").write_text(json.dumps(rep, indent=1) + "\n")
    print(json.dumps(rep, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

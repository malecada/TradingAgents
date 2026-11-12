"""Coverage of the reading list on the weekly top-50 universe. No outcome, no LLM call.

Prints table sizes, how many asset-weeks have text, the reader work list (typed event and opinion documents
that name a universe asset in their summary) and a cost estimate at the on-demand Flash price.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tradingagents.dossier.builder import REDDIT_CAP, TEXT_LOOKBACK_DAYS  # noqa: E402
from tradingagents.dossier.universe import load_cards, weekly_top  # noqa: E402

READ_TYPES = ("event", "analysis_opinion")
PRICE_IN, PRICE_OUT = 0.05, 0.20            # $ per million tokens, Flash on demand
PROMPT_TOKENS, RECORD_TOKENS = 450, 70       # reader instruction; one output record


def load(out: Path, parts: bool) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not parts:
        return pd.read_parquet(out / "items.parquet"), pd.read_parquet(out / "docs.parquet")
    items = pd.concat([pd.read_parquet(p) for p in sorted((out / "parts").glob("items-*.parquet"))], ignore_index=True)
    docs = pd.concat([pd.read_parquet(p) for p in sorted((out / "parts").glob("docs-*.parquet"))], ignore_index=True)
    return items.drop_duplicates(["doc_id", "base"]), docs.drop_duplicates("doc_id")


def summary_assets(alias_map: str) -> list[str]:
    return sorted({v.split(":", 1)[1] for v in json.loads(alias_map).values() if v.startswith("asset:")})


def quantiles(x: pd.Series) -> str:
    q = x.quantile([0.25, 0.5, 0.75, 0.9]).tolist()
    return f"mean {x.mean():.1f}, q25 {q[0]:.0f}, median {q[1]:.0f}, q75 {q[2]:.0f}, q90 {q[3]:.0f}, max {x.max():.0f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/reader")
    ap.add_argument("--start", default="2022-01-01")
    ap.add_argument("--end", default="2024-12-31")
    ap.add_argument("--parts", action="store_true", help="read the month parts (build still running)")
    args = ap.parse_args()
    items, docs = load(Path(args.out), args.parts)
    top = weekly_top(load_cards(), 50, args.start, args.end)
    fridays = sorted(top["date"].unique())
    print(f"items {len(items):,} rows, {items.doc_id.nunique():,} documents; typed documents {len(docs):,}; leaky {int(docs.leaky.sum())}")
    print(items.groupby("source").agg(rows=("doc_id", "size"), docs=("doc_id", "nunique"), typed_rows=("typed", "sum")).to_string())
    print("typed documents by type:", docs["type"].value_counts().to_dict())
    lag = (items.drop_duplicates("doc_id").as_of_ts - items.drop_duplicates("doc_id").event_ts).dt.total_seconds() / 86400
    print(f"capture lag in days: median {lag.median():.2f}, q90 {lag.quantile(0.9):.2f}, share above 2 days {float((lag > 2).mean()):.3f}")

    docs = docs.assign(assets=docs.alias_map.map(summary_assets))
    pairs = docs[docs["type"].isin(READ_TYPES)][["doc_id", "type", "assets", "summary"]].explode("assets").dropna(subset=["assets"])
    pairs = pairs.rename(columns={"assets": "base"})
    items = items.merge(pairs[["doc_id", "base"]].assign(in_summary=True), on=["doc_id", "base"], how="left")
    items["in_summary"] = items["in_summary"].fillna(False).astype(bool)
    # a summary that names no asset token is read for the asset it was filed under, when that asset is the only primary link
    primaries = items[items.salience == "primary"].groupby("doc_id").base.size().rename("n_primary")
    tokens = docs.set_index("doc_id").assets.map(len).rename("n_tokens")
    items = items.join(primaries, on="doc_id").join(tokens, on="doc_id")
    items["focus_only"] = (items.salience == "primary") & (items.n_primary == 1) & (items.n_tokens == 0)
    items["read"] = items["type"].isin(READ_TYPES) & (items["in_summary"] | items["focus_only"])

    ev, asof = items.event_ts, items.as_of_ts
    rows, units, capped_ok, capped_n = [], set(), 0, 0
    for friday in fridays:
        dec = pd.Timestamp(friday) + pd.Timedelta(days=1)
        members = set(top.loc[top["date"] == friday, "base"])
        lo30, lo7 = dec - pd.Timedelta(days=TEXT_LOOKBACK_DAYS), dec - pd.Timedelta(days=7)
        win = items[(ev >= lo30) & (ev <= dec) & (asof <= dec) & items.base.isin(members)]
        last7 = win.event_ts >= lo7
        news = win.source != "reddit"
        g = pd.DataFrame({
            "all_7d": win[last7].groupby("base").size(),
            "all_30d": win.groupby("base").size(),
            "news_7d": win[last7 & news].groupby("base").size(),
            "reddit_7d": win[last7 & ~news].groupby("base").size(),
            "read_news_7d": win[last7 & news & win.read].groupby("base").size(),
            "read_news_30d": win[news & win.read].groupby("base").size(),
            "read_any_7d": win[last7 & win.read].groupby("base").size(),
            "read_any_30d": win[win.read].groupby("base").size(),
        }).reindex(sorted(members)).fillna(0)
        g.insert(0, "friday", friday)
        rows.append(g.reset_index(names="base"))
        units.update(map(tuple, win.loc[win.read, ["doc_id", "base", "focus_only"]].to_numpy()))
        # the dossier rule for community posts: the newest REDDIT_CAP primary posts per asset and week were typed
        red = win[~news & (win.salience == "primary")].sort_values("event_ts", ascending=False).groupby("base").head(REDDIT_CAP)
        capped_ok, capped_n = capped_ok + int(red.typed.sum()), capped_n + len(red)
    panel = pd.concat(rows, ignore_index=True)
    n = len(panel)
    print(f"\nasset-weeks {n:,} over {len(fridays)} Fridays ({pd.Timestamp(fridays[0]).date()} to {pd.Timestamp(fridays[-1]).date()})")
    for col in panel.columns[2:]:
        print(f"  {col:14s} share with any {float((panel[col] > 0).mean()):.3f}; {quantiles(panel[col])}")
    weekly = panel.assign(has=panel.read_any_7d > 0).groupby("friday").has.sum()
    print(f"  assets per week with a readable item in 7 days: min {weekly.min()}, median {weekly.median():.0f}, max {weekly.max()}")
    yearly = panel.assign(year=pd.to_datetime(panel.friday).dt.year).groupby("year")[["all_7d", "news_7d", "reddit_7d", "read_news_7d", "read_any_7d"]].mean().round(1)
    print(yearly.to_string())
    print(f"  dossier rule check: {capped_ok:,} of {capped_n:,} newest-{REDDIT_CAP} primary community posts are typed ({capped_ok / max(1, capped_n):.3f})")
    news_win = items[(items.source != "reddit")]
    print(f"  news rows typed: {float(news_win.typed.mean()):.3f} of all linked news rows")

    unit_frame = pd.DataFrame(sorted(units), columns=["doc_id", "base", "focus_only"]).merge(docs[["doc_id", "type", "summary"]], on="doc_id")
    print(f"\nrecords read for the filed asset because the summary names no asset token: {int(unit_frame.focus_only.sum()):,}")
    unit_frame = unit_frame.merge(items[["doc_id", "source"]].drop_duplicates("doc_id"), on="doc_id")
    per_doc = unit_frame.groupby("doc_id").agg(assets=("base", "size"), chars=("summary", lambda s: len(s.iloc[0])), source=("source", "first"), type=("type", "first"))
    print(f"reader work list: {len(per_doc):,} documents, {len(unit_frame):,} (document, asset) records")
    print(per_doc.groupby(["source", "type"]).agg(docs=("assets", "size"), records=("assets", "sum"), mean_chars=("chars", "mean")).round(0).to_string())
    tok_in = (PROMPT_TOKENS + per_doc.chars / 4).sum()
    tok_out = (per_doc.assets * RECORD_TOKENS).sum()
    one = tok_in * PRICE_IN / 1e6 + tok_out * PRICE_OUT / 1e6
    print(f"one reader pass: {tok_in / 1e6:.1f} M tokens in, {tok_out / 1e6:.1f} M out, ${one:.2f} (${one / len(per_doc):.6f} per document)")
    for rate in (0.2, 0.35, 0.5):
        print(f"  two readers and adjudication on {rate:.0%} of documents: ${one * (2 + 1.6 * rate):.2f}")
    unit_frame.drop(columns=["summary"]).to_parquet(Path(args.out) / "work_list.parquet", index=False)
    panel.to_parquet(Path(args.out) / "coverage_panel.parquet", index=False)


if __name__ == "__main__":
    main()

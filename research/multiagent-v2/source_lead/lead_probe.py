"""Which sources carry an asset before its news article? Text time stamps only; no price is read.

For every gate event of the event-time study (an asset-specific news record at the publication time t0 of its
article) the items of a source that name the same asset are counted in windows around t0. The same counts at
placebo times of the same asset (t0 shifted by whole weeks) give the rate expected without the event. A source
"leads" when it shows more items than the placebo in the windows before t0.

Sources: stored Reddit posts, all stored news items (any type and clock, the event's own document excluded),
Binance announcement titles, and any further table `<extra>/<name>.parquet` with the columns `base`, `ts`
(and optionally `doc_id`).
Usage: lead_probe.py <out.json> [--extra DIR]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tradingagents.eventtime import study

KLINES = ROOT / "data/xsect/klines_1m"
BINS_H = [(-48, -24), (-24, -4), (-4, -1), (-1, -0.25), (-0.25, 0), (0, 0.25), (0.25, 1), (1, 4), (4, 24), (24, 48)]
PLACEBO_WEEKS = (-4, -3, -2, -1, 1, 2, 3, 4)
QUOTES = {"USDT", "BUSD", "USDC", "FDUSD", "TUSD", "BTC", "ETH", "BNB", "TRY", "EUR", "BRL", "DAI", "USD", "GBP",
          "AUD", "RUB", "UAH", "BIDR", "JPY", "ARS", "MXN", "PLN", "RON", "ZAR", "IDRT", "NGN", "VAI", "AEUR", "USDP", "UST"}
BN_NAMES = {48: "listing", 161: "delisting", 128: "airdrop", 157: "maintenance", 49: "news"}


def gate_events() -> pd.DataFrame:
    events = pd.read_parquet(ROOT / "data/eventtime/events.parquet")
    g = study.gate_set(events)
    g = g[g["base"].map(lambda b: study.symbol_file(KLINES, b) is not None)]
    return g[["doc_id", "base", "t0", "event_class", "source", "sign"]].reset_index(drop=True)


def news_items() -> pd.DataFrame:
    """Every stored news item (any type) with the same clock rule as the event table."""
    pub = pd.read_parquet(ROOT / "data/eventtime/pub_times.parquet").set_index("doc_id")["pub_ts"]
    page = pd.read_parquet(ROOT / "data/reader/items.parquet", columns=["doc_id", "base", "source", "event_ts", "as_of_ts"])
    page = page[page["source"] == "wayback"].copy()
    page["ts"] = pd.to_datetime(page["doc_id"].map(pub), utc=True).fillna(pd.to_datetime(page["as_of_ts"], utc=True))
    feed = pd.read_parquet(ROOT / "data/compare/items.parquet", columns=["doc_id", "base", "source", "event_ts", "as_of_ts"])
    ev, asof = pd.to_datetime(feed["event_ts"], utc=True), pd.to_datetime(feed["as_of_ts"], utc=True)
    feed["ts"] = ev.where((asof - ev) <= study.LIVE_LAG, asof)
    return pd.concat([page, feed], ignore_index=True)[["doc_id", "base", "ts"]].drop_duplicates(["doc_id", "base"])


def reddit_items() -> pd.DataFrame:
    d = pd.read_parquet(ROOT / "data/reader/items.parquet", columns=["doc_id", "base", "source", "as_of_ts"])
    d = d[d["source"] == "reddit"]
    return pd.DataFrame({"doc_id": d["doc_id"], "base": d["base"], "ts": pd.to_datetime(d["as_of_ts"], utc=True)})


def binance_items(bases: set[str]) -> pd.DataFrame:
    rows = []
    for path in sorted((ROOT / "data/source_audit/binance").glob("*.jsonl")):
        rows += [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    ann = pd.DataFrame(rows).drop_duplicates("id")
    ann["ts"] = pd.to_datetime(ann["release_ms"], unit="ms", utc=True)

    def tickers(title: str) -> list[str]:
        found = set()
        for tok in re.findall(r"[A-Z0-9]{2,12}", title):
            cands = [tok] + [tok[: -len(q)] for q in QUOTES if tok.endswith(q) and len(tok) > len(q) + 1]
            for c in cands:
                c = re.sub(r"^1000+", "", c)
                if c in bases and c not in QUOTES:
                    found.add(c)
        for m in ("ETH", "BNB"):
            if re.search(rf"\b{m}\b(?!\s*/)(?!-)", title) and not re.search(r"/\s*" + m, title) and m in bases:
                found.add(m)
        return sorted(found)

    ann["base"] = ann["title"].map(tickers)
    out = ann.explode("base").dropna(subset=["base"])
    out["kind"] = out["catalog"].map(BN_NAMES)
    return out.rename(columns={"id": "doc_id"})[["doc_id", "base", "ts", "kind", "title"]]


def counts(events: pd.DataFrame, items: pd.DataFrame, shift_weeks: int = 0) -> np.ndarray:
    """Items of the event's asset per bin, own document excluded. Shape (events, bins)."""
    out = np.zeros((len(events), len(BINS_H)), dtype=float)
    naive = lambda s: pd.DatetimeIndex(s).tz_convert("UTC").tz_localize(None).to_numpy().astype("datetime64[ns]")
    by_base = {b: (naive(g["ts"]), g["doc_id"].astype(str).to_numpy()) for b, g in items.sort_values("ts").groupby("base")}
    t_all = naive(events["t0"] + pd.Timedelta(weeks=shift_weeks))
    for i, (base, doc, t0) in enumerate(zip(events["base"], events["doc_id"].astype(str), t_all)):
        if base not in by_base:
            continue
        ts, docs = by_base[base]
        for j, (a, b) in enumerate(BINS_H):
            lo = np.searchsorted(ts, t0 + np.timedelta64(int(a * 3600e9), "ns"), side="left")
            hi = np.searchsorted(ts, t0 + np.timedelta64(int(b * 3600e9), "ns"), side="left")
            n = hi - lo
            if n and shift_weeks == 0:
                n -= int((docs[lo:hi] == doc).sum())
            out[i, j] = n
    return out


def profile(events: pd.DataFrame, items: pd.DataFrame) -> dict:
    span = (items["ts"].min(), items["ts"].max())
    day = events["t0"].dt.floor("D").to_numpy()
    real = counts(events, items)
    shifted = [counts(events, items, w) for w in PLACEBO_WEEKS]
    placebo = np.mean(shifted, axis=0)
    placebo_log = np.mean([np.log1p(c) for c in shifted], axis=0)
    width = np.array([b - a for a, b in BINS_H])
    rows = {}
    for j, (a, b) in enumerate(BINS_H):
        rate_real, rate_placebo = float(real[:, j].mean() / width[j]), float(placebo[:, j].mean() / width[j])
        excess = study.clustered(real[:, j] - placebo[:, j], day)                    # paired, clustered by day
        # robust to a few very active assets: log(1 + count) against the mean log(1 + count) of the placebo weeks
        logx = study.clustered(np.log1p(real[:, j]) - placebo_log[:, j], day)
        rows[f"{a:g}..{b:g}h"] = {
            "items_per_hour": round(rate_real, 4), "placebo_per_hour": round(rate_placebo, 4),
            "ratio": round(rate_real / rate_placebo, 2) if rate_placebo > 0 else None,
            "excess_t": None if excess["t"] is None else round(excess["t"], 2),
            "log_excess": None if logx["mean"] is None else round(logx["mean"], 4),
            "log_excess_t": None if logx["t"] is None else round(logx["t"], 2),
            "share_events_with_item": round(float((real[:, j] > 0).mean()), 4),
            "share_placebo": round(float(np.mean([(c[:, j] > 0).mean() for c in shifted])), 4)}

    def any_before(c: np.ndarray, hours: float) -> float:
        cols = [k for k, (a, b) in enumerate(BINS_H) if b <= 0 and a >= -hours]
        return float((c[:, cols].sum(axis=1) > 0).mean())

    return {"items": len(items), "assets": int(items["base"].nunique()),
            "span": [str(span[0])[:10], str(span[1])[:10]], "events": len(events),
            "share_events_item_in_4h_before": round(any_before(real, 4), 4),
            "placebo_4h": round(float(np.mean([any_before(c, 4) for c in shifted])), 4),
            "share_events_item_in_24h_before": round(any_before(real, 24), 4),
            "placebo_24h": round(float(np.mean([any_before(c, 24) for c in shifted])), 4),
            "bins": rows}


def listing_leads(events: pd.DataFrame, bn: pd.DataFrame) -> dict:
    """Articles of the listing and delisting classes against the Binance announcement that names the asset."""
    out = {}
    for cls, kind in (("exchange_listing", "listing"), ("exchange_delisting", "delisting")):
        ev = events[events["event_class"] == cls]
        ann = bn[bn["kind"] == kind]
        leads = []
        for base, t0 in zip(ev["base"], ev["t0"]):
            cand = ann[(ann["base"] == base) & ((ann["ts"] - t0).abs() <= pd.Timedelta(hours=72))]
            if len(cand):
                d = (t0 - cand["ts"]).dt.total_seconds() / 60.0
                leads.append(float(d.iloc[d.abs().argmin()]))           # minutes; positive: announcement first
        leads = np.array(leads)
        out[cls] = {"articles": len(ev), "with_binance_announcement_within_72h": len(leads),
                    "announcement_first_share": round(float((leads > 0).mean()), 3) if len(leads) else None,
                    "lead_minutes_quantiles_10_25_50_75_90": [round(float(q), 1) for q in np.quantile(leads, [.1, .25, .5, .75, .9])] if len(leads) else None,
                    "article_within_15_min_after": round(float(((leads > 0) & (leads <= 15)).mean()), 3) if len(leads) else None,
                    "article_within_60_min_after": round(float(((leads > 0) & (leads <= 60)).mean()), 3) if len(leads) else None}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("out")
    ap.add_argument("--extra", help="directory of further source tables (base, ts[, doc_id]) as parquet")
    args = ap.parse_args(argv)
    events = gate_events()
    bases = set(events["base"])
    bn = binance_items(bases)
    sources = {"news_all_stored": news_items(), "reddit_three_forums": reddit_items(),
               "binance_announcements": bn[["doc_id", "base", "ts"]]}
    if args.extra:
        for path in sorted(Path(args.extra).glob("*.parquet")):
            extra = pd.read_parquet(path)
            extra["ts"] = pd.to_datetime(extra["ts"], utc=True)
            if "doc_id" not in extra:
                extra["doc_id"] = [f"{path.stem}:{i}" for i in range(len(extra))]
            sources[path.stem] = extra[["doc_id", "base", "ts"]]
    out = {"events": len(events), "bins_hours": BINS_H, "placebo_weeks": PLACEBO_WEEKS,
           "note": "text time stamps only; no price is read",
           "sources": {}}
    for name, items in sources.items():
        items = items[items["base"].isin(bases)].dropna(subset=["ts"])
        window = events[(events["t0"] >= items["ts"].min() + pd.Timedelta(weeks=5)) & (events["t0"] <= items["ts"].max() - pd.Timedelta(weeks=5))]
        out["sources"][name] = profile(window, items)
        print(name, json.dumps({k: v for k, v in out["sources"][name].items() if k != "bins"}))
    out["binance_listing_leads"] = listing_leads(events, bn)
    Path(args.out).write_text(json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

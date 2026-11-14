"""Audit of a public multi-outlet crypto news archive against the Charter 4 universe (no outcome column is read).

Usage: python -I agg_news_audit.py <repo root> <news.csv> <panel.parquet> <out.json>   (run from the repo root)
The archive is the Hugging Face dataset maryamfakhari/crypto-news-coindesk-2020-2025 (CoinDesk Data news feed).
Only `date` and `base` of the panel are read. The stored Wayback articles are joined by URL to compare times.
The archive states `published_on` in Iran local time; it is converted to UTC with the Asia/Tehran rules.
"""
import glob, json, re, sys
sys.path.insert(0, sys.argv[1])
import numpy as np
import pandas as pd
from urllib.parse import urlsplit
from tradingagents.dossier.entities import build_dictionary
from tradingagents.dossier.universe import base_symbol, load_cards
from tradingagents.reader.items import FastLinker

news = pd.read_csv(sys.argv[2], usecols=["id", "published_on", "title", "body", "url", "categories", "source"], low_memory=False)
naive = pd.to_datetime(news["published_on"], errors="coerce")
news["ts_naive"] = naive.dt.tz_localize("UTC")
news["ts"] = naive.dt.tz_localize("Asia/Tehran", ambiguous="NaT", nonexistent="shift_forward").dt.tz_convert("UTC")
news = news[news["ts"].notna()]
out = {"rows": int(len(news)), "first_utc": str(news["ts"].min()), "last_utc": str(news["ts"].max())}
w = news[(news["ts"] >= "2022-01-01") & (news["ts"] < "2025-01-01")].copy()
w["body_chars"] = w["body"].fillna("").str.len()
out["window_rows"] = int(len(w)); out["per_day"] = round(len(w) / 1096, 1)
out["by_year"] = {str(k): int(v) for k, v in w["ts"].dt.year.value_counts().sort_index().items()}
out["sources_by_year"] = {str(k): int(v) for k, v in w.groupby(w["ts"].dt.year)["source"].nunique().items()}
src = w["source"].value_counts()
out["sources"] = int(src.size); out["top_sources"] = {k: int(v) for k, v in src.head(20).items()}
have = {"cointelegraph", "coindesk", "theblock"}
out["share_from_outlets_already_in_store"] = round(float(w["source"].isin(have).mean()), 3)
out["body_chars"] = {str(q): int(w["body_chars"].quantile(q)) for q in (0.1, 0.25, 0.5, 0.75, 0.9)}
out["title_only_share"] = round(float((w["body_chars"] < 100).mean()), 3)
out["publication_hour_utc_share"] = {f"{a:02d}-{b:02d}": round(float(w["ts"].dt.hour.between(a, b).mean()), 3) for a, b in ((0, 5), (6, 11), (12, 17), (18, 23))}

# ingestion order: a record published long before its neighbours in id order was added late (backfilled)
o = w.sort_values("id")
sec = o["ts"].astype("int64") // 10**9
med = sec.rolling(201, center=True, min_periods=50).median()
late = (med - sec) / 3600
out["ingestion_order"] = {"share_published_over_1h_before_id_neighbours": round(float((late > 1).mean()), 4),
                          "share_over_24h": round(float((late > 24).mean()), 4), "share_over_7d": round(float((late > 168).mean()), 4)}
tags = w["categories"].fillna("").map(lambda s: set(s.split("|")))
out["share_tagged_btc_or_eth"] = round(float(tags.map(lambda t: bool(t & {"BTC", "ETH"})).mean()), 4)

panel = pd.read_parquet(sys.argv[3], columns=["date", "base"])
panel["date"] = pd.to_datetime(panel["date"], utc=True)
test = panel[panel["date"] >= "2023-01-01"].copy()
bases = set(panel["base"].unique()); norm = {re.sub(r"^1000+", "", b): b for b in bases}
out["test_days"] = int(test["date"].nunique())

def coverage(sub, label, days=1):
    """sub: base, ts. An item counts for decision date d when d - days <= ts < d."""
    d0 = sub["ts"].dt.normalize() + pd.Timedelta(days=1)
    key = set()
    for k in range(days):
        key |= set(zip(sub["base"], d0 + pd.Timedelta(days=k)))
    hit = pd.Series([(b, d) in key for b, d in zip(test["base"], test["date"])], index=test.index)
    per_asset = hit.groupby(test["base"]).mean(); per_day = hit.groupby(test["date"]).sum()
    others = per_asset.drop(labels=[b for b in ("BTC", "ETH") if b in per_asset.index])
    by_year = hit.groupby(test["date"].dt.year).mean()
    return {"label": label, "window_days": days, "share_asset_days": round(float(hit.mean()), 4),
            "share_asset_days_by_year": {str(k): round(float(v), 4) for k, v in by_year.items()},
            "BTC": round(float(per_asset.get("BTC", 0)), 3), "ETH": round(float(per_asset.get("ETH", 0)), 3),
            "other_assets_median": round(float(others.median()), 4), "other_assets_q75": round(float(others.quantile(0.75)), 4),
            "other_assets_q90": round(float(others.quantile(0.9)), 4),
            "assets_total": int(per_asset.size), "assets_with_none": int((per_asset == 0).sum()),
            "assets_on_5pct_of_days": int((per_asset >= 0.05).sum()), "assets_on_25pct_of_days": int((per_asset >= 0.25).sum()),
            "median_assets_per_day_of_50": float(per_day.median())}

# (a) the archive's own asset tags
w["tag_bases"] = tags.map(lambda t: sorted({norm[x] for x in t if x in norm}))
tag = w.explode("tag_bases").dropna(subset=["tag_bases"]).rename(columns={"tag_bases": "base"})[["base", "ts", "source"]]
# (b) the project's alias dictionary on title and body, as for the stored articles
cards = load_cards()
linker = FastLinker(build_dictionary(sorted({base_symbol(s) for s in cards["symbol"].unique()})))
links = [linker.link_assets(str(t), str(b)) for t, b in zip(w["title"].fillna(""), w["body"].fillna(""))]
w["n_links"] = [len(x) for x in links]
rows = [(i, b, s) for i, x in zip(w.index, links) for b, s in x]
al = pd.DataFrame(rows, columns=["i", "base", "salience"]).join(w[["ts", "source"]], on="i")
out["alias_linking"] = {"share_articles_linked": round(float((w["n_links"] > 0).mean()), 3),
                        "share_linked_beyond_btc_eth": round(float(al[~al["base"].isin(["BTC", "ETH"])]["i"].nunique() / len(w)), 3),
                        "share_primary_beyond_btc_eth": round(float(al[(~al["base"].isin(["BTC", "ETH"])) & (al["salience"] == "primary")]["i"].nunique() / len(w)), 3)}
# (c) the present reading list (three outlets and three subreddits), same rule, time of first capture
items = pd.read_parquet("data/reader/items.parquet", columns=["doc_id", "base", "source", "as_of_ts", "salience"])
items["ts"] = pd.to_datetime(items["as_of_ts"], utc=True)
st_news = items[items["source"] == "wayback"]
new = al[~al["source"].isin(have)]
out["coverage"] = [
    coverage(st_news, "present store, news, any link"),
    coverage(st_news[st_news["salience"] == "primary"], "present store, news, primary"),
    coverage(items, "present store, news and posts, any link"),
    coverage(tag, "archive, own tags"),
    coverage(al, "archive, alias link"),
    coverage(al[al["salience"] == "primary"], "archive, alias primary"),
    coverage(pd.concat([st_news[["base", "ts"]], new[["base", "ts"]]]), "present news plus archive outlets not in the store, any link"),
    coverage(pd.concat([st_news.loc[st_news["salience"] == "primary", ["base", "ts"]], new.loc[new["salience"] == "primary", ["base", "ts"]]]),
             "present news plus archive outlets not in the store, primary"),
    coverage(st_news, "present store, news, any link", days=7),
    coverage(pd.concat([st_news[["base", "ts"]], new[["base", "ts"]]]), "present news plus archive outlets not in the store, any link", days=7),
    coverage(pd.concat([st_news.loc[st_news["salience"] == "primary", ["base", "ts"]], new.loc[new["salience"] == "primary", ["base", "ts"]]]),
             "present news plus archive outlets not in the store, primary", days=7),
]
prim = al[(al["salience"] == "primary") & ~al["source"].isin(have)]
out["new_documents_to_read"] = {"all_from_new_outlets": int((~w["source"].isin(have)).sum()),
                                "linked_to_a_universe_asset": int(new["i"].nunique()),
                                "primary_for_an_asset_other_than_btc_eth": int(prim[~prim["base"].isin(["BTC", "ETH"])]["i"].nunique())}

# comparison of times with the stored Wayback articles (same URL)
def canon(u):
    p = urlsplit(str(u)); return (p.netloc.lower().removeprefix("www.") + p.path.rstrip("/")).lower()
store = pd.concat([pd.read_parquet(p, columns=["outlet", "url", "event_ts", "as_of_ts"]) for p in sorted(glob.glob("data/dossier/text/wayback/202[234]/*.parquet"))])
store["key"] = store["url"].map(canon); w["key"] = w["url"].map(canon)
j = store.merge(w[["key", "ts", "ts_naive"]].drop_duplicates("key"), on="key", how="inner")
cap = pd.to_datetime(j["as_of_ts"], utc=True)
lag = (cap - j["ts"]).dt.total_seconds() / 3600
raw = (cap - j["ts_naive"]).dt.total_seconds() / 3600
half = cap.dt.year.astype(str) + "H" + ((cap.dt.month > 6) + 1).astype(str)
out["store_join"] = {"store_articles": int(len(store)), "matched": int(len(j)), "matched_by_outlet": {k: int(v) for k, v in j["outlet"].value_counts().items()},
                     "floor_q01_hours_if_read_as_utc": {k: round(float(v), 2) for k, v in raw.groupby(half).quantile(0.01).items()},
                     "floor_q01_hours_after_conversion": {k: round(float(v), 2) for k, v in lag.groupby(half).quantile(0.01).items()},
                     "hours_publication_to_first_capture": {str(q): round(float(lag.quantile(q)), 2) for q in (0.1, 0.25, 0.5, 0.75, 0.9)},
                     "by_outlet_median": {k: round(float(v), 2) for k, v in lag.groupby(j["outlet"]).median().items()},
                     "share_capture_before_stated_publication": round(float((lag < -0.25).mean()), 4),
                     "share_captured_within_1h": round(float(lag.between(-0.25, 1).mean()), 3), "share_within_6h": round(float(lag.between(-0.25, 6).mean()), 3),
                     "share_within_24h": round(float(lag.between(-0.25, 24).mean()), 3)}
json.dump(out, open(sys.argv[4], "w"), indent=1)
print(json.dumps(out, indent=1))

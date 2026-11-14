"""Monthly floor of first capture minus stated publication for the archive, as UTC and after the Asia/Tehran conversion.

Usage: python -I agg_news_tz.py <news.csv> <out.json>   (run from the repo root; reads the stored Wayback articles)
"""
import glob, json, sys
import pandas as pd
from urllib.parse import urlsplit
news = pd.read_csv(sys.argv[1], usecols=["published_on", "url"], low_memory=False)
naive = pd.to_datetime(news["published_on"], errors="coerce")
news["ts_naive"] = naive.dt.tz_localize("UTC")
news["ts"] = naive.dt.tz_localize("Asia/Tehran", ambiguous="NaT", nonexistent="shift_forward").dt.tz_convert("UTC")
def canon(u):
    p = urlsplit(str(u)); return (p.netloc.lower().removeprefix("www.") + p.path.rstrip("/")).lower()
news["key"] = news["url"].map(canon)
store = pd.concat([pd.read_parquet(p, columns=["url", "as_of_ts"]) for p in sorted(glob.glob("data/dossier/text/wayback/202[234]/*.parquet"))])
store["key"] = store["url"].map(canon)
j = store.merge(news.dropna(subset=["ts"]).drop_duplicates("key"), on="key")
cap = pd.to_datetime(j["as_of_ts"], utc=True)
m = cap.dt.strftime("%Y-%m")
raw = (cap - j["ts_naive"]).dt.total_seconds() / 3600
lag = (cap - j["ts"]).dt.total_seconds() / 3600
t = pd.DataFrame({"n": raw.groupby(m).size(), "floor_as_utc": raw.groupby(m).quantile(0.01).round(2), "floor_converted": lag.groupby(m).quantile(0.01).round(2),
                  "median_converted": lag.groupby(m).median().round(2)})
print(t.to_string())
json.dump({k: {"n": int(r["n"]), "floor_as_utc": float(r["floor_as_utc"]), "floor_converted": float(r["floor_converted"]), "median_converted": float(r["median_converted"])}
           for k, r in t.iterrows()}, open(sys.argv[2], "w"), indent=1)

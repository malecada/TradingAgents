"""Time of day of publication in a sample of the stored first captures (no outcome, no model call).

Usage: python pubtime_probe.py <out.json> [n_per_outlet]
For a seeded sample of stored news articles of 2023-2024 the first capture is fetched again and the
schema.org / Open Graph publication and modification times are read. Output: hours from publication to
capture and from publication to the last modification recorded in that capture.
"""
import glob, json, re, sys, time
import pandas as pd, requests

UA = "Mozilla/5.0 (X11; Linux x86_64) research-probe/0.1"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 30
news = pd.concat([pd.read_parquet(p, columns=["outlet", "url", "event_ts", "as_of_ts"]) for p in sorted(glob.glob("data/dossier/text/wayback/202[34]/*.parquet"))])
sample = news.groupby("outlet").sample(N, random_state=11)
LD = re.compile(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', re.S)
META = re.compile(r'<meta[^>]+(?:property|name)="(article:published_time|article:modified_time|og:updated_time)"[^>]+content="([^"]+)"', re.I)

def times(html):
    pub = mod = None
    for m in LD.finditer(html):
        try:
            data = json.loads(m.group(1).strip())
        except ValueError:
            continue
        objs = data if isinstance(data, list) else data.get("@graph", [data]) if isinstance(data, dict) else []
        for o in objs:
            if isinstance(o, dict) and any(k in str(o.get("@type", "")) for k in ("Article", "BlogPosting")):
                pub = pub or o.get("datePublished"); mod = mod or o.get("dateModified")
    for k, v in META.findall(html):
        if k.lower() == "article:published_time": pub = pub or v
        else: mod = mod or v
    return pub, mod

s = requests.Session(); s.headers["User-Agent"] = UA
rows = []
for i, r in enumerate(sample.itertuples()):
    ts = pd.Timestamp(r.as_of_ts).strftime("%Y%m%d%H%M%S")
    rec = {"outlet": r.outlet, "capture": str(r.as_of_ts), "stored_date": str(r.event_ts)[:10]}
    try:
        resp = s.get(f"https://web.archive.org/web/{ts}id_/{r.url}", timeout=90)
        rec["status"] = resp.status_code
        if resp.status_code == 200:
            pub, mod = times(resp.text)
            rec["pub"], rec["mod"] = pub, mod
    except Exception as e:
        rec["status"] = repr(e)[:80]
    rows.append(rec)
    if (i + 1) % 10 == 0:
        print(i + 1, "of", len(sample), flush=True)
    time.sleep(2.5)

df = pd.DataFrame(rows)
cap = pd.to_datetime(df["capture"], utc=True)
pub = pd.to_datetime(df.get("pub"), utc=True, errors="coerce")
mod = pd.to_datetime(df.get("mod"), utc=True, errors="coerce")
has_tod = pub.notna() & ~((pub.dt.hour == 0) & (pub.dt.minute == 0) & (pub.dt.second == 0))
df["lag_h"] = ((cap - pub).dt.total_seconds() / 3600).where(has_tod)
df["mod_gap_h"] = ((mod - pub).dt.total_seconds() / 3600).where(has_tod & mod.notna())
df["pub_hour"] = pub.dt.hour.where(has_tod)
def q(s): return {k: round(float(s.quantile(v)), 2) for k, v in (("q25", .25), ("median", .5), ("q75", .75), ("q90", .9))} if s.notna().any() else {}
out = {"sampled": int(len(df)), "fetched_ok": int((df["status"] == 200).sum()), "with_time_of_day": int(has_tod.sum()),
       "hours_publication_to_capture": q(df["lag_h"]),
       "by_outlet": {o: {"n": int(g["lag_h"].notna().sum()), **q(g["lag_h"])} for o, g in df.groupby("outlet")},
       "share_capture_within_1h": round(float((df["lag_h"] <= 1).sum() / max(1, df["lag_h"].notna().sum())), 3),
       "share_capture_within_6h": round(float((df["lag_h"] <= 6).sum() / max(1, df["lag_h"].notna().sum())), 3),
       "negative_lag": int((df["lag_h"] < -0.1).sum()),
       "modification_recorded": int(df["mod_gap_h"].notna().sum()),
       "share_modified_more_than_10min_after_publication": round(float((df["mod_gap_h"] > 1 / 6).sum() / max(1, df["mod_gap_h"].notna().sum())), 3),
       "publication_hour_utc": q(df["pub_hour"])}
json.dump({"summary": out, "rows": df.drop(columns=["pub_hour"]).to_dict("records")}, open(sys.argv[1], "w"), indent=1, default=str)
print(json.dumps(out, indent=1))

"""Share of price-commentary titles in the archive, known outlets against new outlets (keyword rule, no model call).

Usage: python -I agg_news_titles.py <news.csv> <out.json>
"""
import json, re, sys
import pandas as pd
news = pd.read_csv(sys.argv[1], usecols=["published_on", "title", "source"], low_memory=False)
ts = pd.to_datetime(news["published_on"], errors="coerce").dt.tz_localize("Asia/Tehran", ambiguous="NaT", nonexistent="shift_forward").dt.tz_convert("UTC")
w = news[(ts >= "2022-01-01") & (ts < "2025-01-01")].copy()
PRICE = re.compile(r"\b(price|prices|rall(y|ies|ied)|surg(e|es|ed|ing)|plung(e|es|ed|ing)|soar(s|ed|ing)?|slump(s|ed)?|jump(s|ed)?|drop(s|ped)?|"
                   r"fall(s|ing)?|fell|gain(s|ed)?|dip(s|ped)?|crash(es|ed)?|rebound(s|ed)?|breakout|support|resistance|bull(s|ish)?|bear(s|ish)?|"
                   r"all-time high|ath|prediction|technical analysis|price analysis|target|\$[0-9][0-9,.]*k?|[0-9]+%)\b", re.I)
w["price_title"] = w["title"].fillna("").map(lambda t: bool(PRICE.search(t)))
known = w["source"].isin({"cointelegraph", "coindesk", "theblock"})
by = w.groupby("source")["price_title"].agg(["size", "mean"]).sort_values("size", ascending=False)
out = {"share_price_commentary_titles": {"outlets_already_in_store": round(float(w.loc[known, "price_title"].mean()), 3),
                                         "new_outlets": round(float(w.loc[~known, "price_title"].mean()), 3)},
       "top_new_outlets": {k: {"n": int(r["size"]), "share": round(float(r["mean"]), 3)} for k, r in by[~by.index.isin(["cointelegraph", "coindesk", "theblock"])].head(15).iterrows()},
       "known": {k: {"n": int(r["size"]), "share": round(float(r["mean"]), 3)} for k, r in by[by.index.isin(["cointelegraph", "coindesk", "theblock"])].iterrows()}}
json.dump(out, open(sys.argv[2], "w"), indent=1)
print(json.dumps(out))
for t in w.loc[~known, "title"].sample(14, random_state=5):
    print("-", str(t)[:150])

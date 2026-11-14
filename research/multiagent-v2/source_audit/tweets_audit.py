"""Coverage of the Charter 4 universe by a public crypto-twitter dataset (no outcome column is read).

Usage: python -I tweets_audit.py <train.parquet> <panel.parquet> <out.json>
Dataset: Hugging Face StephanAkkerman/financial-tweets-crypto (collected live from a Discord relay, MIT licence).
Only `date` and `base` of the panel are read.
"""
import json, re, sys
import pandas as pd

d = pd.read_parquet(sys.argv[1], columns=["created_at", "user_name", "text", "tickers", "tweet_type", "channels", "n_posts"])
d["ts"] = pd.to_datetime(d["created_at"], utc=True)
out = {"rows": int(len(d)), "first": str(d["ts"].min()), "last": str(d["ts"].max()),
       "by_year": {str(k): int(v) for k, v in d["ts"].dt.year.value_counts().sort_index().items()}}
w = d[(d["ts"] >= "2022-01-01") & (d["ts"] < "2025-01-01")].copy()
out["window_rows"] = int(len(w)); out["per_day"] = round(len(w) / 1096, 1)
by_month = w.groupby(w["ts"].dt.strftime("%Y-%m")).size()
out["rows_per_month"] = {"min": int(by_month.min()), "median": float(by_month.median()), "max": int(by_month.max()), "months_with_rows": int(by_month.size)}
out["rows_by_half_year"] = {k: int(v) for k, v in w.groupby(w["ts"].dt.year.astype(str) + "H" + ((w["ts"].dt.month > 6) + 1).astype(str)).size().items()}
acc = w["user_name"].value_counts()
out["accounts"] = {"distinct": int(acc.size), "share_top10": round(float(acc.head(10).sum() / len(w)), 3), "share_top50": round(float(acc.head(50).sum() / len(w)), 3)}
chars = w["text"].fillna("").str.len()
out["text_chars"] = {str(q): int(chars.quantile(q)) for q in (0.1, 0.5, 0.9)}
out["tweet_type"] = {str(k): int(v) for k, v in w["tweet_type"].value_counts().head(5).items()}

panel = pd.read_parquet(sys.argv[2], columns=["date", "base"])
panel["date"] = pd.to_datetime(panel["date"], utc=True)
test = panel[panel["date"] >= "2023-01-01"].copy()
bases = set(panel["base"].unique()); norm = {re.sub(r"^1000+", "", b): b for b in bases}
def to_bases(t):
    if t is None:
        return []
    found = set()
    for x in t:
        x = re.sub(r"(USDT|USD|BUSD|PERP|/.*)$", "", str(x).upper().lstrip("$"))
        if x in norm:
            found.add(norm[x])
    return sorted(found)
w["bases"] = w["tickers"].map(to_bases)
out["share_with_universe_ticker"] = round(float((w["bases"].map(len) > 0).mean()), 3)
out["share_with_ticker_beyond_btc_eth"] = round(float(w["bases"].map(lambda b: any(x not in ("BTC", "ETH") for x in b)).mean()), 3)
ex = w.explode("bases").dropna(subset=["bases"]).rename(columns={"bases": "base"})[["base", "ts", "user_name"]]

def coverage(sub, label, days=1):
    d0 = sub["ts"].dt.normalize() + pd.Timedelta(days=1)
    key = set()
    for k in range(days):
        key |= set(zip(sub["base"], d0 + pd.Timedelta(days=k)))
    hit = pd.Series([(b, dd) in key for b, dd in zip(test["base"], test["date"])], index=test.index)
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
out["test_days"] = int(test["date"].nunique())
out["coverage"] = [coverage(ex, "tweets, ticker field"), coverage(ex, "tweets, ticker field", days=7)]
json.dump(out, open(sys.argv[3], "w"), indent=1)
print(json.dumps(out, indent=1))
